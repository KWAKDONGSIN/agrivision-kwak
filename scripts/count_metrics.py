# -*- coding: utf-8 -*-
"""개수(카운팅) 정확도 지표 — MAE · RMSE · R² 를 표 하나로.  작성: 2026-09-19

무엇을 하나
  라벨링 툴이 내보낸 `counts.csv` 또는 통합 데이터셋의 `manifest.csv` 를 읽어,
  **정답 개수(`n_gt`)가 있는 사진**만 골라 «출처별» 로 지표를 낸다.
  출처 = 그 개수를 **누가·무엇이** 세었나:
    n_boxes      사람이 툴에 저장한 상자 수
    n_instances  열매 번호(인스턴스) 수  ← 초벌 출처는 과일마다 다르다(app/instances.py SEED_DIRS)
    n_team_park  박성문 님 자동 상자 수      (counts.csv 에만 있는 칸)
    n_team_im    임성후 님 자동 상자 수      (counts.csv 에만 있는 칸)
    n_human      사람 확정 개수(번호 확정 > 상자 확정에서 유도 · 어긋나면 비어 있다)
                 통합 manifest 에서는 같은 것이 `n_count_human` 이라는 이름이다.

왜 이 네 지표인가 (근거)
  `farjon2023countingreview` (Precision Agriculture 24:1683–1711) **PDF p.16 = 인쇄 p.1698**,
  농업 계수 논문 243편을 조사한 리뷰의 «평가 지표» 절:
    "The standard and widely used metrics for evaluating overall performance are the
     Mean Absolute Error (MAE) and the Mean Square Error (MSE)"
    "In some cases, researchers use the Root Mean Absolute Error (RMAE) or the Root Mean
     Square Error (RMSE)… Two additional commonly used metrics are the relative Root Mean
     Squared Error (rRMSE) and the coefficient of determination (R2)."
  같은 쪽의 식 (1)~(4) 를 그대로 쓴다. n = 사진 수, y = 정답 개수, ŷ = 센 개수:

    식 (1)  e_i  = y_i − ŷ_i                          (사진 한 장의 오차)
    식 (2)  MAE  = (1/n) · Σ |e_i|                     (평균 절대 오차 — 장당 몇 개 틀리나)
    식 (3)  RMSE = sqrt( (1/n) · Σ e_i² )              (큰 오차를 더 무겁게 본다)
    식 (4)  R²   = 1 − Σ e_i² / Σ (y_i − ȳ)²           (정답의 흩어짐 중 설명된 몫)

  한 줄 더 싣는 «총량편향%» 는 farjon 의 식은 아니고 박성문 님 `eval/summary.md` §7.2 가 쓰는
  값이다(Σŷ/Σy − 1). 사진마다는 틀려도 **합계**는 맞을 수 있으므로 같이 본다.

정답(`n_gt`)이 어디서 오나 · 어느 규칙인가  ⚠ 논문에 쓸 때 꼭 밝힐 것
  박성문 님 `bbox_outputs/<과일>/gt_boxes/csv/detections.csv` 의 **사진별 줄 수**(한 줄 = 정답
  상자 하나). 실측 합계 사과 40,468 · 복숭아 977 · 포도 9,832 · **블루베리는 파일이 없다**
  → 블루베리는 이 표에서 아예 빠진다(`n_gt` 빈칸).
  · 사과: 같은 정답을 «세는 규칙» 에 따라 세 값이다 — 제한 없음 40,468 / 툴 화면 규칙(4화소 이상)
    40,467 / `instance_split.MIN_AREA`(10화소) 40,464. 이 스크립트는 **파일에 적힌 값 그대로**
    쓴다(= 제한 없음 40,468 계열).
  · 포도: **송이(bunch) 단위**다. 알 단위가 아니다(CERTH COCO RLE 송이 마스크 → 2,502장 9,832송이).
    0919 사이클4 실측: `data/grape/instances_seed/` 번호 수와 `n_gt` 가 **2,502장 전부 일치**
    (합계 9,832 · hole·cut 0화소) → 포도 `n_gt` 는 CERTH 송이 수가 맞다.

포도 한 줄 (사이클3 3차 판정)
  포도는 **자동 계수를 쓸 수 없다**: 닿은 송이 31.4% · 조각 43.5% 이고 자동 계수가 CC **+62%** ·
  워터셰드 **+123%** 로 부풀린다. 그래서 포도 표 아래에 «자동 계수 참고(CC +62%)» 한 줄을 달고,
  포도 지표는 **정답 송이(9,832)로만** 쓴다(자동 계수 결과는 숨기지 않고 그대로 싣는다).

쓰는 법
  PY=/home/kds0206/.conda/envs/kwak/bin/python
  # ① 툴이 내보낸 폴더 하나 (counts.csv)
  $PY tools/count_metrics.py --counts <exports>/260919_183000_peach/counts.csv
  # ② 통합 데이터셋 manifest (과일 칸이 있어 과일별로 저절로 나뉜다)
  $PY tools/count_metrics.py --counts /data/.../datasets_merged_260918_v3/manifest.csv
  # ③ 여러 개를 한 번에 · 표를 파일로
  $PY tools/count_metrics.py --counts a/counts.csv b/manifest.csv --out reports/counts_metrics.md

만들지 않는 것 (yagni)
  그림·그래프를 만들지 않는다(표만). 마스크를 읽지 않는다 — 이미 센 표를 읽을 뿐이라 1초 안에 끝난다.
"""
import argparse
import csv
import math
import os
import sys

# 표에 싣는 «출처» — (칸 이름, manifest 에서의 다른 이름, 사람 말)
#  순서가 표의 줄 순서다. 사람 확정을 맨 아래에 둔다(툴 방향: 사람 확정이 위다 → 표에서는 결론 줄).
SOURCES = [("n_boxes", "n_boxes", "사람이 저장한 상자"),
           ("n_instances", "n_instances", "열매 번호(초벌 출처는 과일마다)"),
           ("n_team_park", None, "박성문 자동 상자"),
           ("n_team_im", None, "임성후 자동 상자"),
           ("n_human", "n_count_human", "🟢 사람 확정 개수")]
FRUIT_KO = {"peach": "복숭아", "grape": "포도", "apple": "사과", "blueberry": "블루베리"}
# 🔴 **알려진 순환 짝**(과일, 칸) — 센 값과 정답 `n_gt` 가 **같은 파일**에서 나오는 자리.
#   · 사과 `n_instances`  = 원본 마스크의 정답 번호 ↔ 그 마스크로 만든 `gt_boxes`
#   · 포도 `n_instances`  = CERTH 정답 송이 ↔ 같은 송이로 만든 `gt_boxes`
#   (2026-09-19 사이클4 2차: 여기에 없는 «오차 0» 줄은 «⚠오차0» 으로만 적고 순환이라 단정하지 않는다)
KNOWN_LOOP = {("apple", "n_instances"), ("grape", "n_instances")}
FRUITS = ["peach", "grape", "apple", "blueberry"]
# 포도 한 줄 — 사이클3 2차 §5-1 실측(원본 4K 전수 2,502장) · 3차 판정이 «그대로 실어라» 로 확정
GRAPE_NOTE = ("자동 계수 참고(CC **+62%**) — 포도는 닿은 송이 31.4%·조각 43.5% 라 자동 계수가"
              " 부풀린다(워터셰드 +123%). 포도 지표는 **정답 송이 9,832**로만 쓴다.")


def num(v):
    """표 칸 하나 → 수 또는 None. 빈칸·`-`·숫자가 아닌 것은 «없음»(0 이 아니다)."""
    v = (v or "").strip()
    if v in ("", "-", "None"):
        return None
    try:
        return float(v)
    except ValueError:
        return None


def metrics(y, p):
    """farjon p.16 식 (1)~(4). y=정답, p=센 값(같은 길이). 표본이 없으면 None."""
    n = len(y)
    if not n:
        return None
    e = [a - b for a, b in zip(y, p)]                       # 식 (1)
    mae = sum(abs(x) for x in e) / n                        # 식 (2)
    rmse = math.sqrt(sum(x * x for x in e) / n)             # 식 (3)
    ybar = sum(y) / n
    sstot = sum((a - ybar) ** 2 for a in y)
    r2 = (1 - sum(x * x for x in e) / sstot) if sstot else float("nan")   # 식 (4)
    sy, sp = sum(y), sum(p)
    return {"n": n, "gt": sy, "pred": sp, "mae": mae, "rmse": rmse, "r2": r2,
            "bias": (100.0 * (sp / sy - 1)) if sy else float("nan")}


def read_table(path):
    """counts.csv 또는 manifest.csv → (kind, [행 딕셔너리]). 칸 이름으로 어느 쪽인지 안다."""
    with open(path, encoding="utf-8-sig", newline="") as f:
        rows = list(csv.DictReader(f))
    if not rows:
        return None, []
    cols = set(rows[0])
    if "n_team_park" in cols:
        return "counts", rows
    if "n_count_human" in cols or "fruit" in cols:
        return "manifest", rows
    return None, rows


def fruit_of(path, row, forced):
    """이 줄이 어느 과일인가 — manifest 는 `fruit` 칸, counts.csv 는 폴더 이름에서."""
    if forced:
        return forced
    f = (row.get("fruit") or "").strip()
    if f:
        return f
    # exports/<날짜시각>_<과일>/counts.csv 꼴. 못 알아내면 "?" — 표에 그렇게 찍힌다.
    parts = os.path.abspath(path).split(os.sep)
    for seg in reversed(parts):
        for fr in FRUITS:
            if seg.endswith("_" + fr) or seg == fr:
                return fr
    return "?"


def collect(paths, forced_fruit=None):
    """{과일: {출처: (정답목록, 센값목록)}} + 읽은 줄·빠진 줄 세기."""
    per = {}
    tally = {"files": 0, "rows": 0, "no_gt": 0, "kinds": []}
    for path in paths:
        kind, rows = read_table(path)
        tally["files"] += 1
        tally["kinds"].append("%s(%s)" % (os.path.basename(path), kind or "모르는 표"))
        for row in rows:
            tally["rows"] += 1
            gt = num(row.get("n_gt"))
            if gt is None:
                tally["no_gt"] += 1
                continue                       # 정답이 없으면 지표를 낼 수 없다(블루베리 전부)
            fr = fruit_of(path, row, forced_fruit)
            box = per.setdefault(fr, {})
            for key, alt, _ in SOURCES:
                v = num(row.get(key))
                if v is None and alt and alt != key:
                    v = num(row.get(alt))
                if v is None:
                    continue                   # 그 출처가 없는 사진은 **그 줄에서만** 빠진다(0 으로 치지 않는다)
                ys, ps = box.setdefault(key, ([], []))
                ys.append(gt)
                ps.append(v)
    return per, tally


def md(per, tally, paths):
    """마크다운 표. 사람이 그대로 보고서에 붙일 수 있게."""
    L = ["# 개수 정확도 — MAE · RMSE · R²", "",
         "작성: 2026-09-19 · 만든 것: `tools/count_metrics.py`",
         "",
         "지표 정의는 `farjon2023countingreview` PDF p.16(인쇄 p.1698) 식 (1)~(4) 를 그대로 씁니다:",
         "`e=y−ŷ` · `MAE=Σ|e|/n` · `RMSE=√(Σe²/n)` · `R²=1−Σe²/Σ(y−ȳ)²`."
         " 총량편향% = `Σŷ/Σy−1` (farjon 식은 아니고 박성문 `eval/summary.md` §7.2 가 쓰는 값).",
         "",
         "읽은 표: " + " · ".join("`%s`" % k for k in tally["kinds"]),
         "",
         "| 과일 | 출처 | 사진 n | 정답 합계 | 센 합계 | 총량편향% | MAE | RMSE | R² |",
         "|---|---|---:|---:|---:|---:|---:|---:|---:|"]
    order = [f for f in FRUITS if f in per] + [f for f in sorted(per) if f not in FRUITS]
    any_row = False
    loop = []                      # 정답과 같은 파일에서 나온 줄(= 지표가 아니라 «어긋남 없음» 확인)
    zeros = []                     # 오차가 0 인데 «알려진 순환 짝» 은 아닌 줄 (사이클4 2차)
    for fr in order:
        for key, _alt, ko in SOURCES:
            got = per[fr].get(key)
            if not got:
                continue
            m = metrics(*got)
            any_row = True
            # 🔴 순환 경고: 오차가 **정확히 0** 인 줄은 «잘 센 것» 이 아니라 센 값과 정답이 **같은
            # 파일에서** 나온 것이다(사과 원본 번호 ↔ `gt_boxes` · 포도 CERTH 송이 ↔ 같은 정답).
            # 그것을 정확도로 읽으면 사후 정당화가 된다 — 그래서 표 안에서 이름을 붙여 막는다.
            # 🔴 2026-09-19 «개수 세기» 사이클4 **2차 검수**: 전에는 «오차가 정확히 0» 이면 무조건
            #   «⚠순환» 을 붙이고 표 아래에 «센 값과 정답이 같은 파일에서 나왔습니다» 라고 **단정**했다.
            #   그런데 오차 0 은 두 가지다 — ① 정말 같은 파일에서 나온 순환(사과 원본 번호·포도 CERTH
            #   송이) ② 표본이 적어 **사람이 정말 다 맞힌** 경우. 실측(2차 §4): 사람이 확정한 개수가
            #   두 장 다 맞은 표를 넣으면 «🟢 사람 확정 개수 ⚠순환» 이 붙고 «같은 파일에서 나왔다» 는
            #   거짓 설명이 달렸다. → 출처가 **알려진 순환 짝**일 때만 «⚠순환», 나머지는 «⚠오차0».
            zero = m["n"] >= 2 and m["mae"] == 0.0
            circular = zero and (fr, key) in KNOWN_LOOP
            if circular:
                loop.append("%s / %s" % (FRUIT_KO.get(fr, fr), ko))
            elif zero:
                zeros.append("%s / %s" % (FRUIT_KO.get(fr, fr), ko))
            L.append("| %s | %s | %d | %d | %d | %+.2f | %.2f | %.2f | %s |"
                     % (FRUIT_KO.get(fr, fr),
                        ko + (" ⚠순환" if circular else (" ⚠오차0" if zero else "")),
                        m["n"], round(m["gt"]), round(m["pred"]),
                        m["bias"], m["mae"], m["rmse"],
                        "—" if m["r2"] != m["r2"] else "%.3f" % m["r2"]))
    if not any_row:
        L.append("| — | 정답(`n_gt`)이 있는 줄이 없습니다 | 0 | | | | | | |")
    L += ["",
          "- **줄이 없는 출처는 그 사진에 그 값이 없었다는 뜻**입니다. 0 으로 치지 않고 그 줄만 뺍니다"
          " — 그래서 출처마다 `사진 n` 이 다를 수 있습니다(사람 확정 개수는 확정한 사진만).",
          "- 블루베리는 정답 상자 파일(`gt_boxes`)이 **없어** 이 표에 나오지 않습니다"
          " (논문에도 그렇게 적을 것).",
          "- 사과 정답은 세는 규칙에 따라 40,468(제한 없음) / 40,467(4화소) / 40,464(10화소) 입니다."
          " 이 표는 **표에 적힌 값 그대로**(제한 없음 계열)를 씁니다.",
          "- `n_team_park` 와 `n_team_im` 은 **독립 확인이 아닙니다** — 두 폴더의 파일이 4,823개"
          " 바이트까지 같습니다(사이클3 2차 §6). «같은 절차의 두 사본» 으로 읽으십시오."]
    if loop:
        L += ["- 🔴 **«⚠순환» 이 붙은 줄은 정확도가 아닙니다**: " + " · ".join(loop)
              + ". 센 값과 정답이 **같은 파일**에서 나왔습니다 — 알려진 세 경우:"
              " ① 사과 원본 마스크의 정답 번호 ↔ 그 마스크로 만든 `gt_boxes`"
              " ② 포도 CERTH 정답 송이 ↔ 같은 송이로 만든 `gt_boxes`"
              " ③ 통합 데이터셋의 `n_boxes` ↔ 그 상자가 `boxes_source=psm_gt`(= 같은 `gt_boxes`) 일 때."
              " MAE 0 · R² 1.000 은 «두 경로가 어긋나지 않는다» 는 **확인**으로만 읽으십시오"
              " — 논문에 «우리 방법이 오차 0» 으로 쓰면 사후 정당화입니다."]
    if zeros:
        L += ["- ⚠ **«⚠오차0» 이 붙은 줄은 오차가 정확히 0 이지만 «순환» 이라고 단정하지 않습니다**: "
              + " · ".join(zeros)
              + ". 두 가지일 수 있습니다 — ① 센 값과 정답이 **같은 파일**에서 나왔거나(순환)"
              " ② 표본이 적어 **정말로 다 맞은** 경우입니다. `gt_source`·`human_source`"
              "(counts.csv) 또는 `boxes_source`·`instances_source`(manifest) 칸으로 어느 쪽인지"
              " 확인한 뒤에 논문에 쓰십시오."]
    if "grape" in per:
        L += ["- 포도: " + GRAPE_NOTE]
    L += ["",
          "읽은 줄 %d개 중 정답이 없어 뺀 줄 %d개 · 표 %d개."
          % (tally["rows"], tally["no_gt"], tally["files"])]
    return "\n".join(L)


def main(argv=None):
    ap = argparse.ArgumentParser(description="counts.csv / manifest.csv 에서 개수 지표(MAE·RMSE·R²)")
    ap.add_argument("--counts", nargs="+", required=True,
                    help="counts.csv 또는 manifest.csv 경로(여러 개 가능). 폴더를 주면 그 안의 두 이름을 찾는다")
    ap.add_argument("--fruit", default=None, help="counts.csv 에 과일 칸이 없고 경로로도 모를 때만")
    ap.add_argument("--out", default=None, help="마크다운 표를 이 파일로도 쓴다(기본은 화면에만)")
    args = ap.parse_args(argv)

    paths = []
    for p in args.counts:
        if os.path.isdir(p):
            got = [os.path.join(p, n) for n in ("counts.csv", "manifest.csv")
                   if os.path.exists(os.path.join(p, n))]
            if not got:
                print("⚠ 폴더에 counts.csv·manifest.csv 가 없습니다: %s" % p, file=sys.stderr)
            paths += got
        elif os.path.exists(p):
            paths.append(p)
        else:
            print("⚠ 그런 파일이 없습니다: %s" % p, file=sys.stderr)
    if not paths:
        print("읽을 표가 없습니다.", file=sys.stderr)
        return 2
    per, tally = collect(paths, args.fruit)
    text = md(per, tally, paths)
    print(text)
    if args.out:
        os.makedirs(os.path.dirname(os.path.abspath(args.out)), exist_ok=True)
        with open(args.out, "w", encoding="utf-8") as f:
            f.write(text + "\n")
        print("\n→ %s" % args.out, file=sys.stderr)
    return 0


def demo():
    """ponytail: 자체 점검 — **실제 metrics()·num()·read_table()** 을 쓴다(파일 없이 손계산과 대조)."""
    assert num("") is None and num("-") is None and num("3") == 3.0 and num(" 4 ") == 4.0
    assert num("없음") is None
    # 손계산: 정답 [10,10], 센 값 [12,9] → e=[-2,1] · MAE=1.5 · RMSE=√2.5 · Σ(y-ȳ)²=0 → R²=nan
    m = metrics([10, 10], [12, 9])
    assert m["n"] == 2 and abs(m["mae"] - 1.5) < 1e-12, m
    assert abs(m["rmse"] - math.sqrt(2.5)) < 1e-12, m
    assert m["r2"] != m["r2"], m                       # 정답이 다 같으면 R² 는 정의되지 않는다(nan)
    # 손계산: 정답 [1,2,3], 센 값 [1,2,4] → e=[0,0,-1] · MAE=1/3 · RMSE=√(1/3) · R²=1−1/2=0.5
    m = metrics([1, 2, 3], [1, 2, 4])
    assert abs(m["mae"] - 1 / 3) < 1e-12 and abs(m["r2"] - 0.5) < 1e-12, m
    assert abs(m["bias"] - (100.0 * (7 / 6 - 1))) < 1e-12, m
    assert metrics([], []) is None
    # 없는 값은 0 이 아니라 «그 줄만 뺀다» — 그래서 출처마다 n 이 다르다
    rows = [{"n_gt": "10", "n_boxes": "9", "n_human": ""},
            {"n_gt": "20", "n_boxes": "", "n_human": "20"}]
    per = {}
    for r in rows:
        for key, alt, _ in SOURCES:
            v = num(r.get(key))
            if v is None:
                continue
            ys, ps = per.setdefault(key, ([], []))
            ys.append(num(r["n_gt"]))
            ps.append(v)
    assert metrics(*per["n_boxes"])["n"] == 1 and metrics(*per["n_human"])["n"] == 1, per
    assert metrics(*per["n_human"])["mae"] == 0.0
    print("count_metrics.py 자체 점검 통과 (실제 num()·metrics() 로 손계산 5건을 맞춰 봤습니다)")


if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "--selftest":
        demo()
    else:
        sys.exit(main())
