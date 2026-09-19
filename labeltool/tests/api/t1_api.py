# -*- coding: utf-8 -*-
"""사이클 4 1차 — 서버 쪽 시험: 상자·번호 «확정» · 큐 모드 · 내보내기 종류별 확정 · N7·N8.
작성: 2026-09-18

전부 모래상자(127.0.0.1:5311 · cycle_4/stage1/sandbox)에서만 돈다.
공용 T/data·T/exports 에는 한 글자도 쓰지 않는다. 실서버(5111)는 켜지도 붙지도 않는다.
"""
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import sandbox as L                                  # tests/lib/sandbox.py

OUT = {}
FR = "apple"          # 번호가 있는 과일(상자·번호 둘 다 시험)
FR2 = "peach"         # 번호가 없는 과일(분기 확인)


def all_items(a, fruit, extra=""):
    """목록 전부 — page_size 상한이 500 이라 사과 1,001장은 두 쪽으로 온다."""
    out, page = [], 1
    while True:
        j = a.get("/api/list?fruit=%s&page_size=500&page=%d%s" % (fruit, page, extra))
        out += j["items"]
        if page >= j["pages"]:
            return out
        page += 1


def conf_of(rec, kind):
    key = {"mask": "confirmed", "boxes": "confirmed_boxes",
           "instances": "confirmed_instances"}[kind]
    return ((rec or {}).get(key) or {}).get("status")


# ═════════════════════════════ [가] 상자 확정 ═════════════════════════════
def t_boxes(a):
    print("\n[가] 상자 확정 — Enter(맞다) · 저장(수정함) · 마스크 확정과 독립")
    L.reset_status()
    items = a.get("/api/list?fruit=%s&page_size=20" % FR)["items"]
    s0, s1 = items[0]["stem"], items[1]["stem"]
    L.chk("가-0 목록에 새 칸 셋이 있다(confirmed_boxes·confirmed_instances·ai_boxes_status)",
          all(k in items[0] for k in ("confirmed_boxes", "confirmed_instances", "ai_boxes_status")),
          {k: items[0].get(k) for k in ("confirmed_boxes", "confirmed_instances", "ai_boxes_status")})
    it = a.get("/api/item?fruit=%s&stem=%s" % (FR, s0))
    L.chk("가-0b 한 장 상세에도 있다(+ n_boxes·n_inst)",
          all(k in it for k in ("confirmed_boxes", "confirmed_instances", "ai_boxes_status",
                                "n_boxes", "n_inst")),
          {k: it.get(k) for k in ("ai_boxes_status", "n_boxes", "n_inst")})
    OUT["item_new_fields"] = {k: it.get(k) for k in ("ai_boxes_status", "n_boxes", "n_inst")}

    # 먼저 **마스크** 를 확정해 둔다 — 상자 확정이 이것을 건드리지 않는지 보려고
    a.post("/api/status", {"fruit": FR, "stem": s0, "status": "ok", "by": "곽동신", "confirm": True})
    before_mask = conf_of(L.status_of(FR).get(s0), "mask")

    # ① AI 초벌만 있는 사진에서 Enter = 화면의 초벌을 **저장한 뒤** «원본 OK» 로 확정
    #    (ui.js enterConfirmTask 와 같은 순서 — 초벌은 파일이 아니라 화면에만 있기 때문이다)
    seed = a.get("/api/boxes_seed?fruit=%s&stem=%s" % (FR, s0))
    L.chk("가-0c 초벌 상자를 만들 수 있다", seed.get("ok") and seed.get("n", 0) > 0, seed.get("n"))
    a.post("/api/boxes", {"fruit": FR, "stem": s0, "by": "곽동신", "boxes": seed["boxes"]})
    code, r = a.post("/api/status", {"fruit": FR, "stem": s0, "status": "ok", "by": "곽동신",
                                     "confirm": True, "kind": "boxes"})
    rec = L.status_of(FR).get(s0)
    L.chk("가-1 Enter(저장+확정) → confirmed_boxes.status = ok — 저장이 찍은 fixed 를 덮는다", code == 200 and conf_of(rec, "boxes") == "ok",
          (code, conf_of(rec, "boxes")))
    L.chk("가-1b 응답이 kind 를 되돌려 준다", r.get("kind") == "boxes", r.get("kind"))
    L.chk("가-2 ❗마스크 확정(confirmed)은 그대로다(독립)",
          conf_of(rec, "mask") == before_mask == "ok", (before_mask, conf_of(rec, "mask")))
    L.chk("가-2b 번호 확정은 아직 없다", conf_of(rec, "instances") is None, conf_of(rec, "instances"))

    # ② 상자를 고쳐 저장 → fixed
    code, r = a.post("/api/boxes", {"fruit": FR, "stem": s1, "by": "곽동신",
                                    "boxes": [{"xyxy": [10, 10, 60, 60], "cls": "fruit"}]})
    rec1 = L.status_of(FR).get(s1)
    L.chk("가-3 상자 저장 → confirmed_boxes.status = fixed",
          code == 200 and conf_of(rec1, "boxes") == "fixed", (code, conf_of(rec1, "boxes")))
    L.chk("가-3b 그 사진의 마스크 확정은 생기지 않았다", conf_of(rec1, "mask") is None,
          conf_of(rec1, "mask"))
    L.chk("가-4 목록에도 나온다", [x for x in all_items(a, FR)
                                if x["stem"] == s1][0]["confirmed_boxes"] == "fixed")
    L.chk("가-4b ai_boxes_status 가 saved 로 바뀐다",
          a.get("/api/item?fruit=%s&stem=%s" % (FR, s1))["ai_boxes_status"] == "saved")

    # ③ 과일 집계
    f = [x for x in a.get("/api/fruits")["fruits"] if x["fruit"] == FR][0]
    L.chk("가-5 /api/fruits 에 종류별 확정 집계가 있다",
          f.get("n_confirmed_boxes") == 2 and f.get("n_confirmed") == 1,
          {k: f.get(k) for k in ("n_confirmed", "n_confirmed_boxes", "n_confirmed_instances")})
    OUT["fruits_counts"] = {k: f.get(k) for k in
                            ("n_confirmed", "n_confirmed_boxes", "n_confirmed_instances")}
    return s0, s1


# ═════════════════════════════ [나] 번호 확정 ═════════════════════════════
def t_inst(a):
    print("\n[나] 번호 확정 — 사과·블루베리는 되고, 복숭아·포도는 번호 자체가 없다")
    items = a.get("/api/list?fruit=%s&page_size=20" % FR)["items"]
    s = items[2]["stem"]
    code, r = a.post("/api/status", {"fruit": FR, "stem": s, "status": "ok", "by": "곽동신",
                                     "confirm": True, "kind": "instances"})
    rec = L.status_of(FR).get(s)
    L.chk("나-1 kind=instances → confirmed_instances 에만 쓰인다",
          code == 200 and conf_of(rec, "instances") == "ok"
          and conf_of(rec, "mask") is None and conf_of(rec, "boxes") is None,
          {k: conf_of(rec, k) for k in ("mask", "boxes", "instances")})
    f2 = [x for x in a.get("/api/fruits")["fruits"] if x["fruit"] == FR2][0]
    # 🔴 기대값이 바뀌었다 — 2026-09-19 «개수 세기» **사이클4 결정 M1**(사이클3 3차 §2-1):
    # 초벌을 «다시 구현하지 말고 박성문 워터셰드 출력을 쓴다» 로 바꾸면서 `instances.SEED_DIRS` 에
    # 복숭아(`bbox_outputs/peach/all/instance_maps`)와 포도(CERTH 정답 송이 `data/grape/instances_seed`)를
    # 넣었다. 그래서 **네 과일 모두 `has_instances=True`** 다. 전에는 복숭아·포도가 False 였다.
    # (끄려면 `SEED_DIRS` 에서 그 과일 한 줄을 빼고 재시작 — 그러면 이 단정도 옛 값으로 돌아온다.)
    L.chk("나-2 복숭아도 번호본이 있다고 말한다(has_instances=True · 사이클4 M1)",
          f2.get("has_instances") is True, f2.get("has_instances"))
    fb = [x for x in a.get("/api/fruits")["fruits"] if x["fruit"] == "blueberry"][0]
    L.chk("나-3 블루베리는 번호가 있다", fb.get("has_instances") is True, fb.get("has_instances"))
    # 번호가 없는 과일에서도 «확정 칸» 자체는 만들 수 있다(화면이 ③ 를 못 켜게 막는다)
    p0 = a.get("/api/list?fruit=%s&page_size=5" % FR2)["items"][0]["stem"]
    code, _ = a.post("/api/status", {"fruit": FR2, "stem": p0, "status": "ok", "by": "곽동신",
                                     "confirm": True, "kind": "instances"})
    L.chk("나-4 복숭아에 번호 확정을 보내도 서버는 깨지지 않는다(화면이 ③ 를 막는다)", code == 200, code)
    return s


# ═════════════════════════════ [다] 큐 모드 ═════════════════════════════
def t_queue(a, s_box, s_inst):
    print("\n[다] sort=queue 가 mode= 로 그 작업의 미확정을 앞에 세운다")
    q_mask = all_items(a, FR, "&sort=queue")
    q_box = all_items(a, FR, "&sort=queue&mode=boxes")
    idx = lambda q, s: [i for i, x in enumerate(q) if x["stem"] == s][0]      # noqa: E731
    n = len(q_mask)
    L.chk("다-1 mask 큐: 마스크를 확정한 장이 맨 뒤",
          idx(q_mask, s_box) > n - 5, "%d / %d" % (idx(q_mask, s_box), n))
    L.chk("다-2 boxes 큐: 상자를 확정한 장이 맨 뒤(마스크 확정과 자리가 다르다)",
          idx(q_box, s_box) > n - 5 and idx(q_box, s_inst) < n - 5,
          "%s → %d · %s → %d" % (s_box, idx(q_box, s_box), s_inst, idx(q_box, s_inst)))
    q_inst = all_items(a, FR, "&sort=queue&mode=instances")
    L.chk("다-3 instances 큐: 번호를 확정한 장이 맨 뒤",
          idx(q_inst, s_inst) > n - 5, "%d" % idx(q_inst, s_inst))
    L.chk("다-4 mode 가 이상하면 예전(mask)과 똑같다",
          [x["stem"] for x in all_items(a, FR, "&sort=queue&mode=zzz")]
          == [x["stem"] for x in q_mask])
    # «내 큐» = 미확정만 거르기도 모드를 따른다
    c_mask = a.get("/api/list?fruit=%s&sort=queue&confirmed=0&page_size=500" % FR)["total"]
    c_box = a.get("/api/list?fruit=%s&sort=queue&confirmed=0&mode=boxes&page_size=500" % FR)["total"]
    L.chk("다-5 «미확정만» 도 모드를 따른다(마스크 1장 · 상자 2장 확정했으므로 장수가 다르다)",
          c_mask == n - 1 and c_box == n - 2, "mask %d · boxes %d · 전체 %d" % (c_mask, c_box, n))
    OUT["queue"] = {"n": n, "conf0_mask": c_mask, "conf0_boxes": c_box}


# ═════════════════════════════ [라] 내보내기 ═════════════════════════════
def t_export(a, s_box, s_boxfix):
    print("\n[라] 내보내기 «사람 확정만» — 상자 YOLO 는 confirmed_boxes 만(사이클3 2차 중간 5)")
    import time
    caps = a.get("/api/export_plan?fruit=%s" % FR)["caps"]
    L.chk("라-0 export_caps 에 종류별 확정 장수가 있다",
          caps.get("n_confirmed_boxes_out") == 2 and caps.get("n_confirmed_instances_out") == 1,
          {k: caps.get(k) for k in ("n_confirmed_out", "n_confirmed_boxes_out",
                                    "n_confirmed_instances_out")})
    OUT["caps"] = {k: caps.get(k) for k in ("n_confirmed_out", "n_confirmed_boxes_out",
                                            "n_confirmed_instances_out", "n_box_images")}
    # 확정되지 않은 상자를 한 장 더 만들어 둔다 — 그 장은 나가면 안 된다
    other = [x["stem"] for x in all_items(a, FR)
             if x["stem"] not in (s_box, s_boxfix)][0]
    a.post("/api/boxes", {"fruit": FR, "stem": other, "by": "곽동신",
                          "boxes": [{"xyxy": [5, 5, 40, 40]}]})
    # 저장이 곧 확정이므로 일부러 확정을 지운다(«옛 자료 = 확정 칸이 없음» 을 흉내낸다)
    st = L.status_of(FR)
    st[other].pop("confirmed_boxes", None)
    with open("%s/data/%s/status.json" % (L.SB, FR), "w", encoding="utf-8") as f:
        json.dump(st, f, ensure_ascii=False)

    code, r = a.post("/api/export_start", {"fruit": FR, "kinds": ["boxes"],
                                           "confirmed_only": True, "by": "곽동신"})
    L.chk("라-1 상자만 내보내기 시작", code == 200 and r.get("ok"), (code, r))
    job = r.get("job")
    for _ in range(300):
        j = a.get("/api/export_status?job=" + job)
        if j.get("state") != "running":
            break
        time.sleep(0.5)
    out = L.SB + "/exports/" + job
    txt = sorted(n[:-4] for n in os.listdir(out + "/boxes") if n.endswith(".txt"))
    L.chk("라-2 ❗확정한 상자 사진만 txt 가 나온다", txt == sorted([s_box, s_boxfix]), txt)
    L.chk("라-3 ❗확정 없는 사진의 txt 는 안 나간다", other not in txt, other)
    OUT["box_export_confirmed"] = {"txt": txt, "unconfirmed": other}

    # 폴더 이름이 «초 단위 시각 + 과일» 이라 같은 초에 두 번 시작하면 409 다(사이클3 규칙) — 1초 쉰다
    time.sleep(1.2)
    code, r = a.post("/api/export_start", {"fruit": FR, "kinds": ["boxes"],
                                           "confirmed_only": False, "by": "곽동신"})
    if not L.chk("라-3b 두 번째 내보내기가 시작된다", code == 200 and r.get("job"), (code, str(r)[:90])):
        return
    job2 = r.get("job")
    for _ in range(300):
        if a.get("/api/export_status?job=" + job2).get("state") != "running":
            break
        time.sleep(0.5)
    txt2 = sorted(n[:-4] for n in os.listdir(L.SB + "/exports/" + job2 + "/boxes")
                  if n.endswith(".txt"))
    L.chk("라-4 «AI 제안 포함» 이면 저장된 상자 전부가 나간다(예전 그대로)",
          txt2 == sorted([s_box, s_boxfix, other]), txt2)
    OUT["box_export_all"] = txt2


# ═════════════════════════════ [마] N7·N8 ═════════════════════════════
def t_n78(a):
    print("\n[마] N7(stems 타입) · N8(«AI…» 이름) — 500 이 아니라 사람 말로 400")
    s = a.get("/api/list?fruit=%s&page_size=5" % FR)["items"][0]["stem"]
    for bad in ("문자열", 5, {"stem": s}, ["문자열", 5]):
        code, r = a.post("/api/status", {"fruit": FR, "stem": s, "status": "ok", "by": "곽동신",
                                         "confirm": True, "stems": bad})
        L.chk("마-1 stems=%s → 400" % json.dumps(bad, ensure_ascii=False)[:20], code == 400,
              (code, str(r)[:90]))
    code, r = a.post("/api/status", {"fruit": FR, "stem": s, "status": "flag", "by": "AI현자"})
    L.chk("마-2 ❗«AI» 로 시작하는 이름은 400", code == 400, (code, str(r)[:90]))
    L.chk("마-2b 그 이름으로는 아무것도 안 쓰인다",
          (L.status_of(FR).get(s) or {}).get("by") != "AI현자",
          (L.status_of(FR).get(s) or {}).get("by"))
    code, _ = a.post("/api/status", {"fruit": FR, "stem": s, "status": "ok", "by": "곽동신",
                                     "confirm": True, "kind": "zzz"})
    L.chk("마-3 모르는 kind 는 400", code == 400, code)
    OUT["n78"] = "ok"


def main():
    L.sync()
    L.reset_status()
    L.clear_exports()
    p = L.start()
    try:
        a = L.Api()
        s_box, s_boxfix = t_boxes(a)
        s_inst = t_inst(a)
        t_queue(a, s_box, s_inst)
        t_export(a, s_box, s_boxfix)
        t_n78(a)
    finally:
        L.stop(p)
    with open(os.path.join(L.HERE, "t1_api.json"), "w", encoding="utf-8") as f:
        json.dump(OUT, f, ensure_ascii=False, indent=1)
    return L.summary("t1_api")


if __name__ == "__main__":
    sys.exit(1 if main() else 0)
