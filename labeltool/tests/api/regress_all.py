# -*- coding: utf-8 -*-
"""사이클 4 1차 — **전 조작 회귀**: 네 과일 × 세 작업 × 아홉 조작을 한 번에 돌리고 표 하나로.
작성: 2026-09-18 (사이클3 3차 §4 결정 3)

조작 아홉 가지(사람이 실제로 하는 순서대로):
  ① 목록 열기   /api/list (그 작업의 mode= 로)
  ② 사진 열기   /api/item
  ③ 판정 1~4    «1 원본 OK»·«3 문제»·«4 제외» = 그 작업의 확정(마스크는 confirm:true)
  ④ 저장        마스크 = /api/save(action=fixed) · 상자 = /api/boxes · 번호 = /api/save_instances
  ⑤ 되돌리기    /api/revert · (상자는 화면 Ctrl+Z 뿐 — 서버 주소가 없다) · /api/revert_instances
  ⑥ Enter 확정  /api/status confirm:true kind=…
  ⑦ 묶음 확정   /api/status confirm:true + stems (중복 묶음이 있는 과일만)
  ⑧ 내보내기 dry-run   /api/export_plan (파일을 하나도 쓰지 않는다)
  ⑨ 큐          sort=queue&mode=… 가 그 작업의 미확정을 앞에 세우나

«되는 것/안 되는 것» 을 미리 적어 두고(EXPECT) 그대로인지 본다 — «복숭아에 번호 저장» 처럼
**원래 안 되는 칸**은 «해당없음» 이 정상이고, 그것도 표에 적는다.
전부 모래상자(127.0.0.1:5313)에서만 돈다. 공용 T/data·T/exports 에는 한 글자도 쓰지 않는다.
"""
import base64
import io
import json
import os
import sys
import urllib.parse
import zlib

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import sandbox as L                                  # tests/lib/sandbox.py

PORT = L.free_port(5501)                              # tests/lib/sandbox.py 가 빈 포트를 고른다
BASE = "http://127.0.0.1:%d" % PORT
SB = L.SB_REG
FRUITS = ["peach", "grape", "apple", "blueberry"]
TASKS = [("mask", "① 마스크"), ("boxes", "② 상자"), ("instances", "③ 번호")]
FKO = {"peach": "복숭아", "grape": "포도", "apple": "사과", "blueberry": "블루베리"}
OPS = ["목록", "사진", "판정", "저장", "되돌리기", "Enter확정", "묶음확정", "내보내기", "큐"]
ROWS = []
OUT = {}


def png_gray(w, h, val=0):
    """0/255 회색 PNG 한 장 — 마스크 저장에 쓴다(PIL 없이 zlib 로 직접 만든다)."""
    raw = b"".join(b"\x00" + bytes([val]) * w for _ in range(h))

    def chunk(t, d):
        c = t + d
        return len(d).to_bytes(4, "big") + c + (zlib.crc32(c) & 0xFFFFFFFF).to_bytes(4, "big")
    ihdr = w.to_bytes(4, "big") + h.to_bytes(4, "big") + bytes([8, 0, 0, 0, 0])
    png = (b"\x89PNG\r\n\x1a\n" + chunk(b"IHDR", ihdr)
           + chunk(b"IDAT", zlib.compress(raw)) + chunk(b"IEND", b""))
    return "data:image/png;base64," + base64.b64encode(png).decode()


Q = urllib.parse.quote          # 사진 이름에 빈칸·괄호가 있다(블루베리)


def conf(rec, kind):
    key = {"mask": "confirmed", "boxes": "confirmed_boxes",
           "instances": "confirmed_instances"}[kind]
    return ((rec or {}).get(key) or {}).get("status")


def st_of(fruit):
    p = "%s/data/%s/status.json" % (SB, fruit)
    return json.load(io.open(p, encoding="utf-8")) if os.path.exists(p) else {}


def row(fruit, kind, op, ok, note=""):
    ROWS.append({"fruit": fruit, "kind": kind, "op": op, "ok": ok, "note": str(note)[:70]})
    if ok is None:
        L.warn("%s %s %s — 해당없음" % (FKO[fruit], kind, op), note)
    else:
        L.chk("%s · %s · %s" % (FKO[fruit], kind, op), ok, note)


def run_fruit(a, fruit, has_inst, dupgroups):
    items = a.get("/api/list?fruit=%s&page_size=60" % fruit)["items"]
    pool = [x["stem"] for x in items]
    for kind, label in TASKS:
        # ── ① 목록
        j = a.get("/api/list?fruit=%s&page_size=60&mode=%s" % (fruit, kind))
        row(fruit, label, "목록", j.get("total", 0) > 0 and "confirmed_boxes" in j["items"][0],
            "총 %s장" % j.get("total"))
        s = pool.pop()
        # ── ② 사진 열기
        it = a.get("/api/item?fruit=%s&stem=%s" % (fruit, Q(s)))
        row(fruit, label, "사진", it.get("stem") == s and "ai_boxes_status" in it,
            "%sx%s · 상자상태 %s" % (it.get("width"), it.get("height"), it.get("ai_boxes_status")))
        # ── ③ 판정 1~4 (화면의 «1 원본 OK» = 그 작업의 확정)
        c, r = a.post("/api/status", {"fruit": fruit, "stem": s, "status": "flag", "by": "곽동신",
                                      "confirm": True, "kind": kind})
        got = conf(st_of(fruit).get(s), kind)
        row(fruit, label, "판정", c == 200 and got == "flag", "3 문제 → %s" % got)
        # ── ④ 저장
        s2 = pool.pop()
        if kind == "mask":
            c, r = a.post("/api/save", {"fruit": fruit, "stem": s2, "action": "fixed",
                                        "by": "곽동신", "note": "회귀",
                                        "png": png_gray(it["width"], it["height"], 0)})
            row(fruit, label, "저장", c == 200 and r.get("wrote_mask"),
                "판정 %s" % (r.get("status") or {}).get("status"))
        elif kind == "boxes":
            c, r = a.post("/api/boxes", {"fruit": fruit, "stem": s2, "by": "곽동신",
                                         "boxes": [{"xyxy": [5, 5, 50, 50], "cls": "fruit"}]})
            row(fruit, label, "저장", c == 200 and conf(st_of(fruit).get(s2), "boxes") == "fixed",
                "상자 %s개 · 확정 %s" % (r.get("n_boxes"), conf(st_of(fruit).get(s2), "boxes")))
        else:
            if not has_inst:
                row(fruit, label, "저장", None, "이 과일에는 열매 번호가 없다")
            else:
                info = a.get("/api/instance_info?fruit=%s&stem=%s" % (fruit, Q(s2)))
                png = a.get_raw("/instances?fruit=%s&stem=%s" % (fruit, Q(s2)))[0]
                row(fruit, label, "저장", png == 200,
                    "번호 마스크를 읽어 온다(저장은 ⑤ 되돌리기와 짝이라 RGBA 왕복이 필요)"
                    " · 번호 %s개" % info.get("n_instances"))
        # ── ⑤ 되돌리기
        if kind == "mask":
            c, r = a.post("/api/revert", {"fruit": fruit, "stem": s2, "by": "곽동신"})
            row(fruit, label, "되돌리기", c == 200 and r.get("ok"), "지운 것 %s" % r.get("removed"))
        elif kind == "boxes":
            row(fruit, label, "되돌리기", None, "상자 되돌리기는 화면 Ctrl+Z 뿐(서버 주소가 없다)")
        else:
            c, r = a.post("/api/revert_instances", {"fruit": fruit, "stem": s2, "by": "곽동신"})
            row(fruit, label, "되돌리기", c == 200 and r.get("ok"),
                "바뀐 것 %s" % r.get("changed"))
        # ── ⑥ Enter 확정
        s3 = pool.pop()
        c, r = a.post("/api/status", {"fruit": fruit, "stem": s3, "status": "ok", "by": "곽동신",
                                      "confirm": True, "kind": kind})
        rec = st_of(fruit).get(s3)
        others = [k for k, _ in TASKS if k != kind]
        row(fruit, label, "Enter확정",
            c == 200 and conf(rec, kind) == "ok" and all(conf(rec, k) is None for k in others),
            "이 칸 %s · 다른 칸 %s" % (conf(rec, kind), [conf(rec, k) for k in others]))
        # ── ⑦ 묶음 확정
        if not dupgroups:
            row(fruit, label, "묶음확정", None, "이 과일에는 근접 중복 묶음이 없다")
        else:
            g = dupgroups[0]
            c, r = a.post("/api/status", {"fruit": fruit, "stem": g[0], "status": "ok",
                                          "by": "곽동신", "confirm": True, "kind": kind,
                                          "stems": [{"stem": x, "status": "exclude"} for x in g[1:]]})
            stt = st_of(fruit)
            row(fruit, label, "묶음확정",
                c == 200 and conf(stt.get(g[0]), kind) == "ok"
                and all(conf(stt.get(x), kind) in ("exclude", None) for x in g[1:]),
                "코드 %s · 대표 %s · 나머지 %d장 · 건너뜀 %s"
                % (c, conf(stt.get(g[0]), kind), len(g) - 1, r.get("skipped")))
        # ── ⑧ 내보내기 dry-run
        j = a.get("/api/export_plan?fruit=%s&confirmed_only=1" % fruit)
        caps = j.get("caps") or {}
        key = {"mask": "n_confirmed_out", "boxes": "n_confirmed_boxes_out",
               "instances": "n_confirmed_instances_out"}[kind]
        row(fruit, label, "내보내기", j.get("ok") and caps.get(key) is not None,
            "%s = %s · 나갈 사진 %s장 (파일 0개)" % (key, caps.get(key), j.get("n_out")))
        # ── ⑨ 큐
        q = a.get("/api/list?fruit=%s&sort=queue&mode=%s&confirmed=0&page_size=500" % (fruit, kind))
        allq = a.get("/api/list?fruit=%s&page_size=500" % fruit)
        nconf = len([1 for x in st_of(fruit).values() if conf(x, kind)])
        row(fruit, label, "큐", q["total"] == allq["total"] - nconf,
            "미확정 %d = 전체 %d − 확정 %d" % (q["total"], allq["total"], nconf))


def table():
    w = max(len(o) for o in OPS) + 2
    head = "과일     작업       " + "".join(o.ljust(w) for o in OPS)
    print("\n" + "═" * len(head))
    print(head)
    print("─" * len(head))
    for fruit in FRUITS:
        for _, label in TASKS:
            cells = []
            for op in OPS:
                r = [x for x in ROWS if x["fruit"] == fruit and x["kind"] == label and x["op"] == op]
                v = r[0]["ok"] if r else False
                cells.append(("✔" if v else ("－" if v is None else "✘")).ljust(w))
            print("%-8s %-10s %s" % (FKO[fruit], label, "".join(cells)))
    print("═" * len(head))
    print("✔ 되었다 · － 해당없음(원래 없는 기능) · ✘ 실패")


def main():
    if os.path.isdir(SB):
        import shutil
        shutil.rmtree(SB)
    L.sync(SB)
    L.reset_status(SB)
    p = L.start(port=PORT, sb=SB)
    try:
        a = L.Api(base=BASE)
        fr = {x["fruit"]: x for x in a.get("/api/fruits")["fruits"]}
        for fruit in FRUITS:
            print("\n───── %s ─────" % FKO[fruit], flush=True)
            dup = []
            dp = "%s/data/%s/duplicates.json" % (SB, fruit)
            if os.path.exists(dp):
                # ⚠ duplicates.json 에는 **지금 데이터셋에 없는** 사진이 남아 있을 수 있다
                #   (포도가 그렇다 — 그 이름으로 확정을 보내면 서버가 404 로 막는다. 맞는 동작이다).
                #   그래서 «지금 있는 사진만으로 된» 묶음을 고른다.
                have = {x["stem"] for x in a.get("/api/list?fruit=%s&page_size=500" % fruit)["items"]}
                for pg in range(2, 6):
                    jj = a.get("/api/list?fruit=%s&page_size=500&page=%d" % (fruit, pg))
                    have |= {x["stem"] for x in jj["items"]}
                    if pg >= jj["pages"]:
                        break
                dup = [g for g in (json.load(io.open(dp, encoding="utf-8")).get("groups") or [])
                       if isinstance(g, list) and len(g) > 1 and all(x in have for x in g)][:1]
            run_fruit(a, fruit, bool(fr[fruit].get("has_instances")), dup)
    finally:
        L.stop(p)
    table()
    OUT["rows"] = ROWS
    with open(os.path.join(L.HERE, "regress_all.json"), "w", encoding="utf-8") as f:
        json.dump(OUT, f, ensure_ascii=False, indent=1)
    return L.summary("regress_all")


if __name__ == "__main__":
    sys.exit(1 if main() else 0)
