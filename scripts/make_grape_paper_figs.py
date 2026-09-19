# -*- coding: utf-8 -*-
"""논문(main.tex)이 참조하는 **포도 그림**을 실제 데이터·실제 예측으로 만든다.

main.tex 의 그림 자리는 `\\IfFileExists` 로 감싸여 있어 파일이 없으면 빈 액자가 찍힌다.
지금까지 포도 자리가 전부 빈 액자였다. 이 스크립트가 그 파일들을 채운다.

만드는 것 (경로는 main.tex 가 참조하는 그대로)
  문서/260730_논문초안_LaTeX/figures/
    ├── datasets/grape_image.jpg          Fig.2 (g) 포도 원본
    ├── datasets/grape_mask.png           Fig.2 (h) 포도 정답 마스크
    └── results/qualitative_grape.pdf     정성분석 3장 x (원본/정답/예측/오차)

색 규칙 (fold1 정성분석과 동일)
  초록 = TP 맞음 / 빨강 = FN 놓침 / 노랑 = FP 헛짚음

⚠️ 평가와 동일하게 **CenterCrop 512** 영역만 보인다. 채점되는 영역이 거기이기 때문.
   (원본 576x1024 중 가운데 512x512 = 화면의 약 44%)

GPU 1장을 몇 초 사용한다 (**추론만. 학습 아님**).
사용:  CUDA_VISIBLE_DEVICES=<빈GPU> $PY tools/make_grape_paper_figs.py
"""
import json
import sys
from pathlib import Path

import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import numpy as np
import torch
import yaml
from PIL import Image
from torch.nn import functional as F

REPO = Path('/data/project/2026summer/kds0206/semantic-segmentation')
sys.path.insert(0, str(REPO))

from semseg.models import *                    # noqa: E402,F401,F403
from semseg.augmentations import get_val_augmentation   # noqa: E402

PAPER = Path('/data/project/2026summer/kds0206/문서/260730_논문초안_LaTeX')
CFG = REPO / 'configs/grape_grid_0731/grape_unet_convnext_t_cv1.yaml'
CKPT = REPO / 'output/grape_grid_runs/grape_unet_convnext_t_cv1/BackboneUNet_ConvNeXt-T_OrchardBinaryDataset_best.pth'

GREEN = np.array([40, 190, 90], dtype=np.float32)     # TP
RED = np.array([230, 60, 60], dtype=np.float32)       # FN 놓침
YELLOW = np.array([245, 190, 40], dtype=np.float32)   # FP 헛짚음
CROP = 512


def center_crop_np(arr, size=CROP):
    h, w = arr.shape[:2]
    top, left = (h - size) // 2, (w - size) // 2
    return arr[top:top + size, left:left + size]


def load_model(cfg, device):
    model = eval(cfg['MODEL']['NAME'])(cfg['MODEL']['BACKBONE'], 1)
    state = torch.load(CKPT, map_location='cpu', weights_only=True)
    model.load_state_dict(state)
    return model.to(device).eval()


def predict(model, img_rgb, device, tf):
    """img_rgb: uint8 HxWx3 원본 → CenterCrop 512 예측 확률맵(512x512)."""
    t = torch.from_numpy(img_rgb).permute(2, 0, 1)                  # 3,H,W uint8
    dummy = torch.zeros(1, *t.shape[1:], dtype=torch.long)
    t, _ = tf(t, dummy)                                             # CenterCrop + Normalize
    with torch.inference_mode():
        logit = model(t.unsqueeze(0).to(device))
        if logit.shape[-2:] != (CROP, CROP):
            logit = F.interpolate(logit, size=(CROP, CROP), mode='bilinear', align_corners=False)
        prob = torch.sigmoid(logit)[0, 0].cpu().numpy()
    return prob


def overlay(img, gt, pr):
    """TP/FP/FN 색칠. img: uint8 HxWx3, gt/pr: bool."""
    out = img.astype(np.float32).copy()
    for mask, color in ((gt & pr, GREEN), (gt & ~pr, RED), (~gt & pr, YELLOW)):
        if mask.any():
            out[mask] = 0.35 * out[mask] + 0.65 * color
    return out.astype(np.uint8)


def main():
    device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
    cfg = yaml.safe_load(CFG.read_text(encoding='utf-8'))
    root = Path(cfg['DATASET']['ROOT'])
    tf = get_val_augmentation([CROP, CROP])
    model = load_model(cfg, device)

    img_dir, msk_dir = root / 'test/images', root / 'test/masks'
    stems = sorted(p.stem for p in img_dir.glob('*.png'))
    print(f'[i] test {len(stems)}장, device={device}')

    records = []
    for stem in stems:
        img = np.array(Image.open(img_dir / f'{stem}.png').convert('RGB'))
        gt_full = np.array(Image.open(msk_dir / f'{stem}.png').convert('L'))
        gt = center_crop_np(gt_full) > 0
        prob = predict(model, img, device, tf)
        pr = prob > 0.5
        inter, union = (gt & pr).sum(), (gt | pr).sum()
        iou = float(inter / union) if union else 1.0
        records.append({'stem': stem, 'iou': iou,
                        'img': center_crop_np(img), 'gt': gt, 'pr': pr})
        print(f'    {stem}  fg_IoU={iou:.4f}')

    records.sort(key=lambda r: r['iou'])
    mean_iou = float(np.mean([r['iou'] for r in records]))
    print(f'[i] test 평균 fg_IoU = {mean_iou:.4f}  (결과표의 0.859와 대조하세요)')

    # ── ① Fig.2 용 데이터셋 예시 1장 — 중앙값 근처를 고른다(잘된 것만 보이지 않기 위해)
    pick = records[len(records) // 2]
    ds_dir = PAPER / 'figures/datasets'
    ds_dir.mkdir(parents=True, exist_ok=True)
    Image.fromarray(pick['img']).save(ds_dir / 'grape_image.jpg', quality=92)
    Image.fromarray((pick['gt'] * 255).astype(np.uint8)).save(ds_dir / 'grape_mask.png')
    print(f"[+] {ds_dir/'grape_image.jpg'}  (원본: {pick['stem']}, IoU {pick['iou']:.3f})")

    # ── ② 정성분석 — 못 맞힌 것 / 중간 / 잘 맞힌 것 3장
    chosen = [records[0], records[len(records) // 2], records[-1]]
    labels = ['Hardest', 'Median', 'Easiest']
    cols = ['Input (center crop)', 'Ground truth', 'Prediction',
            'Error map (green TP / red FN / yellow FP)']

    fig, axes = plt.subplots(3, 4, figsize=(13.0, 10.2))
    for r, (rec, lab) in enumerate(zip(chosen, labels)):
        panels = [rec['img'],
                  np.repeat((rec['gt'] * 255).astype(np.uint8)[..., None], 3, axis=2),
                  np.repeat((rec['pr'] * 255).astype(np.uint8)[..., None], 3, axis=2),
                  overlay(rec['img'], rec['gt'], rec['pr'])]
        for c, panel in enumerate(panels):
            ax = axes[r, c]
            ax.imshow(panel)
            ax.set_xticks([]); ax.set_yticks([])
            if r == 0:
                ax.set_title(cols[c], fontsize=10)
            if c == 0:
                ax.set_ylabel(f"{lab}\nfg-IoU {rec['iou']:.3f}", fontsize=10)
    fig.suptitle('U-Net + ConvNeXt-T on the CERTH grape test split '
                 f'(20 images, mean fg-IoU {mean_iou:.3f})', fontsize=12)
    fig.tight_layout(rect=(0, 0, 1, 0.97))

    res_dir = PAPER / 'figures/results'
    res_dir.mkdir(parents=True, exist_ok=True)
    for ext in ('pdf', 'png'):
        fig.savefig(res_dir / f'qualitative_grape.{ext}', dpi=160, bbox_inches='tight')
    plt.close(fig)
    print(f"[+] {res_dir/'qualitative_grape.pdf'}")

    out = REPO / 'output/grape_paper_figs.json'
    out.write_text(json.dumps(
        {'mean_test_fg_iou': mean_iou,
         'per_image': [{'stem': r['stem'], 'iou': r['iou']} for r in records],
         'dataset_example': pick['stem'],
         'qualitative': [r['stem'] for r in chosen]},
        ensure_ascii=False, indent=2), encoding='utf-8')
    print(f'[+] {out}')


if __name__ == '__main__':
    main()
