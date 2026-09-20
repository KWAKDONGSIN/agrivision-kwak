"""상자(bounding box) 라벨 — 사진 위에 «투명 필름» 을 덮고 그 위에 네모를 친다.

작성: 2026-09-17 (0917 요청: 검출 팀용 상자 그리기)
저장 위치: data/<fruit>/boxes/<stem>.json   — 원본 데이터셋은 절대 건드리지 않는다.
내보내기:  data/<fruit>/boxes_yolo/<stem>.txt (YOLO 정규화 좌표) + boxes_all.json

server.py 가 이 파일의 register(app, ctx) 를 부른다. ctx 로 경로·잠금·상태 함수를 넘겨받아
서버의 기존 규칙(원본 읽기 전용·파일 잠금·상태 기록)을 그대로 따른다.
"""

from __future__ import annotations
from typing import Any
import json
import os
import threading

import numpy as np
from flask import jsonify, request
from PIL import Image

from api import instances as INST   # 번호 마스크를 어디서 읽을지는 instances.py 한 군데에만 둔다
from domain import rules
from domain.rules import (CLASSES, MAX_BOXES, MIN_SIDE, boxes_of, clean,
                          human_count, is_box_clear_save)

# 0919 사용자: «내가 치는 것 말고도 상자를 친 것이 각자 데이터에 있는가» → 있다. 검출 팀 두 사람이
# 팀 표준 2MP 마스크에서 자동으로 뽑은 상자(`bbox_outputs/<fruit>/all/json/<stem>.json` 의
# detections[].bbox_xyxy, 픽셀 좌표). **읽기 전용** — 남의 폴더에는 아무것도 쓰지 않는다.
# 순서 = 초벌 기본값 순서(박성문 것이 통합 데이터셋의 boxes_source 이기도 하다).
TEAM_BOX_DIRS = [("박성문", "/data/project/2026summer/platform/work/park_seongmoon/bbox_outputs"),
                 ("임성후", "/data/project/2026summer/platform/work/im_seonghu/bbox_outputs")]
TEAM_CLS = {"grape": "bunch"}              # 포도는 «송이» 단위 라벨, 나머지는 알·과실


def team_box_path(who: str, fruit: str, stem: str) -> str | None:
    """팀원이 저장한 상자 파일의 경로를 찾는다."""
    d = dict(TEAM_BOX_DIRS).get(who)
    return os.path.join(d, fruit, "all", "json", stem + ".json") if d else None


def read_team_boxes(who: str, fruit: str, stem: str, w: int, h: int) -> Any:
    """팀원 상자를 툴 형식으로. 사진 크기가 다르면(원본 해상도로 만든 파일) 비율로 맞춘다.
    없으면 None. (json 이 없거나 깨졌으면 None — «없음» 과 같이 다룬다)"""
    p = team_box_path(who, fruit, stem)
    if not p or not os.path.exists(p):
        return None
    try:
        with open(p, encoding="utf-8") as f:
            d = json.load(f)
    except Exception:
        return None
    hw = d.get("image_size_hw") or [h, w]
    sx, sy = w / float(hw[1] or w), h / float(hw[0] or h)
    cls = TEAM_CLS.get(fruit, "fruit")
    out = []
    for det in d.get("detections", []):
        b = det.get("bbox_xyxy")
        if not b or len(b) < 4:
            continue
        out.append({"cls": cls, "src": "auto",
                    "xyxy": [b[0] * sx, b[1] * sy, b[2] * sx, b[3] * sy]})
    return out


def team_count(who: str, fruit: str, stem: str) -> Any:
    """팀원 상자가 **몇 개**인가만 — 좌표를 옮기지 않으니 사진을 열지 않는다(개수 칸·counts.csv 용).

    0919 «개수 세기» 사이클1. `read_team_boxes()` 와 **같은 것을 센다**(bbox_xyxy 가 4개 이상인
    detections). 다른 점 하나: `clean()` 이 2픽셀 미만 상자를 버리므로 화면에 그려지는 개수가
    1~2개 적을 수 있다 — 팀원 초벌은 «참고 값» 이고 사람 확정 개수로는 쓰지 않는다(아래 human_count).
    파일이 없거나 깨졌으면 None(= «없음», 화면은 «-»).
    """
    p = team_box_path(who, fruit, stem)
    if not p or not os.path.exists(p):
        return None
    try:
        with open(p, encoding="utf-8") as f:
            d = json.load(f)
    except Exception:
        return None
    return sum(1 for det in (d.get("detections") or [])
               if isinstance(det.get("bbox_xyxy"), (list, tuple)) and len(det["bbox_xyxy"]) >= 4)


def export_boxes_to(data_dir: Any, fruit: str, out_dir: Any, all_json: Any=None, at: str="", stems: Any=None) -> Any:
    """사람이 저장한 상자 → YOLO txt(out_dir) + 한 파일 JSON(all_json).

    0918 사이클4 결정 1: `stems` 를 주면 **그 사진들만** 낸다(«사람 확정만» 내보내기에서
    `confirmed_boxes` 가 ok/fixed 인 사진만 고르는 데 쓴다 — 사이클3 2차 §2 중간 5 가 남긴 구멍).
    주지 않으면 예전과 한 글자도 다르지 않다(저장된 상자 전부).

    0918 사이클3: 예전에는 이 몸통이 api_boxes_export() **안에만** 있어서 제자리
    (data/<과일>/boxes_yolo/)로만 내보낼 수 있었다. 글자 그대로 빼내어 «데이터 정리» 탭의
    exports/<날짜시각>_<과일>/boxes/ 와 기존 단추가 **같은 함수**를 쓰게 한다.
    줄 내용·정렬·낡은 txt 세는 규칙은 하나도 바꾸지 않았다.

    🔴 0919 «개수 세기» **사이클4**(사이클1 2차 §4-5 마지막 항): 2픽셀이 안 되는 상자를 **여기서도**
    버린다. `clean()` 은 사람이 저장할 때 그런 상자를 버리는데(MIN_SIDE=2), 팀원 json 에서 온 상자가
    이미 파일에 들어 있으면 그 줄이 `w=0.000781` 로 YOLO txt 에 **그대로 나갔다**(실측: 복숭아 정답
    977개에는 0개였지만 규칙이 두 군데에서 달랐다). 검출 학습에서 0폭 상자는 손실이 NaN 이 되거나
    조용히 무시되는 자리라, «화면에 저장되는 규칙» 과 «학습에 나가는 규칙» 을 같은 한 줄로 맞춘다.
    버린 수는 `dropped_small` 로 돌려준다 — 조용히 사라지지 않게.

    🔴 0919 «개수 세기» **사이클5**: 줄이 하나도 없는 json 은 **txt 를 만들지 않고 건너뛴다**
    (아래 `if not lines` 주석). `empty_txt`·`empty_txt_names` 는 그때부터 «0줄로 나간 txt» 가 아니라
    «**건너뛴** 사진» 을 뜻하고, `n_images` 는 실제로 나간 txt 장수다.

    돌려주는 것: None(저장된 상자가 아예 없음) 또는
      {"n_images","n_boxes","stale_txt","stale_txt_names","yolo_dir","dropped_small",
       "empty_txt","empty_txt_names"}
    """
    src = os.path.join(data_dir, fruit, "boxes")
    if not os.path.isdir(src):
        return None
    os.makedirs(out_dir, exist_ok=True)
    if all_json is None:
        all_json = os.path.join(data_dir, fruit, "boxes_all.json")
    keep = None if stems is None else set(stems)
    allrec, n_img, n_box, n_small = [], 0, 0, 0
    empty = []                # 줄이 하나도 없는 txt — 학습에서 «이 사진에는 열매가 없다» 가 된다
    for fn in sorted(os.listdir(src)):
        if not fn.endswith(".json"):
            continue
        if keep is not None and fn[:-5] not in keep:
            continue                      # 확정되지 않은 사진 — txt 를 아예 만들지 않는다
        with open(os.path.join(src, fn), encoding="utf-8") as f:
            rec = json.load(f)
        w, h = rec.get("width") or 1, rec.get("height") or 1
        lines = []
        for b in rec.get("boxes", []):
            x1, y1, x2, y2 = b["xyxy"]
            if x2 - x1 < MIN_SIDE or y2 - y1 < MIN_SIDE:
                n_small += 1                  # 사이클4: clean() 과 **같은 규칙**으로 버린다(위 설명)
                continue
            lines.append("%d %.6f %.6f %.6f %.6f" % (
                CLASSES.index(b.get("cls", "fruit")) if b.get("cls") in CLASSES else 0,
                (x1 + x2) / 2 / w, (y1 + y2) / 2 / h, (x2 - x1) / w, (y2 - y1) / h))
        if not lines:
            # 🔴 0919 «개수 세기» **사이클5**(사이클4 2차 §7-2·§9-5 · 3차 §3 — 사이클4 가 드러내 두고
            # 고치지 않은 구멍을 여기서 닫는다): 상자가 한 줄도 없는 json(= 상자 0개인 **옛 파일**)은
            # **txt 를 아예 만들지 않는다.** 0줄 txt 를 내보내면 검출 학습이 그것을 «이 사진에는
            # 열매가 없다» 는 **정답 라벨**로 읽는다(사이클5 2차 A-9 와 같은 위험).
            # 지금 저장 규칙은 0개 저장을 «파일 지우기» 로 바꿨으므로 새로 생기지는 않는다 —
            # 남아 있는 것은 시험 잔재 2개뿐(`data/peach/boxes/210629-t4-17.json` ·
            # `data/grape/boxes/740.json` — 사람 삭제 목록에 있다).
            # 건너뛴 이름은 그대로 돌려준다(`empty_txt`·`empty_txt_names`) — 조용히 사라지지 않게.
            # 건너뛴 사진은 `n_images` 에도 세지 않는다: 이 숫자는 «나간 txt 장수» 이고 화면·확인창이
            # 그것으로 말한다(사이클4 결함 27 «실제 txt 수» 와 같은 뜻).
            empty.append(rec["stem"])
            continue
        with open(os.path.join(out_dir, rec["stem"] + ".txt"), "w") as f:
            f.write("\n".join(lines) + "\n")
        allrec.append(rec)
        n_img += 1
        n_box += len(lines)
    with open(all_json, "w", encoding="utf-8") as f:
        json.dump({"fruit": fruit, "classes": CLASSES, "at": at,
                   "n_images": n_img, "n_boxes": n_box, "images": allrec},
                  f, ensure_ascii=False, indent=1)
    # N4(사이클4 판정): 상자 json 을 지운 뒤에도 남는 낡은 txt 를 «세어서» 알려 준다.
    # 지우지는 않는다 — 삭제는 사람이 한다(CLAUDE.md 3항).
    # 🔴 0919 «개수 세기» 사이클5 **2차**: 위에서 «건너뛴» 사진의 txt 가 **이미 그 폴더에 있으면**
    # 이 목록에 들지 않았다(그 사진의 json 은 그대로 있으니까). `/box` 화면의 내보내기는 과일마다
    # **고정 폴더**(`data/<과일>/boxes_yolo/`)로 나가므로, 소수정 ④ 이전에 만들어진 **0줄 txt** 는
    # 그 자리에 계속 남는다 — 화면은 «건너뛰었다» 고 말하는데 폴더에는 검출 학습이 «이 사진에는
    # 열매가 없다» 로 읽는 파일이 그대로 있는 셈이다(실서버 실측 2026-09-19 23:1x:
    # `data/peach/boxes_yolo/210629-t4-17.txt` · `data/grape/boxes_yolo/740.txt` 둘 다 0바이트).
    # → **건너뛴 사진의 옛 txt 도 «낡은 txt» 로 센다.** 지우지는 않는다(삭제는 사람 · N4 규칙 그대로).
    empty_set = set(empty)
    stale = [n for n in sorted(os.listdir(out_dir)) if n.endswith(".txt")
             and (not os.path.exists(os.path.join(src, n[:-4] + ".json"))
                  or n[:-4] in empty_set)]
    return {"n_images": n_img, "n_boxes": n_box, "dropped_small": n_small,
            "empty_txt": len(empty), "empty_txt_names": empty[:20],
            "stale_txt": len(stale), "stale_txt_names": stale[:20],
            "yolo_dir": out_dir.replace(os.path.expanduser("~"), "~")}


def register(app: Any, ctx: Any) -> None:
    """Flask 앱에 이 모듈의 주소와 처리 함수를 등록한다."""
    check = ctx["check"]
    data_dir = ctx["DATA_DIR"]
    img_path = ctx["img_path"]
    lock_for = ctx["lock_for"]
    err_json = ctx["err_json"]
    labeled = ctx["labeled"]
    now_str = ctx["now_str"]
    fruits = ctx["FRUITS"]

    def box_path(fruit, stem):
        return os.path.join(data_dir, fruit, "boxes", stem + ".json")

    def size_of(fruit, stem):
        with Image.open(img_path(fruit, stem)) as im:
            return im.size                 # (w, h)

    def read_boxes(fruit, stem):
        p = box_path(fruit, stem)
        if not os.path.exists(p):
            return None
        try:
            with open(p, encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            return None

    @app.route("/api/boxes")
    def api_boxes():
        fruit = request.args.get("fruit", "")
        stem = request.args.get("stem", "")
        check(fruit, stem)
        w, h = size_of(fruit, stem)
        d = read_boxes(fruit, stem)
        saved, d = d is not None, d or {}     # saved 는 «파일을 읽어 냈나» 그대로 (깨진 파일은 False)
        # 0919: 이 사진에 팀원 상자가 몇 개 있는지(없으면 빠짐). 화면이 «저장된 상자 없음» 일 때 초벌로 채운다.
        team = {}
        for who, _ in TEAM_BOX_DIRS:
            tb = read_team_boxes(who, fruit, stem, w, h)
            if tb is not None:
                team[who] = len(tb)
        return jsonify({"ok": True, "fruit": fruit, "stem": stem, "width": w, "height": h,
                        "boxes": d.get("boxes", []), "by": d.get("by"), "at": d.get("at"),
                        "saved": saved, "classes": CLASSES, "team": team})

    @app.route("/api/boxes", methods=["POST"])
    def api_boxes_save():
        d = request.get_json(force=True, silent=True) or {}
        fruit, stem = d.get("fruit", ""), d.get("stem", "")
        check(fruit, stem)
        raw = d.get("boxes")
        if not isinstance(raw, list):
            return err_json("상자 목록(boxes)이 없습니다. 새로고침한 뒤 다시 저장해 주세요.", 400)
        w, h = size_of(fruit, stem)
        try:
            boxes, dropped, over = clean(raw, w, h)
        except ValueError as e:
            return err_json(str(e), 400)
        rec = {"stem": stem, "fruit": fruit, "width": w, "height": h,
               "by": (d.get("by") or "익명").strip()[:rules.NAME_MAX], "at": now_str(),
               "note": (d.get("note") or "").strip()[:rules.NOTE_MAX], "boxes": boxes}
        p = box_path(fruit, stem)
        # 0919 사이클5 **2차 검수**(1차 열린 문제 7 · 실측 `cycle_5/stage2/r1_risks.py` A-5·A-6·A-9):
        # «🧹 전부 지움 → 상자 저장» 은 사람이 상자를 비울 수 있는 **유일한 길**인데, 전에는
        #   ① 빈 목록을 파일에 쓰고 ② 확정을 «수정함» 으로 찍었다. 그러면
        #   ㉠ `confirmed_boxes` 를 비우는 길이 영영 없고(`/api/revert_boxes` 주소는 없다 — A-8 404),
        #   ㉡ 목록 카드가 상자 0개인 사진을 «✔ 확정 · 수정함» 이라고 말하고(A-7),
        #   ㉢ «사람 확정만» 내보내기가 **0줄 txt** 를 만들어 «이 사진에는 열매가 없다» 는
        #      학습 라벨이 데이터셋에 들어간다(A-9 실측: 102줄 → 0줄 txt 가 그대로 나갔다).
        # → 0개 저장은 «저장» 이 아니라 **그 작업의 되돌리기**로 본다: 저장된 상자 파일을 지우고
        #   상자 확정을 비운다(마스크 «수정본 되돌리기»·«번호 되돌리기» 와 같은 뜻이고 같은 함수
        #   `clear_confirm` 을 쓴다). AI 초벌은 «✨ 초벌» 로 언제든 다시 만들 수 있다.
        # 데이터 소실 예외 수정: 입력은 있지만 검증 뒤 전부 탈락한 요청은 거절한다.
        if raw and not boxes:
            return err_json("유효한 상자가 없습니다. 기존 상자는 그대로 두었습니다.", 400)
        if is_box_clear_save(boxes):     # 0개 저장 = 그 작업의 되돌리기(규칙 함수)
            with lock_for("boxes:%s:%s" % (fruit, stem)):
                if os.path.exists(p):
                    os.remove(p)
            cc = ctx.get("clear_confirm")
            cleared = bool(cc and cc(fruit, stem, "boxes")[0])
            return jsonify({"ok": True, "n_boxes": 0, "dropped": dropped, "over": over,
                            "at": rec["at"], "boxes": [], "removed": True,
                            "confirmed_cleared": "boxes" if cleared else None})
        with lock_for("boxes:%s:%s" % (fruit, stem)):
            os.makedirs(os.path.dirname(p), exist_ok=True)
            tmp = p + ".tmp%d.%d" % (os.getpid(), threading.get_ident())  # 0918 사이클4 2차: 같은 파일을 두 요청이 동시에 쓰면 PID 만으로는 임시 이름이 겹쳐 500 이 난다
            with open(tmp, "w", encoding="utf-8") as f:
                json.dump(rec, f, ensure_ascii=False, indent=1)
            os.replace(tmp, p)
        # 0918 사이클4 결정 1: **저장 = 그 작업의 확정(수정함)**. 마스크 쪽 «수정본 저장» 과 같은
        # 규칙이다 — 사람이 상자를 손대어 저장했으면 그 사진의 상자는 «사람이 본 것» 이다.
        # 확정 칸은 `confirmed_boxes` 뿐이라 마스크 확정(`confirmed`)은 건드리지 않는다.
        conf = ctx.get("confirm_status")
        if conf:
            conf(fruit, [(stem, "fixed")], rec["by"], rec["note"], "boxes")
        return jsonify({"ok": True, "n_boxes": len(boxes), "dropped": dropped,
                        "over": over, "at": rec["at"],
                        # D3: 화면은 이 목록으로 자기 상태를 덮어쓴다.
                        # (서버가 버린 상자가 화면에만 남아 «저장했는데 아직 있다» 가 되지 않게)
                        "boxes": boxes})

    @app.route("/api/boxes_seed")
    def api_boxes_seed():
        """열매마다 상자를 하나씩 만들어 «초벌» 로 준다. 저장하지 않는다.
        사람이 화면에서 고친 뒤 저장한다 (AI 가 잘못 만들 수 있으므로).

        0917 사이클3: **번호 마스크가 있으면 번호마다 상자 하나**다(사과 알 단위·블루베리 검출팀
        초벌 단위). 전에는 늘 이진 마스크의 연결성분을 셌기 때문에 붙은 열매가 한 상자로 합쳐져
        사과 `image1` 이 번호 95개인데 상자 30개였다. 번호가 없는 과일(복숭아·포도)은 전과 같이
        이진 연결성분을 쓴다. 무엇을 썼는지는 응답 `source` 에 실어 화면이 그대로 알려 준다.

        🔴 0919 «개수 세기» **사이클4 결정 M1**: 응답에 `seed_source` 를 **더 싣는다**(`source` 는
        옛 이름 그대로 남긴다 — 옛 화면이 깨지지 않게). `seed_source` 는 `instances.py` 의
        `team:박성문` / `certh_gt` / `gt_numbers` / `human_fixed` / `cc4` 다섯 낱말 중 하나이고,
        화면·counts.csv·README 가 **같은 낱말**을 쓴다.
        또 `source=team:<이름>` 인데 그 사람의 상자 파일이 이 사진에 없으면 **404 로 끝내지 않고**
        마스크 갈래로 내려간다(M1: «없을 때만 지금 CC(4-연결) 폴백»). 그 때 `fallback_from` 에
        원래 고른 출처를 실어 화면이 «박성문 상자가 없어 마스크로 대신했다» 고 말할 수 있게 한다.
        """
        fruit = request.args.get("fruit", "")
        stem = request.args.get("stem", "")
        source = request.args.get("source", "gt")
        # ponytail: 번호 없는 과일(복숭아·포도)에서만 뜻이 있다 — 번호가 있으면 무시된다
        check(fruit, stem)
        # 0919: source=team:<이름> 이면 팀원이 뽑아 둔 상자를 초벌로 준다(마스크 계산 없음, 읽기 전용).
        fallback_from = None
        if source.startswith("team:"):
            who = source[5:]
            if who not in dict(TEAM_BOX_DIRS):
                return err_json("모르는 팀원 이름입니다: " + who, 400)
            w, h = size_of(fruit, stem)
            tb = read_team_boxes(who, fruit, stem, w, h)
            if tb is not None:
                try:
                    boxes, _, _ = clean(tb, w, h)
                except ValueError as e:
                    return err_json(str(e), 400)
                return jsonify({"ok": True, "boxes": boxes, "n": len(boxes), "source": source,
                                "seed_source": source})
            # 그 사람 파일이 없는 사진 — 마스크·번호 갈래로 내려간다(M1 폴백)
            fallback_from, source = source, "gt"
        try:
            lab, kind, _ = INST.load_inst(fruit, stem)   # 이진본이 번호본을 자른다(사이클5 N1)
        except ValueError as e:
            return err_json(str(e), 400)
        if lab is not None:
            source = "instances:" + kind
            seed_source = INST.source_name(fruit, kind)
        else:
            source = "ai" if source == "ai" else "gt"
            lab = labeled(fruit, stem, source)
            seed_source = INST.CC4                       # 이진 마스크 4-연결 — 마지막 폴백
        if lab is None:
            return err_json("그 레이어의 마스크가 없어 초벌 상자를 만들 수 없습니다.", 404)
        boxes = boxes_of(lab)
        out = {"ok": True, "boxes": boxes, "n": len(boxes), "source": source,
               "seed_source": seed_source}
        if fallback_from:
            out["fallback_from"] = fallback_from
        return jsonify(out)

    @app.route("/api/boxes_export", methods=["POST"])
    def api_boxes_export():
        """YOLO txt + 한 파일 JSON 으로 내보낸다. 사람이 저장한 상자만 대상."""
        d = request.get_json(force=True, silent=True) or {}
        fruit = d.get("fruit", "")
        if fruit not in fruits:
            return err_json("과일 이름이 잘못됐습니다.", 400)
        # 0918 사이클3: 몸통은 위의 export_boxes_to() 로 옮겼다 — 이 단추와 «데이터 정리» 탭이
        # **같은 함수**를 쓴다. 답(칸 이름·순서·값)은 예전과 한 글자도 다르지 않다.
        res = export_boxes_to(data_dir, fruit,
                              os.path.join(data_dir, fruit, "boxes_yolo"),
                              os.path.join(data_dir, fruit, "boxes_all.json"), at=now_str())
        if res is None:
            return err_json("저장된 상자가 없습니다.", 404)
        out = {"ok": True}
        out.update(res)
        return jsonify(out)

    @app.route("/api/boxes_stats")
    def api_boxes_stats():
        out = {}
        for f in fruits:
            src = os.path.join(data_dir, f, "boxes")
            n_img = n_box = 0
            if os.path.isdir(src):
                for fn in os.listdir(src):
                    if fn.endswith(".json"):
                        n_img += 1
                        try:
                            with open(os.path.join(src, fn), encoding="utf-8") as fh:
                                n_box += len(json.load(fh).get("boxes", []))
                        except Exception:
                            pass
            out[f] = {"n_images": n_img, "n_boxes": n_box}
        return jsonify({"ok": True, "stats": out, "at": now_str()})


def demo() -> None:
    """ponytail: 자체 점검 — **실제 clean()** 을 불러 상자 정리 규칙을 확인한다(서버 없이)."""
    raw = [{"xyxy": [10, 20, 5, 8]},                       # 좌우·위아래 뒤집힘 -> 정렬
           {"xyxy": [0, 0, 1, 1]},                          # 1픽셀 -> 버림
           {"xyxy": [-5, -5, 50, 50], "cls": "bunch"},      # 사진 밖 -> 사진 안으로 자름
           {"xyxy": [3, 3, 9, 9], "cls": "없는이름"},        # 모르는 클래스 -> fruit
           {"nope": 1}]                                     # xyxy 가 없음 -> 버림
    out, dropped, over = clean(raw, 40, 40)
    assert [b["xyxy"] for b in out] == [[5, 8, 10, 20], [0, 0, 40, 40], [3, 3, 9, 9]], out
    assert [b["cls"] for b in out] == ["fruit", "bunch", "fruit"], out
    assert [b["id"] for b in out] == [1, 2, 3], out         # id 는 1부터 다시 붙는다
    assert [b["src"] for b in out] == ["human"] * 3, out
    assert (dropped, over) == (2, 0), (dropped, over)
    out2, _, over2 = clean([{"xyxy": [0, 0, 10, 10]}] * (MAX_BOXES + 5), 40, 40)
    assert (len(out2), over2) == (MAX_BOXES, 5), (len(out2), over2)
    # boxes_of(): 번호 1·2(각 4화소) + 3화소 번호 3(버림) + 두 조각 번호 4(조각 전체를 한 상자로)
    lab = np.array([[1, 1, 0, 2, 2],
                    [1, 1, 0, 2, 2],
                    [4, 4, 0, 0, 4],
                    [0, 0, 0, 0, 4],
                    [3, 3, 3, 0, 0]], dtype=np.uint32)
    b = boxes_of(lab)
    assert [x["xyxy"] for x in b] == [[0, 0, 2, 2], [3, 0, 5, 2], [0, 2, 5, 4]], b
    assert [x["id"] for x in b] == [1, 2, 3], b          # 3화소 번호 3 이 빠지고 id 는 1부터 다시
    assert len(boxes_of(np.zeros((5, 5), np.uint32))) == 0
    assert len(boxes_of(lab, limit=1)) == 1              # MAX_BOXES 상한
    # human_count(): 개수 유도 우선순위·어긋남 (0919 개수 사이클1)
    # 🔴 0919 3차 전 총괄 결정 1: 어긋나면 **개수를 비운다**(전에는 (15, "instances", True) 였다)
    assert human_count(16, 15, "fixed", "ok") == (None, "conflict", True)     # 어긋남 = 비움
    assert human_count(16, 16, "ok", "ok") == (16, "instances", False)        # 같으면 어긋남 아님
    assert human_count(16, 15, "fixed", None) == (16, "boxes", False)         # 번호 확정 없음
    assert human_count(16, 15, "flag", "exclude") == (None, "", False)        # flag·exclude 는 확정 아님
    assert human_count(None, 15, "fixed", None) == (None, "", False)          # 확정은 있는데 셀 수가 없음
    assert human_count(None, None, None, None) == (None, "", False)
    assert human_count(0, None, "ok", None) == (0, "boxes", False)            # 0개도 «값 없음» 이 아니다
    print("boxes.py 자체 점검 통과 (실제 clean()·boxes_of()·human_count() 를 시험했습니다)")


if __name__ == "__main__":
    demo()
