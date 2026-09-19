# -*- coding: utf-8 -*-
"""⑤ 정성분석 — cv1 상위 5개 조합의 예측을 **TP/FP/FN 색으로 구분**해 나란히 보인다.

교수님 0720 지시 [B]-⑤ (0727 재확인):
  "정성분석 (Top5 + 최적화 = 7개)를 Ground Truth와 나란히, TP/FP/FN을 색으로 구분"

색 규칙
  초록 = TP  맞게 찾은 블루베리
  빨강 = FN  블루베리인데 놓친 곳      ← Recall을 깎는 것
  노랑 = FP  배경인데 블루베리라 한 곳  ← Precision을 깎는 것

고르는 사진
  cv1 test 전체를 1위 모델로 훑어 IoU를 잰 뒤,
  **잘 맞힌 것 / 중간 / 못 맞힌 것** 3장을 고른다. 잘 된 것만 보이면 정성분석이 아니다.

출력
  reports/fold1/fig_05_qualitative.png        3장(사진) × (원본+정답+Top5) 격자
  reports/fold1/fig_05_qualitative_zoom.png   가장 어려운 사진 1장 확대
  output/fold1_qualitative.json               사진별·모델별 IoU/P/R 수치

GPU 1장을 몇 분 사용한다 (**추론만. 학습 아님**).
사용:  CUDA_VISIBLE_DEVICES=<빈GPU> $PY tools/make_fold1_qualitative.py
"""
import argparse
import csv
import json
import sys
from pathlib import Path

import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import numpy as np
import torch
import yaml
from matplotlib.font_manager import FontProperties
from PIL import Image
from torch.nn import functional as F

REPO = Path('/data/project/2026summer/kds0206/semantic-segmentation')
sys.path.insert(0, str(REPO))

from semseg.models import *                       # noqa: E402,F401,F403
from semseg.datasets import *                     # noqa: E402,F401,F403
from semseg.augmentations import get_eval_augmentation   # noqa: E402

REG = FontProperties(fname='/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc')
BLD = FontProperties(fname='/usr/share/fonts/opentype/noto/NotoSansCJK-Bold.ttc')

GREEN = np.array([40, 190, 90])      # TP
RED = np.array([230, 60, 60])        # FN — 놓침
YELLOW = np.array([245, 190, 40])    # FP — 잘못 찾음

HEADS = {'ccaseg', 'mask2former', 'oneformer', 'upernet'}
BACKBONES = {'resnet_50', 'resnetd_50', 'convnext_t', 'uniformer_s',
             'poolformer_s36', 'pvtv2_b2', 'mit_b2', 'swin_t'}
HDISP = {'ccaseg': 'CCASeg', 'mask2former': 'Mask2Former',
         'oneformer': 'OneFormer', 'upernet': 'UPerNet'}


def top_runs(fold: int, k: int):
    """cv<fold> 전경 IoU 상위 k개 조합을 (run, head, backbone, iou)로 돌려준다."""
    with (REPO / 'output/results_summary.csv').open() as fh:
        rows = [r for r in csv.DictReader(fh)
                if r['fold'] == str(fold) and r['head'] in HEADS
                and r['backbone'] in BACKBONES and r['fg_IoU']]
    rows.sort(key=lambda r: -float(r['fg_IoU']))
    out = []
    for r in rows:
        ck = sorted((REPO / 'output' / r['run']).glob('*_best.pth'))
        if ck:                                   # 체크포인트 없는 조합은 건너뛴다
            out.append((r['run'], r['head'], r['backbone'], float(r['fg_IoU']), ck[0]))
        if len(out) == k:
            break
    return out


def build_model(cfg_path: Path, ckpt: Path, device):
    cfg = yaml.safe_load(cfg_path.read_text())
    # BCEDice는 출력 채널이 1개다 (이진 분할)
    model = eval(cfg['MODEL']['NAME'])(cfg['MODEL']['BACKBONE'], 1)
    model.load_state_dict(torch.load(str(ckpt), map_location='cpu'))
    return model.to(device).eval(), cfg


@torch.no_grad()
def predict_all(model, ds, device):
    """데이터셋 전체 예측을 bool 배열 리스트로."""
    preds = []
    for i in range(len(ds)):
        image, label = ds[i]
        logits = model(image.unsqueeze(0).to(device))
        if logits.shape[-2:] != label.shape[-2:]:
            logits = F.interpolate(logits, size=label.shape[-2:],
                                   mode='bilinear', align_corners=False)
        preds.append((torch.sigmoid(logits) >= 0.5).squeeze().cpu().numpy().astype(bool))
    return preds


def scores(gt, pr):
    """(IoU, Precision, Recall). **정의되지 않으면 None**을 돌려준다.

    아무것도 예측하지 않으면 Precision은 분모가 0이라 정의되지 않는다.
    이걸 1.0으로 채우면 "아무것도 못 찾았는데 정밀도 100%"라는 엉뚱한 표기가 된다.
    """
    tp = int(np.logical_and(gt, pr).sum())
    fp = int(np.logical_and(~gt, pr).sum())
    fn = int(np.logical_and(gt, ~pr).sum())
    iou = tp / (tp + fp + fn) if (tp + fp + fn) else None
    prec = tp / (tp + fp) if (tp + fp) else None
    rec = tp / (tp + fn) if (tp + fn) else None
    return iou, prec, rec


def fmt(v):
    return '—' if v is None else f'{v:.3f}'


def tpfpfn(im, gt, pr):
    ov = im.copy()
    for mask, color in ((np.logical_and(gt, pr), GREEN),
                        (np.logical_and(gt, ~pr), RED),
                        (np.logical_and(~gt, pr), YELLOW)):
        ov[mask] = (0.35 * ov[mask] + 0.65 * color).astype(np.uint8)
    return ov


def display_pair(ds, idx, size=512):
    """화면용 원본 RGB와 정답 마스크."""
    ip = ds.files[idx]
    im = np.array(Image.open(ip).convert('RGB').resize((size, size), Image.BILINEAR))
    mp = ds.mask_dir / f'{ip.stem}.png' if hasattr(ds, 'mask_dir') else None
    if mp is None or not mp.exists():            # 데이터셋 구현에 따라 경로가 다를 수 있다
        cands = list((ip.parent.parent / 'masks').glob(f'{ip.stem}.*'))
        mp = cands[0] if cands else None
    gt = np.array(Image.open(mp).convert('L').resize((size, size), Image.NEAREST)) > 0
    return im, gt


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--fold', type=int, default=1)
    ap.add_argument('--topk', type=int, default=5)
    ap.add_argument('--outdir', default='reports/fold1')
    args = ap.parse_args()

    device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
    print(f'[info] device = {device}')
    outdir = REPO / args.outdir
    outdir.mkdir(parents=True, exist_ok=True)

    runs = top_runs(args.fold, args.topk)
    print(f'[info] cv{args.fold} 상위 {len(runs)}개 조합:')
    for r in runs:
        print(f'   {HDISP[r[1]]:12s} + {r[2]:15s} fg_IoU={r[3]:.4f}')

    # 데이터셋은 조합마다 같으므로 한 번만 만든다
    cfg0 = yaml.safe_load((REPO / f'configs/blueberry_{runs[0][1]}_{runs[0][2]}'
                           f'_bcedice_cv{args.fold}.yaml').read_text())
    tf = get_eval_augmentation(cfg0['TEST']['IMAGE_SIZE'],
                               seg_fill=cfg0['DATASET']['IGNORE_LABEL'], augment=False)
    ds = eval(cfg0['DATASET']['NAME'])(cfg0['DATASET']['ROOT'], 'test', tf)
    print(f'[info] cv{args.fold} test {len(ds)}장')

    all_preds, model_names = {}, []
    for run, head, backbone, iou, ckpt in runs:
        cfgp = REPO / f'configs/blueberry_{head}_{backbone}_bcedice_cv{args.fold}.yaml'
        model, _ = build_model(cfgp, ckpt, device)
        name = f'{HDISP[head]}\n+{backbone}'
        all_preds[name] = predict_all(model, ds, device)
        model_names.append(name)
        del model
        torch.cuda.empty_cache()
        print(f'[추론 완료] {run}')

    # 1위 모델 기준으로 쉬운/보통/어려운 사진 3장을 고른다
    gts = [(ds[i][1].numpy() == 1) for i in range(len(ds))]
    lead = all_preds[model_names[0]]
    ious = [ (scores(gts[i], lead[i])[0] or 0.0) for i in range(len(ds))]

    # 🔴 전경이 거의 없는 사진은 제외한다.
    #    블루베리가 한 알도 없는 사진은 union=0 이라 IoU가 1.0으로 나오고,
    #    몇 픽셀뿐인 사진은 조금만 빗나가도 IoU가 0.0이 된다.
    #    둘 다 "정성분석 대표 사진"으로는 의미가 없다.
    MIN_FG = 0.005                               # 전경이 전체 화면의 0.5% 이상
    cand = [i for i in range(len(ds)) if gts[i].mean() >= MIN_FG]
    print(f'[선별] 전경 {MIN_FG*100:.1f}% 이상인 사진 {len(cand)}/{len(ds)}장에서 고름')
    if len(cand) < 3:                            # 방어 — 거의 없으면 그냥 전체에서
        cand = list(range(len(ds)))
    order = sorted(cand, key=lambda i: ious[i])
    picks = [('어려운 사진', int(order[0])),
             ('보통 사진', int(order[len(order) // 2])),
             ('쉬운 사진', int(order[-1]))]
    print('[선택]', [(lbl, f'IoU={ious[i]:.3f}') for lbl, i in picks])

    # ---------------- 그림 ----------------
    ncol = 2 + len(model_names)
    fig, axes = plt.subplots(len(picks), ncol, figsize=(3.1 * ncol, 3.4 * len(picks)),
                             squeeze=False)
    record = {}
    for r, (label, idx) in enumerate(picks):
        im, gt_disp = display_pair(ds, idx)
        gt = gts[idx]
        axes[r][0].imshow(im)
        axes[r][0].set_ylabel(f'{label}\n(전경 {gt.mean()*100:.1f}%)',
                              fontproperties=BLD, fontsize=11)
        if r == 0:
            axes[r][0].set_title('원본', fontproperties=BLD, fontsize=12)
        ov = im.copy()
        ov[gt] = (0.3 * ov[gt] + 0.7 * GREEN).astype(np.uint8)
        axes[r][1].imshow(ov)
        if r == 0:
            axes[r][1].set_title('정답(Ground Truth)', fontproperties=BLD, fontsize=12)
        for c, name in enumerate(model_names):
            pr = all_preds[name][idx]
            iou, prec, rec = scores(gt, pr)
            ax = axes[r][2 + c]
            ax.imshow(tpfpfn(im, gt, pr))
            # 점수는 그림 **안쪽 아래**에 얹는다. xlabel로 두면 격자에서 잘린다.
            ax.text(0.5, 0.02, f'IoU {fmt(iou)} · P {fmt(prec)} · R {fmt(rec)}',
                    transform=ax.transAxes, ha='center', va='bottom',
                    fontproperties=REG, fontsize=9, color='white',
                    bbox=dict(facecolor='black', alpha=0.55, pad=2, edgecolor='none'))
            if r == 0:
                axes[r][2 + c].set_title(name, fontproperties=BLD, fontsize=11)
            record.setdefault(label, {})[name.replace('\n', ' ')] = \
                {'IoU': None if iou is None else round(iou,4),
                 'Precision': None if prec is None else round(prec,4),
                 'Recall': None if rec is None else round(rec,4)}
    for ax in axes.ravel():
        ax.set_xticks([])
        ax.set_yticks([])

    fig.suptitle('⑤ 정성분석 — cv1 상위 5개 조합  '
                 '(초록 = 맞게 찾음 · 빨강 = 놓침(Recall↓) · 노랑 = 잘못 찾음(Precision↓))',
                 fontproperties=BLD, fontsize=14)
    fig.tight_layout(rect=[0, 0, 1, 0.96])
    out = outdir / 'fig_05_qualitative.png'
    fig.savefig(out, dpi=140)
    plt.close(fig)
    print(f'[저장] {out}')

    # 가장 어려운 사진 확대판
    idx = picks[0][1]
    im, _ = display_pair(ds, idx)
    gt = gts[idx]
    fig, axes = plt.subplots(1, 2 + len(model_names),
                             figsize=(4.6 * (2 + len(model_names)), 5), squeeze=False)
    axes[0][0].imshow(im)
    axes[0][0].set_title('원본', fontproperties=BLD, fontsize=13)
    ov = im.copy()
    ov[gt] = (0.3 * ov[gt] + 0.7 * GREEN).astype(np.uint8)
    axes[0][1].imshow(ov)
    axes[0][1].set_title('정답', fontproperties=BLD, fontsize=13)
    for c, name in enumerate(model_names):
        pr = all_preds[name][idx]
        iou, prec, rec = scores(gt, pr)
        axes[0][2 + c].imshow(tpfpfn(im, gt, pr))
        axes[0][2 + c].set_title(name, fontproperties=BLD, fontsize=12)
        axes[0][2 + c].text(0.5, 0.02, f'IoU {fmt(iou)} · P {fmt(prec)} · R {fmt(rec)}',
                            transform=axes[0][2 + c].transAxes, ha='center', va='bottom',
                            fontproperties=REG, fontsize=10, color='white',
                            bbox=dict(facecolor='black', alpha=0.55, pad=2, edgecolor='none'))
    for ax in axes.ravel():
        ax.set_xticks([])
        ax.set_yticks([])
    fig.suptitle('가장 어려운 사진 확대 — 어디서 틀리는가',
                 fontproperties=BLD, fontsize=15)
    fig.tight_layout(rect=[0, 0, 1, 0.93])
    out2 = outdir / 'fig_05_qualitative_zoom.png'
    fig.savefig(out2, dpi=140)
    plt.close(fig)
    print(f'[저장] {out2}')

    jpath = REPO / 'output/fold1_qualitative.json'
    jpath.write_text(json.dumps(
        {'fold': args.fold,
         'models': [n.replace('\n', ' ') for n in model_names],
         'picked': {lbl: {'index': i, 'lead_IoU': round(ious[i], 4)} for lbl, i in picks},
         'scores': record}, ensure_ascii=False, indent=2))
    print(f'[저장] {jpath}')


if __name__ == '__main__':
    main()
