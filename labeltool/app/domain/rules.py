# -*- coding: utf-8 -*-
"""데이터 규칙 — **주석이 아니라 이름 있는 함수**로.

구조 사이클 2(2026-09-20) 지시서 §2: «규칙이 코드 주석과 사이클 문서에만 있고 한 장의 목록이
없다» 를 고치는 자리다. 규칙 한 줄마다 함수 하나 · 왜 그렇게 정했나(날짜·사이클)를 docstring
에 적는다. 값과 동작은 한 글자도 바뀌지 않았다 — 옮겨 온 함수는 원래 주석을 그대로 달고 있다.

규칙표(어느 함수가 어느 규칙인가)는 `cycles/260920_structure/cycle_2/stage1/README_5_규칙표_after.md`.
"""

from __future__ import annotations
from typing import Any
import numpy as np
from scipy import ndimage      # boxes_of 가 쓴다(서버가 이미 scipy 를 쓴다)

# status.json 항목의 `src` 표식 — «이 제외를 누가 넣었나». 되돌리기가 **자기가 넣은 것만** 되돌리게
# 하려고 둔다(0917 ab사이클2 P1: 메모 형식이 AI 3회 검수와 같아서 메모로는 구분할 수 없다).
# 표식이 없는 항목(사람 손·AI 판정·옛 판)은 어떤 되돌리기도 건드리지 않는다.
SRC_DUP_BULK = "dup_bulk"       # 진행 현황 탭의 «중복 그룹 일괄 제외 적용»
SRC_DUP_GROUP = "dup_group"     # 편집 화면의 «이 묶음: 대표만 남기고 제외»

CLASSES = ["fruit", "bunch", "other"]      # 0=알/과실, 1=송이, 2=기타
MAX_BOXES = 3000
MIN_SIDE = 2                               # 2픽셀 미만 상자는 실수로 클릭한 것으로 본다


# 0919 «개수 세기» 사이클1 — 지시서 §1-2. **사람 확정 개수를 따로 입력하는 칸은 두지 않는다**(yagni):
# 숫자만 치는 칸을 두면 ㉠ 상자·번호와 어긋난 세 번째 진실이 생기고 ㉡ 되돌리기·확정 규칙을
# 네 번째 종류(`confirmed_counts`)로 또 나눠야 하고 ㉢ 녹취 0908 «AI 초벌 + 사람이 맞다/틀리다»
# 흐름에 없는 작업이 된다. 그래서 개수는 **이미 있는 두 확정에서 유도**한다.
#   ① 번호 확정(ok·fixed)이 있고 번호 수를 알면 → 번호 수 (source="instances")
#   ② 아니면 상자 확정(ok·fixed)이 있고 상자 수를 알면 → 상자 수 (source="boxes")
#   ③ 둘 다 없으면 → 없음 (source="")
# 번호가 먼저인 까닭: 번호는 알 하나하나에 붙은 라벨이고 상자는 그 번호에서 유도된 것이다
# (`boxes_seed` 가 번호 마스크가 있으면 번호마다 상자 하나를 만든다). 상자는 사람이 합치거나
# 나눌 수 있어 «개수의 원본» 이 아니다.
# 🔴 둘 다 확정됐는데 수가 다르면 **개수를 비운다**(2026-09-19 «개수 세기» 사이클1 **3차 전 총괄
# 결정 1**): `n_human=None` · `source="conflict"` · `conflict=True`. 전에는 ①(번호 수)을 그대로
# 썼는데, 그러면 «툴은 고르지 않습니다» 라는 README·help·풍선말이 거짓이 되고(2차 검수 §2-6-가
# 실측: `human_count(16, 15, "fixed", "ok") == (15, "instances", True)`), 16과 15 중 어느 쪽인지
# 사람이 고르지 않은 수가 논문 표(MAE·RMSE·R²)에 실려 나간다 = 사후 정당화. «사람 확정 개수» 는
# 사람이 **한 숫자를 인정한 것**이어야 하므로, 어긋난 사진은 사람이 고칠 때까지 지표에서 빠진다.
def human_count(n_boxes: Any, n_instances: Any, conf_boxes: Any, conf_instances: Any) -> tuple[int | None, str, bool]:
    """(개수, 출처, 어긋남) — 규칙은 위 주석 하나뿐이고 쓰는 곳은 셋(화면·counts.csv·통합 manifest)이다.

    conf_* 는 그 종류의 사람 확정 상태 문자열(ok·fixed·flag·exclude·None). ok·fixed 만 «확정» 으로
    센다(flag = 아직 고칠 것 · exclude = 안 쓸 사진 — 내보내기가 이미 그 둘을 뺀다).
    어긋나면 `(None, "conflict", True)` — 한쪽만 확정이면 그쪽 수를 쓴다.
    """
    ok_i = conf_instances in ("ok", "fixed") and n_instances is not None
    ok_b = conf_boxes in ("ok", "fixed") and n_boxes is not None
    conflict = bool(ok_b and ok_i and n_boxes != n_instances)
    if conflict:
        return None, "conflict", True        # 총괄 결정 1 — 사람이 봐야 한다(툴이 고르지 않는다)
    if ok_i:
        return n_instances, "instances", False
    if ok_b:
        return n_boxes, "boxes", False
    return None, "", False


def clean(raw: Any, w: int, h: int) -> Any:
    """화면이 보낸 상자를 사진 안으로 맞추고 이상한 것은 버린다."""
    out, dropped = [], 0
    over = max(0, len(raw) - MAX_BOXES)   # 3,000개가 넘어 잘린 개수(그냥 사라지면 안 되니 세어 알려 준다)
    for b in raw[:MAX_BOXES]:
        try:
            x1, y1, x2, y2 = (float(v) for v in b.get("xyxy", [])[:4])
        except Exception:
            dropped += 1
            continue
        x1, x2 = sorted((x1, x2))
        y1, y2 = sorted((y1, y2))
        x1 = max(0, min(w - 1, round(x1)));  x2 = max(0, min(w, round(x2)))
        y1 = max(0, min(h - 1, round(y1)));  y2 = max(0, min(h, round(y2)))
        if x2 - x1 < MIN_SIDE or y2 - y1 < MIN_SIDE:
            dropped += 1
            continue
        cls = b.get("cls", "fruit")
        out.append({"id": len(out) + 1,
                    "cls": cls if cls in CLASSES else "fruit",
                    "xyxy": [int(x1), int(y1), int(x2), int(y2)],
                    "src": "auto" if b.get("src") == "auto" else "human"})
    return out, dropped, over


def boxes_of(lab: Any, min_px: int=4, limit: int=MAX_BOXES) -> Any:
    """번호마다 상자 하나 — 배열을 **한 번만** 훑는다(find_objects).

    번호 오름차순으로 주고, min_px(4) 화소 미만인 번호는 뺀다. 잎에 가려 조각난 번호는
    슬라이스가 조각 전체를 덮으므로 상자 하나가 조각 전체를 감싼다.

    0917 사이클4: 예전에는 번호마다 `np.where(lab == v)` 로 2MP 배열을 다시 훑어서
    번호 204개짜리 블루베리 한 장이 **7.55초** 걸렸다(사이클3 2차 실측). 결과는 그대로 두고
    같은 값을 한 자리 아래 시간에 낸다. 규칙 셋(오름차순·4화소 버림·MAX_BOXES 상한)은 그대로다.
    """
    lab = np.asarray(lab).astype(np.int32)     # read_u16 은 uint32, labeled() 는 int32
    cnt = np.bincount(lab.ravel())             # 번호마다 화소 수 — 4화소 규칙을 한 번에 센다
    out = []
    for i, s in enumerate(ndimage.find_objects(lab), start=1):
        if s is None or cnt[i] < min_px:       # 없는 번호(None)와 너무 작은 번호를 뺀다
            continue
        ys, xs = np.nonzero(lab[s] == i)       # 슬라이스 안에서만 본다(다른 번호가 섞여 있어도)
        out.append({"id": len(out) + 1, "cls": "fruit", "src": "auto",
                    "xyxy": [int(s[1].start + xs.min()), int(s[0].start + ys.min()),
                             int(s[1].start + xs.max()) + 1, int(s[0].start + ys.max()) + 1]})
        if len(out) >= limit:
            break
    return out


def pick_representative(group: Any, status: Any) -> Any:
    """그룹의 **첫 장이 대표**다 — duplicates.json 의 순서가 «대표를 앞에» 라는 약속이다.
    그 장이 이미 exclude 면(사람이 «이건 안 쓴다» 고 했으면) 다음 장으로 넘어간다.
    전부 exclude 면 그냥 첫 장을 대표로 둔다(무한 제외 방지).

    0917 ab사이클2 P1 — 전에는 첫 장이 **flag** 여도 다음 장으로 대표를 옮겼다. 그래서
    「일괄 제외 되돌리기」로 나머지가 unreviewed 가 되는 순간 사과 9그룹의 대표가 옮겨 가고,
    원래 대표였던 flag 사진이 «제외» 로 바뀌어 «사람 확인 필요 + 후보 좌표» 메모가 사라졌다
    (flag 68 → 59). flag 는 «사람이 볼 것» 이지 «못 쓸 사진» 이 아니므로 대표 자격이 있다.
    """
    for s in group:
        if status.get(s, {}).get("status", "unreviewed") != "exclude":
            return s
    return group[0]


# ── 이름 붙인 수 (매직 넘버 금지 — 지시서 §2) ────────────────────────────────
NAME_MAX = 40            # 사람 이름 칸(status.json `by`)에 남기는 글자 수
NOTE_MAX = 300           # 메모 칸(`note`)에 남기는 글자 수
PAGE_SIZE_DEFAULT = 120  # 사진 목록 한 쪽 장수(화면 기본값)
PAGE_SIZE_MIN = 20       # 그보다 작게 달라고 해도 이만큼은 준다
PAGE_SIZE_MAX = 500      # 한 번에 줄 수 있는 최대 장수(사과 1,001장은 두 쪽)
CONFIRM_STEMS_MAX = 500  # «묶음째 확정» 한 번에 받는 사진 수
UNDO_STEMS_MAX = 200     # «묶음 되돌리기» 한 번에 받는 사진 수
EXPORT_LIST_MAX = 200    # 내보내기 폴더 목록에 보여 줄 줄 수
DUP_SAMPLE_MAX = 20      # 중복 미리 보기에 예시로 보여 줄 사진 수
THUMB_PX = 200           # 썸네일 한 변(긴 쪽) 화소
THUMB_QUALITY = 72       # 썸네일 JPEG 품질
LABEL_CACHE_MAX = 4      # 연결성분 라벨 배열을 메모리에 몇 장까지 들고 있나
LOGIN_FAIL_SLEEP = 0.5   # 비밀번호가 틀렸을 때 답을 늦추는 초(무차별 대입 속도만 늦춘다)

# «사람 확정» 중에서 **실제로 내보내는** 판정. flag = 아직 고칠 것 · exclude = 안 쓸 사진.
CONFIRM_OUT = ("ok", "fixed")


def goes_out(status: Any) -> bool:
    """그 확정이 내보내기에 **나가나** — `flag`·`exclude`·미확정은 나가지 않는다.

    (0918 사이클3 결정 · export_dataset.py E5 와 같은 규칙. 화면의 «나갈 장수» 도 이것으로 센다)
    """
    return status in CONFIRM_OUT


def ai_name_rejected(by: Any) -> bool:
    """사람 이름이 «AI» 로 시작하면 막는다 — 0918 사이클4 N8.

    `src_of()` 가 `by` 가 "AI" 로 시작하면 그 판정을 **AI 제안**으로 읽기 때문에, 사람이 그 이름을
    쓰면 큐·내보내기·화면이 사람이 누른 것을 AI 초벌로 취급한다(실측 s1_api 검증-10).
    막는 자리는 `/api/status` **하나뿐**이다(그 까닭은 api/masks.py 의 주석).
    """
    return str(by or "").startswith("AI")


def mask_save_keeps_exclude(status: Any) -> bool:
    """마스크를 저장해도 «제외(exclude)» 판정은 **뒤집지 않는다** — 0918 UI사이클5 N-C.

    고치기 전에는 제외 사진에 붓질 한 번을 저장하면 `fixed` 가 되어 AI 3회 검수가 동결한
    제외(사과·블루베리 수백 장)가 데이터셋에 되살아났다. `flag` 는 지금처럼 `fixed` 로 풀린다.
    """
    return status == "exclude"


def merge_exclude_note(old: Any, note: Any) -> str:
    """제외를 지킬 때 메모를 어떻게 남기나 — **앞부분(old)은 늘 그대로 둔다.**

    «중복: …» 으로 시작하는지를 보는 곳(되돌리기·내보내기 기록)이 있어서 앞이 바뀌면 안 된다.
    메모 칸은 이 사진의 옛 메모로 미리 채워져 있으므로 보통 `note` 가 `old` 로 시작한다 —
    그때는 보낸 것을 그대로 쓴다. 칸을 비우고 딴 말을 적은 경우만 뒤에 이어 붙인다
    (0918 UI사이클5 2차: «글자가 똑같을 때만» 으로 보면 옛 메모가 한 번 더 붙었다).
    """
    if note.startswith(old):
        return note
    return (old + " · (수정본 저장) " + note)[:NOTE_MAX] if note else old


def status_after_instance_save(prev_status: Any) -> str:
    """번호를 저장했을 때 판정을 무엇으로 두나 — `exclude`·`flag` 는 그대로, 나머지는 `fixed`.

    0917 ab사이클2 P2: 전에는 무조건 `fixed` 로 덮어써서 3차 판정의 flag 68장이 왜 flag 였는지가
    사라지고 exclude 였던 사진이 내보내기에 되살아났다.
    """
    return prev_status if prev_status in ("exclude", "flag") else "fixed"


def is_box_clear_save(boxes: Any) -> bool:
    """상자 **0개 저장은 «저장» 이 아니라 그 작업의 되돌리기**다 — 0919 사이클5 2차.

    전에는 빈 목록을 파일에 쓰고 확정을 «수정함» 으로 찍어서 ㉠ `confirmed_boxes` 를 비울 길이
    영영 없고 ㉡ «사람 확정만» 내보내기가 **0줄 txt**(= «이 사진에는 열매가 없다» 는 학습 라벨)를
    만들었다. 그래서 상자 파일을 지우고 상자 확정을 벗긴다(`clear_confirm`).
    """
    return not boxes


def zero_instance_save_blocked(n_ids: int, binary_fg: Any) -> bool:
    """번호를 **전부 지운 저장은 서버가 막는다**(400) — 0919 사이클5 3차 결정 1.

    막지 않으면 N6 쓰기(`(arr>0)|keep`)가 이진 마스크까지 비워서, «원본 OK» 로 확정해 둔 사진이
    빈 마스크 PNG 로 나갔다(실측 전경 1,180화소 → 0화소). 열매가 정말 없는 사진은 «4 제외» 가
    바른 길이다 — 이진 전경이 이미 0이면 그대로 저장된다.
    """
    return n_ids == 0 and bool(binary_fg.any())


def keep_numberless_foreground(binary_fg: Any, cur_inst: Any, shape: Any) -> Any:
    """**N6 쓰기 규칙** — «번호가 있던 화소만» 이진본에서 뺄 수 있다(0917 사이클6 보충).

    저장 직전의 «이진본으로 자른» 번호본(`cur_inst`)에서 번호가 **없던** 전경은 그대로 지킨다
    (블루베리 초벌의 구멍·브러시로 넓힌 자리). 브러시로 지운 알은 이진본에 없으므로 여기
    들어오지 않는다 = 되살아나지 않는다. 읽기 규칙(`cut_by_binary`)과 **같은 문장**이다.
    """
    if cur_inst is None:
        return np.zeros(shape, bool)
    return binary_fg & (cur_inst == 0)


def cut_by_binary(inst: Any, binary: Any) -> Any:
    """**«이진본이 번호본을 자른다»** — 0917 사이클4 판정 N1. 파일은 고치지 않고 읽을 때만 자른다.

    이진본이 배경인 자리의 번호는 0 으로 잘라서 준다(«없는 번호» 금지). 이진본이 전경인데 번호가
    없는 자리는 **채우지 않고 센다**(어느 번호인지 정할 수 없고 사람이 N·M 으로 붙일 자리다).
    돌려주는 것: (자른 배열, {"cut": 잘린 화소, "lost_ids": 잘려 사라진 번호 수,
    "hole": 이진본 전경인데 번호 없는 화소}).
    """
    from domain.maskio import ids_of
    out = inst.copy()
    out[~binary] = 0
    return out, {"cut": int((inst != out).sum()),
                 "lost_ids": int(ids_of(inst).size - ids_of(out).size),
                 "hole": int((binary & (out == 0)).sum())}


# ── 규칙이 «여기가 아니라 저기» 에 있는 것 (한 곳에만 두려고 일부러 옮기지 않은 것) ──────
#   · 되돌리기가 그 종류의 사람 확정을 **지운다**      → core/status_store.py clear_confirm()
#   · 묶음 확정에서 **이미 확정한 구성원은 건너뛴다**   → core/status_store.py confirm_status()
#   · 판정을 덮을 때 옛 판정을 `prev` 에 한 벌 남긴다   → core/status_store.py update_status()
#   · 개수 유도(번호 확정 > 상자 확정 · 어긋나면 비움)  → 이 파일 human_count()
#   · 근접 중복 묶음의 대표 고르기                     → 이 파일 pick_representative()
