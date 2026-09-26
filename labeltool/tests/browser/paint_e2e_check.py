# 그림판 끝-끝 시험 뒤, 저장된 마스크·번호·상자 파일이 화면의 라벨(L)과 같은지 디스크에서 대조한다
"""작성: 2026-09-24
쓰는 법: python paint_e2e_check.py <모래상자 폴더> <out_dir> <browser>
  <out_dir>/<browser>_result.json 의 stem·W·H 와 <browser>_L.bin(저장 직전 L, uint16 LE)을 읽어
  <모래상자>/data/peach/{masks_fixed,instances_fixed,boxes}/<stem>.* 와 비교한다.
"""
import json
import os
import sys

import numpy as np
from PIL import Image

HOLE = 65535
sb, out, br = sys.argv[1:4]
res = json.load(open(os.path.join(out, br + "_result.json"), encoding="utf-8"))
stem, W, H = res["stem"], res["W"], res["H"]
L = np.fromfile(os.path.join(out, br + "_L.bin"), dtype="<u2").reshape(H, W)
d = os.path.join(sb, "data", "peach")
fails = 0


def chk(name, cond, detail=""):
    global fails
    fails += not cond
    print(("PASS " if cond else "FAIL ") + name + ("  " + str(detail) if detail else ""))


m = np.array(Image.open(os.path.join(d, "masks_fixed", stem + ".png")))
chk("마스크 크기", m.shape[:2] == (H, W), m.shape)
mb = (m if m.ndim == 2 else m[..., 0]) > 0
chk("마스크 = 칠한 곳(L>0, 회색 포함)", np.array_equal(mb, L > 0), "다른 화소 %d" % int((mb != (L > 0)).sum()))

ins = np.array(Image.open(os.path.join(d, "instances_fixed", stem + ".png"))).astype(np.int64)
want = np.where(L == HOLE, 0, L).astype(np.int64)
# 서버는 번호를 1부터 다시 매길 수 있으므로 «같은 나눔» 인지(번호 이름이 아니라 묶음)로 본다
pairs = set(zip(ins[want > 0].tolist(), want[want > 0].tolist()))
chk("번호 파일: 번호 없는 칸 0", int((ins[want == 0] > 0).sum()) == 0, int((ins[want == 0] > 0).sum()))
chk("번호 파일: 같은 나눔(1:1)", len(pairs) == len({a for a, _ in pairs}) == len({b for _, b in pairs}),
    "짝 %d · 파일 번호 %d · 화면 번호 %d" % (len(pairs), len({a for a, _ in pairs}), len({b for _, b in pairs})))

bx = json.load(open(os.path.join(d, "boxes", stem + ".json"), encoding="utf-8"))
boxes = bx.get("boxes", bx) if isinstance(bx, dict) else bx
ids = [v for v in np.unique(want) if v and (want == v).sum() >= 4]
chk("상자 수 = 번호 수(4화소 이상)", len(boxes) == len(ids), "상자 %d · 번호 %d" % (len(boxes), len(ids)))
ok_box = 0
for v in ids:
    ys, xs = np.nonzero(want == v)
    t = [int(xs.min()), int(ys.min()), int(xs.max()) + 1, int(ys.max()) + 1]
    ok_box += any(list(map(int, b.get("xyxy", []))) == t for b in boxes)
chk("상자 좌표 = 번호 바깥 네모", ok_box == len(ids), "%d/%d" % (ok_box, len(ids)))

st = json.load(open(os.path.join(d, "status.json"), encoding="utf-8")).get(stem, {})
chk("status 사람 확정", bool(st), json.dumps(st, ensure_ascii=False)[:200])
# C18 작업 기록: 모래상자 app/logs/worklog.jsonl 에 이 사진 저장 줄(수정 1번 이상)과 빼기 줄이 있다
wl = os.path.join(sb, "app", "logs", "worklog.jsonl")
rows = [json.loads(x) for x in open(wl, encoding="utf-8")] if os.path.exists(wl) else []
sv = [r for r in rows if r["stem"] == stem and r["action"] == "save"]
chk("C18 작업 기록 저장 줄", bool(sv) and sv[0]["edits"] >= 1 and sv[0]["active_s"] > 0 and sv[0]["n_save"] >= 1, sv[:1])
chk("C18 작업 기록 빼기 줄", any(r["action"] == "exclude" for r in rows), len(rows))
print("%s 디스크 대조: %s" % (br, "통과" if not fails else "실패 %d" % fails))
sys.exit(1 if fails else 0)
