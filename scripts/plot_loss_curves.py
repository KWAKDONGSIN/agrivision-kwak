"""
Plot train / val / test loss convergence curves from TensorBoard event files.

Reads scalars logged by tools/train.py (train/loss, val/loss, test/loss, and
optionally val/mIoU, test/mIoU, val/fg_IoU, test/fg_IoU) and renders matplotlib
figures suitable for reports.

Usage examples:
    # Single experiment
    python tools/plot_loss_curves.py \
        --logdir output/upernet_pvtv2_b2_bcedice_cv1/logs \
        --out output/upernet_pvtv2_b2_bcedice_cv1/loss_curves.png

    # Compare multiple experiments (one figure per metric)
    python tools/plot_loss_curves.py \
        --logdir output/upernet_pvtv2_b2_bcedice_cv1/logs \
                 output/mask2former_pvtv2_b2_bcedice_cv1/logs \
        --labels UperNet Mask2Former \
        --out output/compare_loss.png \
        --compare
"""
import argparse
from pathlib import Path

import matplotlib.pyplot as plt
from tensorboard.backend.event_processing.event_accumulator import EventAccumulator


SCALAR_TAGS = {
    'train_loss': 'train/loss',
    'val_loss':   'val/loss',
    'test_loss':  'test/loss',
    'val_miou':   'val/mIoU',
    'test_miou':  'test/mIoU',
    'val_fg_iou': 'val/fg_IoU',
    'test_fg_iou': 'test/fg_IoU',
    # 2026-07-27 교수님 지시: "밸리데이션이랑 트레인 정확도 ... 수렴하는지를 봐야 되니까"
    # train.py 는 train_eval/* 로 학습셋 자체의 지표를 이미 기록하고 있으나
    # 이 스크립트가 읽지 않아 그래프에 나오지 않았다.
    'train_eval_loss':   'train_eval/loss',
    'train_eval_miou':   'train_eval/mIoU',
    'train_eval_fg_iou': 'train_eval/fg_IoU',
}


def load_scalars(logdir: Path) -> dict:
    """Return {key: ([steps], [values])} for tags present in the run."""
    ea = EventAccumulator(str(logdir), size_guidance={'scalars': 0})
    ea.Reload()
    available = set(ea.Tags().get('scalars', []))
    out = {}
    for key, tag in SCALAR_TAGS.items():
        if tag not in available:
            continue
        events = ea.Scalars(tag)
        steps = [e.step for e in events]
        vals = [e.value for e in events]
        out[key] = (steps, vals)
    return out


def plot_single(scalars: dict, title: str, out_path: Path) -> None:
    fig, axes = plt.subplots(1, 2, figsize=(13, 4.5))

    ax = axes[0]
    # train/loss 는 '학습 도중' 누적 평균이라 증강·dropout이 켜진 상태의 값이고,
    # train_eval/loss 는 학습이 끝난 뒤 eval 모드로 다시 잰 값이다.
    # 0727 미팅에서 "train보다 val loss가 더 작다"고 지적된 현상은 이 둘을 나란히
    # 그려 봐야 진단이 된다 (train_eval < val 이면 정상, 여전히 뒤집혀 있으면 진짜 문제).
    for key, color, label in [
        ('train_loss', 'tab:blue',   'train (running)'),
        ('train_eval_loss', 'tab:cyan', 'train (eval mode)'),
        ('val_loss',   'tab:orange', 'val'),
        ('test_loss',  'tab:green',  'test'),
    ]:
        if key in scalars:
            steps, vals = scalars[key]
            ax.plot(steps, vals, color=color, label=label, linewidth=1.5)
    ax.set_xlabel('Epoch')
    ax.set_ylabel('Loss')
    ax.set_title(f'{title} — loss')
    ax.grid(True, alpha=0.3)
    ax.legend()

    ax = axes[1]
    plotted = False
    for key, color, label in [
        ('train_eval_fg_iou', 'tab:blue', 'train fg IoU'),
        ('val_fg_iou',  'tab:orange', 'val fg IoU'),
        ('test_fg_iou', 'tab:green',  'test fg IoU'),
        ('train_eval_miou', 'tab:cyan', 'train mIoU'),
        ('val_miou',    'tab:red',    'val mIoU'),
        ('test_miou',   'tab:purple', 'test mIoU'),
    ]:
        if key in scalars:
            steps, vals = scalars[key]
            ax.plot(steps, vals, color=color, label=label, linewidth=1.5)
            plotted = True
    ax.set_xlabel('Epoch')
    ax.set_ylabel('IoU')
    ax.set_title(f'{title} — IoU')
    ax.grid(True, alpha=0.3)
    if plotted:
        ax.legend()

    fig.tight_layout()
    out_path.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(out_path, dpi=150)
    print(f'[plot] saved {out_path}')
    plt.close(fig)


def plot_compare(runs: list, out_path: Path, share_y: bool = False,
                 loss_ylim=None) -> None:
    """runs: list of (label, scalars_dict).

    share_y=True 면 loss 계열 subplot끼리 y축 범위를 하나로 맞춘다.
    2026-07-27 교수님 지적: "지금 저 와이 축이 다 다르니까 사실은 너무 비교가
    안 되는 것 같아요. 와이 축을 고정 시켜놓고요."
    """
    metrics = [
        ('train_loss', 'Train loss'),
        ('train_eval_loss', 'Train loss (eval mode)'),
        ('val_loss',   'Val loss'),
        ('test_loss',  'Test loss'),
        ('train_eval_fg_iou', 'Train fg IoU'),
        ('val_fg_iou', 'Val fg IoU'),
        ('test_fg_iou', 'Test fg IoU'),
    ]
    present = [(k, t) for k, t in metrics if any(k in s for _, s in runs)]
    n = len(present)
    cols = min(3, n)
    rows = (n + cols - 1) // cols
    fig, axes = plt.subplots(rows, cols, figsize=(5.5 * cols, 4 * rows), squeeze=False)

    for idx, (key, title) in enumerate(present):
        ax = axes[idx // cols][idx % cols]
        for label, scalars in runs:
            if key not in scalars:
                continue
            steps, vals = scalars[key]
            ax.plot(steps, vals, label=label, linewidth=1.5)
        ax.set_xlabel('Epoch')
        ax.set_ylabel(title)
        ax.set_title(title)
        ax.grid(True, alpha=0.3)
        ax.legend()

    # --- y축 통일 (교수님 지시) -------------------------------------------
    # loss 계열끼리, IoU 계열끼리 각각 같은 범위를 쓰게 한다.
    if share_y:
        for family, keys in (('loss', [k for k, _ in present if k.endswith('loss')]),
                             ('iou',  [k for k, _ in present if k.endswith('iou')])):
            vals = [v for key in keys for _, s in runs if key in s for v in s[key][1]]
            if not vals:
                continue
            if family == 'loss':
                lo, hi = (loss_ylim if loss_ylim else (0.0, max(vals) * 1.05))
            else:
                lo, hi = 0.0, 1.0                   # IoU는 0~1이 자연스러운 고정 범위
            for idx, (key, _) in enumerate(present):
                if key in keys:
                    axes[idx // cols][idx % cols].set_ylim(lo, hi)

    for idx in range(len(present), rows * cols):
        axes[idx // cols][idx % cols].axis('off')

    fig.tight_layout()
    out_path.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(out_path, dpi=150)
    print(f'[plot] saved {out_path}')
    plt.close(fig)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--logdir', nargs='+', required=True,
                    help='One or more TensorBoard logdirs (output/<exp>/logs).')
    ap.add_argument('--labels', nargs='+', default=None,
                    help='Optional labels matching --logdir order.')
    ap.add_argument('--out', type=str, required=True,
                    help='Output figure path (.png/.pdf). For per-run mode without '
                         '--compare and multiple logdirs, this is a directory.')
    ap.add_argument('--compare', action='store_true',
                    help='Overlay all runs on the same figure (one subplot per metric).')
    ap.add_argument('--no-test', action='store_true',
                    help='Skip test/* curves even if present in the event files.')
    ap.add_argument('--share-y', action='store_true',
                    help='Unify the y-axis across loss subplots (and fix IoU to 0-1). '
                         '2026-07-27 교수님 지시 — y축이 제각각이면 비교가 안 된다.')
    ap.add_argument('--loss-ylim', type=float, nargs=2, default=None,
                    metavar=('LO', 'HI'),
                    help='Explicit y-range for loss subplots, e.g. --loss-ylim 0 1.2')
    args = ap.parse_args()

    logdirs = [Path(p) for p in args.logdir]
    labels = args.labels or [p.parent.name for p in logdirs]
    if len(labels) != len(logdirs):
        raise SystemExit('--labels count must match --logdir count')

    runs = []
    for label, ld in zip(labels, logdirs):
        scalars = load_scalars(ld)
        if args.no_test:
            scalars = {k: v for k, v in scalars.items() if not k.startswith('test_')}
        if not scalars:
            print(f'[warn] no scalars found in {ld}')
        runs.append((label, scalars))

    out = Path(args.out)
    if args.compare:
        plot_compare(runs, out, share_y=args.share_y, loss_ylim=args.loss_ylim)
    else:
        if len(runs) == 1:
            plot_single(runs[0][1], runs[0][0], out)
        else:
            out.mkdir(parents=True, exist_ok=True)
            for label, scalars in runs:
                plot_single(scalars, label, out / f'{label}.png')


if __name__ == '__main__':
    main()
