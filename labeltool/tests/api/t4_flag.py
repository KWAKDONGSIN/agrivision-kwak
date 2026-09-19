# -*- coding: utf-8 -*-
"""t4 — 판정 «문제 있음(flag)» 갈래와 «AI» 이름 막기. 작성: 2026-09-20

왜 있나 (사이클 1 2차 검수 §5 «기준선이 덮지 못하는 것» 마지막 줄 · §10-3)
  얼려 둔 표본 12장에는 판정 `flag` 이 **한 장도 없다.** 그래서 기준선 ①②⑤ 는 flag 갈래를
  한 번도 지나지 않는다. 기준선 파일을 늘리면 «다시 뜨기(rebaseline)» 가 필요하고, 그것은
  같은 기준선을 쓰는 **구조 사이클 3** 을 흔든다 → 그래서 기준선 대신 **이 시험**으로 덮는다.

무엇을 못박나 (`app/api/masks.py` · `app/domain/rules.py` · `app/core/status_store.py`)
  ① `POST /api/save action=flag` → status=flag · 마스크는 쓰지 않는다
  ② flag 인 사진에 **수정본을 저장**하면 fixed 로 풀리고, 옛 flag 는 `prev` 에 한 벌 남는다
     (0918 UI사이클4 2차: 이 `prev` 가 없어 flag 사유·좌표가 단추 두 번에 사라졌다)
  ③ `POST /api/revert` 는 그 `prev` 로 **판정과 메모를 되살린다**
  ④ flag 로도 «사람 확정» 을 할 수 있고(`confirmed.status = flag`),
     내보내기 셈에서 **확정 장수에는 들지만 «나갈 장수» 에는 안 든다**(flag 제외 규칙)
  ⑤ «AI» 로 시작하는 이름은 `/api/status` 가 400 으로 막는다(0918 사이클4 N8)
"""
import base64
import io
import json
import os
import sys

from PIL import Image

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import sandbox as L                                   # tests/lib/sandbox.py

FR = "peach"
NOTE = "t4 사람 확인 필요 x1,y1,x2,y2: 12,34,56,78"


def gray_png(w, h, v=0):
    buf = io.BytesIO()
    Image.new("L", (w, h), v).save(buf, format="PNG")
    return "data:image/png;base64," + base64.b64encode(buf.getvalue()).decode()


def clear_one(fruit, stem):
    """**내 모래상자의** status.json 에서 그 한 장의 기록만 지운다(= «아직 안 봄» 으로 만든다).

    공용 `T/data` 는 건드리지 않는다 — `L.reset_status()` 가 만든 모래상자 사본만 고친다.
    왜 필요한가: AI 3회 검수가 복숭아 **전부**에 판정을 넣어 두어서, «판정이 없던 사진에
    flag 를 저장하면 그 flag 가 prev 에 남는다» 를 실제 자료로는 볼 수 없다.
    """
    p = os.path.join(L.SB, "data", fruit, "status.json")
    d = json.load(io.open(p, encoding="utf-8")) if os.path.exists(p) else {}
    d.pop(stem, None)
    with io.open(p, "w", encoding="utf-8") as f:
        json.dump(d, f, ensure_ascii=False, indent=1, sort_keys=True)


def main():
    L.sync()
    L.reset_status()
    p = L.start()
    try:
        a = L.Api()
        items = a.get("/api/list?fruit=%s&page_size=500" % FR)["items"]
        # AI 3회 검수가 이미 판정을 넣어 둔 사진을 쓰면 첫 저장이 그 판정을 `prev` 에 넣어 버려서
        # («맨 처음 것을 지킨다» 규칙) 뒤의 flag 가 prev 에 남지 못한다 — 그것도 규칙이므로
        # [나] 에서 따로 확인한다. 여기서는 **판정이 없는 사진**이 필요해서 한 장을 비운다.
        cand = [r["stem"] for r in items if not r.get("has_fixed")]
        s = next((r["stem"] for r in items
                  if r["status"] == "unreviewed" and not r.get("has_fixed")), None)
        s2 = next((r["stem"] for r in items
                   if r["status"] in ("ok", "fixed") and not r.get("has_fixed")), None)
        if s is None and len(cand) >= 2:
            s = cand[0] if cand[0] != s2 else cand[1]
            clear_one(FR, s)
            it0 = a.get("/api/item?fruit=%s&stem=%s" % (FR, s))
            L.chk("t4-0a 한 장을 «아직 안 봄» 으로 비웠다(모래상자 사본만)",
                  it0.get("status") == "unreviewed", (s, it0.get("status")))
        L.chk("t4-0 판정이 없는 사진과 AI 판정이 있는 사진을 하나씩 찾았다",
              bool(s) and bool(s2) and s != s2, (s, s2))
        if not s or not s2:
            return L.summary("t4_flag")
        it = a.get("/api/item?fruit=%s&stem=%s" % (FR, s))
        w, h = int(it["width"]), int(it["height"])
        it2 = a.get("/api/item?fruit=%s&stem=%s" % (FR, s2))
        w2, h2 = int(it2["width"]), int(it2["height"])

        # ① flag 저장
        code, r = a.post("/api/save", {"fruit": FR, "stem": s, "action": "flag",
                                       "by": "t4", "note": NOTE})
        L.chk("t4-1 action=flag → 200 · status=flag · 마스크는 쓰지 않는다",
              code == 200 and r["status"]["status"] == "flag" and r["wrote_mask"] is False,
              (code, r.get("status", {}).get("status"), r.get("wrote_mask")))
        L.chk("t4-1b 메모가 그대로 남는다", r["status"].get("note") == NOTE, r["status"].get("note"))

        # ② flag 사진에 수정본 저장 → fixed · prev 에 flag
        code, r = a.post("/api/save", {"fruit": FR, "stem": s, "action": "fixed",
                                       "by": "t4", "note": "붓질 한 번", "png": gray_png(w, h, 0)})
        rec = L.status_of(FR).get(s) or {}
        L.chk("t4-2 수정본 저장 → status=fixed", code == 200 and rec.get("status") == "fixed",
              (code, rec.get("status")))
        L.chk("t4-2b 옛 flag 가 prev 에 한 벌 남는다(사유를 잃지 않는다)",
              (rec.get("prev") or {}).get("status") == "flag"
              and (rec.get("prev") or {}).get("note") == NOTE, rec.get("prev"))

        # ③ 되돌리기 → flag·메모 되살림
        code, r = a.post("/api/revert", {"fruit": FR, "stem": s, "by": "t4"})
        rec = L.status_of(FR).get(s) or {}
        L.chk("t4-3 되돌리기 → 판정 flag 로 되살림", code == 200 and rec.get("status") == "flag",
              (code, rec.get("status")))
        L.chk("t4-3b 메모도 되살림", rec.get("note") == NOTE, rec.get("note"))
        L.chk("t4-3c 되살린 뒤 prev 는 지운다(두 번 되돌리기가 겹치지 않게)",
              "prev" not in rec, rec.get("prev"))

        # ④ flag 로 사람 확정
        before = a.get("/api/export_list")["fruits"][FR]
        code, r = a.post("/api/status", {"fruit": FR, "stem": s, "status": "flag",
                                        "by": "t4", "note": NOTE, "confirm": True})
        rec = L.status_of(FR).get(s) or {}
        L.chk("t4-4 flag 로도 사람 확정을 할 수 있다",
              code == 200 and (rec.get("confirmed") or {}).get("status") == "flag",
              (code, rec.get("confirmed")))
        after = a.get("/api/export_list")["fruits"][FR]
        L.chk("t4-4b 확정 장수는 늘고", after["n_confirmed"] == before["n_confirmed"] + 1,
              (before["n_confirmed"], after["n_confirmed"]))
        L.chk("t4-4c «나갈 장수» 는 그대로다(flag 는 내보내기에서 빠진다)",
              after["n_confirmed_out"] == before["n_confirmed_out"],
              (before["n_confirmed_out"], after["n_confirmed_out"]))
        L.chk("t4-4d 확정 집계의 flag 칸이 1 늘었다",
              after["confirmed_counts"]["flag"] == before["confirmed_counts"]["flag"] + 1,
              (before["confirmed_counts"]["flag"], after["confirmed_counts"]["flag"]))

        # [나] AI 가 이미 판정해 둔 사진 — 첫 저장이 그 판정을 prev 에 넣고, 뒤의 저장은 덮지 않는다
        #      («AI 가 넣은 판정은 지우지 않는다» 0918 사이클2 N1 · 0919 사이클5 2차)
        ai_before = dict(L.status_of(FR).get(s2) or {})
        a.post("/api/save", {"fruit": FR, "stem": s2, "action": "flag", "by": "t4", "note": NOTE})
        rec2 = L.status_of(FR).get(s2) or {}
        L.chk("t4-6 AI 판정이 있던 사진: 첫 저장이 그 판정을 prev 에 한 벌 남긴다",
              (rec2.get("prev") or {}).get("status") == ai_before.get("status"),
              (ai_before.get("status"), rec2.get("prev")))
        a.post("/api/save", {"fruit": FR, "stem": s2, "action": "fixed", "by": "t4",
                             "note": "붓질", "png": gray_png(w2, h2, 0)})
        rec2b = L.status_of(FR).get(s2) or {}
        L.chk("t4-6b 두 번째 저장은 prev 를 덮지 않는다(맨 처음 것을 지킨다)",
              rec2b.get("prev") == rec2.get("prev"), (rec2.get("prev"), rec2b.get("prev")))
        code, r = a.post("/api/revert", {"fruit": FR, "stem": s2, "by": "t4"})
        rec2c = L.status_of(FR).get(s2) or {}
        L.chk("t4-6c 되돌리기는 **맨 처음(AI) 판정**으로 되살린다",
              rec2c.get("status") == ai_before.get("status"),
              (ai_before.get("status"), rec2c.get("status")))

        # ⑤ «AI» 이름 막기
        code, r = a.post("/api/status", {"fruit": FR, "stem": s, "status": "ok",
                                        "by": "AI 3회 검수(t4)"})
        L.chk("t4-5 «AI» 로 시작하는 이름은 400", code == 400 and "AI" in (r.get("error") or ""),
              (code, r.get("error")))
    finally:
        L.stop(p)
    return L.summary("t4_flag")


if __name__ == "__main__":
    sys.exit(1 if main() else 0)
