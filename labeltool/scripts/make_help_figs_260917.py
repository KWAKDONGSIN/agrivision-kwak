# -*- coding: utf-8 -*-
"""사용법 페이지(app/static/help.html)에 넣을 예시 그림. 작성: 2026-09-17
최종 수정: 2026-09-19 («개수 세기» 사이클4 · M12)
실행: /home/kds0206/.conda/envs/kwak/bin/python scripts/make_help_figs_260917.py
출력: app/static/help/*.jpg  (원본·data/ 는 읽기만 한다)
그림은 툴 화면을 찍은 것이 아니라, 툴과 같은 색 규칙으로 실제 데이터에서 다시 그린 것이다(서버에 브라우저가 없음).

🔴 2026-09-19 M12 — **«내 수정본» 색이 초록에서 시안(하늘색)으로 바뀌었다.** 0919 사용자 지적
(«잎이 초록이라 마킹이 안 보인다») 으로 화면을 고쳤는데(`app/static/app.js` 의 `#00e5ff`), 이 그림은
아직 초록이라 사용법 페이지와 실제 화면의 색이 **달랐다**. 색값은 화면과 **한 글자도 같게** 둔다:
  · 수정본 시안  `#00e5ff` = (0, 229, 255)   ← app.js ctx.strokeStyle · ui.js 색 설명 · help.html 색표
  · 상자 테두리도 같은 `#00e5ff` (전에는 `#00c8ff` 로 미묘하게 달랐다)
색을 또 바꿀 일이 생기면 **화면 쪽을 먼저 고치고 그 hex 를 여기에 옮겨 적는다**(두 군데에 규칙을 두지 않는다).
"""
import json
from pathlib import Path

import numpy as np
from PIL import Image
from scipy import ndimage
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.font_manager import FontProperties

T = Path(__file__).resolve().parents[1]
STD = Path('/data/project/2026summer/kds0206/datasets_resized_2mp')
OUT = T / 'app/static/help'
OUT.mkdir(parents=True, exist_ok=True)
FP = FontProperties(fname='/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc')
RED, BLUE, GREEN, YEL = (230, 40, 40), (40, 110, 255), (30, 190, 80), (255, 215, 0)
CYAN = (0, 229, 255)          # = #00e5ff — 화면의 «내 수정본» 색과 같은 값(위 설명)
CYAN_HEX = '#00e5ff'          # 상자 테두리(matplotlib 는 hex 를 받는다)


def rgb(p): return np.array(Image.open(p).convert('RGB'))
def mask(p):
    a = np.array(Image.open(p)); return (a.max(axis=2) if a.ndim == 3 else a) > 0
def paint(img, m, c, a=.5):
    o = img.copy(); o[m] = ((1 - a) * img[m] + a * np.array(c)).astype(np.uint8); return o
def edge(m): return m & ~ndimage.binary_erosion(m, iterations=3)


def save(fig, name):
    # 🔴 2026-09-19 «개수 세기» 사이클4 **2차 검수**: `tight_layout()` 만 쓰면 **제목 글자의 윗부분이
    #   그림 위 테두리에서 잘렸다**(실측 `ex4_box.jpg` 위 여백 **0px** — «사진 (확대)» 의 ㅅ·ㅈ 윗선이 깎임).
    #   사용법 페이지에 그대로 실리는 그림이라 `bbox_inches='tight'` + 여백 0.06in 을 준다.
    #   (그림 내용·색·글자는 한 자도 바뀌지 않는다 — 바깥 여백만 생긴다.)
    fig.tight_layout(); p = OUT / name
    fig.savefig(p, dpi=100, bbox_inches='tight', pad_inches=0.06, pil_kwargs={'quality': 85})
    plt.close(fig); print(p.name, p.stat().st_size // 1024, 'KB')


def panels(ims, titles, name, size):
    f, ax = plt.subplots(1, len(ims), figsize=size)
    for a, im, t in zip(np.atleast_1d(ax), ims, titles):
        a.imshow(im); a.set_title(t, fontproperties=FP, fontsize=14); a.axis('off')
    save(f, name)


def crop_to(m, pad=80):
    ys, xs = np.where(m); H, W = m.shape
    return slice(max(ys.min() - pad, 0), min(ys.max() + pad, H)), slice(max(xs.min() - pad, 0), min(xs.max() + pad, W))


# 1) 원본 그대로 OK — 빨강(원본)과 파랑(AI)이 거의 같은 복숭아
s = '210629-t2-of12-01'
img, gt, ai = rgb(STD / 'peach/images' / (s + '.png')), mask(STD / 'peach/masks' / (s + '.png')), mask(T / 'data/peach/proposals' / (s + '.png'))
panels([img, paint(img, gt, RED), paint(img, ai, BLUE)], ['사진', '빨강 = 원본 GT', '파랑 = AI 제안 (원본과 거의 같음 → «원본 그대로 OK»)'], 'ex1_ok.jpg', (16, 5.2))

# 2) 라벨이 빠진 열매 — 차이 보기(노랑 = AI 만 잡은 곳) → 고쳐서 «수정본 저장»
s = '210629-t4-17'
img, gt, ai = rgb(STD / 'peach/images' / (s + '.png')), mask(STD / 'peach/masks' / (s + '.png')), mask(T / 'data/peach/proposals' / (s + '.png'))
fx = mask(T / 'data/peach/masks_fixed' / (s + '.png'))
added = fx & ~gt
sl = (slice(280, 740), slice(100, 580))   # 새로 넣은 복숭아 3개가 모여 있는 자리
d = paint(paint(img, gt, RED), ai & ~gt, YEL, .65)
g = paint(img, fx, CYAN); g[edge(added)] = (255, 255, 255)   # 0919 M12: 초록 → 시안(화면과 같게)
panels([img[sl], d[sl], g[sl]], ['사진 (확대)', '«차이 보기»: 노랑 = AI 만 잡은 곳 = 라벨이 빠진 후보', '하늘색(시안) = 고쳐서 저장한 수정본 (흰 테두리 = 새로 넣은 열매)'], 'ex2_fix.jpg', (16, 5.6))

# 3) 거의 같은 사진(중복) → 대표 1장만 남기고 «제외»
grp = json.load(open(T / 'data/grape/duplicates.json'))['groups'][0][:3]
panels([rgb(STD / 'grape/images' / (x + '.png')) for x in grp], ['포도 %s%s' % (x, ' (대표로 남김)' if i == 0 else ' → 제외') for i, x in enumerate(grp)], 'ex3_dup.jpg', (15, 8.6))

# 4) 상자 모드 — 사과 번호마다 상자 하나(초벌)
s = '20150919_174151_image1'
img = rgb(STD / 'apple/images' / (s + '.png')); inst = np.array(Image.open(STD / 'apple/masks' / (s + '.png'))).astype(np.int32)
big = int(np.argmax(np.bincount(inst.ravel())[1:]) + 1)
cy, cx = [int(v) for v in ndimage.center_of_mass(inst == big)]
R = 190; sl = (slice(max(cy - R, 0), cy + R), slice(max(cx - R, 0), cx + R)); y0, x0 = sl[0].start, sl[1].start
film = (0.75 * img + 0.25 * 255).astype(np.uint8)
f, ax = plt.subplots(1, 2, figsize=(12, 6.2))
ax[0].imshow(img[sl]); ax[0].set_title('사진 (확대)', fontproperties=FP, fontsize=14)
ax[1].imshow(film[sl]); ax[1].set_title('상자 모드: «마스크에서 초벌 생성» → 알마다 상자 하나', fontproperties=FP, fontsize=14)
for i, b in enumerate(ndimage.find_objects(inst), 1):
    if b is None or (inst[b] == i).sum() < 4: continue
    ys, xs = b
    ax[1].add_patch(plt.Rectangle((xs.start - x0, ys.start - y0), xs.stop - xs.start, ys.stop - ys.start, fill=False, ec=CYAN_HEX, lw=2))
for a in ax: a.set_xlim(0, 2 * R); a.set_ylim(2 * R, 0); a.axis('off')
save(f, 'ex4_box.jpg')

# 5) 열매 번호 편집 네 가지 — 같은 사과 확대 부분에서 고치기 전/후를 흉내 냄
sub, im = inst[sl].copy(), img[sl]
rng = np.random.RandomState(3); pal = rng.randint(70, 255, (int(inst.max()) + 5, 3))
ids = [i for i in np.unique(sub) if i > 0 and (sub == i).sum() > 300]
near = lambda a: [j for j in ids if j != a and (ndimage.binary_dilation(sub == a, iterations=6) & (sub == j)).any()]
pair = next(((a, near(a)[0]) for a in ids if near(a)), (ids[0], ids[1]))
new = int(inst.max()) + 1


def draw(a, arr, title, mark=None):
    o = im.copy(); m = arr > 0; o[m] = (0.4 * im[m] + 0.6 * pal[arr[m]]).astype(np.uint8)
    a.imshow(o); a.set_title(title, fontproperties=FP, fontsize=13); a.axis('off')
    for i in np.unique(arr[m]):
        if (arr == i).sum() < 300: continue
        y, x = ndimage.center_of_mass(arr == i)
        a.text(x, y, str(i), color='white', fontsize=11, ha='center', va='center', weight='bold',
               bbox=dict(boxstyle='round,pad=.15', fc='black', ec='none', alpha=.6))
    if mark is not None: mark(a)


d_ = sub.copy(); d_[d_ == big] = 0
m_ = sub.copy(); m_[m_ == pair[1]] = pair[0]
x_ = sub.copy(); yy, xx = np.where(sub == big); xm = int(xx.mean()); x_[(sub == big) & (np.arange(sub.shape[1])[None, :] > xm)] = new; x_[(sub == big) & (np.abs(np.arange(sub.shape[1])[None, :] - xm) <= 1)] = 0
free = ndimage.distance_transform_edt(sub == 0); free[:40] = free[-40:] = 0; free[:, :40] = free[:, -40:] = 0; fy, fx_ = np.unravel_index(np.argmax(free), free.shape); r = int(min(free.max() * .8, 28))
n_ = sub.copy(); Y, X = np.ogrid[:sub.shape[0], :sub.shape[1]]; n_[((Y - fy) ** 2 + (X - fx_) ** 2 <= r * r) & (sub == 0)] = new
f, ax = plt.subplots(2, 4, figsize=(18, 9.4))
for k, (arr, t0, t1, mk) in enumerate([
        (d_, '지우기 전: %d번을 클릭' % big, 'D 키 → %d번이 사라짐' % big, None),
        (m_, '합치기 전: %d번 클릭, %d번 클릭' % pair, 'M 키 → 둘 다 %d번' % pair[0], None),
        (x_, '나누기 전: %d번 위에 선을 긋기' % big, 'X 키 → %d번과 새 번호 %d번' % (big, new), lambda a: a.plot([xm, xm], [yy.min() - 8, yy.max() + 8], color='yellow', lw=2.5)),
        (n_, '붙이기 전: 빈 자리에 영역 그리기', 'N 키 → 새 번호 %d번' % new, lambda a: a.add_patch(plt.Circle((fx_, fy), r, fill=False, ec='yellow', lw=2.5)))]):
    draw(ax[0, k], sub, t0, mk); draw(ax[1, k], arr, t1)
save(f, 'ex5_numbers.jpg')
