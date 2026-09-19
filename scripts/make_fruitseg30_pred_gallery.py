# -*- coding: utf-8 -*-
"""학습된 FruitSeg30 모델이 test 사진에 실제로 그린 결과를 그림으로 뽑는다.

"서버에서 학습이 정말 잘 돌아갔는가"를 눈으로 확인시켜 주는 자료다.
test 390장 전부에 대해 예측을 돌려 사진별 IoU를 재고, 그 중에서
잘 맞힌 것 / 보통 / 못 맞힌 것을 골라 갤러리로 만든다.

만드는 것 (reports/figures/gallery/):
  pred_by_class_p1..p2.png   과일 30종 각각 1장씩 — 원본 / 정답 / 모델예측
  pred_best_p1.png           가장 잘 맞힌 사진 (원본/정답/예측/틀린곳)
  pred_worst_p1.png          가장 못 맞힌 사진 (같은 4단)
  pred_typical_p1..p2.png    평균적인 사진
  fig_fruitseg30_per_image_iou.png   사진 390장의 IoU 분포 히스토그램
그리고 output/fruitseg30_per_image_iou.json 에 사진별 IoU를 저장한다.

GPU 1장을 몇 분 사용한다 (추론만, 학습 아님).

사용:  CUDA_VISIBLE_DEVICES=<빈GPU> $PY tools/make_fruitseg30_pred_gallery.py
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
from matplotlib.font_manager import FontProperties
from PIL import Image
from torch.nn import functional as F

REPO = Path('/data/project/2026summer/kds0206/semantic-segmentation')
sys.path.insert(0, str(REPO))

from semseg.models import *                      # noqa: E402,F401,F403
from semseg.datasets import *                    # noqa: E402,F401,F403
from semseg.augmentations import get_eval_augmentation   # noqa: E402

CFG_PATH = REPO / 'configs/fruitseg_upernet_resnet_50_bcedice_200ep.yaml'
OUTDIR = REPO / 'reports/figures/gallery'
FIGDIR = REPO / 'reports/figures'
IOU_JSON = REPO / 'output/fruitseg30_per_image_iou.json'

REG = FontProperties(fname='/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc')
BLD = FontProperties(fname='/usr/share/fonts/opentype/noto/NotoSansCJK-Bold.ttc')
INK, MUTE, BLUE, GOOD, BAD = '#111827', '#6b7280', '#2563eb', '#0a7d33', '#b23b3b'

GREEN = np.array([40, 190, 90])     # 맞게 찾은 과일
RED = np.array([230, 60, 60])       # 과일인데 놓침 (미검출)
YELLOW = np.array([245, 190, 40])   # 배경인데 과일이라 함 (오검출)


def ko(stem: str) -> str:
    return stem.split('__')[0].replace('_', ' ')


def overlay(im, m, color, alpha=0.45):
    ov = im.copy()
    ov[m == 1] = ((1 - alpha) * ov[m == 1] + alpha * color).astype(np.uint8)
    return ov


def diff_map(im, gt, pr):
    """맞은 곳=초록, 놓친 곳=빨강, 잘못 찾은 곳=노랑."""
    ov = im.copy()
    for mask, color in ((gt & pr, GREEN), (gt & ~pr, RED), (~gt & pr, YELLOW)):
        ov[mask] = (0.35 * ov[mask] + 0.65 * color).astype(np.uint8)
    return ov


# ------------------------------------------------------------------ 추론
@torch.no_grad()
def run_inference():
    cfg = yaml.safe_load(CFG_PATH.read_text())
    device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
    print(f'[info] device = {device}'
          + (f' ({torch.cuda.get_device_name(0)})' if device.type == 'cuda' else ''))

    transform = get_eval_augmentation(cfg['TEST']['IMAGE_SIZE'],
                                      seg_fill=cfg['DATASET']['IGNORE_LABEL'], augment=False)
    ds = eval(cfg['DATASET']['NAME'])(cfg['DATASET']['ROOT'], 'test', transform)

    model = UPerNet(cfg['MODEL']['BACKBONE'], 1)          # BCEDice → 출력 채널 1개
    ckpt = Path(cfg['TEST']['MODEL_PATH'])
    if not ckpt.exists():
        raise FileNotFoundError(f'체크포인트가 없습니다: {ckpt}')
    model.load_state_dict(torch.load(str(ckpt), map_location='cpu'))
    model = model.to(device).eval()
    print(f'[info] 체크포인트 로드: {ckpt.name}')

    records = []
    for i in range(len(ds)):
        image, label = ds[i]
        logits = model(image.unsqueeze(0).to(device))
        if logits.shape[-2:] != label.shape[-2:]:
            logits = F.interpolate(logits, size=label.shape[-2:], mode='bilinear', align_corners=False)
        pred = (torch.sigmoid(logits) >= 0.5).squeeze().cpu().numpy().astype(bool)
        gt = (label.numpy() == 1)
        inter = np.logical_and(gt, pred).sum()
        union = np.logical_or(gt, pred).sum()
        records.append({'file': ds.files[i].name,
                        'cls': ds.files[i].stem.split('__')[0],
                        'iou': float(inter / union) if union else 1.0,
                        'gt_ratio': float(gt.mean()),
                        'pred_ratio': float(pred.mean())})
        np.save(_cache_path(ds.files[i].name), pred)
        if (i + 1) % 50 == 0:
            print(f'  ... {i + 1}/{len(ds)}')
    print(f'[info] 추론 완료: {len(records)}장')
    return cfg, ds, records


CACHE = REPO / 'output' / '_fruitseg30_pred_cache'


def _cache_path(name: str) -> Path:
    CACHE.mkdir(parents=True, exist_ok=True)
    return CACHE / f'{Path(name).stem}.npy'


def load_display(ds, name):
    """화면에 그릴 원본 RGB, 정답, 예측을 512x512로 맞춰 돌려준다."""
    img_path = ds.img_dir / name
    im = np.array(Image.open(img_path).convert('RGB').resize((512, 512), Image.BILINEAR))
    mp = ds.mask_dir / f'{Path(name).stem}.png'
    gt = np.array(Image.open(mp).convert('L').resize((512, 512), Image.NEAREST)) > 0
    pr = np.load(_cache_path(name)).astype(bool)
    return im, gt, pr


# --------------------------------------------------- 그림 ① 과일 종류별 예측
def fig_by_class(ds, records, out_prefix: Path, classes_per_page=15):
    by_cls = {}
    for r in records:                       # 클래스별로 IoU 중앙값에 가까운 대표 1장
        by_cls.setdefault(r['cls'], []).append(r)
    reps = []
    for c in sorted(by_cls):
        rs = sorted(by_cls[c], key=lambda r: r['iou'])
        reps.append(rs[len(rs) // 2])

    pages = [reps[i:i + classes_per_page] for i in range(0, len(reps), classes_per_page)]
    for pi, chunk in enumerate(pages, 1):
        nrow = len(chunk)
        fig, axes = plt.subplots(nrow, 3, figsize=(7.6, 2.45 * nrow))
        axes = np.atleast_2d(axes)
        for r_i, rec in enumerate(chunk):
            im, gt, pr = load_display(ds, rec['file'])
            panels = [(im, None), (overlay(im, gt.astype(np.uint8), RED), None),
                      (overlay(im, pr.astype(np.uint8), np.array([60, 130, 246])), None)]
            for col, (arr, cm) in enumerate(panels):
                ax = axes[r_i, col]
                ax.imshow(arr, cmap=cm)
                ax.axis('off')
                if r_i == 0:
                    ax.set_title(['원본 사진', '사람이 만든 정답', '모델이 예측한 것'][col],
                                 fontproperties=BLD, fontsize=10.5, color=INK, pad=6)
            axes[r_i, 0].text(-0.05, 0.5, f"{ko(rec['file'])}\nIoU {rec['iou']:.3f}",
                              transform=axes[r_i, 0].transAxes, rotation=90,
                              va='center', ha='center', fontproperties=REG, fontsize=8, color=MUTE)
        fig.suptitle(f'모델 예측 결과 — 과일 종류별 ({pi}/{len(pages)})  ·  각 종류의 중간 성적 사진',
                     fontproperties=BLD, fontsize=13, color=INK)
        fig.tight_layout(rect=[0.015, 0, 1, 0.965])
        out = Path(f'{out_prefix}_p{pi}.png')
        fig.savefig(out, dpi=112)
        plt.close(fig)
        print(f'[fig] {out}')
    return len(pages)


# ----------------------------------------------- 그림 ② 잘/보통/못 맞힌 사진 4단
def fig_quad(ds, picks, title, out: Path):
    nrow = len(picks)
    fig, axes = plt.subplots(nrow, 4, figsize=(10.2, 2.75 * nrow))
    axes = np.atleast_2d(axes)
    for r_i, rec in enumerate(picks):
        im, gt, pr = load_display(ds, rec['file'])
        panels = [im, overlay(im, gt.astype(np.uint8), RED),
                  overlay(im, pr.astype(np.uint8), np.array([60, 130, 246])),
                  diff_map(im, gt, pr)]
        for col, arr in enumerate(panels):
            ax = axes[r_i, col]
            ax.imshow(arr)
            ax.axis('off')
            if r_i == 0:
                ax.set_title(['① 원본', '② 정답(빨강)', '③ 모델 예측(파랑)', '④ 채점'][col],
                             fontproperties=BLD, fontsize=11, color=INK, pad=6)
        axes[r_i, 0].text(-0.05, 0.5, f"{ko(rec['file'])}\nIoU {rec['iou']:.3f}",
                          transform=axes[r_i, 0].transAxes, rotation=90,
                          va='center', ha='center', fontproperties=REG, fontsize=8.5, color=MUTE)
    fig.suptitle(title, fontproperties=BLD, fontsize=13, color=INK)
    fig.text(0.5, 0.012,
             '④ 채점 색: 초록 = 맞게 찾음   빨강 = 과일인데 놓침   노랑 = 배경인데 과일이라 함',
             ha='center', fontproperties=REG, fontsize=9.5, color=MUTE)
    fig.tight_layout(rect=[0.015, 0.028, 1, 0.955])
    fig.savefig(out, dpi=112)
    plt.close(fig)
    print(f'[fig] {out}')


# ------------------------------------------------------- 그림 ③ IoU 분포
def fig_iou_hist(records, out: Path):
    ious = np.array([r['iou'] for r in records])
    fig, ax = plt.subplots(figsize=(8.2, 4.4))
    ax.hist(ious, bins=30, color=BLUE, alpha=.85, edgecolor='white')
    ax.axvline(ious.mean(), color=BAD, ls='--', lw=2)
    ax.text(ious.mean(), ax.get_ylim()[1] * .93, f'  평균 {ious.mean():.3f}',
            fontproperties=BLD, fontsize=11, color=BAD, va='top')
    ax.set_xlabel('사진 한 장의 IoU (1에 가까울수록 정답과 똑같음)', fontproperties=REG, fontsize=11)
    ax.set_ylabel('사진 수', fontproperties=REG, fontsize=11)
    ax.set_title(f'test {len(ious)}장 각각의 성적 분포  ·  0.9 이상 {(ious >= .9).sum()}장 '
                 f'({(ious >= .9).mean() * 100:.1f}%)',
                 fontproperties=BLD, fontsize=13, color=INK)
    ax.spines[['top', 'right']].set_visible(False)
    ax.grid(axis='y', alpha=.25)
    fig.tight_layout()
    fig.savefig(out, dpi=150)
    plt.close(fig)
    print(f'[fig] {out}')


def main():
    OUTDIR.mkdir(parents=True, exist_ok=True)
    cfg, ds, records = run_inference()

    ious = np.array([r['iou'] for r in records])
    IOU_JSON.write_text(json.dumps({
        'checkpoint': cfg['TEST']['MODEL_PATH'],
        'n_images': len(records),
        'mean_iou': float(ious.mean()), 'median_iou': float(np.median(ious)),
        'min_iou': float(ious.min()), 'max_iou': float(ious.max()),
        'n_ge_090': int((ious >= .9).sum()), 'n_lt_050': int((ious < .5).sum()),
        'per_image': records,
    }, ensure_ascii=False, indent=1), encoding='utf-8')
    print(f'[json] {IOU_JSON}')

    srt = sorted(records, key=lambda r: r['iou'])
    fig_by_class(ds, records, OUTDIR / 'pred_by_class')
    fig_quad(ds, srt[-4:][::-1], '가장 잘 맞힌 사진 4장 (test 세트)', OUTDIR / 'pred_best_p1.png')
    fig_quad(ds, srt[:4], '가장 못 맞힌 사진 4장 (test 세트) — 어디서 틀리는지 보는 자료',
             OUTDIR / 'pred_worst_p1.png')
    mid = len(srt) // 2
    fig_quad(ds, srt[mid - 2:mid + 2], '평균적인 사진 4장 (test 세트)', OUTDIR / 'pred_typical_p1.png')
    fig_iou_hist(records, FIGDIR / 'fig_fruitseg30_per_image_iou.png')
    print('[done]')


if __name__ == '__main__':
    main()
