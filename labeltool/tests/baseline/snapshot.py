# -*- coding: utf-8 -*-
"""기준선(baseline) 뜨기 · 대조하기.  작성: 2026-09-19

리팩터 전후로 **동작이 바뀌지 않았는지** 증명하는 자료를 한 폴더에 모은다.
`tests/run_all.sh --rebaseline` 이 이 파일을 부른다. 직접 부를 때:

    python tests/baseline/snapshot.py --rebaseline      # 기준선을 새로 뜬다(덮어쓴다)
    python tests/baseline/snapshot.py --check           # 지금 코드와 대조해 다른 칸을 표로

담는 것 다섯 가지
  ① 고정 표본(네 과일 × 3장 = 12장)에 대한 API 응답 JSON — **변하는 칸을 지운 뒤** 저장 + sha256
  ② 내보내기(모래상자 · «AI 제안 포함» · 네 과일 × mask·instances·boxes·counts) 산출 파일 sha256
  ③ 회귀 묶음별 통과/실패 수 (`run_all.sh` 가 남긴 `_out/bundles.tsv` 를 읽는다)
  ④ 정적 파일·서버 코드 sha256 (참고용 — 리팩터하면 **당연히 바뀐다**)
  ⑤ **① 이 지나지 않는 나머지 라우트 전부** — 읽기(GET)·**쓰기(POST)**·로그인·그림 바이트 ·
     그리고 그 쓰기가 디스크에 남긴 것(status.json·boxes/*.json·boxes_yolo/*.txt·masks_fixed ·
     instances_fixed)의 지문. 2026-09-19 2차 검수가 «① 은 GET 7개뿐이라 라우트 37개 중 11개만
     지난다» 는 것을 실측해서 넣었다(`cycle_1/stage2_review.md` §1).

왜 «표본 데이터셋» 을 따로 만드나
  실제 원본 폴더를 그대로 쓰면 네 과일 4,071장을 내보내야 하고(수 분·수 GB) 그 사이 사람이
  실서버에서 라벨을 고치면 기준선이 흔들린다. 그래서
    · 사진·마스크는 고정 표본 12장만 담은 작은 폴더(`_sandbox/dataset_sample`)를 만들고
    · `status.json`·`duplicates.json` 은 **fixtures 에 얼려 둔 사본**(`fixtures/status_260920/`)을 쓴다.
  이러면 기준선은 **코드만의 함수**가 된다(사람이 라벨을 고쳐도 안 흔들린다).

합격 기준
  ①·②·⑤ 가 다르면 **실패**(동작이 바뀌었다는 뜻).
  ③ 은 실패 수가 늘면 실패(이번 실행에서 **안 돌린** 묶음은 경고). ④ 는 **경고만** —
  리팩터는 코드 지문을 바꾸는 일이니까.
"""
import argparse
import base64
import csv
import io
import json
import os
import re
import shutil
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
import zlib

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(os.path.dirname(HERE), "lib"))
import sandbox as L                                            # noqa: E402

FIX = L.FIX
BASE_DIR = os.path.join(FIX, "baseline_260920")
STEMS_TXT = os.path.join(FIX, "stems.txt")
FROZEN = os.path.join(FIX, "status_260920")
SB = os.path.join(L.SB_ROOT, "sb_base")
SAMPLE = os.path.join(L.SB_ROOT, "dataset_sample")
N_PER_FRUIT = 3
Q = urllib.parse.quote

# ── «변하는 칸» — 이름이 이 목록에 걸리는 칸은 값을 지운다(⟨지움⟩ 으로)
VOLATILE_KEYS = {
    "at", "started", "finished", "mtime", "ts", "time", "now", "pid", "elapsed",
    "sec", "secs", "seconds", "took", "job", "out", "dir", "data_root", "port", "sig",
    "generated", "updated", "created", "date", "when", "host", "url", "path", "outdir",
    "log", "version", "build", "uptime", "started_at", "finished_at", "counted_at",
}
# 🔴 2026-09-19 2차 검수 §3-2: `by` 를 이 목록에서 **뺐다.** 얼린 판정 자료 + 고정된 검수자 이름
#   (`기준선`)을 쓰므로 `by` 는 돌릴 때마다 같다 — 지워 두면 «누가 확정했다고 적히나» 가 리팩터로
#   깨져도 안 잡힌다(실측: ① 에서 60칸이 `by` 라는 이유만으로 비어 있었다).
# ── 값 규칙(VOLATILE_VAL)을 **적용하지 않는** 칸 이름. 이 칸에는 뜻 있는 값이 들어 있다.
NEVER_BY_VALUE = {"stem", "stems", "rep", "name", "fruit", "note", "error", "msg", "why",
                  "empty_txt_names", "stale_txt_names", "members", "changed", "skipped"}
# ── 값 안에 시각·PID·경로가 박혀 있는 것도 지운다
VOLATILE_VAL = re.compile(
    r"(\d{4}-\d{2}-\d{2}[ T]\d{2}:\d{2})"            # 2026-09-19 22:00
    # 🔴 2026-09-19 2차 검수 §3-1: 전에는 `(\d{6}_\d{6})` 였다. 사과 사진 이름
    #   `20150919_174151_image1` 안의 `150919_174151` 이 여기 걸려서 **사과 `stem` 18칸과
    #   `note` 8칸이 통째로 비어 있었다**(실측). 즉 «사과 사진을 열면 그 사진이 오나» 를
    #   기준선이 못 봤다. 앞뒤가 숫자가 아닐 때만 «내보내기 폴더 이름» 으로 본다.
    r"|((?<!\d)\d{6}_\d{6}(?!\d))"                    # 260919_220945 (내보내기 폴더 이름)
    r"|(/data/project/)"                              # 절대경로
    r"|(/home/)"
    r"|(\d{2}:\d{2}:\d{2})")                          # 22:00:00
SCRUB = "⟨지움⟩"


def scrub(o, key=""):
    """변하는 칸을 지운다(구조는 그대로 남긴다 — 칸이 사라졌는지도 보려고)."""
    if isinstance(o, dict):
        return {k: scrub(v, k) for k, v in sorted(o.items())}
    if isinstance(o, list):
        return [scrub(v, key) for v in o]
    if key.lower() in VOLATILE_KEYS:
        return SCRUB if o not in (None, "", 0, False) else o
    if key.lower() in NEVER_BY_VALUE:
        return o                       # 뜻 있는 칸 — 값 규칙을 적용하지 않는다(§3-1)
    if isinstance(o, str) and VOLATILE_VAL.search(o):
        return SCRUB
    return o


def dump(o):
    return json.dumps(o, ensure_ascii=False, indent=1, sort_keys=True)


# ───────────────────────── 고정 표본 ─────────────────────────
def read_stems():
    out = {}
    if not os.path.exists(STEMS_TXT):
        return out
    for ln in io.open(STEMS_TXT, encoding="utf-8"):
        ln = ln.strip()
        if not ln or ln.startswith("#"):
            continue
        f, s = ln.split("\t", 1)
        out.setdefault(f, []).append(s)
    return out


def make_stems():
    """고정 표본을 정한다 — 과일마다 **이름 오름차순 첫 3장**. 한 번 정하면 파일로 굳는다."""
    got = {}
    for f in L.FRUITS:
        got[f] = L.images_of(f)[:N_PER_FRUIT]
    with io.open(STEMS_TXT, "w", encoding="utf-8") as fp:
        fp.write("# 기준선 고정 표본 — 과일마다 이름 오름차순 첫 3장. 작성: 2026-09-19\n")
        fp.write("# 한 줄에 «과일<탭>사진이름». 이 파일을 바꾸면 기준선을 다시 떠야 한다.\n")
        for f in L.FRUITS:
            for s in got[f]:
                fp.write("%s\t%s\n" % (f, s))
    return got


def freeze_status(stems):
    """status.json·duplicates.json 에서 **표본 12장 몫만** 떼어 fixtures 에 얼린다."""
    os.makedirs(FROZEN, exist_ok=True)
    for f in L.FRUITS:
        src = os.path.join(L.T, "data", f, "status.json")
        st = json.load(io.open(src, encoding="utf-8")) if os.path.exists(src) else {}
        small = {s: st[s] for s in stems.get(f, []) if s in st}
        with io.open(os.path.join(FROZEN, f + ".status.json"), "w", encoding="utf-8") as fp:
            fp.write(dump(small))
        dsrc = os.path.join(L.T, "data", f, "duplicates.json")
        dup = json.load(io.open(dsrc, encoding="utf-8")) if os.path.exists(dsrc) else {}
        keep = set(stems.get(f, []))
        groups = [g for g in (dup.get("groups") or [])
                  if isinstance(g, list) and len([x for x in g if x in keep]) >= 2]
        with io.open(os.path.join(FROZEN, f + ".duplicates.json"), "w", encoding="utf-8") as fp:
            fp.write(dump({"groups": [[x for x in g if x in keep] for g in groups]}))


def apply_frozen(sb):
    for f in L.FRUITS:
        d = os.path.join(sb, "data", f)
        os.makedirs(d, exist_ok=True)
        for a, b in (("status.json", "status.json"), ("duplicates.json", "duplicates.json")):
            p = os.path.join(FROZEN, f + "." + a)
            if os.path.exists(p):
                shutil.copy2(p, os.path.join(d, b))


# ───────────────────────── ① API 응답 ─────────────────────────
def collect_api(a, stems, prefix="api"):
    got = {}

    def g(name, path):
        code, body = a.get2(path)
        got[prefix + name] = {"http": code, "body": scrub(body)}

    g("_fruits", "/api/fruits")
    g("_export_list", "/api/export_list")
    for f in L.FRUITS:
        g("_list__%s" % f, "/api/list?fruit=%s&page_size=120&page=1" % f)
        g("_export_plan__%s__confirmed" % f, "/api/export_plan?fruit=%s&confirmed_only=1" % f)
        g("_export_plan__%s__all" % f, "/api/export_plan?fruit=%s&confirmed_only=0" % f)
        for s in stems.get(f, []):
            g("_item__%s__%s" % (f, s), "/api/item?fruit=%s&stem=%s" % (f, Q(s)))
            g("_boxes__%s__%s" % (f, s), "/api/boxes?fruit=%s&stem=%s" % (f, Q(s)))
            g("_instance_info__%s__%s" % (f, s),
              "/api/instance_info?fruit=%s&stem=%s" % (f, Q(s)))
    return got


# 과일마다 «세 장에 세 종류를 하나씩» 확정한다 — 사진마다 한 종류만 두므로
# «한 종류를 확정해도 다른 종류는 그대로» 라는 규칙까지 응답에 남는다.
CONFIRM_PLAN = [("mask", "ok"), ("boxes", "fixed"), ("instances", "ok")]


def confirm_scenario(a, stems):
    """실제 `/api/status` 를 불러 **사람 확정** 상태를 만든다.

    공용 `data/status.json` 에는 2026-09-19 현재 `confirmed_*` 기록이 **한 건도 없다**(확정 기능이
    새것이라 아직 아무도 안 썼다). 그대로 두면 기준선이 «확정» 관련 길을 하나도 지나지 않는다.
    그래서 JSON 을 손으로 지어내지 않고 **서버에게 시켜서** 만든다 — 규칙은 코드가 정한다.
    """
    got = []
    for f in L.FRUITS:
        ss = stems.get(f, [])
        for (kind, status), s in zip(CONFIRM_PLAN, ss):
            code, r = a.post("/api/status", {"fruit": f, "stem": s, "status": status,
                                             "by": "기준선", "confirm": True, "kind": kind})
            got.append((f, s, kind, status, code, bool(r.get("ok", code == 200))))
    ok = len([1 for x in got if x[5]])
    print("[기준선] 확정 시나리오 %d건 중 %d건 성공(나머지는 그 과일에 없는 종류 — 그것도 응답에 담긴다)"
          % (len(got), ok), flush=True)
    return got


# ───────────────────────── ② 내보내기 ─────────────────────────
TIMEISH = re.compile(r"(at|time|date|mtime|when|job|dir|out|path|by)$", re.I)


def norm_csv(path):
    """CSV 에서 **시각·경로·사람 이름 칸을 빼고** 남은 칸만 이어 붙인다(지문을 뜨려고)."""
    rows = list(csv.reader(io.open(path, encoding="utf-8")))
    if not rows:
        return b""
    head = rows[0]
    keep = [i for i, h in enumerate(head) if not TIMEISH.search(h.strip())]
    out = io.StringIO()
    w = csv.writer(out, lineterminator="\n")
    for r in rows:
        w.writerow([r[i] if i < len(r) else "" for i in keep])
    return out.getvalue().encode("utf-8")


def seed_boxes(a, stems):
    """내보내기 ② 가 **상자 YOLO txt** 까지 덮게, 표본 12장에 **고정된 상자**를 저장한다.

    ① API 응답을 먼저 뜬 **뒤에** 부른다(판정 자료를 건드리기 때문).
    좌표는 사진 크기의 고정 비율이라 사진마다 값이 정해진다 — 돌릴 때마다 같다.
    """
    n = 0
    for f in L.FRUITS:
        for s in stems.get(f, []):
            it = a.get("/api/item?fruit=%s&stem=%s" % (f, Q(s)))
            w, h = int(it.get("width") or 0), int(it.get("height") or 0)
            if w < 20 or h < 20:
                continue
            bx = [{"xyxy": [w // 10, h // 10, w // 2, h // 2], "cls": "fruit"},
                  {"xyxy": [w // 2, h // 2, w - w // 10, h - h // 10], "cls": "bunch"}]
            code, r = a.post("/api/boxes", {"fruit": f, "stem": s, "by": "기준선", "boxes": bx})
            if code == 200:
                n += 1
    print("[기준선] 표본 %d장에 고정 상자 2개씩 저장(② 가 YOLO txt 까지 덮게)" % n, flush=True)
    return n


def export_one(a, fruit, confirmed_only=False):
    kinds = ["mask", "instances", "boxes", "counts"]
    code, r = a.post("/api/export_start",
                     {"fruit": fruit, "kinds": kinds, "confirmed_only": confirmed_only,
                      "by": "기준선"})
    if code != 200 or not r.get("ok"):
        return {"__error": "%s %s" % (code, r)}
    job = r["job"]
    for _ in range(900):
        j = a.get("/api/export_status?job=%s" % Q(job))
        if j.get("state") in ("done", "error"):
            break
        time.sleep(0.5)
    out = os.path.join(SB, "exports", job)
    got = {"__state": j.get("state"), "__n_images": j.get("n_images"),
           "__n_instances": j.get("n_instances"), "__n_boxes": j.get("n_boxes"),
           "__n_box_images": j.get("n_box_images"), "__n_counts": j.get("n_counts"),
           "__n_dropped": j.get("n_dropped")}
    for d, _, fns in os.walk(out):
        for fn in sorted(fns):
            p = os.path.join(d, fn)
            rel = os.path.relpath(p, out)
            if fn.lower().endswith(".json"):
                # json 은 **변하는 칸을 지운 뒤** 지문을 뜬다(`boxes_all.json` 의 `at`,
                # `job.json` 의 시각·폴더 이름 때문에 그냥 sha256 을 뜨면 매번 달라진다)
                try:
                    body = dump(scrub(json.load(io.open(p, encoding="utf-8"))))
                except Exception as e:                      # noqa: BLE001
                    got[rel] = "⟨json 을 못 읽었다: %s⟩" % e
                    continue
                got[rel] = L.sha256_bytes(body.encode("utf-8")) + "  (변하는 칸 지움)"
            elif fn.lower().endswith(".csv"):
                got[rel] = L.sha256_bytes(norm_csv(p)) + "  (시각·경로·이름 칸 제외)"
            else:
                got[rel] = L.sha256(p)
    return got


# ───────────────────────── ⑤ 나머지 라우트 · 쓰기 경로 ─────────────────────────
# 2026-09-19 2차 검수 실측: 라우트는 `server.py` 26 + `boxes.py` 5 + `instances.py` 6 = **37개**인데
# ① 은 GET 7개(fruits·export_list·list·export_plan·item·boxes·instance_info)만 지난다.
# 여기서 **나머지 전부**를 한 번씩 부르고, 쓰기가 디스크에 남긴 것까지 지문으로 굳힌다.
# 순서가 곧 기준선이다 — 줄을 끼워 넣지 말고 **끝에 붙인다**(그러면 기존 칸이 안 흔들린다).

def png_gray(w, h, val=0):
    """0/255 회색 PNG 한 장(PIL 없이 zlib 로 직접) — `/api/save` 의 수정본 마스크로 쓴다."""
    raw = b"".join(b"\x00" + bytes([val]) * w for _ in range(h))

    def chunk(t, d):
        c = t + d
        return len(d).to_bytes(4, "big") + c + (zlib.crc32(c) & 0xFFFFFFFF).to_bytes(4, "big")
    ihdr = w.to_bytes(4, "big") + h.to_bytes(4, "big") + bytes([8, 0, 0, 0, 0])
    png = (b"\x89PNG\r\n\x1a\n" + chunk(b"IHDR", ihdr)
           + chunk(b"IDAT", zlib.compress(raw)) + chunk(b"IEND", b""))
    return "data:image/png;base64," + base64.b64encode(png).decode()


def collect_routes(a, stems, port, sb):
    """⑤ — ① 이 안 지나는 라우트 전부 + 쓰기 뒤 디스크 상태."""
    got = {}

    def G(name, path):                              # JSON 을 돌려주는 GET
        code, body = a.get2(path)
        got["r_" + name] = {"http": code, "body": scrub(body)}

    def B(name, path):                              # 그림·HTML 처럼 바이트를 돌려주는 GET
        try:
            code, raw = a.get_bytes(path)
        except Exception as e:                                          # noqa: BLE001
            got["r_" + name] = {"http": "⟨예외⟩", "err": str(e)[:120]}
            return
        got["r_" + name] = {"http": code, "bytes": len(raw),
                            "sha256": L.sha256_bytes(raw)}

    def P(name, path, body):                        # 쓰기(POST)
        code, r = a.post(path, body)
        s = scrub(r)
        if isinstance(s, dict) and isinstance(s.get("png"), str) and len(s["png"]) > 200:
            s["png"] = "⟨png sha256 %s⟩" % L.sha256_bytes(s["png"].encode("utf-8"))[:32]
        got["w_" + name] = {"http": code, "body": s}
        return code, r

    first = {f: (stems.get(f) or [None] * 3) for f in L.FRUITS}

    # ── (1) 읽기만 하는 나머지 GET ────────────────────────────────────
    G("health", "/api/health")
    G("stats", "/api/stats")
    G("boxes_stats", "/api/boxes_stats")
    G("instance_stats", "/api/instance_stats")
    G("export_status__없는job", "/api/export_status?job=%s" % Q("없는job"))
    G("item__없는사진", "/api/item?fruit=peach&stem=%s" % Q("없는사진_260920"))
    G("boxes__없는과일", "/api/boxes?fruit=%s&stem=x" % Q("없는과일"))
    for f in L.FRUITS:
        G("instance_errors__%s" % f, "/api/instance_errors?fruit=%s" % f)
        G("duplicate_preview__%s" % f, "/api/duplicate_preview?fruit=%s" % f)
        for mode in ("mask", "boxes", "instances"):
            G("queue__%s__%s" % (f, mode),
              "/api/list?fruit=%s&sort=queue&mode=%s&confirmed=0&page_size=500" % (f, mode))
        s0 = first[f][0]
        if s0:
            G("boxes_seed__%s" % f, "/api/boxes_seed?fruit=%s&stem=%s" % (f, Q(s0)))
            B("img__%s" % f, "/img?fruit=%s&stem=%s" % (f, Q(s0)))
            B("mask__%s" % f, "/mask?fruit=%s&stem=%s" % (f, Q(s0)))
            B("thumb__%s" % f, "/thumb?fruit=%s&stem=%s&w=240" % (f, Q(s0)))
            B("instances_png__%s" % f, "/instances?fruit=%s&stem=%s" % (f, Q(s0)))
    B("page_index", "/")
    B("page_box", "/box")
    B("static_app_js", "/static/app.js")

    # ── (2) 로그인·잠금 (쿠키 없는 새 연결로) ──────────────────────────
    base = "http://127.0.0.1:%d" % port

    def raw_open(path, data=None):
        req = urllib.request.Request(base + path, data=data, method="POST" if data else "GET")
        try:
            with urllib.request.urlopen(req, timeout=60) as fp:
                return fp.status, len(fp.read())
        except urllib.error.HTTPError as e:
            return e.code, len(e.read())
        except Exception as e:                                         # noqa: BLE001
            return "⟨예외⟩", str(e)[:80]
    got["r_login_GET"] = dict(zip(("http", "bytes"), raw_open("/login")))
    got["r_login_POST_틀린비밀번호"] = dict(zip(
        ("http", "bytes"), raw_open("/login", urllib.parse.urlencode({"password": "틀림"}).encode())))
    got["r_api_로그인없이"] = dict(zip(("http", "bytes"), raw_open("/api/fruits")))
    got["r_page_로그인없이"] = dict(zip(("http", "bytes"), raw_open("/")))

    # ── (3) 쓰기 — 마스크 ─────────────────────────────────────────────
    for f in L.FRUITS:
        s1 = first[f][1]
        if not s1:
            continue
        it = a.get("/api/item?fruit=%s&stem=%s" % (f, Q(s1)))
        w, h = int(it.get("width") or 0), int(it.get("height") or 0)
        # 클릭 지점은 «초벌 상자의 첫 상자 가운데» — 사진 가운데를 찍으면 대개 배경이라
        # «그 지점은 비어 있습니다» 갈래만 지난다(실측). 열매 안쪽을 찍어야 연결성분 PNG 가 나온다.
        seed = a.get("/api/boxes_seed?fruit=%s&stem=%s" % (f, Q(s1)))
        bx = (seed.get("boxes") or [{}])[0].get("xyxy")
        cx, cy = ((bx[0] + bx[2]) // 2, (bx[1] + bx[3]) // 2) if bx else (w // 2, h // 2)
        P("component__%s" % f, "/api/component",
          {"fruit": f, "stem": s1, "source": "ai", "x": cx, "y": cy})
        P("component__밖__%s" % f, "/api/component",
          {"fruit": f, "stem": s1, "source": "ai", "x": w + 10, "y": h + 10})
        if w >= 8 and h >= 8:
            P("save_fixed__%s" % f, "/api/save",
              {"fruit": f, "stem": s1, "action": "fixed", "by": "기준선", "note": "기준선 쓰기",
               "png": png_gray(w, h, 0)})
        P("save_ok__%s" % f, "/api/save",
          {"fruit": f, "stem": s1, "action": "ok", "by": "기준선", "note": "기준선 ok"})
        P("revert__%s" % f, "/api/revert", {"fruit": f, "stem": s1, "by": "기준선"})

    # ── (4) 쓰기 — 열매 번호 (지금 번호본을 그대로 되보낸다 = 왕복) ───────
    for f in L.FRUITS:
        s2 = first[f][2]
        if not s2:
            continue
        code, raw = a.get_bytes("/instances?fruit=%s&stem=%s" % (f, Q(s2)))
        if code == 200 and raw[:4] == b"\x89PNG":
            P("save_instances__%s" % f, "/api/save_instances",
              {"fruit": f, "stem": s2, "by": "기준선",
               "png": "data:image/png;base64," + base64.b64encode(raw).decode()})
        else:
            got["w_save_instances__%s" % f] = {"http": code, "body": "⟨번호본이 없다⟩"}
        P("revert_instances__%s" % f, "/api/revert_instances",
          {"fruit": f, "stem": s2, "by": "기준선"})

    # ── (5) 쓰기 — 근접 중복 묶음 ─────────────────────────────────────
    # 얼린 판정 자료의 `duplicates.json` 은 네 과일 모두 **묶음 0개**다(실측) → 중복 관련 라우트
    # 여섯 개가 «묶음이 없다» 갈래만 지난다. 그래서 표본 12장으로 된 묶음 하나를 모래상자에만
    # 만들어 준다(공용 자료는 건드리지 않는다). 대표 = 첫 장, 나머지 = 둘째 장.
    DUP_FRUIT = "peach"
    g = [s for s in (stems.get(DUP_FRUIT) or [])][:2]
    if len(g) == 2:
        dp = os.path.join(sb, "data", DUP_FRUIT, "duplicates.json")
        with io.open(dp, "w", encoding="utf-8") as fp:
            fp.write(dump({"groups": [g]}))
        G("duplicate_preview__묶음있음", "/api/duplicate_preview?fruit=%s" % DUP_FRUIT)
        P("exclude_group", "/api/exclude_group",
          {"fruit": DUP_FRUIT, "stem": g[0], "by": "기준선"})
        P("undo_exclude_group", "/api/undo_exclude_group",
          {"fruit": DUP_FRUIT, "stem": g[0], "stems": g[1:], "by": "기준선"})
        P("apply_duplicate_exclusions", "/api/apply_duplicate_exclusions",
          {"fruit": DUP_FRUIT, "by": "기준선"})
        P("undo_duplicate_exclusions", "/api/undo_duplicate_exclusions",
          {"fruit": DUP_FRUIT, "by": "기준선"})
        P("export_excluded", "/api/export_excluded", {"fruit": DUP_FRUIT})

    # ── (6) 쓰기 — `/box` 화면의 상자 내보내기 (`export_boxes_to`) ──────
    # 🔴 이 길이 ① 에도 ② 에도 없었다. 2026-09-19 23:19 에 «개수 세기» 사이클5 가 바로 이 함수의
    # «줄 0개 json» 갈래를 고쳤는데 기준선이 아무것도 못 잡았다(2차 §1-1). 그래서
    #   (가) 그냥 한 번  (나) «상자 0개 json + 이미 있는 0바이트 txt» 를 만들어 두고 한 번
    # 두 번 부른다 — empty_txt·n_images·stale_txt 세 숫자가 그 갈래를 담는다.
    for f in L.FRUITS:
        P("boxes_export__%s" % f, "/api/boxes_export", {"fruit": f})
    EB_FRUIT = "peach"
    eb = (stems.get(EB_FRUIT) or [None])[0]
    if eb:
        it = a.get("/api/item?fruit=%s&stem=%s" % (EB_FRUIT, Q(eb)))
        bd = os.path.join(sb, "data", EB_FRUIT, "boxes")
        yd = os.path.join(sb, "data", EB_FRUIT, "boxes_yolo")
        os.makedirs(bd, exist_ok=True)
        os.makedirs(yd, exist_ok=True)
        with io.open(os.path.join(bd, "기준선_빈상자.json"), "w", encoding="utf-8") as fp:
            fp.write(dump({"stem": "기준선_빈상자", "width": it.get("width") or 100,
                           "height": it.get("height") or 100, "boxes": []}))
        io.open(os.path.join(yd, "기준선_빈상자.txt"), "w").close()      # 옛 0바이트 txt 를 흉내
        P("boxes_export__빈상자갈래", "/api/boxes_export", {"fruit": EB_FRUIT})

    # ── (7) 쓰기가 디스크에 남긴 것 ───────────────────────────────────
    for f in L.FRUITS:
        d = os.path.join(sb, "data", f)
        p = os.path.join(d, "status.json")
        if os.path.exists(p):
            got["after_status__%s" % f] = scrub(json.load(io.open(p, encoding="utf-8")))
        bd = os.path.join(d, "boxes")
        if os.path.isdir(bd):
            got["after_boxes_json__%s" % f] = {
                fn: L.sha256_bytes(dump(scrub(json.load(io.open(os.path.join(bd, fn),
                                                                encoding="utf-8")))).encode("utf-8"))
                for fn in sorted(os.listdir(bd)) if fn.endswith(".json")}
        yd = os.path.join(d, "boxes_yolo")
        if os.path.isdir(yd):
            got["after_boxes_yolo__%s" % f] = {
                fn: "%d바이트 %s" % (os.path.getsize(os.path.join(yd, fn)),
                                   L.sha256(os.path.join(yd, fn))[:16])
                for fn in sorted(os.listdir(yd))}
        ap = os.path.join(d, "boxes_all.json")
        if os.path.exists(ap):
            got["after_boxes_all__%s" % f] = scrub(json.load(io.open(ap, encoding="utf-8")))
        for sub in ("masks_fixed", "instances_fixed"):
            sd = os.path.join(d, sub)
            got["after_%s__%s" % (sub, f)] = (
                {fn: L.sha256(os.path.join(sd, fn)) for fn in sorted(os.listdir(sd))}
                if os.path.isdir(sd) else "⟨폴더 없음⟩")
        el = os.path.join(d, "excluded_list.txt")
        if os.path.exists(el):
            body = [ln for ln in io.open(el, encoding="utf-8").read().splitlines()
                    if not ln.startswith("#")]        # 머리글에 시각이 있다
            got["after_excluded_list__%s" % f] = body
    return got


# ───────────────────────── ③④ ─────────────────────────
def read_bundles():
    p = os.path.join(L.OUT_DIR, "bundles.tsv")
    if not os.path.exists(p):
        return {}
    out = {}
    for ln in io.open(p, encoding="utf-8"):
        c = ln.rstrip("\n").split("\t")
        if len(c) < 3 or c[0] == "묶음":
            continue
        # `browser/`·`baseline/` 줄은 넣지 않는다 — 브라우저 묶음은 `--browser` 일 때만 돌아서
        # 있을 때와 없을 때 ③ 이 달라져 버린다(기준선이 «옵션에 따라» 달라지면 안 된다).
        if c[0].startswith("browser/") or c[0].startswith("baseline/"):
            continue
        out[c[0]] = {"통과": c[1], "실패": c[2]}
    return out


def code_sha():
    got = {}
    for root, want in ((os.path.join(L.T, "app", "static"), None),
                       (os.path.join(L.T, "app"), (".py", ".sh")),
                       (os.path.join(L.T, "export"), (".py",))):
        for d, _, fns in os.walk(root):
            if "__pycache__" in d or "/cache" in d or "/logs" in d:
                continue
            if want is None and d != root and not d.endswith("help"):
                continue
            for fn in sorted(fns):
                if fn.startswith("_backup_"):
                    continue
                if want and not fn.endswith(want):
                    continue
                p = os.path.join(d, fn)
                if want is None and d != root and not os.path.basename(d) == "help":
                    continue
                got[os.path.relpath(p, L.T)] = L.sha256(p)
    return got


# ───────────────────────── 뜨기 · 대조 ─────────────────────────
def take():
    """지금 코드로 ①②④ 를 재 본다(③ 은 run_all.sh 가 남긴 것을 읽는다)."""
    stems = read_stems() or make_stems()
    if not os.path.isdir(FROZEN):
        freeze_status(stems)
    L.sample_dataset(stems, SAMPLE)
    if os.path.isdir(SB):
        shutil.rmtree(SB)
    L.sync(SB)
    apply_frozen(SB)
    L.clear_exports(SB)
    port = L.free_port(5601)
    routes = {}
    p = L.start(port=port, sb=SB, data_root=SAMPLE)
    try:
        a = L.Api(base="http://127.0.0.1:%d" % port)
        api = collect_api(a, stems, "api")     # ① 판정 자료를 건드리기 «전» (확정 0건 상태)
        seed_boxes(a, stems)
        confirm_scenario(a, stems)
        api.update(collect_api(a, stems, "api2"))   # ①b 상자 저장 + 사람 확정을 한 «뒤»
        exp = {f: export_one(a, f) for f in L.FRUITS}
        # 「사람 확정만」 갈래도 한 과일은 실제로 내보내 본다(①b 에서 확정을 만들었으므로 나온다)
        exp["apple__confirmed_only"] = export_one(a, "apple", confirmed_only=True)
        # ⑤ 나머지 라우트·쓰기 — ①② 를 **다 뜬 뒤에** 부른다. 그래야 ①② 칸이 한 칸도 안 흔들린다.
        routes = collect_routes(a, stems, port, SB)
        # 쓰기가 끝난 뒤 한 번 더 내보낸다 — 「상자 0개 json」 갈래가 job 내보내기에도 있는지 본다
        exp["peach__after_writes"] = export_one(a, "peach")
    finally:
        L.stop(p)
    return {"stems": stems, "api": api, "exports": exp, "routes": routes,
            "bundles": read_bundles(), "code": code_sha()}


PREV_DIR = os.path.join(FIX, "_baseline_prev")


def keep_prev():
    """옛 기준선을 **지우지 않고** `fixtures/_baseline_prev/<날짜시각>/` 로 치운다.

    2026-09-19 2차 검수 §4-2: 이 폴더는 git 밖에 있어서, 전에는 `--rebaseline` 한 번이
    옛 판을 **되돌릴 수 없게** 덮어썼다. 「전과 무엇이 달라졌나」 를 볼 수 있어야 한다.
    최근 **10판**만 남기고 더 오래된 것은 지운다(그건 이미 두 판 뒤의 것이다).
    """
    if not os.path.isdir(BASE_DIR):
        return None
    os.makedirs(PREV_DIR, exist_ok=True)
    tag = time.strftime("%y%m%d_%H%M%S")
    dst = os.path.join(PREV_DIR, tag)
    if os.path.exists(dst):
        shutil.rmtree(dst)
    shutil.move(BASE_DIR, dst)
    olds = sorted(d for d in os.listdir(PREV_DIR) if os.path.isdir(os.path.join(PREV_DIR, d)))
    for d in olds[:-10]:
        shutil.rmtree(os.path.join(PREV_DIR, d))
    print("[기준선] 옛 판을 남겨 두었습니다 → %s" % dst, flush=True)
    return dst


def write(snap):
    prev = keep_prev()
    if os.path.isdir(BASE_DIR):
        shutil.rmtree(BASE_DIR)
    os.makedirs(os.path.join(BASE_DIR, "api"))
    lines = []
    for name in sorted(snap["api"]):
        body = dump(snap["api"][name])
        with io.open(os.path.join(BASE_DIR, "api", name + ".json"), "w", encoding="utf-8") as f:
            f.write(body + "\n")
        lines.append("%s  api/%s.json" % (L.sha256_bytes(body.encode("utf-8")), name))
    with io.open(os.path.join(BASE_DIR, "api_sha256.txt"), "w", encoding="utf-8") as f:
        f.write("# 고정 표본 API 응답 지문 — 변하는 칸을 지운 뒤(⟨지움⟩) 뜬 것. 작성: 2026-09-19\n")
        f.write("\n".join(lines) + "\n")
    for name, obj in (("exports.json", snap["exports"]), ("bundles.json", snap["bundles"]),
                      ("code_sha256.json", snap["code"]), ("stems.json", snap["stems"]),
                      ("routes.json", snap.get("routes") or {})):
        with io.open(os.path.join(BASE_DIR, name), "w", encoding="utf-8") as f:
            f.write(dump(obj) + "\n")
    n_api = len(snap["api"])
    n_exp = sum(len(v) for v in snap["exports"].values())
    n_rt = len(snap.get("routes") or {})
    with io.open(os.path.join(BASE_DIR, "README.md"), "w", encoding="utf-8") as f:
        f.write("""# 기준선 baseline_260920

작성: 2026-09-19

`tests/run_all.sh --rebaseline` 이 만든 폴더입니다. **리팩터 전 코드**(카운팅 사이클 4 판 ·
실서버 PID 964494 와 같은 판)의 «동작» 을 숫자로 굳혀 둔 것입니다.

| 파일 | 무엇 | 개수 |
|---|---|---:|
| `api/*.json` + `api_sha256.txt` | 고정 표본 API 응답(변하는 칸 지움) | %d |
| `exports.json` | 내보내기 산출 파일 sha256 | %d |
| `bundles.json` | 회귀 묶음별 통과/실패 | %d |
| `code_sha256.json` | 정적 파일·서버 코드 sha256(**참고용**) | %d |
| `stems.json` | 고정 표본 12장 | 12 |
| `routes.json` | ⑤ 나머지 라우트·쓰기 경로·쓰기 뒤 디스크 | %d |

- 고정 표본 목록: `tests/fixtures/stems.txt`
- 얼려 둔 판정 자료: `tests/fixtures/status_260920/` (표본 12장 몫만)
- 대조: `bash tests/run_all.sh --check-baseline`
- `api/*.json` 안의 `⟨지움⟩` 은 «시각·PID·경로·사람 이름처럼 돌릴 때마다 달라지는 칸» 입니다.
  구조(어느 칸이 있었는지)는 남겨 두었으므로 **칸이 사라지면 잡힙니다.**
- `code_sha256.json` 이 달라지는 것은 **정상**입니다(리팩터가 하는 일). 실패로 세지 않습니다.
- 옛 기준선은 지우지 않고 `tests/fixtures/_baseline_prev/<날짜시각>/` 에 최근 10판 남깁니다.
  «전과 무엇이 달라졌나» 는 `diff -r` 로 봅니다(이 폴더는 git 밖입니다).
""" % (n_api, n_exp, len(snap["bundles"]), len(snap["code"]), n_rt))
    return n_api, n_exp, n_rt


def load():
    if not os.path.isdir(BASE_DIR):
        return None
    got = {"api": {}}
    d = os.path.join(BASE_DIR, "api")
    for fn in sorted(os.listdir(d)):
        if fn.endswith(".json"):
            got["api"][fn[:-5]] = json.load(io.open(os.path.join(d, fn), encoding="utf-8"))
    for name, key in (("exports.json", "exports"), ("bundles.json", "bundles"),
                      ("code_sha256.json", "code"), ("stems.json", "stems"),
                      ("routes.json", "routes")):
        p = os.path.join(BASE_DIR, name)
        got[key] = json.load(io.open(p, encoding="utf-8")) if os.path.exists(p) else {}
    return got


def flat(o, prefix=""):
    """중첩 사전을 «경로 → 값» 으로 펼친다(다른 칸만 표로 뽑으려고)."""
    if isinstance(o, dict):
        out = {}
        for k, v in o.items():
            out.update(flat(v, prefix + "/" + str(k) if prefix else str(k)))
        return out
    if isinstance(o, list):
        out = {}
        for i, v in enumerate(o):
            out.update(flat(v, "%s[%d]" % (prefix, i)))
        return out
    return {prefix: o}


def diff_table(title, old, new, hard=True):
    a, b = flat(old), flat(new)
    keys = sorted(set(a) | set(b))
    rows = [(k, a.get(k, "⟨없던 칸⟩"), b.get(k, "⟨사라진 칸⟩")) for k in keys
            if a.get(k, "⟨없던 칸⟩") != b.get(k, "⟨사라진 칸⟩")]
    print("\n── %s : 다른 칸 %d개 %s" % (title, len(rows), "" if hard else "(참고용 · 실패로 세지 않음)"),
          flush=True)
    if rows:
        w = min(90, max(len(r[0]) for r in rows))
        print("  %-*s | %-30s | %-30s" % (w, "칸", "기준선", "지금"))
        print("  " + "-" * (w + 68))
        for k, x, y in rows[:200]:
            print("  %-*s | %-30s | %-30s" % (w, k[:w], str(x)[:30], str(y)[:30]))
        if len(rows) > 200:
            print("  … 나머지 %d개 생략" % (len(rows) - 200))
    return len(rows) if hard else 0


# `merged` 묶음은 **공용 팀 자료**(`data/*/status.json`)를 읽는다 — 팀원이 판정을 바꾸면 통과 수가
# 따라 움직인다(2026-09-19 22:55 실측: 누가 복숭아를 확정해서 `test_fixes_m2.py F7-c` 의
# «복숭아 상자 977줄» 이 975줄이 됐다). 그래서 통과 수는 그 묶음만 **경고**로 본다.
# 반대로 **실패 수는 어느 묶음이든 늘면 실패**이고, 통과 수가 **줄면**(시험이 사라졌다) 실패다.
NOT_HERMETIC = ("merged/",)


def diff_bundles(old, new):
    rows = []
    hard = 0
    for k in sorted(set(old) | set(new)):
        a, b = old.get(k, {}), new.get(k, {})
        for cell in ("통과", "실패"):
            x, y = a.get(cell, "⟨없던 묶음⟩"), b.get(cell, "⟨사라진 묶음⟩")
            if x == y:
                continue
            soft = False
            if x == "⟨없던 묶음⟩":
                # 🔴 2026-09-20 구조 사이클 2: 시험 **묶음이 새로 늘어난** 것은 경고다.
                #   («시험이 늘었다 → 경고» 라는 아래 규칙과 같은 뜻인데, 칸이 아니라 묶음째
                #    늘어난 경우가 빠져 있어서 u6·t3·t4 를 더하면 ③ 이 거짓 실패였다.)
                soft = True
            elif y in ("⟨사라진 묶음⟩", "⟨없던 묶음⟩"):
                # 🔴 2026-09-19 2차 검수 §4-1: ③ 은 `_out/bundles.tsv` — 즉 **이번 실행에서 실제로
                # 돌린 묶음** 만 들어 있다. `--only=` 나 `--no-merged` 로 돌리거나 `snapshot.py --check`
                # 를 혼자 부르면 안 돌린 묶음이 «사라진 묶음» 으로 보여 **거짓 실패**가 났다
                # (실측: 23:28 `--check` 단독 실행이 «merged 사라짐» 으로 rc=1). 안 돌린 것은 경고다.
                # 시험이 정말 사라졌으면 **돌린 묶음의 통과 수가 줄어드는 것**으로 잡힌다.
                soft = True
            elif cell == "통과" and k.startswith(NOT_HERMETIC):
                soft = True                      # 공용 자료를 읽는 묶음의 통과 수
            elif cell == "통과":
                try:
                    soft = int(y) > int(x)       # 시험이 늘었다 → 경고
                except Exception:
                    soft = False
            elif cell == "실패":
                # 🔴 2026-09-20 구조 사이클 2: 실패 수가 **줄어든** 것은 경고다(고친 것이다).
                #   README §4 ③ 은 «실패 수가 **늘거나** 통과 수가 **줄면** 실패» 라고 적어 두었는데
                #   코드는 «달라지면 실패» 였다. 그래서 `F7-c` 를 고쳐 merged 가 535/1 → 536/0 이 되자
                #   ③ 이 «실패 1개» 로 나왔다(좋아진 것을 실패라고 말한 셈).
                try:
                    soft = int(y) < int(x)
                except Exception:
                    soft = False
            rows.append((k + "/" + cell, x, y, soft))
            if not soft:
                hard += 1
    print("\n── ③ 회귀 묶음 통과/실패 : 다른 칸 %d개 (그중 실패로 세는 것 %d개)"
          % (len(rows), hard), flush=True)
    if rows:
        w = min(60, max(len(r[0]) for r in rows))
        print("  %-*s | %-14s | %-14s | %s" % (w, "칸", "기준선", "지금", "판정"))
        print("  " + "-" * (w + 48))
        for k, x, y, soft in rows:
            print("  %-*s | %-14s | %-14s | %s" % (w, k[:w], x, y, "경고" if soft else "실패"))
    return hard


def check():
    base = load()
    if base is None:
        print("기준선이 없습니다 — 먼저 `bash tests/run_all.sh --rebaseline` 을 돌리세요.")
        return 1
    now = take()
    bad = 0
    bad += diff_table("① API 응답(고정 표본)", base["api"], now["api"])
    bad += diff_table("② 내보내기 산출 지문", base["exports"], now["exports"])
    bad += diff_table("⑤ 나머지 라우트·쓰기 경로", base.get("routes") or {},
                      now.get("routes") or {})
    nb = now.get("bundles") or {}
    if nb:
        bad += diff_bundles(base["bundles"], nb)
    else:
        print("\n── ③ 회귀 묶음 : 이번에는 안 돌렸습니다(`run_all.sh` 없이 부르면 비어 있습니다)")
    diff_table("④ 정적 파일·서버 코드 sha256", base["code"], now["code"], hard=False)
    print("\n[기준선 대조] 합격 기준(①②③⑤) 다른 칸 **%d개**" % bad, flush=True)
    return 1 if bad else 0


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--rebaseline", action="store_true", help="기준선을 새로 뜬다(덮어쓴다)")
    ap.add_argument("--check", action="store_true", help="지금 코드와 대조한다")
    ap.add_argument("--refreeze-status", action="store_true",
                    help="fixtures/status_260920 을 지금 status.json 으로 다시 얼린다")
    ap.add_argument("--restems", action="store_true", help="고정 표본 12장을 다시 고른다")
    g = ap.parse_args()
    if g.restems:
        stems = make_stems()
        freeze_status(stems)
        print("고정 표본을 다시 골랐습니다: %s" % STEMS_TXT)
    elif g.refreeze_status:
        freeze_status(read_stems() or make_stems())
        print("판정 자료를 다시 얼렸습니다: %s" % FROZEN)
    if g.check:
        return check()
    if g.rebaseline or not (g.restems or g.refreeze_status):
        snap = take()
        n_api, n_exp, n_rt = write(snap)
        print("\n[기준선] 새로 떴습니다 → %s" % BASE_DIR)
        print("  ① API 응답 %d개 · ② 내보내기 지문 %d개 · ③ 묶음 %d개 · ④ 코드 지문 %d개"
              " · ⑤ 라우트·쓰기 %d개"
              % (n_api, n_exp, len(snap["bundles"]), len(snap["code"]), n_rt))
        print("  합격 기준(①②③⑤) 항목 수 = %d" % (n_api + n_exp + len(snap["bundles"]) + n_rt))
    return 0


if __name__ == "__main__":
    sys.exit(main())
