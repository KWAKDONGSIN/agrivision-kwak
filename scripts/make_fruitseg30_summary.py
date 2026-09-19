"""FruitSeg30 결과를 7/27 랩미팅 슬라이드 4개에 맞춰 정리한다 (곽동신 담당).

숫자를 하드코딩하지 않고 전부 실제 산출물에서 읽습니다.
  ① 데이터셋 개수·해상도  <- output/fruitseg30_stats.json, fruitseg30_split_stats.json
  ② 200에폭 성능          <- output/fruitseg_runs/.../logs (TensorBoard)
  ③ test 성능             <- logs/fruitseg30_test_eval.log (val.py 출력)
  ④ loss 그래프           <- reports/figures/fig_fruitseg30_loss.png

학습이 아직 안 끝났으면 그 항목만 '학습 진행 중'으로 적고 나머지는 채웁니다.
따라서 **여러 번 다시 실행해도 안전**합니다.

사용:  $PY tools/make_fruitseg30_summary.py
"""
import json
import re
from datetime import datetime
from pathlib import Path

import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import numpy as np
from matplotlib.font_manager import FontProperties
from PIL import Image

REPO = Path('/data/project/2026summer/kds0206/semantic-segmentation')
BASE = Path('/data/project/2026summer/kds0206')
RUN = REPO / 'output/fruitseg_runs/upernet_resnet_50_bcedice_200ep'
FIGDIR = REPO / 'reports/figures'
DOC = BASE / '문서/260725_FruitSeg30_발표슬라이드_정리.md'
DATASET = BASE / 'dataset_fruitseg30'

REG = FontProperties(fname='/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc')
BLD = FontProperties(fname='/usr/share/fonts/opentype/noto/NotoSansCJK-Bold.ttc')
BLUE, INK, MUTE = '#2563eb', '#111827', '#6b7280'


# ------------------------------------------------------------------ 유틸
def load_json(p: Path):
    return json.loads(p.read_text()) if p.exists() else None


def load_scalars(logdir: Path) -> dict:
    """TensorBoard 이벤트에서 스칼라를 읽는다. {태그: [(epoch, 값), ...]}"""
    if not logdir.is_dir():
        return {}
    from tensorboard.backend.event_processing.event_accumulator import EventAccumulator
    acc = EventAccumulator(str(logdir), size_guidance={'scalars': 0})
    acc.Reload()
    out = {}
    for tag in acc.Tags().get('scalars', []):
        out[tag] = [(e.step, e.value) for e in acc.Scalars(tag)]
    return out


def parse_test_log(p: Path):
    """val.py의 tabulate 출력에서 클래스별 지표를 뽑는다."""
    if not p.exists():
        return None
    rows = {}
    for line in p.read_text(errors='ignore').splitlines():
        m = re.match(r'^\s*(background|blueberry)\s+([\d.]+)\s+([\d.]+)\s+([\d.]+)\s+([\d.]+)\s*$', line)
        if m:
            rows[m.group(1)] = {
                'IoU': float(m.group(2)), 'Dice': float(m.group(3)),
                'Precision': float(m.group(4)), 'Recall': float(m.group(5)),
            }
    return rows or None


def fmt(x, n=4):
    return f'{x:.{n}f}' if isinstance(x, (int, float)) else str(x)


# --------------------------------------------------- 그림 ① 클래스별 장수
def fig_class_counts(raw_stats, out: Path):
    per = raw_stats['per_group']
    fg = raw_stats['per_group_fg_ratio_mean']
    names = sorted(per, key=lambda k: -per[k])
    vals = [per[k] for k in names]

    fig, ax = plt.subplots(figsize=(11, 5.2))
    bars = ax.bar(range(len(names)), vals, color=BLUE, alpha=.85)
    ax.set_xticks(range(len(names)))
    ax.set_xticklabels([n.replace('_', ' ') for n in names], rotation=55,
                       ha='right', fontproperties=REG, fontsize=8.5)
    ax.set_ylabel('이미지 장수', fontproperties=REG, fontsize=11)
    ax.set_title(f'FruitSeg30 클래스별 이미지 수 (총 {raw_stats["total_pairs"]}장 / {len(names)}개 클래스)',
                 fontproperties=BLD, fontsize=13, color=INK)
    for b, v in zip(bars, vals):
        ax.text(b.get_x() + b.get_width() / 2, v + 1, str(v),
                ha='center', fontproperties=REG, fontsize=7.5, color=MUTE)
    ax.spines[['top', 'right']].set_visible(False)
    ax.grid(axis='y', alpha=.25)
    fig.tight_layout()
    fig.savefig(out, dpi=150)
    plt.close(fig)
    print(f'[fig] {out}')

    # 전경 비율도 같이
    out2 = out.with_name('fig_fruitseg30_fg_ratio.png')
    fig, ax = plt.subplots(figsize=(11, 5.2))
    order = sorted(fg, key=lambda k: -fg[k])
    ax.bar(range(len(order)), [fg[k] * 100 for k in order], color='#059669', alpha=.85)
    ax.set_xticks(range(len(order)))
    ax.set_xticklabels([n.replace('_', ' ') for n in order], rotation=55,
                       ha='right', fontproperties=REG, fontsize=8.5)
    ax.set_ylabel('전경(과일) 픽셀 비율 %', fontproperties=REG, fontsize=11)
    ax.set_title('클래스별 전경 비율 — 평균 %.1f%% (블루베리 데이터셋은 약 2.4%%)'
                 % (raw_stats['fg_ratio']['mean'] * 100),
                 fontproperties=BLD, fontsize=13, color=INK)
    ax.spines[['top', 'right']].set_visible(False)
    ax.grid(axis='y', alpha=.25)
    fig.tight_layout()
    fig.savefig(out2, dpi=150)
    plt.close(fig)
    print(f'[fig] {out2}')


# ------------------------------------------------------- 그림 ① 데이터 예시
def fig_examples(out: Path, n=4):
    img_dir = DATASET / 'train/images'
    mask_dir = DATASET / 'train/masks'
    if not img_dir.is_dir():
        return
    files = sorted(img_dir.iterdir())
    picks = [files[int(i * len(files) / (n + 1))] for i in range(1, n + 1)]

    fig, axes = plt.subplots(3, n, figsize=(3.1 * n, 9.6))
    for j, ip in enumerate(picks):
        im = np.array(Image.open(ip).convert('RGB'))
        mk = np.array(Image.open(mask_dir / f'{ip.stem}.png').convert('L'))
        binm = (mk > 0).astype(np.uint8)
        ov = im.copy()
        ov[binm == 1] = (0.55 * ov[binm == 1] + 0.45 * np.array([255, 60, 60])).astype(np.uint8)
        for i, (arr, ttl, cm) in enumerate([(im, '원본 이미지', None),
                                            (binm * 255, '마스크 (과일=흰색)', 'gray'),
                                            (ov, '겹쳐보기', None)]):
            ax = axes[i, j]
            ax.imshow(arr, cmap=cm)
            ax.axis('off')
            if i == 0:
                ax.set_title(ip.stem.replace('_', ' ')[:24], fontproperties=REG, fontsize=9)
            if j == 0:
                ax.text(-0.08, 0.5, ttl, transform=ax.transAxes, rotation=90,
                        va='center', ha='center', fontproperties=BLD, fontsize=11, color=INK)
    fig.suptitle('FruitSeg30 예시 — 30개 과일을 합쳐 "과일(1) vs 배경(0)" 이진 분할',
                 fontproperties=BLD, fontsize=14, color=INK)
    fig.tight_layout(rect=[0.02, 0, 1, 0.97])
    fig.savefig(out, dpi=130)
    plt.close(fig)
    print(f'[fig] {out}')


# ---------------------------------------------------------------- 본문
def main():
    FIGDIR.mkdir(parents=True, exist_ok=True)
    DOC.parent.mkdir(parents=True, exist_ok=True)

    raw = load_json(REPO / 'output/fruitseg30_stats.json')
    split = load_json(REPO / 'output/fruitseg30_split_stats.json')
    scalars = load_scalars(RUN / 'logs')
    test = parse_test_log(REPO / 'logs/fruitseg30_test_eval.log')
    manifest = load_json(DATASET / 'split_manifest.json')

    if raw:
        fig_class_counts(raw, FIGDIR / 'fig_fruitseg30_class_counts.png')
    fig_examples(FIGDIR / 'fig_fruitseg30_examples.png')

    # ② 학습 곡선에서 요약 숫자 뽑기
    done_epochs = len(scalars.get('train/loss', []))
    val_fg = scalars.get('val/fg_IoU', [])
    val_loss = scalars.get('val/loss', [])
    best_val = min(val_loss, key=lambda t: t[1]) if val_loss else None
    best_fg = max(val_fg, key=lambda t: t[1]) if val_fg else None
    last_fg = val_fg[-1] if val_fg else None
    training_done = done_epochs >= 200

    L = []
    A = L.append
    A('# FruitSeg30 — 7/27 랩미팅 발표 슬라이드 정리 (곽동신)')
    A('')
    A(f'작성: 2026-07-25   ·   최종 갱신: {datetime.now().strftime("%Y-%m-%d %H:%M")}')
    A('')
    A('> 이 문서는 `tools/make_fruitseg30_summary.py`가 **실제 산출물에서 숫자를 읽어** 자동 생성합니다.')
    A('> 학습이 끝나면 다시 실행되어 ②③④가 채워집니다.')
    A('')
    A('## 한눈에 보기')
    A('')
    A('| 슬라이드 | 상태 |')
    A('|---|---|')
    A(f'| ① 데이터셋 개수·해상도 | {"✅ 완료" if raw else "❌ 통계 없음"} |')
    A(f'| ② 200에폭 성능 | {"✅ 완료" if training_done else f"⏳ 학습 중 ({done_epochs}/200 epoch)"} |')
    A(f'| ③ test 성능 | {"✅ 완료" if test else "⏳ 학습 종료 후 자동 실행"} |')
    A(f'| ④ loss 그래프 | {"✅ 완료" if (FIGDIR / "fig_fruitseg30_loss.png").exists() else "⏳ 학습 종료 후 자동 생성"} |')
    A('')
    A('실험 조건 (팀 공통값 그대로, 데이터 경로만 변경):')
    A('')
    A('| 항목 | 값 |')
    A('|---|---|')
    A('| 조합 | **UPerNet + ResNet-50** |')
    A('| 입력 크기 | 512 × 512 |')
    A('| 배치 | 2 (누적 4회 → 실효 배치 8) |')
    A('| 손실 | BCEDice |')
    A('| 옵티마이저 | AdamW, lr 1e-4, weight decay 0.01 |')
    A('| 에폭 | 200 (early stopping 꺼짐 → 전부 완주) |')
    A('| 증강 | HFlip(0.5) → Rotation(60°, 0.3) → RandomCrop → Normalize |')
    A('| config | `configs/fruitseg_upernet_resnet_50_bcedice_200ep.yaml` |')
    A('')
    A('---')
    A('')

    # ---------------- 슬라이드 ①
    A('## 슬라이드 ① — 데이터셋 개수·해상도')
    A('')
    if raw and split:
        sizes = raw['image_sizes']
        A('**넣을 표**')
        A('')
        A('| 항목 | 값 |')
        A('|---|---|')
        A(f'| 데이터셋 | FruitSeg30 (Mendeley 공개, DOI 10.17632/vkht8pfsp3.3) |')
        A(f'| 전체 이미지 | **{raw["total_pairs"]:,}장** (이미지-마스크 쌍) |')
        A(f'| 클래스 | **{len(raw["per_group"])}개 과일** → 전부 합쳐 과일 vs 배경 **이진 분할** |')
        A(f'| 해상도 | **512 × 512 로 통일** (원본은 {len(sizes)}종: '
          + ', '.join(f'{k} {v}장' for k, v in sorted(sizes.items(), key=lambda t: -t[1])) + ') |')
        A(f'| 학습 분할 | train **{split["per_group"]["train"]:,}** / val **{split["per_group"]["val"]}** / '
          f'test **{split["per_group"]["test"]}** (7:1:2) |')
        A(f'| 전경(과일) 픽셀 비율 | 평균 **{raw["fg_ratio"]["mean"]*100:.1f}%** '
          f'(중앙값 {raw["fg_ratio"]["median"]*100:.1f}%, 범위 {raw["fg_ratio"]["min"]*100:.1f}~{raw["fg_ratio"]["max"]*100:.1f}%) |')
        A('')
        A('**넣을 그림**')
        A('')
        A('- `reports/figures/fig_fruitseg30_class_counts.png` — 클래스별 장수 막대그래프')
        A('- `reports/figures/fig_fruitseg30_examples.png` — 원본/마스크/겹쳐보기 예시')
        A('- `reports/figures/fig_fruitseg30_fg_ratio.png` — 클래스별 전경 비율 (여유 있으면)')
        A('')
        A('**말할 내용**')
        A('')
        A(f'- "FruitSeg30은 과일 {len(raw["per_group"])}종 {raw["total_pairs"]:,}장짜리 공개 데이터셋이고, '
          '종류를 구분하지 않고 **과일이냐 배경이냐**만 맞히는 이진 분할로 바꿔서 썼습니다."')
        A('- "7:1:2로 나눴는데, 어떤 과일이 test에만 몰리지 않도록 **과일 종류별로 각각 나눴습니다**."')
        A(f'- "전경 비율이 평균 {raw["fg_ratio"]["mean"]*100:.0f}%로, **블루베리(약 2~3%)와 정반대**입니다. '
          '블루베리는 작은 알갱이가 흩어져 있고 이건 과일이 화면을 크게 채웁니다. '
          '→ 같은 모델이라도 성능이 다르게 나올 수 있는 이유."')
        conv = len(manifest.get('converted', [])) if manifest else 0
        if conv:
            A(f'- (질문 대비) "원본 {conv}장은 512가 아니었고 사진 회전정보(EXIF) 때문에 '
              '마스크와 크기가 어긋나 있었습니다. 회전을 적용해 바로잡고 512로 맞춘 뒤 썼습니다."')
    else:
        A('⚠️ 통계 JSON이 없습니다. `tools/dataset_stats.py`를 먼저 실행하세요.')
    A('')
    A('---')
    A('')

    # ---------------- 슬라이드 ②
    A('## 슬라이드 ② — 200에폭 학습 성능')
    A('')
    if done_epochs == 0:
        A('⏳ 아직 학습 기록이 없습니다.')
    else:
        A(f'현재 기록된 학습: **{done_epochs} / 200 epoch**'
          + ('  ✅ 완주' if training_done else '  ⏳ 진행 중 — 끝난 뒤 이 문서가 다시 갱신됩니다') + '\n')
        A('**넣을 표** (val = 검증 세트, 5에폭마다 기록)')
        A('')
        A('| 항목 | 값 |')
        A('|---|---|')
        if best_val:
            A(f'| 최저 val loss | **{best_val[1]:.4f}** (epoch {best_val[0]+1}) ← best 체크포인트 기준 |')
        if best_fg:
            A(f'| 최고 val fg_IoU | **{best_fg[1]:.4f}** (epoch {best_fg[0]+1}) |')
        if last_fg:
            A(f'| 마지막 val fg_IoU | {last_fg[1]:.4f} (epoch {last_fg[0]+1}) |')
        for tag, label in [('val/mIoU', 'val mIoU'), ('val/fg_Dice', 'val fg_Dice'),
                           ('val/fg_Precision', 'val fg_Precision'), ('val/fg_Recall', 'val fg_Recall')]:
            if scalars.get(tag):
                A(f'| 최고 {label} | {max(v for _, v in scalars[tag]):.4f} |')
        A('')
        A('**말할 내용**')
        A('')
        A('- "팀 공통 조건(UPerNet+ResNet-50, 512×512, batch 2, BCEDice, AdamW 1e-4)을 '
          '그대로 두고 **데이터 경로만** FruitSeg30으로 바꿔 200에폭 돌렸습니다."')
        if best_fg:
            A(f'- "검증 세트 기준 전경 IoU가 최고 **{best_fg[1]:.3f}** 까지 올라갔습니다."')
        A('- "best 체크포인트는 **val loss가 가장 낮은 시점**으로 저장됩니다(팀 공통 기준)."')
    A('')
    A('---')
    A('')

    # ---------------- 슬라이드 ③
    A('## 슬라이드 ③ — test 세트 성능')
    A('')
    if test:
        A('**넣을 표** (한 번도 학습에 쓰지 않은 test 세트)')
        A('')
        A('| 클래스 | IoU | Dice | Precision | Recall |')
        A('|---|---|---|---|---|')
        for k, ko in [('blueberry', '과일 (전경)'), ('background', '배경')]:
            if k in test:
                r = test[k]
                A(f'| {ko} | **{r["IoU"]:.4f}** | {r["Dice"]:.4f} | {r["Precision"]:.4f} | {r["Recall"]:.4f} |')
        if 'blueberry' in test and 'background' in test:
            miou = (test['blueberry']['IoU'] + test['background']['IoU']) / 2
            A(f'| **mIoU (평균)** | **{miou:.4f}** | | | |')
        A('')
        A('**말할 내용**')
        A('')
        fgv = test.get('blueberry', {}).get('IoU')
        if fgv is not None:
            A(f'- "학습에 한 번도 안 쓴 test {split["per_group"]["test"] if split else ""}장에서 '
              f'전경 IoU **{fgv:.3f}** 이 나왔습니다."')
        A('- "표의 클래스 이름이 `blueberry`로 나오는 건 코드가 블루베리용 데이터 클래스를 '
          '재사용하기 때문이고, 실제 의미는 **과일(전경)** 입니다."')
        A('- "블루베리는 전경이 2~3%라 mIoU가 배경에 묻혀서 fg_IoU를 봤는데, '
          '이 데이터셋은 전경이 30%대라 **mIoU도 의미가 있습니다.** 둘 다 적었습니다."')
    else:
        A('⏳ 학습이 끝나면 `tools/val.py --split test` 가 자동 실행되어 여기 채워집니다.')
        A('')
        A('직접 돌리려면:')
        A('```bash')
        A('cd /data/project/2026summer/kds0206/semantic-segmentation')
        A('export PY=/home/kds0206/.conda/envs/kwak/bin/python')
        A('export PYTHONPATH=/data/project/2026summer/kds0206/semantic-segmentation:$PYTHONPATH')
        A('CUDA_VISIBLE_DEVICES=2 $PY tools/val.py \\')
        A('  --cfg configs/fruitseg_upernet_resnet_50_bcedice_200ep.yaml \\')
        A('  --split test \\')
        A(f'  --model-path {RUN}/UPerNet_ResNet-50_BlueberryDataset_best.pth')
        A('```')
    A('')
    A('---')
    A('')

    # ---------------- 슬라이드 ④
    A('## 슬라이드 ④ — loss 그래프')
    A('')
    lossfig = FIGDIR / 'fig_fruitseg30_loss.png'
    if lossfig.exists():
        A(f'**넣을 그림**: `reports/figures/fig_fruitseg30_loss.png`')
        A('')
        A('**말할 내용**')
        A('')
        A('- "파란 선이 학습 loss, 주황 선이 검증 loss입니다. 둘 다 내려가면 정상적으로 배우는 중입니다."')
        A('- "검증 loss만 다시 올라가면 **과적합**(외운 것)이라는 신호인데, best 체크포인트는 '
          '검증 loss가 가장 낮았던 시점으로 저장돼 있습니다."')
        A('- "검증은 5에폭마다 재므로 주황 선이 파란 선보다 점이 듬성듬성합니다."')
    else:
        A('⏳ 학습이 끝나면 자동 생성됩니다 → `reports/figures/fig_fruitseg30_loss.png`')
        A('')
        A('직접 돌리려면:')
        A('```bash')
        A('$PY tools/plot_loss_curves.py \\')
        A(f'  --logdir {RUN}/logs \\')
        A('  --labels "FruitSeg30 UPerNet+ResNet-50" \\')
        A('  --out reports/figures/fig_fruitseg30_loss.png')
        A('```')
    A('')
    A('---')
    A('')

    # ---------------- 경로 정리
    A('## 파일이 어디 있나 (전부 절대경로)')
    A('')
    A('| 무엇 | 경로 |')
    A('|---|---|')
    A(f'| 그림 폴더 | `{FIGDIR}/` |')
    A(f'| 학습 결과·체크포인트 | `{RUN}/` |')
    A(f'| 학습 로그 (실시간) | `{REPO}/logs/fruitseg30_pipeline.log` |')
    A(f'| test 평가 로그 | `{REPO}/logs/fruitseg30_test_eval.log` |')
    A(f'| 데이터셋 (7:1:2) | `{DATASET}/` |')
    A(f'| 분할 기록 (재현용) | `{DATASET}/split_manifest.json` |')
    A(f'| 데이터 통계 JSON | `{REPO}/output/fruitseg30_stats.json` |')
    A(f'| config | `{REPO}/configs/fruitseg_upernet_resnet_50_bcedice_200ep.yaml` |')
    A(f'| 원본 zip | `{BASE}/incoming/` |')
    A(f'| 발표 PPT | `{BASE}/incoming/7월 27일 랩미팅.pptx` |')
    A('')
    A('## 진행 상황 확인 명령')
    A('')
    A('```bash')
    A('cd /data/project/2026summer/kds0206/semantic-segmentation')
    A('')
    A('# 지금 몇 에폭인지')
    A("tr '\\r' '\\n' < logs/fruitseg30_pipeline.log | grep -oE 'Epoch: \\[[0-9]+/200\\]' | tail -1")
    A('')
    A('# 학습이 살아있는지 (줄이 나오면 진행 중)')
    A('ps -u kds0206 -f | grep train.py | grep -v grep')
    A('')
    A('# 에러가 났는지 (아무것도 안 나오면 정상)')
    A("grep -iE 'error|traceback|out of memory' logs/fruitseg30_pipeline.log")
    A('')
    A('# 이 문서 다시 만들기 (숫자 갱신)')
    A('/home/kds0206/.conda/envs/kwak/bin/python tools/make_fruitseg30_summary.py')
    A('```')
    A('')

    DOC.write_text('\n'.join(L))
    print(f'\n[doc] {DOC}')
    print(f'      학습 진행: {done_epochs}/200 epoch, test결과={"있음" if test else "없음"}')


if __name__ == '__main__':
    main()
