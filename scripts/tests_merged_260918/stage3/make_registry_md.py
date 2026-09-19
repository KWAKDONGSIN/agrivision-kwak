#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""출처 등록표(문서/260918_통합데이터셋_출처등록표.md)를 build_summary.json 에서 기계적으로 다시 만든다.

- 표의 값(경로·주인·시각·개수·지문)은 **전부** build_summary.json 의 input_registry 에서 읽는다.
  사람이 손으로 고치지 않는다. 숫자가 어긋나면 build_summary.json 쪽이 맞다.
- 0920·0921 재빌드 뒤에도 이 스크립트를 그대로 다시 돌리면 된다.

쓰는 법:
    PY=/home/kds0206/.conda/envs/kwak/bin/python
    $PY semantic-segmentation/tools/tests_merged_260918/stage3/make_registry_md.py
        # 가장 최근 datasets_merged_* 를 스스로 찾아 문서/260918_통합데이터셋_출처등록표.md 를 덮어쓴다

    $PY .../make_registry_md.py --summary <폴더>/build_summary.json --out <경로.md>
    $PY .../make_registry_md.py --stdout          # 파일을 건드리지 않고 화면에만
"""
from __future__ import annotations

import argparse
import datetime as _dt
import json
import pathlib
import sys

ROOT = pathlib.Path("/data/project/2026summer/kds0206")
DEFAULT_OUT = ROOT / "문서/260918_통합데이터셋_출처등록표.md"
WRITTEN_ON = "2026-09-18"  # 이 문서를 처음 만든 날. 파일명의 날짜와 같다(바꾸지 않는다).

OWNER_KO = {
    "kds0206": "곽동신",
    "psm0717": "박성문",
    "cih0210": "최인훈",
    "lsh0616": "임성후",
}

SHORTEN = [
    ("/data/project/2026summer/kds0206/", "…/kds0206/"),
    ("/data/project/2026summer/platform/", "…/platform/"),
    ("/data/project/2026summer/", "…/"),
]

# (섹션 제목, 키가 이 중 하나로 시작하면 그 섹션) — 위에서부터 먼저 맞는 것
SECTIONS = [
    ("검수판 · 원본 (곽동신)", ("original:", "reviewed:")),
    ("라벨링 툴 data/ (공용 · 읽기 전용)", ("tool:",)),
    ("박성문 — 사과 번호 점검(apple_check)", ("psm:apple_check:",)),
    ("박성문 — 상자·번호맵", ("psm:",)),
    ("최인훈 — 복숭아 중복 감사 · 마스크 감사", ("cih:",)),
    ("임성후 — watershed 상자", ("lsh:",)),
]
SECTION_ORDER_FIX = [0, 1, 3, 2, 4, 5]  # 문서에 싣는 순서(박성문 상자표를 apple_check 보다 먼저)

FRUIT_KO = {"apple": "사과", "grape": "포도", "peach": "복숭아", "blueberry": "블루베리"}


def short(path: str) -> str:
    for a, b in SHORTEN:
        if path.startswith(a):
            return b + path[len(a):]
    return path


def owner_of(entry: dict) -> str:
    if not entry.get("exists"):
        return "**없음**"
    return OWNER_KO.get(entry.get("owner") or "", entry.get("owner") or "—")


def when_of(entry: dict) -> str:
    return entry.get("mtime") or entry.get("latest_mtime") or "—"


def size_of(entry: dict) -> str:
    if not entry.get("exists"):
        return "—"
    if entry.get("kind") == "dir":
        return f"파일 {entry.get('n_files', 0)}개"
    if entry.get("n_rows") is not None:
        return f"{entry['n_rows']}행"
    size = entry.get("size")
    if size is None:
        return "—"
    return f"{size / 1024:.1f}KB"


def fp_kind(entry: dict) -> str:
    fp = entry.get("fingerprint")
    if fp == "names+size+mtime":
        return "이름+크기+시각"
    if fp == "content":
        return "내용"
    return "—"


def fp_value(entry: dict) -> str:
    sha = entry.get("sha256") or ""
    return f"`{sha[:12]}`" if sha else "`—`"


def section_of(key: str) -> int:
    for i, (_title, prefixes) in enumerate(SECTIONS):
        if key.startswith(prefixes):
            return i
    return len(SECTIONS)  # 그 밖


def table(rows: list[tuple[str, dict]]) -> list[str]:
    out = [
        "| 키 | 경로 | 주인 | 시각 | 크기·개수 | 지문 기준 | 지문 sha256(앞 12) | 어디에 썼나 |",
        "|---|---|---|---|---|---|---|---|",
    ]
    for key, e in rows:
        out.append(
            f"| `{key}` | `{short(e.get('path', '—'))}` | {owner_of(e)} | {when_of(e)} | "
            f"{size_of(e)} | {fp_kind(e)} | {fp_value(e)} | {e.get('used_for', '—')} |"
        )
    return out


def build(summary_path: pathlib.Path, now: str) -> str:
    s = json.loads(summary_path.read_text(encoding="utf-8"))
    reg = s["input_registry"]
    out_dir = pathlib.Path(s["out_dir"]).name
    missing = s.get("missing_inputs", [])
    n_dir = sum(1 for v in reg.values() if v.get("kind") == "dir")
    n_file = sum(1 for v in reg.values() if v.get("kind") == "file")

    L: list[str] = []
    A = L.append

    A(f"작성: {WRITTEN_ON}")
    A(f"최종 수정: {now} (정본 v3 기준으로 다시 뜸 — 폴더 줄에도 지문이 들어감)")
    A("")
    A("# 통합 데이터셋 — 출처 등록표")
    A("")
    A(f"**어느 빌드 기준인가 — `{out_dir}/` (정본, {s['built_at']} 완성 · {s['elapsed_sec']}초).**")
    A("")
    A(f"`{out_dir}/` 를 만들 때 **읽은 파일 전부**입니다. 스크립트")
    A("(`semantic-segmentation/tools/build_merged_dataset.py`)가 빌드할 때마다 같은 내용을")
    A("`build_summary.json` 의 `input_registry` 에 기계적으로 남기고, 이 문서는 그것을 표로 옮긴 것입니다.")
    A("**전부 읽기 전용입니다 — 한 글자도 쓰지 않았습니다.**")
    A("")
    A(f"- 이 표의 출처: `{summary_path}`")
    A(f"- 빌드 시각: {s['built_at']} · 소요 {s['elapsed_sec']}초")
    A(f"- 읽은 입력 {len(reg)}개 (폴더 {n_dir} · 파일 {n_file} · «없음» {len(missing)})")
    A(f"- 빌드 스크립트 지문: `{(s.get('script_sha256') or '')[:12]}`")
    A("- 이 표는 사람이 손으로 쓰지 않습니다. 다시 뜨는 명령은 맨 아래 «이 표를 다시 만들려면» 에 있습니다.")
    A("- 표의 «크기·개수» 에서 `N행` 은 **머리글 줄을 뺀 데이터 줄 수**입니다(파일의 줄 수보다 1 적습니다).")
    A("")
    A("## 지문(sha256)이 무엇인가")
    A("")
    A("파일이나 폴더가 **바뀌었는지**를 한 줄로 알아보는 값입니다.")
    A("")
    A("- **파일**은 `내용` 을 통째로 읽어 지문을 냅니다 — 한 글자만 달라져도 값이 바뀝니다.")
    A("- **폴더**는 안쪽 «파일 이름 + 크기 + 시각(mtime)» 목록으로 지문을 냅니다")
    A("  (내용을 읽지 않으므로 빠르고, 같은 폴더면 몇 번을 떠도 같은 값이 나옵니다).")
    A("  그래서 **파일 수와 최신 시각은 그대로인데 안쪽 파일 하나만 바뀐** 경우도 잡힙니다")
    A("  (2026-09-18 3차 검수 결정 D4. 그 전 판인 `_v2` 에서는 폴더 줄의 지문 칸이 `—` 였습니다).")
    A("- **빈 폴더(파일 0개)는 전부 같은 지문 `e3b0c44298fc…`** 가 나옵니다 — 값이 겹쳐도 이상한 것이 아닙니다.")
    A("- 지문 칸이 `—` 인 줄은 그 경로에 **아무것도 없는** 줄입니다(아래 ««없음» 이었던 입력» 표 참조).")
    A("")
    A("## 왜 이 표가 필요한가")
    A("")
    A("통합 데이터셋의 한 칸 한 칸이 **누가 만든 무엇에서 왔는지** 되짚을 수 있어야 하기 때문입니다.")
    A("팀원이 파일을 새로 올리면 다음 빌드가 이 표를 직전 빌드의 것과 견줘 **«바뀐 입력»** 을 찍어 줍니다")
    A("(`README.md` 아래쪽과 로그). 그래서 «누가 무엇을 새로 올렸는지» 를 사람이 챙기지 않아도 됩니다.")
    A("")

    # ── 섹션별 표 ────────────────────────────────────────────────
    buckets: dict[int, list[tuple[str, dict]]] = {}
    for key in sorted(reg):
        buckets.setdefault(section_of(key), []).append((key, reg[key]))

    order = [i for i in SECTION_ORDER_FIX if i in buckets]
    order += [i for i in sorted(buckets) if i not in order]
    for i in order:
        title = SECTIONS[i][0] if i < len(SECTIONS) else "그 밖 (새로 생긴 입력)"
        A(f"## {title}")
        A("")
        L.extend(table(buckets[i]))
        A("")

    # ── «없음» ─────────────────────────────────────────────────
    A("## 이번 빌드에서 «없음» 이었던 입력")
    A("")
    if missing:
        A(f"**{len(missing)}개.** 그 경로에 파일·폴더가 없어서 빌드가 «없음» 으로 적고 그대로 진행했습니다")
        A("(그 칸은 비어 나갑니다). 아래 목록이 **다음 빌드의 기준선**입니다 — 이 7개는 원래 없는 것이라")
        A("«있다 → 없다» 사고로 세지 않습니다. 반대로 **여기 없던 것이 «없음» 으로 새로 나타나면 사고**이고,")
        A("그때는 빌드가 exit 3 으로 멈춥니다(3차 검수 결정 D3).")
        A("")
        A("| 키 | 경로 | 원래 어디에 쓰려던 것인가 |")
        A("|---|---|---|")
        for key in missing:
            e = reg.get(key, {})
            A(f"| `{key}` | `{short(e.get('path', '—'))}` | {e.get('used_for', '—')} |")
    else:
        A("**없습니다.** 읽으려던 입력이 전부 있었습니다.")
    A("")

    # ── 반영하지 않은 것(설명) ───────────────────────────────────
    A("## 읽었지만 «반영하지 않은» 것")
    A("")
    A("| 무엇 | 왜 |")
    A("|---|---|")
    A("| `psm:<과일>:all.json` | 임성후 판과 **바이트 동일**(2026-09-18 md5 대조) — 따로 세지 않았습니다 |")
    A("| `psm:<과일>:all.instance_maps` | 블루베리만 씁니다(`instances_source=detect_seed`). "
      "사과는 원본 마스크가 곧 번호 마스크(`reviewed_number_mask`)라 더 정확하고, 포도·복숭아는 채택 결정이 없습니다 |")
    A("| `cih:peach_dup:clusters.txt` | 해밍 22 로 묶으면 125장 중 112장이 한 덩어리가 되어 쓸 수 없습니다 |")
    A("| `cih:mask_audit:mask_stats.csv` | `reason` 칸이 **없습니다**(전체 4,823장 통계표). "
      "`reason` 은 `suspects.csv` 에서 읽습니다 |")
    A("| `psm:apple_check:duplicates_*.csv`·`per_image.csv`·`summary.json` | 참고용. 통합 manifest 에는 넣지 않았습니다 |")
    A("")

    A("## 🔴 사용자가 말한 이름과 실제 파일이 다른 것 (2026-09-18 실측)")
    A("")
    A("| 들은 것 | 실제 | 어떻게 했나 |")
    A("|---|---|---|")
    A("| 박성문 `gt_boxes` 는 **apple·blueberry** 만 있고 peach·grape 는 없다 | 거꾸로입니다. "
      "`gt_boxes` 가 있는 것은 **apple(1,001) · grape(2,502) · peach(125)** 이고, "
      "**blueberry 에는 `gt_boxes` 가 없습니다**(`all/` 만 있음) | 있는 과일은 `psm_gt`, 블루베리만 `lsh` 로 되넘김 |")
    A("| 최인훈 `mask_audit_260908` 의 `reason` 은 `mask_stats.csv` 에 있다 | "
      "**`suspects.csv` 가 맞습니다.** `reason` 칸이 있는 것은 suspects.csv(240행, 전부 `bottom_5pct_ratio`)이고, "
      "`mask_stats.csv`(4,823행)에는 `reason` 칸이 **없습니다** | "
      "`mask_audit_reason` 은 **suspects.csv** 에서 읽음. mask_stats.csv 는 등록만 |")
    A("| 박성문 `apple_check/review_list.csv` 에 사람 판정 `verdict` | 맞습니다(판정 465줄·사진 283장, "
      "`ok_one_apple` 422 · `duplicate_polygon` 16 · `unclear` 14 · `border_artifact` 6 · "
      "`one_apple_two_ids` 5 · `two_apples_one_id` 2). `confirmed_errors.csv` 는 그중 확정된 38줄·32장 | "
      "둘 다 `apple_check_verdict` 에 모음 |")
    A("| 임성후 판과 박성문 판이 «같은 stem 이면 최신 우선» | 두 사람의 `<과일>/all/` 은 **같은 파일**입니다"
      "(같은 mtime·같은 지문). 실제 차이는 박성문이 **09-12 에 `gt_boxes` 를 더 만들었다**는 것 | "
      "`gt_boxes`(정답 마스크 기반)를 위로 두고, 없으면 `all/`(watershed)로 |")
    A("")

    # ── 상자 두 판 비교 ─────────────────────────────────────────
    cross = s.get("box_crosscheck") or {}
    if cross:
        A("## 상자 두 판(정답 기반 vs watershed)이 얼마나 다른가")
        A("")
        A("| 과일 | 견준 장수 | 개수가 다른 장 | 평균 차이(개) | 보기 |")
        A("|---|---:|---:|---:|---|")
        for fruit in ("apple", "grape", "peach", "blueberry"):
            c = cross.get(fruit)
            if not c:
                continue
            ex = " · ".join(
                f"{x['stem']}: {x['lsh']}→{x['psm_gt']}" for x in (c.get("examples") or [])[:2]
            )
            A(f"| {FRUIT_KO[fruit]} | {c.get('n_both', 0)} | {c.get('n_count_differs', 0)} | "
              f"{c.get('mean_abs_diff', 0)} | {ex or '—'} |")
        A("")
        A("`lsh`(watershed 추정) → `psm_gt`(정답 마스크에서 뽑은 상자) 순으로 적었습니다.")
        A("**우리는 `psm_gt` 를 씁니다** — 사람이 만든 정답 마스크에서 나온 상자라 추정이 섞이지 않습니다.")
        A("블루베리는 `gt_boxes` 가 없어 `lsh`(미검증 추정)를 쓰므로, **블루베리 상자는 «참고»** 로 보십시오.")
        A("")

    # ── 다시 만들려면 ───────────────────────────────────────────
    A("## 이 표를 다시 만들려면")
    A("")
    A("빌드가 끝난 뒤 아래 한 줄이면 됩니다(새 빌드를 스스로 찾습니다). 손으로 고치지 마십시오.")
    A("")
    A("```bash")
    A("PY=/home/kds0206/.conda/envs/kwak/bin/python")
    A("cd /data/project/2026summer/kds0206")
    A("$PY semantic-segmentation/tools/tests_merged_260918/stage3/make_registry_md.py")
    A("```")
    A("")
    A("특정 빌드를 지정하려면 `--summary <폴더>/build_summary.json`,")
    A("파일을 건드리지 않고 화면으로만 보려면 `--stdout` 을 주십시오.")
    A("")
    A("빌드할 때마다 `build_summary.json` 에 같은 내용이 자동으로 들어갑니다. 이 문서는 사람이 읽기 위한 사본이므로,")
    A("숫자가 어긋나면 **`build_summary.json` 쪽이 맞습니다.**")
    return "\n".join(L) + "\n"


def newest_summary() -> pathlib.Path:
    cands = []
    for d in ROOT.glob("datasets_merged_*"):
        f = d / "build_summary.json"
        if not f.is_file():
            continue
        try:
            s = json.loads(f.read_text(encoding="utf-8"))
        except Exception:
            continue
        if "input_registry" in s:  # 등록표가 없는 첫 판(_v1)은 건너뛴다
            cands.append((s.get("built_at", ""), f))
    if not cands:
        sys.exit("build_summary.json(input_registry 포함)을 가진 datasets_merged_* 폴더가 없습니다.")
    return max(cands)[1]


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--summary", help="build_summary.json 경로(기본: 가장 최근 빌드)")
    ap.add_argument("--out", default=str(DEFAULT_OUT), help="쓸 md 경로")
    ap.add_argument("--stdout", action="store_true", help="파일을 쓰지 않고 화면에만")
    a = ap.parse_args()

    summary = pathlib.Path(a.summary) if a.summary else newest_summary()
    now = _dt.datetime.now().strftime("%Y-%m-%d %H:%M")
    text = build(summary, now)

    if a.stdout:
        sys.stdout.write(text)
        return
    out = pathlib.Path(a.out)
    out.write_text(text, encoding="utf-8")
    print(f"썼습니다: {out}  (기준 빌드: {summary})")


if __name__ == "__main__":
    main()
