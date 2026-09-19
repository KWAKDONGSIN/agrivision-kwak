import torch
import argparse
import yaml
import time
import math
import sys
import csv
import json
import psutil  # RAM 확인용
import multiprocessing as mp
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from tabulate import tabulate
from tqdm import tqdm
from torch.utils.data import DataLoader, SequentialSampler
from pathlib import Path
from torch.utils.tensorboard import SummaryWriter
from torch.amp import GradScaler
from torch.nn import functional as F
from torch.nn.parallel import DistributedDataParallel as DDP
from torch.utils.data import DistributedSampler, RandomSampler
from torch import distributed as dist

from semseg.models import *
from semseg.datasets import *
from semseg.augmentations import get_train_augmentation, get_eval_augmentation, describe_train_augmentation
from semseg.losses import get_loss
from semseg.schedulers import get_scheduler
from semseg.optimizers import get_optimizer
from semseg.metrics import Metrics
from semseg.utils.utils import fix_seeds, setup_cudnn, cleanup_ddp, setup_ddp


def _resolve_model_name(name: str) -> str:
    return name.replace('-', '').replace('_', '')


def _safe_path(s: str) -> str:
    return str(s).replace("/", "_").replace("\\", "_").replace(" ", "")


def _use_binary_output(loss_cfg) -> bool:
    return loss_cfg['NAME'] in {'BinaryCrossEntropy', 'BCEDice', 'IoUFocal'}


def _get_model_output_channels(dataset, loss_cfg) -> int:
    return 1 if _use_binary_output(loss_cfg) else dataset.n_classes


def _prepare_pred_mask(logits: torch.Tensor, loss_cfg) -> torch.Tensor:
    if logits.ndim == 3:
        logits = logits.unsqueeze(1)
    if _use_binary_output(loss_cfg):
        return (torch.sigmoid(logits) >= 0.5).squeeze(1).long()
    return logits.softmax(dim=1).argmax(dim=1)


@torch.no_grad()
def validate(model, dataloader, device, loss_fn, loss_cfg, use_amp):
    model.eval()
    metrics = Metrics(dataloader.dataset.n_classes, dataloader.dataset.ignore_label, device)
    val_loss = 0.0
    count = 0
    
    for img, lbl in dataloader:
        img = img.to(device)
        lbl = lbl.to(device)
        
        with torch.amp.autocast('cuda', enabled=use_amp):
            logits = model(img)
            # Loss is calculated after the output has been aligned to the label.
            
            # 해상도 보정 (Interpolation)
            target_h, target_w = lbl.shape[-2], lbl.shape[-1]
            if logits.shape[-2:] != lbl.shape[-2:]:
                logits = F.interpolate(logits, size=(target_h, target_w), mode='bilinear', align_corners=False)
            
            loss = loss_fn(logits, lbl)
            preds = _prepare_pred_mask(logits, loss_cfg)

        val_loss += loss.item()
        count += 1
        metrics.update(preds, lbl)

    if dist.is_initialized():
        dist.all_reduce(metrics.hist, op=dist.ReduceOp.SUM)
        loss_tensor = torch.tensor([val_loss, count], device=device)
        dist.all_reduce(loss_tensor, op=dist.ReduceOp.SUM)
        val_loss = loss_tensor[0].item()
        count = loss_tensor[1].item()

    mean_loss = val_loss / max(count, 1)
    
    # 클래스별 IoU 및 mIoU 계산
    ious, miou = metrics.compute_iou()
    # 클래스별 F1(Dice) 및 mF1(mDice) 계산
    f1, mf1 = metrics.compute_f1()
    # 클래스별 Precision 및 mPrecision 계산
    precision, mprecision = metrics.compute_precision()
    # 클래스별 Recall 및 mRecall 계산
    recall, mrecall = metrics.compute_recall()

    pixel_acc, mean_acc = metrics.compute_pixel_acc()

    return (
        mean_loss, miou, mf1, ious, f1, mprecision, mrecall,
        precision, recall, pixel_acc, mean_acc,
    )


def _write_training_artifacts(save_dir: Path, history: list) -> None:
    """Write numeric history and convergence plots with fixed y-axes."""
    if not history:
        return

    save_dir.mkdir(parents=True, exist_ok=True)
    (save_dir / "training_history.json").write_text(
        json.dumps(history, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    with (save_dir / "training_history.csv").open(
        "w", newline="", encoding="utf-8-sig"
    ) as handle:
        writer = csv.DictWriter(handle, fieldnames=list(history[0].keys()))
        writer.writeheader()
        writer.writerows(history)

    epochs = [row["epoch"] for row in history]
    fig, (loss_ax, metric_ax) = plt.subplots(1, 2, figsize=(12, 4.5))
    for key, label in (
        ("train_loss", "train loss"),
        ("train_eval_loss", "train-eval loss"),
        ("val_loss", "validation loss"),
    ):
        values = [row.get(key) for row in history]
        if any(value is not None for value in values):
            loss_ax.plot(epochs, values, marker="o", label=label)
    loss_ax.set(xlabel="Epoch", ylabel="Loss")
    loss_ax.set_ylim(bottom=0)
    loss_ax.grid(alpha=0.25)
    loss_ax.legend()

    for key, label in (
        ("train_pixel_accuracy", "train pixel accuracy"),
        ("val_pixel_accuracy", "validation pixel accuracy"),
        ("train_fg_iou", "train foreground IoU"),
        ("val_fg_iou", "validation foreground IoU"),
    ):
        values = [row.get(key) for row in history]
        if any(value is not None for value in values):
            metric_ax.plot(epochs, values, marker="o", label=label)
    metric_ax.set(xlabel="Epoch", ylabel="Score")
    metric_ax.set_ylim(0, 1)
    metric_ax.grid(alpha=0.25)
    metric_ax.legend()

    fig.suptitle("Convergence (fixed y-axes)")
    fig.tight_layout()
    fig.savefig(save_dir / "convergence_fixed_axes.png", dpi=180)
    plt.close(fig)


def main(cfg, gpu, save_dir):
    start = time.time()
    # A fixed, configurable worker count avoids spawning every logical CPU on Windows.
    num_workers = int(cfg['TRAIN'].get('NUM_WORKERS', min(4, mp.cpu_count())))
    device = torch.device(cfg['DEVICE'])
    is_main = (not dist.is_initialized()) or dist.get_rank() == 0

    # --- [System Check] ---
    if is_main:
        print("\n" + "="*30)
        print(" >>> SYSTEM CHECK <<<")
        print(f" 1. CUDA Available: {torch.cuda.is_available()}")
        if torch.cuda.is_available():
            if device.index is not None:
                print(f" 2. Target GPU: {torch.cuda.get_device_name(device.index)} (Index: {device.index})")
            else:
                print(f" 2. Target GPU: {torch.cuda.get_device_name(0)} (Default)")
        
        ram_gb = psutil.virtual_memory().total / 1024**3
        print(f" 3. Total System RAM: {ram_gb:.1f} GB")
        print("="*30 + "\n")
    # ----------------------

    train_cfg = cfg['TRAIN']
    dataset_cfg, model_cfg = cfg['DATASET'], cfg['MODEL']
    loss_cfg, optim_cfg, sched_cfg = cfg['LOSS'], cfg['OPTIMIZER'], cfg['SCHEDULER']

    epochs, lr = train_cfg['EPOCHS'], optim_cfg['LR']

    traintransform = get_train_augmentation(
        train_cfg['IMAGE_SIZE'],
        seg_fill=dataset_cfg['IGNORE_LABEL'],
        augment=bool(train_cfg.get('AUGMENT', True)),
        aug_cfg=train_cfg.get('AUGMENTATIONS'),
    )
    # 어떤 증강이 실제로 적용됐는지 로그에 남깁니다 (논문 Methods에 그대로 옮겨 적을 수 있게)
    if is_main:
        print("[AUGMENT] " + describe_train_augmentation(
            train_cfg.get('AUGMENTATIONS'), bool(train_cfg.get('AUGMENT', True))))
    trainset = eval(dataset_cfg['NAME'])(dataset_cfg['ROOT'], 'train', traintransform)
    model_output_channels = _get_model_output_channels(trainset, loss_cfg)

    model_name = _resolve_model_name(model_cfg['NAME'])
    model_cls = eval(model_name)

    if model_name in ['CondNet', 'LightHam', 'TopFormer', 'Lawin'] and model_cfg.get('HEAD_CHANNELS') is not None:
        model = model_cls(model_cfg['BACKBONE'], model_output_channels, model_cfg['HEAD_CHANNELS'])
    else:
        model = model_cls(model_cfg['BACKBONE'], model_output_channels)

    model.init_pretrained(model_cfg.get('PRETRAINED', None))
    model = model.to(device)

    if train_cfg['DDP']:
        sampler = DistributedSampler(trainset, dist.get_world_size(), dist.get_rank(), shuffle=True)
        model = DDP(model, device_ids=[gpu])
    else:
        sampler = RandomSampler(trainset)

    trainloader = DataLoader(
        trainset,
        batch_size=train_cfg['BATCH_SIZE'],
        num_workers=num_workers,
        drop_last=True,
        pin_memory=True,
        sampler=sampler
    )

    iters_per_epoch = len(trainset) // train_cfg['BATCH_SIZE']
    accum_enabled = bool(train_cfg.get('ACCUM_ENABLE', False))
    accum_steps = max(1, int(train_cfg.get('ACCUM_STEPS', 1))) if accum_enabled else 1
    optimizer_steps_per_epoch = math.ceil(iters_per_epoch / accum_steps)
    loss_fn = get_loss(
        loss_cfg['NAME'],
        trainset.ignore_label,
        None,
        pos_weight=loss_cfg.get('POS_WEIGHT', 1.0),
        alpha=loss_cfg.get('ALPHA', 0.25),
        gamma=loss_cfg.get('GAMMA', 2.0),
        thresh=loss_cfg.get('THRESH', 0.7),
        smoothing=loss_cfg.get('SMOOTHING', 0.1),
        bce_weight=loss_cfg.get('BCE_WEIGHT', 1.0),
        dice_weight=loss_cfg.get('DICE_WEIGHT', 1.0),
        iou_weight=loss_cfg.get('IOU_WEIGHT', 1.0),
        focal_weight=loss_cfg.get('FOCAL_WEIGHT', 1.0),
        smooth=loss_cfg.get('SMOOTH', 1e-6),
    )
    optimizer = get_optimizer(model, optim_cfg['NAME'], lr, optim_cfg['WEIGHT_DECAY'])
    scheduler = get_scheduler(
        sched_cfg['NAME'],
        optimizer,
        epochs * optimizer_steps_per_epoch,
        sched_cfg['POWER'],
        optimizer_steps_per_epoch * sched_cfg['WARMUP'],
        sched_cfg['WARMUP_RATIO']
    )

    scaler = GradScaler('cuda', enabled=train_cfg['AMP'])
    writer = SummaryWriter(str(save_dir / 'logs'))

    if is_main and accum_steps > 1:
        print(f"[Train] Gradient accumulation enabled: ACCUM_STEPS={accum_steps} "
              f"(effective batch = BATCH_SIZE * ACCUM_STEPS = {train_cfg['BATCH_SIZE'] * accum_steps})")

    # Gradient clipping — 0 이하이면 비활성(기존 동작과 동일).
    # CCASeg 계열은 LKCA의 곱셈 어텐션 때문에 활성값이 커져 loss가 nan/inf로 발산한 사례가 있어,
    # 그런 조합에서만 config로 켜서 쓴다. 예) TRAIN: { GRAD_CLIP: 1.0 }
    grad_clip = float(train_cfg.get('GRAD_CLIP', 0.0))
    if is_main and grad_clip > 0:
        print(f"[Train] Gradient clipping enabled: max_norm={grad_clip}")

    early_stop_cfg = train_cfg.get('EARLY_STOP', {})
    early_stop_enabled = bool(early_stop_cfg.get('ENABLE', False))
    early_stop_patience = int(early_stop_cfg.get('PATIENCE', 10))
    early_stop_min_delta = float(early_stop_cfg.get('MIN_DELTA', 0.0))
    early_stop_monitor = str(early_stop_cfg.get('MONITOR', 'val_loss')).lower()
    early_stop_check_interval = int(early_stop_cfg.get('CHECK_INTERVAL', train_cfg.get('EVAL_INTERVAL', 1)))
    early_stop_start_epoch = int(early_stop_cfg.get('START_EPOCH', 0))
    early_stop_check_interval = max(1, early_stop_check_interval)

    val_loader = None
    eval_transform = None
    if early_stop_enabled or train_cfg.get('EVAL_INTERVAL', 1) > 0:
        eval_size = cfg.get('EVAL', {}).get('IMAGE_SIZE', train_cfg['IMAGE_SIZE'])
        eval_transform = get_eval_augmentation(
            eval_size,
            seg_fill=dataset_cfg['IGNORE_LABEL'],
            use_crop=bool(cfg.get('EVAL', {}).get('CROP', False)),
            augment=bool(cfg.get('EVAL', {}).get('AUGMENT', False)),
        )
        val_split = cfg.get('EVAL', {}).get('SPLIT', 'val')
        valset = eval(dataset_cfg['NAME'])(dataset_cfg['ROOT'], val_split, eval_transform)

        if train_cfg['DDP']:
            val_sampler = DistributedSampler(valset, dist.get_world_size(), dist.get_rank(), shuffle=False)
        else:
            val_sampler = SequentialSampler(valset)

        val_loader = DataLoader(valset, batch_size=1, num_workers=num_workers, pin_memory=True, sampler=val_sampler)

    # 학습 중 train set 평가 (augmentation OFF, val과 동일 조건) — overfitting 모니터링용, early stopping에 영향 X
    eval_train_cfg = train_cfg.get('EVAL_TRAIN_SPLIT', {})
    eval_train_enabled = bool(eval_train_cfg.get('ENABLE', True))
    eval_train_interval = max(1, int(eval_train_cfg.get('INTERVAL', early_stop_check_interval)))
    train_eval_loader = None
    train_evalset = None
    if eval_train_enabled:
        if eval_transform is None:
            eval_size = cfg.get('EVAL', {}).get('IMAGE_SIZE', train_cfg['IMAGE_SIZE'])
            eval_transform = get_eval_augmentation(
                eval_size,
                seg_fill=dataset_cfg['IGNORE_LABEL'],
                use_crop=bool(cfg.get('EVAL', {}).get('CROP', False)),
                augment=bool(cfg.get('EVAL', {}).get('AUGMENT', False)),
            )
        train_evalset = eval(dataset_cfg['NAME'])(dataset_cfg['ROOT'], 'train', eval_transform)
        if train_cfg['DDP']:
            train_eval_sampler = DistributedSampler(train_evalset, dist.get_world_size(), dist.get_rank(), shuffle=False)
        else:
            train_eval_sampler = SequentialSampler(train_evalset)
        train_eval_loader = DataLoader(train_evalset, batch_size=1, num_workers=num_workers, pin_memory=True, sampler=train_eval_sampler)
        if is_main:
            print(f"[Train] EVAL_TRAIN_SPLIT enabled (every {eval_train_interval} epoch(s)) — overfitting monitor, "
                  f"does NOT affect early stopping")

    # 학습 중 test set loss 모니터링 (수렴 곡선용, early stopping에는 영향 X)
    test_during_train_cfg = train_cfg.get('TEST_DURING_TRAIN', {})
    test_during_train_enabled = bool(test_during_train_cfg.get('ENABLE', False))
    test_during_train_interval = max(1, int(test_during_train_cfg.get('INTERVAL', early_stop_check_interval)))
    test_loader = None
    if test_during_train_enabled:
        if eval_transform is None:
            eval_size = cfg.get('EVAL', {}).get('IMAGE_SIZE', train_cfg['IMAGE_SIZE'])
            eval_transform = get_eval_augmentation(
                eval_size,
                seg_fill=dataset_cfg['IGNORE_LABEL'],
                use_crop=bool(cfg.get('EVAL', {}).get('CROP', False)),
                augment=bool(cfg.get('EVAL', {}).get('AUGMENT', False)),
            )
        testset = eval(dataset_cfg['NAME'])(dataset_cfg['ROOT'], 'test', eval_transform)
        if train_cfg['DDP']:
            test_sampler = DistributedSampler(testset, dist.get_world_size(), dist.get_rank(), shuffle=False)
        else:
            test_sampler = SequentialSampler(testset)
        test_loader = DataLoader(testset, batch_size=1, num_workers=num_workers, pin_memory=True, sampler=test_sampler)
        if is_main:
            print(f"[Train] TEST_DURING_TRAIN enabled (every {test_during_train_interval} epoch(s)) — logged to TB only, "
                  f"does NOT affect early stopping")

    best_score = None
    best_epoch = -1  # epoch index of last improvement (for epoch-based patience)

    # 통계 기록 리스트
    ram_usage_history = []
    vram_usage_history = []
    epoch_times = []  # [추가] 에포크당 소요 시간 기록
    history = []

    for epoch in range(epochs):
        epoch_start = time.time()  # [추가] 에포크 시작 시간 기록
        
        model.train()
        if train_cfg['DDP']:
            sampler.set_epoch(epoch)
        
        if torch.cuda.is_available():
            torch.cuda.reset_peak_memory_stats(device)

        train_loss = 0.0
        
        pbar = tqdm(
            enumerate(trainloader),
            total=iters_per_epoch,
            desc=f"Epoch: [{epoch+1}/{epochs}] Iter: [{0}/{iters_per_epoch}] LR: {lr:.8f} Loss: {train_loss:.8f}",
            disable=not is_main
        )

        optimizer.zero_grad(set_to_none=True)

        for it, (img, lbl) in pbar:
            img = img.to(device)
            lbl = lbl.to(device)

            with torch.amp.autocast('cuda', enabled=train_cfg['AMP']):
                logits = model(img)
                if logits.shape[-2:] != lbl.shape[-2:]:
                    logits = F.interpolate(logits, size=lbl.shape[-2:], mode='bilinear', align_corners=False)
                loss = loss_fn(logits, lbl)

            unscaled_loss_value = loss.item()
            if accum_steps > 1:
                loss = loss / accum_steps

            scaler.scale(loss).backward()

            do_step = ((it + 1) % accum_steps == 0) or ((it + 1) == iters_per_epoch)
            if do_step:
                if grad_clip > 0:
                    # AMP 사용 시 clip 전에 반드시 unscale 해야 실제 gradient 크기로 자를 수 있다
                    scaler.unscale_(optimizer)
                    torch.nn.utils.clip_grad_norm_(model.parameters(), grad_clip)
                scaler.step(optimizer)
                scaler.update()
                optimizer.zero_grad(set_to_none=True)
                scheduler.step()
            torch.cuda.synchronize()

            lr_list = scheduler.get_lr()
            lr = sum(lr_list) / len(lr_list)
            train_loss += unscaled_loss_value

            if is_main:
                ram_used = psutil.virtual_memory().used / 1024**3  # GB
                gpu_mem = 0.0
                if torch.cuda.is_available():
                    gpu_mem = torch.cuda.memory_allocated(device) / 1024**2 # MB

                # 기록 저장
                ram_usage_history.append(ram_used)
                vram_usage_history.append(gpu_mem)

                pbar.set_description(
                    f"Epoch: [{epoch+1}/{epochs}] Iter: [{it+1}/{iters_per_epoch}] LR: {lr:.8f} Loss: {train_loss/(it+1):.8f}"
                )
                
                pbar.set_postfix({
                    'GPU': f'{gpu_mem:.0f}MB', 
                    'RAM': f'{ram_used:.1f}GB'
                })

        train_loss /= (it + 1)
        if is_main:
            writer.add_scalar('train/loss', train_loss, epoch)
        torch.cuda.empty_cache()

        # [추가] 에포크 종료 후 시간 계산
        epoch_end = time.time()
        epoch_duration = epoch_end - epoch_start
        epoch_times.append(epoch_duration) # 리스트에 저장

        # ---------------------------
        # Train-split 평가 (augmentation OFF, val과 동일 조건) — overfitting 모니터
        # ---------------------------
        run_train_eval = (train_eval_loader is not None) and ((epoch + 1) % eval_train_interval == 0)
        tr_loss = tr_fg_iou = tr_pixel_acc = None
        if run_train_eval:
            tr_loss, tr_miou, tr_mdice, tr_ious, tr_dices, tr_mprecision, tr_mrecall, tr_precisions, tr_recalls, tr_pixel_acc, tr_mean_acc = validate(
                model, train_eval_loader, device, loss_fn, loss_cfg, train_cfg['AMP']
            )
            tr_fg_iou = float(tr_ious[1]) if len(tr_ious) >= 2 else None
            if is_main:
                tqdm.write("\n" + "-" * 60)
                tqdm.write(f" [Epoch {epoch+1} Train-eval Report]")
                tqdm.write(f" Train Loss: {tr_loss:.6f} | mIoU: {tr_miou:.4f} | mDice: {tr_mdice:.4f} | mPrec: {tr_mprecision:.4f} | mRecall: {tr_mrecall:.4f}")
                if len(tr_ious) >= 2:
                    tqdm.write(f" Foreground (class 1) | IoU: {float(tr_ious[1]):.4f} | Dice: {float(tr_dices[1]):.4f} | Prec: {float(tr_precisions[1]):.4f} | Recall: {float(tr_recalls[1]):.4f}")
                header = ['Class', 'IoU', 'Dice', 'Precision', 'Recall']
                table_data = []
                for cls_name, iou_score, dice_score, prec_score, rec_score in zip(train_evalset.CLASSES, tr_ious, tr_dices, tr_precisions, tr_recalls):
                    table_data.append([cls_name, f"{iou_score:.4f}", f"{dice_score:.4f}", f"{prec_score:.4f}", f"{rec_score:.4f}"])
                tqdm.write(tabulate(table_data, headers=header, tablefmt='simple'))
                tqdm.write("-" * 60)

                writer.add_scalar('train_eval/loss', tr_loss, epoch)
                writer.add_scalar('train_eval/mIoU', tr_miou, epoch)
                writer.add_scalar('train_eval/mDice', tr_mdice, epoch)
                writer.add_scalar('train_eval/mPrecision', tr_mprecision, epoch)
                writer.add_scalar('train_eval/mRecall', tr_mrecall, epoch)
                writer.add_scalar('train_eval/pixel_accuracy', tr_pixel_acc, epoch)
                if len(tr_ious) >= 2:
                    writer.add_scalar('train_eval/fg_IoU', float(tr_ious[1]), epoch)
                    writer.add_scalar('train_eval/fg_Dice', float(tr_dices[1]), epoch)
                    writer.add_scalar('train_eval/fg_Precision', float(tr_precisions[1]), epoch)
                    writer.add_scalar('train_eval/fg_Recall', float(tr_recalls[1]), epoch)

        # ---------------------------
        # Validation 및 결과 출력
        # ---------------------------
        stop_training = False
        run_validation = (val_loader is not None) and ((epoch + 1) % early_stop_check_interval == 0)

        v_loss = v_fg_iou = v_pixel_acc = None
        if run_validation:
            v_loss, v_miou, v_mdice, v_ious, v_dices, v_mprecision, v_mrecall, v_precisions, v_recalls, v_pixel_acc, v_mean_acc = validate(model, val_loader, device, loss_fn, loss_cfg, train_cfg['AMP'])
            
            if is_main:
                # 1. 터미널에 줄 긋기
                tqdm.write("\n" + "-" * 60)
                tqdm.write(f" [Epoch {epoch+1} Validation Report]")
                # [추가] 현재 에포크 소요 시간 출력
                tqdm.write(f" Time Taken: {epoch_duration:.2f} s")
                tqdm.write(f" Val Loss: {v_loss:.6f} | mIoU: {v_miou:.4f} | mDice: {v_mdice:.4f} | mPrec: {v_mprecision:.4f} | mRecall: {v_mrecall:.4f}")
                # Foreground (class 1) metrics — for binary blueberry seg, this is the meaningful number;
                # mIoU/mDice include background which is ~0.99 and dominates the average.
                if len(v_ious) >= 2:
                    fg_iou = float(v_ious[1])
                    v_fg_iou = fg_iou
                    fg_dice = float(v_dices[1])
                    fg_prec = float(v_precisions[1])
                    fg_recall = float(v_recalls[1])
                    tqdm.write(f" Foreground (class 1) | IoU: {fg_iou:.4f} | Dice: {fg_dice:.4f} | Prec: {fg_prec:.4f} | Recall: {fg_recall:.4f}")

                # 2. 클래스별 IoU, Dice, Precision, Recall 표 출력
                header = ['Class', 'IoU', 'Dice', 'Precision', 'Recall']
                table_data = []
                for cls_name, iou_score, dice_score, prec_score, rec_score in zip(valset.CLASSES, v_ious, v_dices, v_precisions, v_recalls):
                    table_data.append([cls_name, f"{iou_score:.4f}", f"{dice_score:.4f}", f"{prec_score:.4f}", f"{rec_score:.4f}"])
                
                tqdm.write(tabulate(table_data, headers=header, tablefmt='simple'))
                tqdm.write("-" * 60 + "\n")

                # 3. Tensorboard 기록
                writer.add_scalar('val/loss', v_loss, epoch)
                writer.add_scalar('val/mIoU', v_miou, epoch)
                writer.add_scalar('val/mDice', v_mdice, epoch)
                writer.add_scalar('val/mPrecision', v_mprecision, epoch)
                writer.add_scalar('val/mRecall', v_mrecall, epoch)
                writer.add_scalar('val/pixel_accuracy', v_pixel_acc, epoch)
                
                for cls_name, iou_score in zip(valset.CLASSES, v_ious):
                    writer.add_scalar(f"val/IoU_{cls_name}", iou_score, epoch)

                if len(v_ious) >= 2:
                    writer.add_scalar('val/fg_IoU', float(v_ious[1]), epoch)
                    writer.add_scalar('val/fg_Dice', float(v_dices[1]), epoch)
                    writer.add_scalar('val/fg_Precision', float(v_precisions[1]), epoch)
                    writer.add_scalar('val/fg_Recall', float(v_recalls[1]), epoch)

                # Early Stopping 로직
                if early_stop_monitor == 'val_loss':
                    current_metric = v_loss
                elif early_stop_monitor == 'val_iou':
                    current_metric = v_miou 
                    writer.add_scalar(f"val/{early_stop_monitor}", current_metric, epoch)
                else: 
                    current_metric = train_loss

                is_minimize = early_stop_monitor in {'train_loss', 'val_loss'}
                if is_minimize:
                    improved = (best_score is None) or (current_metric < (best_score - early_stop_min_delta))
                else:
                    improved = (best_score is None) or (current_metric > (best_score + early_stop_min_delta))

                if improved:
                    best_score = current_metric
                    best_epoch = epoch
                    safe_backbone = _safe_path(model_cfg['BACKBONE'])
                    save_dir.mkdir(parents=True, exist_ok=True)
                    torch.save(
                        model.module.state_dict() if train_cfg['DDP'] else model.state_dict(),
                        save_dir / f"{model_cfg['NAME']}_{safe_backbone}_{dataset_cfg['NAME']}_best.pth",
                    )
                    tqdm.write(f" >>> New Best Model Saved! ({early_stop_monitor}: {best_score:.6f})")
                else:
                    epochs_since_best = (epoch - best_epoch) if best_epoch >= 0 else 0
                    tqdm.write(f" No Improvement. Epochs since best: {epochs_since_best}/{early_stop_patience} (Best: {best_score:.6f})")
                    if early_stop_enabled and (epoch + 1) >= early_stop_start_epoch and best_epoch >= 0 and epochs_since_best >= early_stop_patience:
                        stop_training = True

        # Test set monitoring — TB에만 기록, early stopping과 무관
        run_test = (test_loader is not None) and ((epoch + 1) % test_during_train_interval == 0)
        if run_test:
            t_loss, t_miou, t_mdice, t_ious, t_dices, t_mprecision, t_mrecall, t_precisions, t_recalls, t_pixel_acc, t_mean_acc = validate(
                model, test_loader, device, loss_fn, loss_cfg, train_cfg['AMP']
            )
            if is_main:
                tqdm.write(f" [Epoch {epoch+1} Test ] Loss: {t_loss:.6f} | mIoU: {t_miou:.4f} | mDice: {t_mdice:.4f}")
                if len(t_ious) >= 2:
                    tqdm.write(f" [Epoch {epoch+1} Test ] fg IoU: {float(t_ious[1]):.4f} | fg Dice: {float(t_dices[1]):.4f}")
                writer.add_scalar('test/loss', t_loss, epoch)
                writer.add_scalar('test/mIoU', t_miou, epoch)
                writer.add_scalar('test/mDice', t_mdice, epoch)
                writer.add_scalar('test/mPrecision', t_mprecision, epoch)
                writer.add_scalar('test/mRecall', t_mrecall, epoch)
                writer.add_scalar('test/pixel_accuracy', t_pixel_acc, epoch)
                if len(t_ious) >= 2:
                    writer.add_scalar('test/fg_IoU', float(t_ious[1]), epoch)
                    writer.add_scalar('test/fg_Dice', float(t_dices[1]), epoch)

        if is_main:
            history.append(
                {
                    "epoch": epoch + 1,
                    "learning_rate": float(lr),
                    "epoch_seconds": float(epoch_duration),
                    "train_loss": float(train_loss),
                    "train_eval_loss": None if tr_loss is None else float(tr_loss),
                    "val_loss": None if v_loss is None else float(v_loss),
                    "train_pixel_accuracy": None if tr_pixel_acc is None else float(tr_pixel_acc),
                    "val_pixel_accuracy": None if v_pixel_acc is None else float(v_pixel_acc),
                    "train_fg_iou": tr_fg_iou,
                    "val_fg_iou": v_fg_iou,
                }
            )
            _write_training_artifacts(save_dir, history)
        
        if train_cfg['DDP']:
            stop_signal = torch.tensor(1 if stop_training else 0).to(device)
            dist.all_reduce(stop_signal, op=dist.ReduceOp.MAX)
            stop_training = stop_signal.item() == 1

        if stop_training:
            if is_main:
                print("Early stopping triggered. Stopping training.")
            break

    if is_main:
        safe_backbone = _safe_path(model_cfg['BACKBONE'])
        save_dir.mkdir(parents=True, exist_ok=True)
        torch.save(
            model.module.state_dict() if train_cfg['DDP'] else model.state_dict(),
            save_dir / f"{model_cfg['NAME']}_{safe_backbone}_{dataset_cfg['NAME']}.pth",
        )
        writer.close()

    pbar.close()
    end = time.gmtime(time.time() - start)

    if is_main:
        # 최종 통계 계산 및 출력
        table = [['Total Training Time', time.strftime("%H:%M:%S", end)]]
        
        # [추가] 평균 에포크 시간 계산
        if epoch_times:
            avg_epoch_time = sum(epoch_times) / len(epoch_times)
            table.append(['Average Epoch Time', f"{avg_epoch_time:.2f} s"])

        if ram_usage_history:
            avg_ram = sum(ram_usage_history) / len(ram_usage_history)
            table.append(['Average RAM Usage', f"{avg_ram:.2f} GB"])
            
        if vram_usage_history:
            avg_vram = sum(vram_usage_history) / len(vram_usage_history)
            max_vram = max(vram_usage_history)
            table.append(['Average VRAM Usage', f"{avg_vram:.2f} MB"])
            table.append(['Peak VRAM Usage', f"{max_vram:.2f} MB"])

        print(tabulate(table, numalign='right'))


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--cfg', type=str, default='configs/custom.yaml', help='Configuration file to use')
    args = parser.parse_args()

    with open(args.cfg, encoding='utf-8') as f:
        cfg = yaml.load(f, Loader=yaml.SafeLoader)

    fix_seeds(3407)
    setup_cudnn()
    gpu = setup_ddp()

    save_dir = Path(cfg['SAVE_DIR'])
    save_dir.mkdir(parents=True, exist_ok=True)

    main(cfg, gpu, save_dir)
    cleanup_ddp()
