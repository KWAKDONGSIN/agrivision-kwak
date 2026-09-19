"""**1폴드(cv1) 전 조합 결과**를 교수님이 지정한 순서 그대로 만든다.

왜 이 순서인가
  0720 미팅 지시 [B] + 0727 미팅 재확인(55:30 "파일 폴드 하기 전에 1 폴드에 대해서만
  쭉 다 결과를 한번 좀 만들어 보세요" / 56:15 "결과 PPT에 있는 결과들" 순서대로).
  위장관 논문 PPT 슬라이드 16~23 순서와 동일하다:

    ① Loss(수렴) 그래프  ← 맨 앞. "학습이 됐다"를 먼저 보인다
    ② Precision / Recall ← 0720에 새로 추가. Dice보다 앞
    ③ Dice / IoU
    ④ 학습시간 + GPU 메모리 ← 0720에 새로 추가
    ⑤ 정성분석(TP/FP/FN)   ← tools/make_fold1_qualitative.py 가 담당
    ⑥ 고도화               ← 별도 실험

입력 (전부 이미 서버에 있는 것. 새 학습 없음)
    output/results_summary.csv   지표 (aggregate_results.py 산출)
    output/run_cost.csv          학습시간·VRAM (parse_run_cost.py 산출)
    output/<run>/logs/           TensorBoard 이벤트 (loss 곡선용)

출력
    reports/fold1/fig_01_loss_curves.png       32조합 loss 곡선 (y축 통일)
    reports/fold1/fig_02_precision_recall.png
    reports/fold1/fig_03_dice_iou.png
    reports/fold1/fig_04_time_memory.png
    reports/fold1/260727_cv1_전결과.md          표 전부 + 결측 명시

사용 예
    $PY tools/parse_run_cost.py          # 먼저 비용 CSV를 만들고
    $PY tools/make_fold1_results.py      # 그다음 이것
"""
import argparse
import csv
from pathlib import Path

import matplotlib
matplotlib.use('Agg')
import matplotlib.font_manager as fm
import matplotlib.pyplot as plt
import numpy as np
from tensorboard.backend.event_processing.event_accumulator import EventAccumulator

# 벤치마크 32조합만 본다. bisenetv2/lightham/fpn 등 단발 실험이 같은 CSV에 섞여 있다.
HEADS = ['ccaseg', 'mask2former', 'oneformer', 'upernet']
BACKBONES = ['resnet_50', 'resnetd_50', 'convnext_t', 'uniformer_s',
             'poolformer_s36', 'pvtv2_b2', 'mit_b2', 'swin_t']
DISP = {'resnet_50': 'ResNet-50', 'resnetd_50': 'ResNetD-50', 'convnext_t': 'ConvNeXt-T',
        'uniformer_s': 'UniFormer-S', 'poolformer_s36': 'PoolFormer-S36',
        'pvtv2_b2': 'PVTv2-B2', 'mit_b2': 'MiT-B2', 'swin_t': 'Swin-T'}
HDISP = {'ccaseg': 'CCASeg', 'mask2former': 'Mask2Former',
         'oneformer': 'OneFormer', 'upernet': 'UPerNet'}


def setup_font():
    for f in fm.findSystemFonts():
        if 'NotoSansCJK' in f or 'NotoSerifCJK' in f:
            fm.fontManager.addfont(f)
    plt.rcParams['font.family'] = ['Noto Sans CJK JP', 'DejaVu Sans']
    plt.rcParams['axes.unicode_minus'] = False


def load_tables(root: Path, fold: int):
    """지표 CSV와 비용 CSV를 (head, backbone) 키로 합친다."""
    met, cost = {}, {}
    with (root / 'output/results_summary.csv').open() as fh:
        for r in csv.DictReader(fh):
            if r['fold'] == str(fold) and r['head'] in HEADS and r['backbone'] in BACKBONES:
                met[(r['head'], r['backbone'])] = r
    cpath = root / 'output/run_cost.csv'
    if cpath.exists():
        with cpath.open() as fh:
            for r in csv.DictReader(fh):
                if r['fold'] == str(fold) and r['head'] in HEADS and r['backbone'] in BACKBONES:
                    cost[(r['head'], r['backbone'])] = r
    return met, cost


def f(row, key):
    """CSV 값 -> float. 없으면 None."""
    if not row:
        return None
    v = row.get(key, '')
    try:
        return float(v)
    except (TypeError, ValueError):
        return None


# ---------------------------------------------------------------- ① Loss 곡선
def fig_loss_curves(root: Path, fold: int, out: Path):
    """32조합 loss 곡선을 4행(헤더) × 8열(백본) 격자로. **y축을 전부 통일**한다.

    교수님 0727 지시: "와이 축이 다 다르니까 사실은 너무 비교가 안 되는 것 같아요."
    """
    curves, ymax = {}, 0.0
    for h in HEADS:
        for b in BACKBONES:
            ld = root / f'output/{h}_{b}_bcedice_cv{fold}/logs'
            if not ld.is_dir():
                continue
            ea = EventAccumulator(str(ld), size_guidance={'scalars': 0})
            try:
                ea.Reload()
            except Exception:
                continue
            tags = set(ea.Tags().get('scalars', []))
            d = {}
            for key, tag in (('train', 'train/loss'), ('val', 'val/loss'),
                             ('train_eval', 'train_eval/loss')):
                if tag in tags:
                    ev = ea.Scalars(tag)
                    # TensorBoard step은 0부터, 사람이 읽는 에폭은 1부터
                    d[key] = ([e.step + 1 for e in ev], [e.value for e in ev])
            if d:
                curves[(h, b)] = d
                for _, vals in d.values():
                    # 초반 폭주값이 y축을 다 먹지 않도록 상위 5%는 잘라서 상한을 잡는다
                    ymax = max(ymax, float(np.percentile(vals, 95)))

    ymax = min(ymax * 1.15, 2.0)
    fig, axes = plt.subplots(len(HEADS), len(BACKBONES),
                             figsize=(3.0 * len(BACKBONES), 2.5 * len(HEADS)),
                             squeeze=False, sharex=True, sharey=True)
    for i, h in enumerate(HEADS):
        for j, b in enumerate(BACKBONES):
            ax = axes[i][j]
            d = curves.get((h, b))
            if not d:
                ax.text(.5, .5, '없음', ha='center', va='center',
                        transform=ax.transAxes, color='crimson', fontsize=13)
                ax.set_facecolor('#f7f7f7')
            else:
                for key, c, lab, ls in (('train', 'tab:red', 'train(학습중)', '--'),
                                        ('train_eval', 'tab:blue', 'train(재측정)', '-'),
                                        ('val', 'tab:orange', 'val', '-')):
                    if key in d:
                        ax.plot(*d[key], color=c, lw=1.2, ls=ls, label=lab)
            ax.set_ylim(0, ymax)
            ax.grid(alpha=.3)
            if i == 0:
                ax.set_title(DISP[b], fontsize=10)
            if j == 0:
                ax.set_ylabel(f'{HDISP[h]}\nLoss', fontsize=9)
            if i == len(HEADS) - 1:
                ax.set_xlabel('Epoch', fontsize=9)
    handles, labels = axes[0][0].get_legend_handles_labels()
    if handles:
        fig.legend(handles, labels, loc='lower center', ncol=3, fontsize=10,
                   bbox_to_anchor=(0.5, -0.005))
    fig.suptitle(f'① Loss 수렴 곡선 — cv{fold} 전 조합 (y축 통일: 0~{ymax:.2f})', fontsize=14)
    fig.tight_layout(rect=[0, 0.03, 1, 0.97])
    fig.savefig(out, dpi=140, bbox_inches='tight')
    plt.close(fig)
    return len(curves)


# ------------------------------------------------- 공통: 헤더×백본 그룹 막대그래프
def grouped_bar(ax, met, key, title, ylabel):
    x = np.arange(len(BACKBONES))
    w = 0.8 / len(HEADS)
    for i, h in enumerate(HEADS):
        vals = [f(met.get((h, b)), key) for b in BACKBONES]
        ys = [0 if v is None else v for v in vals]
        bars = ax.bar(x + i * w - 0.4 + w / 2, ys, w, label=HDISP[h])
        for xi, (bar, v) in enumerate(zip(bars, vals)):
            if v is None:                        # 없는 조합은 빈칸으로 표시(0으로 오해 금지)
                ax.text(bar.get_x() + w / 2, 0.01, '×', ha='center',
                        color='crimson', fontsize=11, fontweight='bold')
    ax.set_xticks(x)
    ax.set_xticklabels([DISP[b] for b in BACKBONES], rotation=30, ha='right', fontsize=9)
    ax.set_title(title, fontsize=12)
    ax.set_ylabel(ylabel)
    ax.grid(axis='y', alpha=.3)
    ax.legend(fontsize=9)


def fig_pr(met, out, fold):
    fig, axes = plt.subplots(1, 2, figsize=(15, 5))
    grouped_bar(axes[0], met, 'fg_Precision', f'Precision (전경) — cv{fold}', 'Precision')
    grouped_bar(axes[1], met, 'fg_Recall', f'Recall (전경) — cv{fold}', 'Recall')
    for ax in axes:
        ax.set_ylim(0.7, 1.0)
    fig.suptitle('② Precision / Recall  (교수님 0720 지시로 Dice보다 앞에 배치)', fontsize=14)
    fig.tight_layout(rect=[0, 0, 1, 0.94])
    fig.savefig(out, dpi=140)
    plt.close(fig)


def fig_dice_iou(met, out, fold):
    fig, axes = plt.subplots(1, 2, figsize=(15, 5))
    grouped_bar(axes[0], met, 'fg_Dice', f'Dice (전경) — cv{fold}', 'Dice')
    grouped_bar(axes[1], met, 'fg_IoU', f'IoU (전경) — cv{fold}', 'IoU')
    axes[0].set_ylim(0.7, 1.0)
    axes[1].set_ylim(0.6, 1.0)
    fig.suptitle('③ Dice / IoU  (배경 99%가 섞이는 mIoU 대신 전경 단독 지표)', fontsize=14)
    fig.tight_layout(rect=[0, 0, 1, 0.94])
    fig.savefig(out, dpi=140)
    plt.close(fig)


def fig_cost(met, cost, out, fold):
    """④ 학습시간 + GPU 메모리. 오른쪽은 '효율 대비 성능' 산점도."""
    fig, axes = plt.subplots(1, 3, figsize=(19, 5))

    # 학습시간(분)
    x = np.arange(len(BACKBONES))
    w = 0.8 / len(HEADS)
    for i, h in enumerate(HEADS):
        ys = [(f(cost.get((h, b)), 'total_sec') or 0) / 60 for b in BACKBONES]
        axes[0].bar(x + i * w - 0.4 + w / 2, ys, w, label=HDISP[h])
    axes[0].set_xticks(x)
    axes[0].set_xticklabels([DISP[b] for b in BACKBONES], rotation=30, ha='right', fontsize=9)
    axes[0].set_title(f'학습시간 (분) — cv{fold}')
    axes[0].set_ylabel('분')
    axes[0].grid(axis='y', alpha=.3)
    axes[0].legend(fontsize=9)

    # Peak VRAM
    for i, h in enumerate(HEADS):
        ys = [f(cost.get((h, b)), 'peak_vram_mb') or 0 for b in BACKBONES]
        axes[1].bar(x + i * w - 0.4 + w / 2, ys, w, label=HDISP[h])
    axes[1].set_xticks(x)
    axes[1].set_xticklabels([DISP[b] for b in BACKBONES], rotation=30, ha='right', fontsize=9)
    axes[1].set_title(f'Peak GPU 메모리 (MB) — cv{fold}')
    axes[1].set_ylabel('MB')
    axes[1].grid(axis='y', alpha=.3)
    axes[1].legend(fontsize=9)

    # 시간 vs 성능
    for h in HEADS:
        xs, ys, lb = [], [], []
        for b in BACKBONES:
            t, v = f(cost.get((h, b)), 'total_sec'), f(met.get((h, b)), 'fg_IoU')
            if t and v:
                xs.append(t / 60)
                ys.append(v)
                lb.append(DISP[b])
        axes[2].scatter(xs, ys, s=55, label=HDISP[h], alpha=.85)
    axes[2].set_xlabel('학습시간 (분)')
    axes[2].set_ylabel('전경 IoU')
    axes[2].set_title('시간 대비 성능 — 왼쪽 위가 좋음')
    axes[2].grid(alpha=.3)
    axes[2].legend(fontsize=9)

    fig.suptitle('④ 학습시간 + GPU 메모리  (교수님 0720 지시로 신규 추가)', fontsize=14)
    fig.tight_layout(rect=[0, 0, 1, 0.94])
    fig.savefig(out, dpi=140)
    plt.close(fig)


def md_table(met, cost, keys, headers):
    """헤더×백본 표를 마크다운으로. 값이 없으면 '—'."""
    lines = ['| 헤더 | 백본 | ' + ' | '.join(headers) + ' |',
             '|---|---|' + '---|' * len(headers)]
    for h in HEADS:
        for b in BACKBONES:
            cells = []
            for src, key, fmtstr in keys:
                row = (met if src == 'met' else cost).get((h, b))
                v = f(row, key)
                cells.append('—' if v is None else fmtstr.format(v))
            lines.append(f'| {HDISP[h]} | {DISP[b]} | ' + ' | '.join(cells) + ' |')
    return '\n'.join(lines)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--fold', type=int, default=1)
    ap.add_argument('--root', default='.')
    ap.add_argument('--outdir', default='reports/fold1')
    args = ap.parse_args()

    setup_font()
    root = Path(args.root).resolve()
    outdir = root / args.outdir
    outdir.mkdir(parents=True, exist_ok=True)
    met, cost = load_tables(root, args.fold)
    total = len(HEADS) * len(BACKBONES)
    print(f'[불러옴] 지표 {len(met)}/{total} 조합, 비용 {len(cost)}/{total} 조합')

    n = fig_loss_curves(root, args.fold, outdir / 'fig_01_loss_curves.png')
    print(f'[①] loss 곡선 {n}/{total} — fig_01_loss_curves.png')
    fig_pr(met, outdir / 'fig_02_precision_recall.png', args.fold)
    print('[②] Precision/Recall — fig_02_precision_recall.png')
    fig_dice_iou(met, outdir / 'fig_03_dice_iou.png', args.fold)
    print('[③] Dice/IoU — fig_03_dice_iou.png')
    fig_cost(met, cost, outdir / 'fig_04_time_memory.png', args.fold)
    print('[④] 시간/메모리 — fig_04_time_memory.png')

    # ----- 마크다운 보고서 -----
    missing_met = [f'{HDISP[h]}+{DISP[b]}' for h in HEADS for b in BACKBONES
                   if (h, b) not in met]
    missing_cost = [f'{HDISP[h]}+{DISP[b]}' for h in HEADS for b in BACKBONES
                    if (h, b) not in cost]
    ranked = sorted(((f(met[k], 'fg_IoU'), k) for k in met if f(met[k], 'fg_IoU')),
                    reverse=True)

    doc = [f'# cv{args.fold} 1폴드 전 조합 결과', '',
           f'작성: 2026-07-27',
           '',
           '> 교수님 0727 지시(55:30) *"파일 폴드 하기 전에 1 폴드에 대해서만 쭉 다 결과를 '
           '한번 좀 만들어 보세요"* 에 대한 산출물입니다.',
           '> 순서는 0720 지시 [B] = 위장관 논문 PPT 슬라이드 16~23 순서를 그대로 따랐습니다.',
           '> **새로 학습한 것은 없습니다.** 이미 서버에 있던 결과를 모아 정리한 것입니다.', '',
           '## 커버리지', '',
           f'- 지표 확보: **{len(met)}/{total}** 조합',
           f'- 학습시간·GPU메모리 확보: **{len(cost)}/{total}** 조합', '']
    if missing_met:
        doc += [f'- 🔴 **지표 없음**: {", ".join(missing_met)}', '']
    if missing_cost:
        doc += [f'- ⚠️ **시간/메모리 없음**: {", ".join(missing_cost)} '
                '(학습은 됐으나 스윕 로그가 남아 있지 않음)', '']

    doc += ['---', '', '## ① Loss 수렴 곡선', '',
            '![loss](fig_01_loss_curves.png)', '',
            '**y축을 0~공통상한으로 통일**했습니다 (교수님 0727 지시: *"와이 축을 고정 시켜놓고요"*).',
            '',
            '- 빨간 점선 `train(학습중)` = 증강이 켜진 상태로 에폭 내내 누적한 평균',
            '- 파란 실선 `train(재측정)` = 에폭이 끝난 뒤 증강 없이 다시 잰 값',
            '- 주황 실선 `val`',
            '',
            '**`val`과 비교해야 하는 것은 파란 실선입니다.** 빨간 점선과 비교하면 '
            '"train보다 val이 더 낮다"는 착시가 생깁니다.', '',
            '---', '', '## ② Precision / Recall', '',
            '![pr](fig_02_precision_recall.png)', '',
            md_table(met, cost,
                     [('met', 'fg_Precision', '{:.4f}'), ('met', 'fg_Recall', '{:.4f}')],
                     ['전경 Precision', '전경 Recall']), '',
            '---', '', '## ③ Dice / IoU', '',
            '![diceiou](fig_03_dice_iou.png)', '',
            md_table(met, cost,
                     [('met', 'fg_Dice', '{:.4f}'), ('met', 'fg_IoU', '{:.4f}'),
                      ('met', 'mIoU', '{:.4f}')],
                     ['전경 Dice', '전경 IoU', 'mIoU(참고)']), '',
            '> `mIoU`는 배경이 약 97.6%를 차지해 조합 간 차이가 묻힙니다. '
            '**본문 지표는 전경 IoU/Dice를 씁니다.**', '',
            '---', '', '## ④ 학습시간 + GPU 메모리', '',
            '![cost](fig_04_time_memory.png)', '',
            md_table(met, cost,
                     [('cost', 'total_sec', '{:.0f}'), ('cost', 'avg_epoch_sec', '{:.1f}'),
                      ('cost', 'peak_vram_mb', '{:.0f}'), ('cost', 'avg_ram_gb', '{:.1f}')],
                     ['총 학습시간(초)', '에폭당(초)', 'Peak VRAM(MB)', '평균 RAM(GB)']), '',
            '> ⚠️ 학습시간은 **조기 종료 시점이 조합마다 달라** 그대로 비교하면 불공정합니다. '
            '**에폭당 시간**이 더 공정한 비교입니다.', '',
            '---', '', '## 전경 IoU 순위 (cv1)', '',
            '| 순위 | 헤더 | 백본 | 전경 IoU |', '|---|---|---|---|']
    for i, (v, (h, b)) in enumerate(ranked, 1):
        doc.append(f'| {i} | {HDISP[h]} | {DISP[b]} | {v:.4f} |')

    doc += ['', '---', '', '## ⑤ 정성분석 (TP/FP/FN)', '',
            '![qual](fig_05_qualitative.png)', '',
            '![qual2](fig_05_qualitative_zoom.png)', '',
            '생성: `CUDA_VISIBLE_DEVICES=<빈GPU> $PY tools/make_fold1_qualitative.py` '
            '(추론만, 학습 아님)', '',
            '- **초록 = TP** 맞게 찾음 / **빨강 = FN** 놓침(Recall을 깎음) / '
            '**노랑 = FP** 잘못 찾음(Precision을 깎음)',
            '- 대표 사진은 1위 모델 기준으로 **어려운 / 보통 / 쉬운** 3장을 골랐습니다.',
            '  전경이 화면의 0.5% 미만인 사진 14장은 제외했습니다 — 블루베리가 거의 없는 사진은 '
            'IoU가 1.0 또는 0.0으로 튀어 대표성이 없기 때문입니다.', '',
            '### 🔴 정성분석에서 나온 발견', '',
            '`Camera 3 Video (121)_2041.bmp` (test 83번)에서 **상위 5개 조합이 전부 IoU 0.000**입니다.',
            '',
            '- 이 사진의 정답은 **개체 2개뿐이고 각각 2,162 / 2,505 픽셀**로, 보통 블루베리 한 알'
            '(중앙값 약 700픽셀)보다 **3배 이상 큰 덩어리**입니다.',
            '- 확대 그림(`fig_05_qualitative_zoom.png`)에서 보면 정답이 칠한 두 영역은 '
            '**잎 모양에 가깝고**, 그 자리에 블루베리 열매가 보이지 않습니다.',
            '- 서로 구조가 다른 5개 모델(UPerNet·CCASeg·Mask2Former × ConvNeXt·PVTv2·Swin·MiT)이 '
            '**모두 그 자리를 배경으로 예측**했습니다. 모델 쪽 결함이라기보다 '
            '**주석 오류가 의심되는 사례**입니다.',
            '- ⚠️ 다만 이는 **그림을 보고 판단한 것**이며, 원 데이터 제작자에게 확인한 것은 '
            '아닙니다. 논문에 쓸 때는 "annotation ambiguity로 보인다" 수준으로 쓰는 것이 안전합니다.',
            '- → **논문 정성분석 절의 "실패 사례"로 쓸 수 있는 재료**입니다. '
            '이런 표본이 test에 몇 장이나 있는지 세어 두면 더 좋습니다.', '',
            '## ⑥ 고도화 · 통계검정', '',
            '🔴 **1폴드만으로는 통계 검정을 할 수 없습니다.** Friedman·t-검정은 폴드가 여러 개 '
            '있어야 성립합니다. 교수님 지시대로 지금은 1폴드로 "학습이 됐다"만 확인하고, '
            '폴드를 늘린 뒤 통계로 갑니다.', '']

    mdpath = outdir / f'260727_cv{args.fold}_전결과.md'
    mdpath.write_text('\n'.join(doc))
    print(f'[저장] {mdpath}')


if __name__ == '__main__':
    main()
