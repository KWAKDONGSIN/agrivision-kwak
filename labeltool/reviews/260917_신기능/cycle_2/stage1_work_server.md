작성: 2026-09-17

# 0917 새 기능 5회 검수 — 사이클 2 · 1차 작업(다) 갈래: 서버 쪽 중복 정리 (Opus 5)

담당 파일 **둘만**: `app/instances.py`, `export/export_dataset.py`
백업: `app/_backup_260917_c2c_instances.py`, `export/_backup_260917_c2c_export_dataset.py` (고치기 전 원본, md5 일치 확인)
근거 표기: 📄 실측(명령·경로 명시) · ❌ AI 판단

---

## ① 합격 기준 (먼저 적고 그다음 실행했습니다)

| # | 합격 기준 | 결과 |
|---|---|---|
| A1 | `instances.py` 의 `source_of`·`_read_u16`·`_png_u16_bytes`·`SEED_DIRS` 와 `export_dataset.py` 의 `instance_source`·`copy_instances`·`SEED_DIRS` 가 **한 군데**로 합쳐진다. 새 파일은 만들지 않는다 | ✅ |
| A2 | `python3 -c "import ast; ast.parse(...)"` 두 파일 통과 · `python3 app/boxes.py` 자체 점검 통과 | ✅ |
| A3 | `/api/instance_info` — 사과=`gt` · 블루베리=`seed` · 복숭아=없음(`has:false`) | ✅ |
| A4 | `/instances` 가 uint16(`mode I;16`)을 그대로 준다 (0/255 로 바뀌지 않는다) | ✅ |
| A5 | `/api/instance_errors?fruit=apple` = 38행 32장 | ✅ |
| A6 | `export_dataset.py --fruit apple --instances --dry-run` 이 3장으로 나오고, 사과 3장 실제 내보내기가 **원본과 화소 단위로 일치**(열매 95·102·99 = 296) | ✅ |
| A7 | 복숭아 `--instances` 는 0장 (`instances/` 폴더가 아예 생기지 않음) | ✅ |
| A8 | **합치기 전/후 산출물이 바이트 단위로 같다** (내보낸 마스크·번호마스크·manifest.csv, `/instances` 응답 PNG, errors json) | ✅ |
| A9 | 옛 코드와 새 코드가 «있을 수 있는 모든 조합»에서 같은 답을 준다 | ⚠️ 48조합 중 **1곳만 다름**(의도한 것, ③-3) |
| A10 | 원본 데이터셋·`work/park_seongmoon/` 을 건드리지 않는다 · 파일 삭제 없음 · GPU 없음 · 새 패키지 없음 | ✅ |

## ② 한 줄 결론

두 벌이던 번호 마스크 규칙을 `app/instances.py` 한 군데로 합쳐 **-23줄**(중복 로직 40줄 삭제)이 됐고, 내보낸 파일과 서버 응답이 **합치기 전과 바이트 단위로 같습니다**. 다른 곳은 단 한 군데 — 「사람이 고친 번호가 있는데 원본이 0/255 이진」인 사진에 `layer=gt` 를 물으면 옛 코드는 그 이진 마스크를 번호인 척 200 으로 줬고 새 코드는 404 를 줍니다(❌ 고쳐진 것이 맞다고 판단, 지금 데이터로는 도달 불가).

## ③ 합친 내용과 줄 수 변화

### ③-1 어디로 합쳤나 — 새 파일 없음

`export/` 가 이미 `app/` 을 `sys.path` 에 넣어 `maskio`·`dupes` 를 가져다 쓰고 있었으므로(파일 맨 위) **같은 방식으로 `instances` 를 하나 더 가져다 쓰는 것**이 가장 짧았습니다. 새 모듈은 만들지 않았습니다(ponytail: 파일 수 최소).

```python
# export/export_dataset.py:L30
from instances import source_of, read_u16, write_u16_atomic, ids_of  # noqa: E402
```

`app/instances.py` 에서 `register()` **밖(모듈 최상위)** 으로 올린 것 — 이제 서버와 내보내기가 같은 함수를 씁니다:

| 함수 | 하는 일 | 쓰는 곳 |
|---|---|---|
| `read_u16(path)` | 번호 마스크를 uint32 2차원으로(RGB 저장본은 첫 채널) | 서버 3곳 · export 1곳 |
| `png_u16_bytes(arr)` | uint16 `I;16` PNG 바이트 | 서버 `/instances` |
| `write_u16_atomic(path, arr)` | 임시파일 → `os.replace` 원자적 저장 | 서버 저장 · export 복사 |
| `ids_of(arr)` | 0 을 뺀 번호 목록 (`.size` 가 열매 수) | 서버 2곳 · export 1곳 |
| `inst_fixed_path` · `seed_path` | 경로 | `source_of` |
| `source_of(fruit, stem, allow_fixed=True)` | **어디서 읽을지 한 군데 규칙** — 고친 것 > 초벌 > 원본번호 | 서버 3곳 · export 1곳 |

`gt_path`·`DATA_DIR` 을 인자로 받지 않고 `dupes` 를 그대로 믿습니다 — 📄 `server.py:L305` 의 `gt_path()` 가 `os.path.join(DUP.dataset_for(fruit), fruit, "masks", stem+".png")` 이고 `server.py:L34 DATA_DIR` 이 `dupes.py:L13 DATA_DIR` 과 같은 값(둘 다 `ROOT/data`)이라 **인자 두 개가 통째로 없어집니다**. 그 전제를 코드에 `ponytail:` 주석으로 남겼습니다(⑤-1).

### ③-2 지운 중복 · 줄 수

| 파일 | 전 | 후 | 차 |
|---|---|---|---|
| `app/instances.py` | 209 | 225 | **+16** (공용 함수가 이 파일로 들어옴) |
| `export/export_dataset.py` | 196 | 157 | **-39** |
| 합계 | 405 | 382 | **-23줄** |

`net: -23 lines.` 줄 수보다 중요한 것: **같은 규칙을 두 번 쓴 곳이 2벌 → 1벌**(40줄 삭제). 지운 것:

- `export_dataset.py` `instance_source()` 26줄 · `copy_instances()` 12줄 · `PARK`/`SEED_DIRS` 2줄 → **전부 삭제**, `instances.py` 것을 씀. 특히 «0/255 이진은 번호 마스크가 아니다» 판정과 «uint16 로 쓰기» 가 두 벌이던 것이 한 벌이 됐습니다(경로 상수도 한 군데 — 한쪽만 바뀌어 조용히 갈릴 위험 제거).
- `instances.py serve_instances` — `layer=="gt"` 가 `source_of` 를 부른 뒤 결과를 되집던 7줄 → `allow_fixed=(layer != "gt")` **3줄**(사이클1 ⑤ 지적 그대로).
- `instances.py api_save_instances` — `makedirs`+`tmp`+`write`+`replace` 5줄 → `write_u16_atomic(p, arr)` **1줄**.
- `np.unique(arr)` + `arr[arr>0]` 2줄짜리가 세 군데 → `ids_of(...)` 한 줄씩.
- `register()` 의 `data_dir = ctx["DATA_DIR"]` — 쓰는 곳이 없어져 삭제.
- (추가 ponytail) `export_one()` 의 `root = DUP.dataset_for(fruit) if hasattr(DUP, "dataset_for") else DATASET` — 📄 `dupes.py:L22` 에 그 함수가 항상 있으므로 **죽은 분기**. `root = DUP.dataset_for(fruit)` 로.

manifest.csv 의 `instances_source` 칸 이름은 검출 팀이 읽는 표라 **예전 이름을 그대로** 둬야 해서 표시 이름만 1줄로 옮겼습니다: `INST_LABEL = {"fixed": "instances_fixed", "seed": "detect_seed", "gt": "원본번호"}`.

### ③-3 딱 한 군데 달라진 것 (의도함)

📄 `parity_instances.py` 가 찾은 유일한 차이 — 조합 `고친 것 있음 + 초벌 없음 + 원본이 0/255 이진` 에 `layer=gt`:

| | 옛 코드 | 새 코드 |
|---|---|---|
| `/instances?...&layer=gt` | `200`, `X-Instance-Source: gt` (0/255 이진 마스크를 **번호 마스크인 척** 줌) | `404` 「이 사진에는 열매 번호 마스크가 없습니다」 |

❌ 새 쪽이 맞다고 판단합니다. 옛 분기는 `source_of` 가 이미 갖고 있는 «0/255 는 번호가 아니다» 검사를 건너뛰어, 화면이 255 를 «열매 255번» 으로 그리게 되는 자리였습니다. 📄 **지금 데이터로는 도달할 수 없습니다** — `data/<과일>/instances_fixed/` 가 네 과일 모두 0개(`ls | wc -l`), 사과는 원본이 번호 마스크이고 블루베리는 초벌이 있어 초벌이 먼저 이깁니다. 복숭아·포도에서 누가 번호를 저장한 뒤에야 닿습니다. 코드에 `ponytail:` 주석으로 적어 뒀습니다(`instances.py serve_instances`).

## ④ 실행 증거 (전부 실제로 돌린 것)

서버: `127.0.0.1:5111`, 원본 폴더 `datasets_reviewed_260916`(재시작해도 `run.sh` 가 이어받음), 재시작 `bash app/run.sh restart` → PID 2883365 → **2888468**.
증거 파일: `cycles/260917_신기능/cycle_2/stage1_server/` (헤더·PNG·errors json·대조 스크립트)

### ④-1 문법·자체 점검
```
python3 -c "import ast; ast.parse(...)"  app/instances.py, export/export_dataset.py  → ast.parse OK
/…/kwak/bin/python -m py_compile 두 파일                                            → py_compile OK
python3 app/boxes.py                                                                 → boxes.py 자체 점검 통과
```

### ④-2 옛 코드 ↔ 새 코드 전수 대조 (살아 있는 서버·실데이터를 안 건드리는 방법)
`stage1_server/parity_instances.py` — 백업본(옛 `instances.py`)과 새 `instances.py` 를 각각 Flask `test_client` 로 띄워 임시폴더에서 대조. **고친것 있음/없음 × 초벌 있음/없음 × 원본 없음/이진/번호 = 12조합**, 각 조합에 `layer=auto·gt·fixed` 와 `/api/instance_info` 까지:
```
조합 12개 × (auto·gt·fixed + info) → 다른 곳 1
  f1_s0_bin  gt   옛 (200,'gt',ad7a4799b2be)   새 (404,None,'-')   ← 다름 (③-3, 의도함)
  나머지 47곳 + info 12곳 전부 상태·X-Instance-Source·응답 바이트(sha256) 동일
```

### ④-3 살아 있는 서버 (재시작 뒤) — 합치기 전 응답과 대조
```
/api/instance_info?fruit=apple&stem=20150919_174151_image1
  → {"has":true,"source":"gt","n":95,"max_id":95,"has_fixed":false,"editable":true}   (전과 동일)
/api/instance_info?fruit=blueberry&stem=Camera 1 Video (1)_1
  → {"has":true,"source":"seed","n":55,...}                                            (전과 동일)
/api/instance_info?fruit=peach&stem=210629-t1-01
  → {"has":false,"n":0,"source":null}                                                  (전과 동일)
/instances?fruit=apple&...        → 200  X-Instance-Source: gt    Content-Type: image/png
/instances?fruit=blueberry&...    → 200  X-Instance-Source: seed
/instances?fruit=peach&...        → 404
/instances?...&layer=gt (사과)    → 200        /instances?...&layer=fixed (사과) → 404 (고친 것 없음)
/api/instance_errors?fruit=apple  → ok true, n(행) 38, n_stems(장) 32                  ← 합격기준 A5
```
받은 PNG 를 PIL 로 열어본 것 — **uint16 그대로**:
```
apple : mode I;16  dtype uint16  max 95  | sha256 전 708816e55e3a8143 후 708816e55e3a8143  같음
bb    : mode I;16  dtype uint16  max 55  | sha256 전 cf7e07754cb1eec0 후 cf7e07754cb1eec0  같음
errors json  : cmp → 바이트 동일
```

### ④-4 내보내기 — 합치기 전/후 바이트 동일 + 원본과 화소 단위 일치
사과 1,001장을 다 내보내면 무거워서, 원본을 **심볼릭 링크만** 걸어 3장짜리 임시 원본 폴더를 만들고(`LABELTOOL_DATA_ROOT`, 원본은 읽기만) 첫 3장을 썼습니다. 📄 그 3장의 열매 수가 **95·102·99** 로 «이전 실측» 과 같아 같은 시험임을 확인했습니다.
```
--fruit apple --instances --dry-run  → [apple] 전체 3장 → 포함 3 · 열매 번호 마스크 3장 내보낼 예정
--fruit apple --instances --out …    → 열매 번호 마스크 3장 (열매 296개)      # 296 = 95+102+99

합치기 전(out_before) ↔ 후(out_after) 전체 파일 sha256:  파일 10개 / 10개, 다른 파일 0개
  images 3장 · masks 3장 · instances 3장 · manifest.csv 전부 같음

내보낸 번호 마스크 vs 원본 마스크(datasets_resized_2mp/apple/masks) 화소 전체 비교:
  20150919_174151_image1.png    mode=I;16  화소전체일치=True  열매=95
  20150919_174151_image101.png  mode=I;16  화소전체일치=True  열매=102
  20150919_174151_image106.png  mode=I;16  화소전체일치=True  열매=99
  → 열매 합계 296, 전부 일치=True
```
복숭아(번호 없음)·블루베리(초벌):
```
--fruit peach --instances --dry-run → 열매 번호 마스크 0장 내보낼 예정
--fruit peach --instances --out …   → 열매 번호 마스크 0장 (열매 0개) · instances/ 폴더 없음(=0장)
                                      manifest 의 instances_source 칸 전부 빈칸           ← 합격기준 A7
--fruit blueberry --instances --dry-run → 열매 번호 마스크 1195장 내보낼 예정 (초벌 1195개와 일치)
```

### ④-5 시험한 것 / 안 한 것 (사이클1 ⑥-5 의무)

| 시험한 것 | 방법 |
|---|---|
| `/instances` auto·gt·fixed 세 갈래, 12조합 전수 | ④-2 `test_client` 대조 |
| `/api/instance_info` 사과·블루베리·복숭아 | ④-2 전수 + ④-3 살아 있는 서버 |
| `/api/instance_errors` | ④-3 (38행 32장, json 바이트 동일) |
| `--instances` 내보내기 (사과 실제·복숭아 실제·블루베리 dry-run) | ④-4, 전/후 바이트 동일 + 원본과 화소 일치 |
| `write_u16_atomic` 이 쓴 uint16 PNG | ④-4 (내보낸 3장이 옛 `copy_instances` 결과와 바이트 동일) |

| **안 한 것** | 왜 · 무엇으로 갈음했나 |
|---|---|
| `POST /api/save_instances` · `POST /api/revert_instances` 를 살아 있는 서버에 실제로 쏘기 | 공용 `data/<과일>/` (instances_fixed·masks_fixed·status.json)을 건드리게 되고 지금 다른 작업자가 번호 편집 화면을 만드는 중이라 피했습니다. 이 경로에서 바뀐 것은 저장 5줄 → `write_u16_atomic(p, arr)` 1줄뿐이고, 그 함수가 쓴 결과는 ④-4 에서 옛 코드와 **바이트 동일**함을 확인했습니다. ❌ 그래도 «POST 를 실제로 눌러 본» 증거는 아닙니다 — 2차가 확인해 주십시오(⑥-4). |
| 블루베리 `--instances` 실제 내보내기(1195장) | dry-run 장수만 확인. 실제 쓰기는 용량·시간이 큽니다. |
| 브라우저 화면 | 내 담당 파일이 아닙니다(`app.js`·`index.html` 은 다른 작업자). |
| 포도 | 원본에 번호가 없어 복숭아와 같은 갈래입니다. |

## ⑤ 가정한 것

1. **`server.py` 의 `DATA_DIR`·`gt_path` 가 `dupes` 것과 같다** — 📄 지금 코드로 확인(`server.py:L34, L305` ↔ `dupes.py:L13, L22`). 서버가 나중에 다른 `data` 폴더를 가리키게 되면 `instances.py` 의 `inst_fixed_path`·`source_of` 가 조용히 갈립니다. 그 자리에 `ponytail:` 주석으로 «그때는 ctx 를 받아야 한다» 를 적어 뒀습니다.
2. **`export_dataset.py` 가 이제 flask 를 간접으로 필요로 합니다**(`instances.py` 가 `from flask import ...` 를 하므로). 📄 `kwak` 환경(flask 3.1.3)과 `python3`(anaconda base) 둘 다 있어서 지금은 문제 없습니다. ❌ flask 없는 파이썬으로 내보내기를 돌리면 `ImportError` 가 납니다 — 완전히 떼려면 `read_u16`/`png_u16_bytes` 류를 flask 를 안 쓰는 `app/maskio.py` 로 옮기는 편이 낫지만, `maskio.py` 는 이번 갈래에서 **쓰면 안 되는 파일**이라 손대지 않았습니다(사이클 5 정리 후보).
3. manifest.csv 의 칸 이름(`instances_fixed`·`detect_seed`·`원본번호`)은 검출 팀이 읽으므로 바꾸면 안 된다고 보고 `INST_LABEL` 로 **그대로 유지**했습니다.
4. 사과 3장 시험이 «이전 실측» 과 같은 3장이라는 근거는 열매 수 95·102·99 가 일치한다는 것뿐입니다(이전 보고서에 stem 이름이 없었습니다).
5. `dry-run` 이 열매 «개수» 를 세지 않는 것은 전부터 의도된 것이라 그대로 뒀습니다(파일을 읽지 않으므로. `export_dataset.py` 의 기존 `ponytail:` 주석).

## ⑥ 2차 검수가 재현할 절차

```bash
cd /data/project/2026summer/platform/work/kwak_dongsin/260916_라벨링툴
PY=/home/kds0206/.conda/envs/kwak/bin/python
S=$(mktemp -d)           # 시험 산출물은 여기만 (공용 폴더에 쓰지 않습니다)

# 1) 문법·자체 점검
python3 -c "import ast,io; [ast.parse(io.open(p,encoding='utf-8').read(),p) for p in ('app/instances.py','export/export_dataset.py')]; print('OK')"
python3 app/boxes.py

# 2) 옛 코드 ↔ 새 코드 전수 대조 (서버·실데이터 안 건드림). 「다른 곳 1」 이 정답 — ③-3 그 한 줄
$PY cycles/260917_신기능/cycle_2/stage1_server/parity_instances.py

# 3) 사과 3장: 원본에 링크만 걸어 임시 원본 폴더 → 내보내기 → 원본과 화소 비교
D=/data/project/2026summer/kds0206/datasets_resized_2mp
mkdir -p $S/mini/apple/images $S/mini/apple/masks
for s in 20150919_174151_image1 20150919_174151_image101 20150919_174151_image106; do
  ln -sf $D/apple/images/$s.png $S/mini/apple/images/$s.png
  ln -sf $D/apple/masks/$s.png  $S/mini/apple/masks/$s.png; done
LABELTOOL_DATA_ROOT=$S/mini $PY export/export_dataset.py --fruit apple --instances --dry-run   # 3장
LABELTOOL_DATA_ROOT=$S/mini $PY export/export_dataset.py --fruit apple --instances --out $S/out
# → 「열매 번호 마스크 3장 (열매 296개)」 · instances/*.png 가 원본 masks/*.png 와 화소 전체 일치(mode I;16)
$PY export/export_dataset.py --fruit peach --instances --dry-run                               # 0장

# 3-1) 백업본으로 되돌려 같은 내보내기를 한 뒤 sha256 을 비교하면 «전/후 바이트 동일» 을 직접 확인할 수 있습니다
#      (백업: app/_backup_260917_c2c_instances.py · export/_backup_260917_c2c_export_dataset.py)

보안 관련 값·설정 세부는 공개본에서 생략했습니다.
bash app/run.sh restart
보안 관련 값·설정 세부는 공개본에서 생략했습니다.
보안 관련 값·설정 세부는 공개본에서 생략했습니다.
curl -s -b $S/ck "http://127.0.0.1:5111/api/instance_info?fruit=apple&stem=20150919_174151_image1"      # source gt, n 95
curl -s -b $S/ck -G --data-urlencode "fruit=blueberry" --data-urlencode "stem=Camera 1 Video (1)_1" \
     http://127.0.0.1:5111/api/instance_info                                                            # source seed
curl -s -b $S/ck -G --data-urlencode "fruit=peach" --data-urlencode "stem=210629-t1-01" \
     http://127.0.0.1:5111/api/instance_info                                                            # has false
curl -s -b $S/ck -D- -o $S/a.png "http://127.0.0.1:5111/instances?fruit=apple&stem=20150919_174151_image1" | grep -i x-instance
$PY -c "from PIL import Image; im=Image.open('$S/a.png'); print(im.mode)"                               # I;16
curl -s -b $S/ck "http://127.0.0.1:5111/api/instance_errors?fruit=apple" | $PY -c "import json,sys; d=json.load(sys.stdin); print(d['n'], d['n_stems'])"   # 38 32
```

**4) 2차가 추가로 봐 주면 좋은 것** — 내가 안 한 `POST /api/save_instances` → `/api/revert_instances` 왕복(④-5). 번호 편집 화면 작업자와 겹치지 않을 때, 사과 한 장으로 저장 → `has_fixed:true`·`layer=fixed` 200 확인 → **`/api/revert_instances` 로 되돌리기**(파일 삭제 명령 대신 이 API 를 쓰면 `instances_fixed`·`masks_fixed`·`status.json` 이 함께 정리됩니다). 그 사진의 `status` 가 되돌린 뒤 `unreviewed` 가 되는 것은 원래 동작입니다.

## ⑦ 남긴 것 · 되돌린 것

- 시험 산출물은 전부 **임시폴더(scratchpad)** 에만 만들었고 공용 `data/` 는 쓰지 않았습니다. `parity_instances.py` 는 자기 임시폴더를 스스로 지웁니다.
- `stage1_server/cookie_before.txt`·`cookie_after.txt` 는 30일짜리 로그인 쿠키가 들어 있어 **내용을 덮어썼습니다**(삭제는 사람이).
- 남긴 증거: `stage1_server/` 의 `parity_instances.py`, `hdr_*.txt`, `inst_*_apple.png`·`inst_*_bb.png`, `errors_before.json`·`errors_after.json`. 지워도 되는 것은 사람이 판단해 주십시오(규칙 3).
- 서버는 **켜 둔 상태**입니다(PID 2888468). 내가 재시작하기 전 PID 는 2883365 로, 내 작업 중에 다른 작업자가 한 번 재시작한 흔적이 있습니다 — 번호 편집 화면 작업자와 서버를 같이 쓰는 중이니 2차도 재시작 전에 알려 주는 편이 좋습니다.
