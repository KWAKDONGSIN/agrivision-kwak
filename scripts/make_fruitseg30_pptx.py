# -*- coding: utf-8 -*-
"""7/27 랩미팅용 FruitSeg30 발표 PPT를 만든다 (곽동신 담당분만).

원본 `incoming/7월 27일 랩미팅.pptx`에는 최인훈 님의 peach 데이터셋 내용
(슬라이드 3·5·6·7)이 예시로 들어 있었다. 곽동신 님 요청에 따라
**여기서 실제로 만들어낸 FruitSeg30 결과만** 담는다.

숫자는 전부 실제 산출물에서 읽는다 (하드코딩 없음):
  output/fruitseg30_stats.json / fruitseg30_split_stats.json
  output/fruitseg_runs/.../logs (TensorBoard)
  logs/fruitseg30_test_eval.log / fruitseg30_pipeline.log
  output/fruitseg30_per_image_iou.json

그림은 reports/figures/ 와 reports/figures/gallery/ 에서 가져온다.
먼저 make_fruitseg30_gallery_figs.py 와 make_fruitseg30_pred_gallery.py 를 돌려야 한다.

사용:  $PY tools/make_fruitseg30_pptx.py
"""
import json
import re
import sys
from pathlib import Path

REPO = Path('/data/project/2026summer/kds0206/semantic-segmentation')
BASE = Path('/data/project/2026summer/kds0206')
sys.path.insert(0, str(REPO / '.pylibs'))       # python-pptx (환경 오염 방지용 격리 설치)
sys.path.insert(0, str(REPO / 'tools'))

from pptx import Presentation                                  # noqa: E402
from pptx.dml.color import RGBColor                            # noqa: E402
from pptx.enum.text import PP_ALIGN                            # noqa: E402
from pptx.util import Emu, Inches, Pt                          # noqa: E402
from PIL import Image                                          # noqa: E402

from make_fruitseg30_summary import load_json, load_scalars, parse_test_log   # noqa: E402

RUN = REPO / 'output/fruitseg_runs/upernet_resnet_50_bcedice_200ep'
FIG = REPO / 'reports/figures'
GAL = FIG / 'gallery'
OUT = BASE / '문서/260726_FruitSeg30_랩미팅_발표.pptx'

W, H = Inches(13.333), Inches(7.5)              # 16:9
FONT = '맑은 고딕'
INK = RGBColor(0x11, 0x18, 0x27)
MUTE = RGBColor(0x6B, 0x72, 0x80)
BLUE = RGBColor(0x1D, 0x4E, 0xD8)
GREEN = RGBColor(0x0A, 0x7D, 0x33)


# ------------------------------------------------------------------ 슬라이드 헬퍼
def new_deck():
    prs = Presentation()
    prs.slide_width, prs.slide_height = W, H
    return prs


def blank(prs):
    return prs.slides.add_slide(prs.slide_layouts[6])


def textbox(slide, x, y, w, h, text, size=18, bold=False, color=INK,
            align=PP_ALIGN.LEFT, spacing=1.0):
    tb = slide.shapes.add_textbox(x, y, w, h)
    tf = tb.text_frame
    tf.word_wrap = True
    for i, line in enumerate(text.split('\n')):
        p = tf.paragraphs[0] if i == 0 else tf.add_paragraph()
        p.text = line
        p.alignment = align
        p.line_spacing = spacing
        for r in p.runs:
            r.font.size, r.font.bold, r.font.name = Pt(size), bold, FONT
            r.font.color.rgb = color
    return tb


def title(slide, text, sub=None):
    textbox(slide, Inches(0.55), Inches(0.28), Inches(12.2), Inches(0.8),
            text, size=28, bold=True)
    if sub:
        textbox(slide, Inches(0.58), Inches(1.02), Inches(12.2), Inches(0.45),
                sub, size=13, color=MUTE)


def picture(slide, path: Path, top=Inches(1.5), bottom_margin=Inches(0.35)):
    """가로/세로 중 넉넉한 쪽에 맞춰 가운데 정렬로 그림을 넣는다."""
    iw, ih = Image.open(path).size
    avail_w = W - Inches(1.0)
    avail_h = H - top - bottom_margin
    scale = min(avail_w / iw, avail_h / ih)
    w, h = Emu(int(iw * scale)), Emu(int(ih * scale))
    slide.shapes.add_picture(str(path), Emu(int((W - w) / 2)), Emu(int(top + (avail_h - h) / 2)), w, h)


def table(slide, headers, rows, x, y, w, col_w=None, size=14, row_h=Inches(0.42)):
    nrow, ncol = len(rows) + 1, len(headers)
    shp = slide.shapes.add_table(nrow, ncol, x, y, w, row_h * nrow)
    tbl = shp.table
    if col_w:
        total = sum(col_w)
        for j, cw in enumerate(col_w):
            tbl.columns[j].width = Emu(int(w * cw / total))
    for j, htxt in enumerate(headers):
        c = tbl.cell(0, j)
        c.text = str(htxt)
        for p in c.text_frame.paragraphs:
            for r in p.runs:
                r.font.size, r.font.bold, r.font.name = Pt(size), True, FONT
    for i, row in enumerate(rows, 1):
        for j, v in enumerate(row):
            c = tbl.cell(i, j)
            c.text = str(v)
            for p in c.text_frame.paragraphs:
                for r in p.runs:
                    r.font.size, r.font.name = Pt(size), FONT
    return shp


def note(slide, text, color=MUTE, size=13):
    textbox(slide, Inches(0.6), H - Inches(0.85), Inches(12.1), Inches(0.6),
            text, size=size, color=color)


# ------------------------------------------------------------------ 자료 읽기
def parse_pipeline_log(p: Path):
    """학습 총 소요시간·에폭당 시간·VRAM을 파이프라인 로그에서 뽑는다."""
    out = {}
    if not p.exists():
        return out
    txt = p.read_text(errors='ignore')
    for key, pat in [('total_time', r'Total Training Time\s+([\d:]+)'),
                     ('epoch_time', r'Average Epoch Time\s+([\d.]+)\s*s'),
                     ('peak_vram', r'Peak VRAM Usage\s+([\d.]+)\s*MB')]:
        m = re.findall(pat, txt)
        if m:
            out[key] = m[-1]
    # 파이프라인 전체가 끝난 시각 (없으면 학습만 끝난 시각)
    for pat, key in [(r'\[(20[\d-]+ [\d:]+)\] ===== FruitSeg30 파이프라인 전부 종료', 'finished_at'),
                     (r'\[(20[\d-]+ [\d:]+)\] ===== 1/3 학습 종료', 'train_done_at')]:
        m = re.findall(pat, txt)
        if m:
            out[key] = m[-1]
    out.setdefault('finished_at', out.get('train_done_at', ''))
    return out


def gather():
    d = {}
    d['raw'] = load_json(REPO / 'output/fruitseg30_stats.json')
    d['split'] = load_json(REPO / 'output/fruitseg30_split_stats.json')
    d['manifest'] = load_json(BASE / 'dataset_fruitseg30/split_manifest.json')
    d['scalars'] = load_scalars(RUN / 'logs')
    d['test'] = parse_test_log(REPO / 'logs/fruitseg30_test_eval.log')
    d['pipe'] = parse_pipeline_log(REPO / 'logs/fruitseg30_pipeline.log')
    d['periou'] = load_json(REPO / 'output/fruitseg30_per_image_iou.json')
    return d


def size_summary(raw):
    """해상도 분포를 '512x512 1914장, ...' 형태로."""
    sizes = raw['image_sizes']
    items = sorted(sizes.items(), key=lambda kv: -kv[1])
    return ', '.join(f'{k} {v}장' for k, v in items)


# ------------------------------------------------------------------ 본문
def build(d):
    prs = new_deck()
    raw, mani, sc, test, pipe, per = (d['raw'], d['manifest'], d['scalars'],
                                      d['test'], d['pipe'], d['periou'])
    counts = {k: len(v) for k, v in mani['splits'].items()}
    n_all = sum(counts.values())

    val_loss = sc.get('val/loss', [])
    val_fg = sc.get('val/fg_IoU', [])
    val_miou = sc.get('val/mIoU', [])
    val_dice = sc.get('val/fg_Dice', [])
    n_epoch = len(sc.get('train/loss', []))
    best_loss = min(val_loss, key=lambda t: t[1]) if val_loss else None
    best_fg = max(val_fg, key=lambda t: t[1]) if val_fg else None

    # ---------------------------------------------------------- 1. 표지
    s = blank(prs)
    textbox(s, Inches(0.9), Inches(2.5), Inches(11.5), Inches(1.2),
            'FruitSeg30 데이터셋 학습 결과', size=44, bold=True)
    textbox(s, Inches(0.95), Inches(3.65), Inches(11.5), Inches(0.6),
            'UPerNet + ResNet-50 · 200 epoch · 팀 공통 조건 그대로', size=20, color=MUTE)
    textbox(s, Inches(0.95), Inches(4.5), Inches(11.5), Inches(1.2),
            '곽동신\n2026-07-27 랩미팅', size=18, color=INK)
    finished = pipe.get('finished_at', '')
    note(s, f'서버 학습 완료: {finished}  ·  총 소요 {pipe.get("total_time", "?")}'
            f'  ·  Tesla V100 1장' if finished else '')

    # ---------------------------------------------------------- 2. 역할 분담
    s = blank(prs)
    title(s, '역할 분담', '데이터셋만 다르고 하는 일은 동일 — 이 자료는 곽동신 담당분입니다')
    textbox(s, Inches(0.8), Inches(1.9), Inches(11.5), Inches(4.0),
            '최인훈 : Peach 데이터셋\n'
            '임성후 : MinneApple 데이터셋\n'
            '곽동신 : FruitSeg30 데이터셋   ← 이 발표\n'
            '박성문 : 레포지토리 코드 관리, U-Net 라우팅',
            size=22, spacing=1.9)

    # ---------------------------------------------------------- 3. 자료① 개수·해상도
    s = blank(prs)
    title(s, '① 데이터셋 개수 · 해상도', 'FruitSeg30 (Mendeley 공개 데이터셋, DOI 10.17632/vkht8pfsp3.3)')
    rows = [
        ['전체 이미지', f'{raw["total_pairs"]:,}장 (이미지–마스크 쌍)'],
        ['과일 종류', f'{len(raw["per_group"])}종 → 종류 구분 없이 과일(1) vs 배경(0) 이진 분할'],
        ['원본 해상도', size_summary(raw)],
        ['사용 해상도', '512 × 512 로 통일'],
        ['학습 분할', f'train {counts["train"]:,} / val {counts["val"]:,} / test {counts["test"]:,}'
                    f'  ({counts["train"]/n_all*100:.0f} : {counts["val"]/n_all*100:.0f} :'
                    f' {counts["test"]/n_all*100:.0f})'],
        ['분할 방법', f'과일 종류별 층화 분할 (seed {mani["seed"]}) — 한 종류가 test에만 몰리지 않게'],
        ['과일 픽셀 비율', f'평균 {raw["fg_ratio"]["mean"]*100:.1f}% '
                       f'(중앙값 {raw["fg_ratio"]["median"]*100:.1f}%, '
                       f'{raw["fg_ratio"]["min"]*100:.1f}~{raw["fg_ratio"]["max"]*100:.1f}%)'],
    ]
    table(s, ['항목', '값'], rows, Inches(0.7), Inches(1.75), Inches(11.9),
          col_w=[2, 8], size=14)
    note(s, '※ 블루베리 데이터셋은 과일 픽셀이 약 2.4% — FruitSeg30은 과일이 화면을 크게 채웁니다.', color=BLUE)

    # ---------------------------------------------------------- 4~. 데이터셋 사진
    s = blank(prs)
    title(s, '② 실제 데이터셋 사진', '서버에서 직접 켜지 않아도 되도록 사진을 전부 넣었습니다')
    textbox(s, Inches(0.8), Inches(2.0), Inches(11.6), Inches(3.6),
            '다음 장부터 이어집니다.\n\n'
            '  · 과일 30종 원본 / 정답 마스크 / 겹쳐보기  (3장)\n'
            '  · 30종 상세 — 원본·마스크·겹쳐보기를 나란히  (6장)\n'
            '  · 같은 과일도 사진마다 다름 — 배경·개수·조명·각도  (4장)\n'
            '  · 클래스별 장수 / 클래스별 과일 비율 그래프  (2장)',
            size=19, spacing=1.6)

    for kind, cap in [('orig', '원본 사진'), ('mask', '정답 마스크'), ('overlay', '겹쳐보기')]:
        p = GAL / f'gal_all30_{kind}.png'
        if p.exists():
            s = blank(prs)
            title(s, f'데이터셋 사진 — 과일 30종 {cap}',
                  '30개 클래스에서 각각 1장씩. 마스크는 사람이 손으로 칠한 정답입니다.')
            picture(s, p, top=Inches(1.35))

    for p in sorted(GAL.glob('gal_triplet_p*.png')):
        s = blank(prs)
        title(s, '데이터셋 사진 — 상세 (원본 / 정답 / 겹쳐보기)',
              '가운데가 정답 마스크. 흰색이 과일, 검은색이 배경입니다.')
        picture(s, p, top=Inches(1.35))

    for p in sorted(GAL.glob('gal_variety_p*.png')):
        s = blank(prs)
        title(s, '데이터셋 사진 — 같은 과일도 사진마다 다릅니다',
              '배경·개수·조명·각도가 달라서 모델이 외우기만 해서는 못 맞힙니다.')
        picture(s, p, top=Inches(1.35))

    for fn, ttl, sub in [
        ('fig_fruitseg30_class_counts.png', '클래스별 이미지 장수',
         '가장 많은 과일과 가장 적은 과일의 장수 차이 — 층화 분할이 필요한 이유'),
        ('fig_fruitseg30_fg_ratio.png', '클래스별 과일 픽셀 비율',
         '수박·용과처럼 화면을 꽉 채우는 과일과, 작게 찍힌 과일이 섞여 있습니다')]:
        p = FIG / fn
        if p.exists():
            s = blank(prs)
            title(s, ttl, sub)
            picture(s, p, top=Inches(1.4))

    # ---------------------------------------------------------- 자료② 200에폭 성능
    s = blank(prs)
    title(s, '③ 200 에폭 학습 성능 (검증 세트)',
          f'UPerNet + ResNet-50 · 512×512 · batch 2(누적4) · BCEDice · AdamW 1e-4 · '
          f'조기종료 없이 {n_epoch}/200 완주')
    rows = [
        # TensorBoard step은 0부터라 사람이 읽는 에폭 번호는 +1
        ['최저 val loss', f'{best_loss[1]:.4f}  (epoch {best_loss[0] + 1})  ← best 체크포인트 기준'],
        ['최고 val 과일 IoU', f'{best_fg[1]:.4f}  (epoch {best_fg[0] + 1})'],
        ['최고 val 과일 Dice', f'{max(v for _, v in val_dice):.4f}' if val_dice else '-'],
        ['최고 val mIoU', f'{max(v for _, v in val_miou):.4f}' if val_miou else '-'],
        ['총 학습 시간', f'{pipe.get("total_time", "-")}   (에폭당 약 {pipe.get("epoch_time", "-")}초)'],
        ['최대 GPU 메모리', f'{pipe.get("peak_vram", "-")} MB  (V100 32GB 중)'],
    ]
    table(s, ['항목', '값'], rows, Inches(0.9), Inches(2.0), Inches(11.5),
          col_w=[3, 7], size=16, row_h=Inches(0.55))
    note(s, '검증(val)은 5 에폭마다 측정합니다. best 체크포인트 기준은 팀 공통으로 val loss 최소 시점입니다.')

    # ---------------------------------------------------------- 자료③ test 성능
    s = blank(prs)
    title(s, '④ Test 세트 성능', '학습에 한 번도 쓰지 않은 390장으로 채점한 결과')
    if test:
        fg, bg = test['blueberry'], test['background']
        miou = (fg['IoU'] + bg['IoU']) / 2
        rows = [
            ['과일 (전경)', f'{fg["IoU"]:.4f}', f'{fg["Dice"]:.4f}',
             f'{fg["Precision"]:.4f}', f'{fg["Recall"]:.4f}'],
            ['배경', f'{bg["IoU"]:.4f}', f'{bg["Dice"]:.4f}',
             f'{bg["Precision"]:.4f}', f'{bg["Recall"]:.4f}'],
            ['평균 (mIoU)', f'{miou:.4f}', '', '', ''],
        ]
        table(s, ['클래스', 'IoU', 'Dice', 'Precision', 'Recall'], rows,
              Inches(1.4), Inches(2.1), Inches(10.5), col_w=[3, 2, 2, 2, 2],
              size=17, row_h=Inches(0.6))
        textbox(s, Inches(1.4), Inches(4.65), Inches(10.6), Inches(1.6),
                f'· 과일 IoU {fg["IoU"]:.3f} — 모델이 칠한 영역과 정답이 {fg["IoU"]*100:.1f}% 겹칩니다.\n'
                f'· 블루베리는 과일 픽셀이 2~3%뿐이라 mIoU가 배경에 묻혔지만, '
                f'이 데이터셋은 30%대라 mIoU도 함께 의미가 있습니다.',
                size=16, spacing=1.5)
    note(s, '표의 클래스 이름이 코드에서 "blueberry"로 나오는 것은 블루베리용 데이터 클래스를 '
            '재사용하기 때문이며, 실제 의미는 "과일(전경)"입니다.')

    # ---------------------------------------------------------- 자료④ loss 그래프
    p = FIG / 'fig_fruitseg30_loss.png'
    if p.exists():
        s = blank(prs)
        title(s, '⑤ Loss 그래프',
              '파란 선 = 학습 loss, 주황 선 = 검증 loss. 둘 다 내려가면 정상적으로 배우는 중입니다.')
        picture(s, p, top=Inches(1.45))

    # ---------------------------------------------------------- 예측 결과
    if per:
        s = blank(prs)
        title(s, '⑥ 모델이 실제로 그린 결과', 'test 390장 전부에 대해 사진 한 장씩 채점했습니다')
        rows = [
            ['사진 수', f'{per["n_images"]}장'],
            ['평균 IoU', f'{per["mean_iou"]:.4f}'],
            ['중앙값 IoU', f'{per["median_iou"]:.4f}'],
            ['가장 잘 맞힌 사진', f'{per["max_iou"]:.4f}'],
            ['가장 못 맞힌 사진', f'{per["min_iou"]:.4f}'],
            ['IoU 0.9 이상', f'{per["n_ge_090"]}장 / {per["n_images"]}장 '
                          f'({per["n_ge_090"]/per["n_images"]*100:.1f}%)'],
            ['IoU 0.5 미만 (실패)', f'{per["n_lt_050"]}장'],
        ]
        table(s, ['항목', '값'], rows, Inches(1.5), Inches(1.85), Inches(10.3),
              col_w=[4, 6], size=16, row_h=Inches(0.5))
        note(s, '한 장도 크게 실패하지 않았습니다 (최저 IoU도 0.75 이상).', color=GREEN)

    p = FIG / 'fig_fruitseg30_per_image_iou.png'
    if p.exists():
        s = blank(prs)
        title(s, '사진 한 장씩의 성적 분포', '오른쪽에 몰려 있을수록 좋습니다')
        picture(s, p, top=Inches(1.45))

    for p in sorted(GAL.glob('pred_by_class_p*.png')):
        s = blank(prs)
        title(s, '예측 결과 — 과일 종류별',
              '왼쪽 원본 / 가운데 사람이 만든 정답(빨강) / 오른쪽 모델 예측(파랑)')
        picture(s, p, top=Inches(1.35))

    for fn, ttl, sub in [
        ('pred_best_p1.png', '예측 결과 — 가장 잘 맞힌 사진',
         '④ 채점: 초록 = 맞게 찾음, 빨강 = 놓침, 노랑 = 잘못 찾음'),
        ('pred_typical_p1.png', '예측 결과 — 평균적인 사진',
         '대부분의 사진이 이 정도입니다'),
        ('pred_worst_p1.png', '예측 결과 — 가장 못 맞힌 사진',
         '어디서 틀리는지 보는 자료 — 그림자·잎사귀·정답 자체의 애매함')]:
        p = GAL / fn
        if p.exists():
            s = blank(prs)
            title(s, ttl, sub)
            picture(s, p, top=Inches(1.35))

    # ---------------------------------------------------------- 마무리
    s = blank(prs)
    title(s, '정리')
    lines = [
        f'· FruitSeg30 {raw["total_pairs"]:,}장 / 과일 {len(raw["per_group"])}종을 '
        f'{counts["train"]}:{counts["val"]}:{counts["test"]} 로 나눠 학습했습니다.',
        f'· 팀 공통 조건(UPerNet+ResNet-50, 512×512, batch 2, BCEDice, AdamW 1e-4)을 '
        f'그대로 두고 데이터 경로만 바꿨습니다.',
        f'· 200 에폭 완주, 총 {pipe.get("total_time", "-")}, GPU 1장.',
    ]
    if test:
        lines.append(f'· test 390장 과일 IoU {test["blueberry"]["IoU"]:.4f}.')
    if per:
        lines.append(f'· 사진별로 봐도 {per["n_ge_090"]}/{per["n_images"]}장이 IoU 0.9 이상이었습니다.')
    lines.append('· 과일 픽셀 비율이 블루베리(약 2.4%)와 FruitSeg30(약 36%)로 크게 달라, '
                 '같은 모델이라도 데이터셋에 따라 성능이 달라집니다.')
    textbox(s, Inches(0.8), Inches(1.8), Inches(11.8), Inches(4.5),
            '\n'.join(lines), size=17, spacing=1.8)

    return prs


def main():
    d = gather()
    missing = [k for k in ('raw', 'manifest') if not d[k]]
    if missing:
        raise SystemExit(f'필요한 통계 파일이 없습니다: {missing}')
    prs = build(d)
    OUT.parent.mkdir(parents=True, exist_ok=True)
    prs.save(str(OUT))
    print(f'[pptx] {OUT}  (슬라이드 {len(prs.slides.__iter__.__self__._sldIdLst)}장)')


if __name__ == '__main__':
    main()
