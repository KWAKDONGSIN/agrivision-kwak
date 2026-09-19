# -*- coding: utf-8 -*-
"""
수정판 데이터셋 내보내기 (작업자 A)
작성: 2026-09-16

masks_fixed 에 사람이 고친 마스크가 있으면 그것을, 없으면 팀 표준 데이터셋의 원본 마스크를
써서 새 폴더에 «수정판 데이터셋» 을 만든다. 원본은 절대 건드리지 않는다.
  - 이미지: 심볼릭 링크(용량 0). --copy-images 를 주면 실제 복사
  - 마스크: 0/255 로 통일한 실제 PNG (원본이 인스턴스 라벨/0-1/RGB 여도 0/255 로 맞춰 저장)
  - 빼는 것 ①  status = exclude
  - 빼는 것 ②  근접 중복(data/<fruit>/duplicates.json): 그룹마다 대표 1장만 남기고 나머지 제외
                 (--keep-duplicates 로 끌 수 있음)
  - manifest.csv 에 어떤 마스크가 어디서 왔는지 · 왜 빠졌는지를 전부 기록

사용 예:
  PY=/home/kds0206/.conda/envs/kwak/bin/python
  $PY export/export_dataset.py --fruit peach --out /tmp/peach_fixed --dry-run
  $PY export/export_dataset.py --fruit peach --out ~/datasets_fixed/peach
"""
import os
import sys
import csv
import json
import argparse

sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "app"))
from maskio import load_mask_bool, save_mask_atomic          # noqa: E402
import dupes as DUP                                          # noqa: E402  (과일별 원본 폴더, 0917)
from dupes import read_status, load_duplicate_groups, representative_map, DATA_DIR, DATASET, FRUITS  # noqa: E402
# 번호 마스크 규칙(어디서 읽을지·uint16 로 쓰기·열매 수 세기)은 app/instances.py 한 군데에만 둔다
from instances import source_of, load_inst, mask_path_of, write_u16_atomic, ids_of  # noqa: E402


def main():
    ap = argparse.ArgumentParser(description="수정판 데이터셋 내보내기")
    ap.add_argument("--fruit", required=True, choices=FRUITS + ["all"])
    ap.add_argument("--out", default=None,
                    help="만들 폴더 (--fruit all 이면 그 아래 과일별 폴더). --dry-run 만 할 때는 없어도 됩니다")
    ap.add_argument("--dry-run", action="store_true", help="실제로 쓰지 않고 무엇을 할지만 보여줌")
    ap.add_argument("--keep-duplicates", action="store_true",
                    help="근접 중복 자동 제외를 끄고 전부 넣는다(기본은 그룹당 1장만)")
    ap.add_argument("--drop-flag", action="store_true", help="'문제 있음(flag)' 인 사진도 제외")
    # 0918 사이클2: 방향 문서 §3-1 «내보내기는 사람이 확정한 것만». **기본값은 아직 바꾸지 않는다**
    # (사이클 3 이 «사람 확정만» 을 기본으로 삼을지 정한다). 지금은 옵션을 켤 때만 걸린다.
    ap.add_argument("--confirmed-only", action="store_true",
                    help="사람이 «확정» 한 사진만 내보낸다(AI 제안만 있는 사진은 전부 빠진다)")
    ap.add_argument("--copy-images", action="store_true", help="심볼릭 링크 대신 실제 복사")
    ap.add_argument("--instances", action="store_true",
                    help="열매 번호(인스턴스) 마스크도 <out>/instances/ 로 내보낸다 (0917 검출 팀 요청)")
    # 0919 «개수 세기» 사이클1 (지시서 §1-3) — 사진마다 «열매가 몇 개인가» 를 표 한 장으로
    ap.add_argument("--counts", action="store_true",
                    help="개수 표 <out>/counts.csv 도 만든다 (상자·번호·팀원 초벌·사람 확정 개수)")
    args = ap.parse_args()
    if not args.out and not args.dry_run:
        ap.error("--out 이 필요합니다 (무엇이 들어갈지만 보려면 --dry-run)")

    print("원본 폴더(LABELTOOL_DATA_ROOT): %s" % DATASET)
    print("판정 기록: %s/<과일>/status.json · 수정본: %s/<과일>/masks_fixed/" % (DATA_DIR, DATA_DIR))
    fruits = FRUITS if args.fruit == "all" else [args.fruit]
    for fruit in fruits:
        if not args.out:
            out = "(--dry-run: 아직 정하지 않음)"
        elif args.fruit == "all":
            out = os.path.join(args.out, fruit)
        else:
            out = args.out
        # 0918 사이클3: 같은 폴더로 두 번 돌리면 **말없이 덮어쓰던 것**(사이클2 2차 실측 «바-8»)을 막는다.
        # 비어 있는 폴더는 괜찮다 — 시험들이 mkdtemp() 로 빈 폴더를 미리 만들어 넘긴다.
        if not args.dry_run and os.path.isdir(out) and os.listdir(out):
            sys.exit("[%s] 멈춥니다 — 그 폴더에 이미 파일이 있습니다(덮어쓰기 금지): %s" % (fruit, out))
        export_one(fruit, out, args)


# manifest.csv 의 instances_source 칸 이름. 검출 팀이 읽는 표라 예전 이름을 그대로 쓴다
INST_LABEL = {"fixed": "instances_fixed", "seed": "detect_seed", "gt": "원본번호"}


def check_cell(chk):
    """manifest 의 instances_check 칸 — «이진본이 번호본을 자른» 결과. 아무 일도 없으면 빈칸.

    cut=잘린 화소 · lost_ids=잘려서 아예 사라진 번호 수 · hole=이진본 전경인데 번호가 없는 화소
    (hole 은 채우지 않는다 — 사람이 번호 모드에서 N·M 으로 붙일 자리다).
    """
    if chk.get("err"):
        return "err:" + chk["err"][:60]
    if chk.get("skip"):
        return chk["skip"]          # 0918 사이클4: «번호 미확정» — 번호 파일을 안 낸 이유
    return " ".join("%s=%d" % (k, chk[k]) for k in ("cut", "lost_ids", "hole") if chk.get(k))


def conf_cells(conf):
    """manifest 뒤에 붙는 «사람 확정» 4칸 — confirmed_status·confirmed_by·confirmed_at·source.

    0918 사이클3(사이클2 2차 N6): 예전 표에는 «누가 확정했나» 칸이 없어 `status`·`by` 칸이
    AI 제안인지 사람 확정인지 구별할 수 없었다. `source` 는 그 줄의 **최종 판정이 어디서 왔나**
    (human = 사람이 확정 · ai = AI 제안뿐)이고, 나머지 칸은 사람 확정이 없으면 빈칸이다.
    """
    if not conf:
        return ["", "", "", "ai"]
    return [conf.get("status", ""), conf.get("by", ""), conf.get("at", ""), "human"]


# ────────────────────────────── 개수 표 (counts.csv) — 0919 «개수 세기» 사이클1, 지시서 §1-3
# 칸 이름은 지시서 그대로. 규칙(사람 확정 개수를 어디서 유도하나)은 툴 `app/boxes.py human_count()`
# **한 군데**에 있고 여기서 그것을 가져다 쓴다 — 화면의 «개수» 칸과 같은 값이 나온다.
COUNTS_COLS = ["stem", "n_boxes", "n_instances", "n_team_park", "n_team_im",
               # 2026-09-19 사이클2 논문대조 1차: **정답 개수**가 없으면 MAE·RMSE·R²
               # (farjon2023countingreview p.16 식 (1)~(4))를 셀 수 없다. 두 칸을 더한다.
               "n_gt", "gt_source",
               "n_human", "human_source", "count_conflict", "confirmed_by", "confirmed_at"]

# 검출 팀 박성문 님의 «정답 상자» 표 (읽기 전용). 한 줄 = 상자 하나이므로 사진마다 줄을 센다.
#   blueberry 는 gt_boxes 가 **없다**(`all/` 은 watershed 자동 추정이라 정답이 아니다) → 빈칸·«-»
GT_CSV = ("/data/project/2026summer/platform/work/park_seongmoon/bbox_outputs/"
          "%s/gt_boxes/csv/detections.csv")
GT_LABEL = "psm_gt_boxes"
_gt_cache = {}


def gt_counts(fruit):
    """{stem: 정답 상자 수} — 없으면 빈 딕셔너리. 과일마다 한 번만 읽는다."""
    if fruit in _gt_cache:
        return _gt_cache[fruit]
    out = {}
    p = GT_CSV % fruit
    if os.path.exists(p):
        try:
            with open(p, encoding="utf-8", newline="") as f:
                for r in csv.DictReader(f):
                    n = (r.get("image_name") or "").strip()
                    if n.lower().endswith(".png"):
                        n = n[:-4]
                    if n:
                        out[n] = out.get(n, 0) + 1
        except Exception:
            out = {}
    _gt_cache[fruit] = out
    return out


def _cell(v):
    """None 은 빈칸 — «0개» 와 «셀 수 없음/파일 없음» 을 표에서 구별한다."""
    return "" if v is None else str(v)


def n_boxes_saved(fruit, stem):
    """사람이 저장한 상자 개수 — 파일이 없거나 깨졌으면 None(툴 server.py n_boxes_of() 와 같다)."""
    p = os.path.join(DATA_DIR, fruit, "boxes", stem + ".json")
    try:
        with open(p, encoding="utf-8") as f:
            return len(json.load(f).get("boxes") or [])
    except Exception:
        return None


def _conf(rec, key):
    c = rec.get(key) if isinstance(rec, dict) else None
    return c if isinstance(c, dict) else {}


def counts_rows(fruit, confirmed_only=False, st=None, only=None):
    """counts.csv 의 줄들 + 사람 확정 개수가 있는 사진 수. 파일을 쓰지 않는다(시험이 이것을 본다).

    기본(«사람 확정만») 은 `n_human` 이 있는 사진만 낸다. «AI 제안 포함» 이면 (그 job 이 내보낸)
    사진을 전부 내되 확정이 없는 줄은 `n_human`·`human_source`·`confirmed_*` 가 빈칸이다(§1-3).

    `only` = **그 job 이 내보낸 stem 들**(집합). 🔴 0919 3차 전 **총괄 결정 2**(2차 검수 §4-2):
    전에는 상자·번호 확정만 보았기 때문에 마스크를 «제외» 로 확정한 사진이나 근접 중복으로 빠진
    사진도 줄이 남았다 — MAE·R² 는 «그 데이터셋» 에 대해 재는 값이라 분모가 달라진다. 이제
    `counts.csv` 는 같은 job 의 `manifest.csv` 에서 «포함» 인 사진만 담는다. `None` 이면 거르지
    않는다(시험이 규칙만 볼 때 쓰는 길 — 내보내는 두 길은 늘 `only` 를 받는다).

    `st` = 판정 기록(status.json)을 **불러 준 쪽에서** 넘기는 것. 0919 개수 사이클1 2차 검수 B-1:
    `export_one()` 이 맨 앞에서 읽은 것과 여기서 다시 읽은 것이 달라서(그 사이에 누가 확정하면)
    **같은 job 의 manifest 와 counts.csv 가 다른 스냅샷**이 됐다(실측 `stage2/a2_stale.py` [다]).
    주지 않으면 예전처럼 여기서 읽는다(개수만 내보내는 길·CLI).
    """
    from boxes import human_count, team_count          # 상자·개수 규칙은 툴 app/ 한 곳에만 둔다
    import instances as INST
    src_img = os.path.join(DUP.dataset_for(fruit), fruit, "images")
    if not os.path.isdir(src_img):
        return [], 0
    stems = sorted(n[:-4] for n in os.listdir(src_img) if n.lower().endswith(".png"))
    if st is None:
        st = read_status(fruit)
    gt = gt_counts(fruit)                              # 박성문 정답 상자 수(없는 과일은 빈 딕셔너리)
    rows, n_human = [], 0
    for s in stems:
        if only is not None and s not in only:
            continue                                   # 총괄 결정 2 — 나가지 않은 사진은 표에 없다
        rec = st.get(s, {})
        nb = n_boxes_saved(fruit, s)
        # 🔴 2차 검수 A-1: 캐시 값은 **지문이 맞을 때만** 쓴다(전에는 `cache.get(s)` 였다 —
        # 사람이 번호를 고친 뒤에도 옛 개수가 표에 적혔다. 툴 화면과 **같은 함수**를 쓴다).
        ni = INST.count_fresh(fruit, s)
        cb = _conf(rec, "confirmed_boxes").get("status")
        ci = _conf(rec, "confirmed_instances").get("status")
        # 번호를 확정했는데 캐시에 개수가 없으면 그 한 장만 지금 센다 — 확정한 사진은 드물어 값이
        # 싸고, 세지 않으면 «번호로 확정했는데 표에는 상자 수» 라는 조용한 거짓말이 된다.
        if ni is None and ci in ("ok", "fixed"):
            ni = INST.count_now(fruit, s)              # 총괄 결정 3 — 센 값을 캐시에 적는다
        nh, hsrc, conflict = human_count(nb, ni, cb, ci)
        if confirmed_only and nh is None:
            continue
        c = _conf(rec, "confirmed_instances") if hsrc == "instances" else (
            _conf(rec, "confirmed_boxes") if hsrc == "boxes" else {})
        ngt = gt.get(s)
        rows.append([s, _cell(nb), _cell(ni), _cell(team_count("박성문", fruit, s)),
                     _cell(team_count("임성후", fruit, s)),
                     _cell(ngt), GT_LABEL if ngt is not None else "-",
                     _cell(nh), hsrc,
                     "1" if conflict else "0", c.get("by", ""), c.get("at", "")])
        if nh is not None:
            n_human += 1
    return rows, n_human


def write_counts_csv(fruit, out, args, st=None, only=None):
    """<out>/counts.csv 를 쓴다. 돌려주는 것: 적은 줄 수(머리줄은 빼고).

    `st` 를 주면 그 **스냅샷**으로 센다(export_one 이 manifest 에 쓴 것과 같은 것 — 2차 검수 B-1).
    `only` 를 주지 않으면 **같은 옵션으로 지금 내보내면 나갈 사진**을 스스로 구한다(총괄 결정 2) —
    «개수» 만 골라 내보내는 길(server.py export_worker)이 이 자리다. 사진은 한 장도 나가지 않지만
    표는 «그 옵션이면 나갈 사진» 과 같아야 한다.
    """
    if only is None:
        only = included_stems(fruit, args, st=st)
    rows, n_human = counts_rows(fruit, bool(getattr(args, "confirmed_only", False)),
                                st=st, only=only)
    os.makedirs(out, exist_ok=True)
    p = os.path.join(out, "counts.csv")
    with open(p, "w", encoding="utf-8", newline="") as f:
        w = csv.writer(f)
        w.writerow(COUNTS_COLS)
        w.writerows(rows)
    print("     개수 표 %d줄 → %s  (사람이 확정한 개수가 있는 사진 %d장)" % (len(rows), p, n_human))
    return len(rows)


def exclude_reason(s, rec, args, rep_of):
    """이 사진을 **왜 빼나** — 빈 문자열이면 «포함». 판단 내용은 한 줄도 바꾸지 않았다(옮긴 것뿐).

    🔴 0919 3차 전 **총괄 결정 2**: `export_one()` 안에만 있던 판단을 밖으로 냈다. `counts.csv` 가
    «나간 사진» 만 담으려면 `included_stems()` 가 **같은 판단**을 써야 하고, 두 벌로 베끼면 곧
    갈라진다(사이클3 2차 의미-1 이 그런 갈라짐이었다).
    getattr — `export_one()` 을 **직접 부르는 시험들**(cycles/260917_신기능/…/n1_cut.py·n6_save.py)이
    argparse.Namespace 를 손으로 만들어 넘기므로, 새 옵션이 없어도 예전처럼 돌아야 한다.
    """
    status = rec.get("status", "unreviewed")
    conf = rec.get("confirmed") if isinstance(rec.get("confirmed"), dict) else None
    if conf:
        # 사람 확정이 최종이다(방향 문서 §5) — 확정이 있으면 AI 의 중복·제외 판단은 더 보지 않는다
        # (사람이 이미 그것을 보고 눌렀다). **두 모드가 여기서 똑같이 판단한다.**
        #
        # 0918 사이클3 **2차 검수**(의미-1): 전에는 이 갈래가 `confirmed_only` 일 때만 돌아서,
        # «AI 제안 포함» 은 사람 확정을 **아예 보지 않았다**. 그래서
        #   · 사람이 «제외» 로 확정한 사진이 그대로 나가고(오염 — manifest 에는 «포함 ·
        #     confirmed_status=exclude · source=human» 이라고 제 손으로 적혀 있었다)
        #   · 사람이 «원본 OK» 로 확정한 사진이 AI 제외 때문에 빠졌다(손실).
        # 화면의 풍선말도 «**사람이 확정하지 않은 사진도** AI 제안을 그대로 적용해 내보냅니다»
        # 라고 말한다 — 코드가 그 말을 어기고 있었다. 지금은 말대로 한다.
        if conf.get("status") == "exclude":
            return "confirmed_exclude"
        # 0918 사이클3 결정 2(사이클2 3차 판정 §4-2): 사람이 «문제 있음» 으로 확정한 것은
        # **아직 고칠 것**이라 «확실한 데이터셋» 이 아니다 → 기본 제외. 포함 옵션은 두지 않는다
        # (원하면 고쳐서 «수정함» 으로 확정하면 된다). manifest: 제외 · confirmed_flag
        if conf.get("status") == "flag":
            return "confirmed_flag"
        return ""
    if getattr(args, "confirmed_only", False):
        return "not_confirmed"
    if s in rep_of and rep_of[s] != s:
        return "duplicate_of:" + rep_of[s]
    if status == "exclude":
        return "status_exclude"
    if getattr(args, "drop_flag", False) and status == "flag":
        return "status_flag"
    return ""


def included_stems(fruit, args, st=None):
    """이 옵션으로 **지금 내보내면 «포함» 이 될 사진들**(집합). 파일은 하나도 읽지도 쓰지도 않는다
    (status.json·duplicates.json 만 본다). 총괄 결정 2 — `counts.csv` 를 여기에 맞춘다."""
    src_img = os.path.join(DUP.dataset_for(fruit), fruit, "images")
    if not os.path.isdir(src_img):
        return set()
    if st is None:
        st = read_status(fruit)
    groups = [] if getattr(args, "keep_duplicates", False) else load_duplicate_groups(fruit)
    rep_of = representative_map(groups, st) if groups else {}
    return {n[:-4] for n in os.listdir(src_img) if n.lower().endswith(".png")
            and not exclude_reason(n[:-4], st.get(n[:-4], {}) or {}, args, rep_of)}


def export_one(fruit, out, args, on_step=None, st=None):
    """한 과일을 내보낸다. `on_step(i, n)` 을 주면 사진 한 장마다 불러 준다(진행 막대용, 0918 사이클3).

    돌려주는 것: 무엇이 얼마나 나갔는지 세어 놓은 딕셔너리(서버의 job.json·진행 막대가 쓴다).

    `st` = 판정 기록(status.json) 스냅샷. 주면 그것으로 판단한다 — 0919 «개수 세기» **사이클4**
    (사이클1 2차 §2-4 가 남긴 것): 한 번의 내보내기 안에서 `read_status()` 가 **세 번** 불렸다
    (여기 · `write_counts_csv` · 서버 `export_worker` 의 상자 갈래). 사과 1,001장 내보내기는 수십
    초가 걸려서, 그 사이에 누가 확정하면 manifest·counts.csv·상자 YOLO 가 **서로 다른 스냅샷**을
    보고 갈렸다. 부르는 쪽이 한 번 읽어 세 자리에 같은 것을 넘긴다.
    """
    root = DUP.dataset_for(fruit)
    src_img = os.path.join(root, fruit, "images")
    if not os.path.isdir(src_img):
        # 이 원본 폴더에 그 과일이 없을 수 있다(예: 검수판 데이터셋에는 복숭아·포도만 있음)
        print("[%s] 건너뜀 — 이미지 폴더가 없습니다: %s" % (fruit, src_img))
        return {"fruit": fruit, "skipped": True, "n_total": 0, "n_out": 0, "n_dropped": 0,
                "out": out, "msg": "이미지 폴더가 없습니다: %s" % src_img}
    stems = sorted(n[:-4] for n in os.listdir(src_img) if n.lower().endswith(".png"))
    if st is None:
        st = read_status(fruit)          # CLI 는 그대로(스냅샷을 넘기지 않는다) — 답이 한 글자도 다르지 않다

    groups = [] if args.keep_duplicates else load_duplicate_groups(fruit)
    rep_of = representative_map(groups, st) if groups else {}

    rows = []
    n_fixed = n_orig = 0
    n_inst = n_inst_obj = 0
    n_cut = n_lost = n_hole = 0
    n_skip_status = n_skip_dup = 0
    for i, s in enumerate(stems):
        if on_step:
            on_step(i, len(stems))
        rec = st.get(s, {})
        status = rec.get("status", "unreviewed")
        conf = rec.get("confirmed") if isinstance(rec.get("confirmed"), dict) else None
        reason = exclude_reason(s, rec, args, rep_of)   # 판단은 위 한 군데에만 있다(총괄 결정 2)

        if reason:
            if reason.startswith("duplicate_of"):
                n_skip_dup += 1
            else:
                n_skip_status += 1
            rows.append([s, "제외", status, "", "", "", reason, rec.get("by", ""), rec.get("note", "")]
                        + conf_cells(conf))
            continue

        # 마스크 우선순위(masks_fixed > 원본)는 instances.py 한 곳에 둔다 —
        # 번호본을 그 이진본으로 자르는 쪽과 **같은 규칙**이어야 한다(사이클4 판정 N1).
        src = mask_path_of(fruit, s)
        source = "masks_fixed" if (os.sep + "masks_fixed" + os.sep) in src else "원본"
        if source == "masks_fixed":
            n_fixed += 1
        else:
            n_orig += 1
        arr, inst_kind, chk = None, None, {}
        # 0918 사이클4 결정 1: 열매 번호도 **자기 확정 칸**(confirmed_instances)을 본다.
        # 마스크 확정으로 **대체하지 않는다** — 번호를 한 번도 보지 않은 사람의 «원본 OK» 가
        # 번호까지 확정한 것처럼 새어 나가면 안 된다(방향 문서 §3-1 «작업마다 따로 확정»).
        # «AI 제안 포함»(confirmed_only=False)에서는 예전과 같이 전부 나간다.
        ci = rec.get("confirmed_instances") if isinstance(rec.get("confirmed_instances"), dict) else None
        inst_ok = True
        if args.instances and getattr(args, "confirmed_only", False):
            inst_ok = bool(ci) and ci.get("status") in ("ok", "fixed")
        if args.instances and not inst_ok:
            chk = {"skip": "번호 미확정"}
        elif args.instances and args.dry_run:
            inst_kind = source_of(fruit, s)[1]      # dry-run 은 파일을 쓰지 않으니 출처만 본다
        elif args.instances:
            try:
                arr, inst_kind, chk = load_inst(fruit, s)
            except ValueError as e:                 # 크기가 다르면 자르지 않고 manifest 에 적는다
                arr, inst_kind, chk = None, None, {"err": str(e)}
        rows.append([s, "포함", status, source, INST_LABEL.get(inst_kind, ""), check_cell(chk),
                     "", rec.get("by", ""), rec.get("note", "")] + conf_cells(conf))
        if args.dry_run:
            if inst_kind:
                n_inst += 1
            continue
        os.makedirs(os.path.join(out, "images"), exist_ok=True)
        os.makedirs(os.path.join(out, "masks"), exist_ok=True)
        dst_i = os.path.join(out, "images", s + ".png")
        if os.path.islink(dst_i) or os.path.exists(dst_i):
            os.remove(dst_i)
        if args.copy_images:
            import shutil
            shutil.copy2(os.path.join(src_img, s + ".png"), dst_i)
        else:
            os.symlink(os.path.join(src_img, s + ".png"), dst_i)
        save_mask_atomic(os.path.join(out, "masks", s + ".png"), load_mask_bool(src))
        if arr is not None:
            write_u16_atomic(os.path.join(out, "instances", s + ".png"), arr)
            n_inst_obj += int(ids_of(arr).size)
            n_inst += 1
            n_cut += bool(chk.get("cut"))
            n_lost += int(chk.get("lost_ids") or 0)
            n_hole += bool(chk.get("hole"))

    if on_step:
        on_step(len(stems), len(stems))
    res = {"fruit": fruit, "n_total": len(stems), "n_out": n_fixed + n_orig,
           "n_fixed": n_fixed, "n_orig": n_orig,
           "n_dropped": n_skip_status + n_skip_dup,
           "n_dropped_status": n_skip_status, "n_dropped_dup": n_skip_dup,
           "n_instances": n_inst, "n_objects": n_inst_obj,
           "confirmed_only": bool(getattr(args, "confirmed_only", False)),
           "dry_run": bool(args.dry_run), "out": out}
    print("[%s] 전체 %d장 → 포함 %d (수정본 %d / 원본 %d) · 제외 %d (상태 %d + 근접중복 %d)"
          % (fruit, len(stems), n_fixed + n_orig, n_fixed, n_orig,
             n_skip_status + n_skip_dup, n_skip_status, n_skip_dup))
    if args.instances:
        if args.dry_run:
            # ponytail: dry-run 은 파일을 읽지 않으므로 열매 «개수» 는 세지 않는다(장수만 센다)
            print("     열매 번호 마스크 %d장 내보낼 예정 → %s/instances/" % (n_inst, out))
        else:
            print("     열매 번호 마스크 %d장 (열매 %d개) → %s/instances/" % (n_inst, n_inst_obj, out))
            print("     번호본을 이진본으로 자른 장 %d(사라진 번호 %d개) · 전경인데 번호 없는 장 %d"
                  "(사람이 N 으로 붙일 자리) — 장마다 manifest 의 instances_check 칸"
                  % (n_cut, n_lost, n_hole))
    if groups:
        print("     근접 중복 그룹 %d개를 읽어 그룹당 1장만 남겼습니다 (끄려면 --keep-duplicates)" % len(groups))
    inc = {r[0] for r in rows if r[1] == "포함"}    # 총괄 결정 2 — counts.csv 는 이 사진들만
    if args.dry_run:
        if getattr(args, "counts", False):
            # ponytail: dry-run 은 파일을 쓰지 않는다. 몇 줄이 될지만 세어 말해 준다.
            print("     개수 표 %d줄 만들 예정 → %s/counts.csv"
                  % (len(counts_rows(fruit, bool(getattr(args, "confirmed_only", False)),
                                     st=st, only=inc)[0]), out))
        print("     (--dry-run 이라 아무 파일도 만들지 않았습니다. 내보낼 곳: %s)" % out)
        return res
    # 🟠 0919 개수 사이클1 **2차 검수 E-1**: 나갈 사진이 **0장**이면 위 반복문이 폴더를 만들지 않아
    # 이 줄이 FileNotFoundError 로 죽었다(실측: `--confirmed-only` · 사람 확정 0건인 지금 상태).
    # 화면(«데이터 정리» 탭)은 api_export_start 가 폴더를 먼저 만들어 괜찮았고, **명령줄만** 죽었다
    # (README §19-3 이 적어 둔 그 명령이다). 폴더를 만들고 «0장» manifest 를 정직하게 남긴다.
    os.makedirs(out, exist_ok=True)
    mp = os.path.join(out, "manifest.csv")
    with open(mp, "w", encoding="utf-8", newline="") as f:
        w = csv.writer(f)
        w.writerow(["stem", "포함여부", "status", "mask_source", "instances_source", "instances_check",
                    "excluded_reason", "by", "note",
                    # 0918 사이클3(N6) — 앞 9칸은 **한 칸도 바꾸지 않았다**(검출 팀이 읽는 표라서)
                    "confirmed_status", "confirmed_by", "confirmed_at", "source"])
        w.writerows(rows)
    if getattr(args, "counts", False):       # 0919 «개수 세기» — **같은 job 안에서** 같이 나간다
        # 2차 검수 B-1: manifest 를 만든 것과 **같은 스냅샷**(st)으로 센다.
        # 총괄 결정 2: 그리고 **같은 manifest 에서 «포함» 인 사진만**(inc) 센다.
        res["n_counts"] = write_counts_csv(fruit, out, args, st=st, only=inc)
    print("     만들었습니다: %s  (manifest: %s)" % (out, mp))
    return res


if __name__ == "__main__":
    main()
