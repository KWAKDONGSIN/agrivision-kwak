대행: Codex (Claude 한도 초과)
작성: 2026-09-20
최종 수정: 2026-09-20 03:26

# 라벨링·검수 툴 인수인계

사람이 사진의 마스크·상자·열매 번호를 고치고 확정하는 도구입니다. AI 결과는 초벌입니다.
원본 사진·마스크는 읽기만 하고, 사람 수정은 툴 `data/`에 따로 저장합니다.
이 문서의 경로는 특별히 적지 않으면 툴 폴더 기준입니다. 구조표는 `app/` 기준입니다.

## 1. 5분 시작

잘못 칠한 마스킹: `E` 지우개로 일부를 지우거나 `G` 자동지움으로 덩어리를 지웁니다.
전부 비우려면 오른쪽 패널 → 더 보기 → 전부 지우기를 누릅니다. 저장 전 `Ctrl+Z`로 되돌릴 수 있습니다.
번호는 ③ 번호 모드에서 고른 뒤 `D`로 지웁니다. 원본 파일은 어느 방법으로도 고치지 않습니다.

### 처음 이어받을 때: 모래상자에서 실행

아래 명령은 **이미 복사해 둔 작업 폴더**에서 실행합니다. 실서버의 `app/run.sh`를 시험용으로 누르지 않습니다.
이 서버에서는 Python 환경이 `/home/kds0206/.conda/envs/kwak/bin/python`, Node가 `/home/kds0206/.local/node22/bin/node`입니다.
필요 패키지: Flask, Pillow, numpy, scipy; 전체 시험에는 기존 통합 스크립트와 로컬 데이터가 필요합니다.

```bash
# 현재 폴더에 app/ tests/ scripts/ export/ data/가 있는지 확인
PY=/home/kds0206/.conda/envs/kwak/bin/python
# 테스트 도구가 빈 포트를 찾고 자기 서버만 닫는 실행 예제(쓰기 없음)
PYTHONPATH="tests/lib${PYTHONPATH:+:$PYTHONPATH}" "$PY" - <<'PYCODE'
import sandbox as L
p = L.start(port=L.free_port(5901), sb=L.T, pw='handoff-local')
try:
    print('서버 실행 확인. 로그인 화면 응답은 start()가 확인했습니다.')
finally:
    L.stop(p)
PYCODE
bash tests/run_all.sh --browser
```

전체 시험은 약 8~10분이 걸렸습니다(2026-09-20, 이 서버의 실측 503초).
`data/`에는 원본의 **복사본**을 두어야 합니다. 테스트는 `tests/_sandbox/`에서 추가 사본을 만들어 씁니다.
자료가 없는 공개 Git 사본만으로는 통합/브라우저 시험을 재현할 수 없습니다. 로컬 설치 경로는 §6을 봅니다.

### 운영 서버

보안 관련 값·설정 세부는 공개본에서 생략했습니다.
보안 관련 값·설정 세부는 공개본에서 생략했습니다.
인증이 없는 `/api/health`로 상태만 확인할 수 있습니다. 로그는 `app/logs/server.log`, PID는 `app/logs/server.pid`입니다.

```bash
curl -s http://127.0.0.1:5111/api/health
# 배포 검증을 끝낸 운영 담당자만 실행: bash app/run.sh restart
```

`run.sh restart`는 명시하지 않으면 마지막 데이터 루트를 이어받습니다. 포도·복숭아는 검수판,
사과·블루베리는 그 과일 폴더가 없을 때 기본 원본으로 돌아갑니다(`core/paths.py:dataset_for`).
남의 프로세스/5100·5101·5105·5001은 종료하지 않습니다. 이번 구조 전환은 사이클 5 최종 판정 전까지 보류입니다.

## 2. 구조도: 어디를 고치는가

`server.py`는 앱 생성과 register 호출만 하며 93줄입니다. 파이썬은 core → domain/API → server 조립으로 읽습니다.
`boxes.py`, `instances.py`, `dupes.py`, `maskio.py`는 외부 스크립트의 옛 import를 살리는 호환 파일입니다.
새 코드는 아래 실제 모듈에서 고칩니다. 문법상 타입과 설명은 공개 최상위 함수에 붙였으며,
복합 레코드/배열처럼 형식이 다양한 곳은 거짓으로 좁히지 않고 `Any`를 남겼습니다. 완전한 정적 타입 검증은 아닙니다.

| app/ 안 파일 | 역할 | 먼저 볼 함수 |
|---|---|---|
| `core/paths.py` | 경로·과일 목록·입력 이름 검증 | `dataset_for()`, `status_file()`, `img_path()`, `gt_path()` |
| `core/auth.py` | 로그인·서명 쿠키·시도 제한 | `make_auth_cookie()`, `auth_cookie_ok()`, `safe_next()`, `login_rate_ok()` |
| `core/status_store.py` | 판정 읽기·원자적 저장·확정 | `read_status()`, `write_status()`, `backup_status()`, `update_status()` |
| `core/util.py` | 스레드 잠금·시각·오류 응답 | `lock_for()`, `now_str()`, `as_int()`, `short_path()` |
| `domain/rules.py` | 데이터 규칙과 숫자 상수 | `human_count()`, `clean()`, `boxes_of()`, `pick_representative()` |
| `domain/statusfmt.py` | 판정 스키마·팀원 자료 해석 | `src_of()`, `confirmed_of()`, `verdict_of()`, `load_scores()` |
| `domain/maskio.py` | 이진/16비트 PNG 입출력 | `load_mask_bool()`, `load_mask_raw()`, `raw_to_png_bytes()`, `bool_to_png_bytes()` |
| `domain/dupes.py` | 근접 중복 묶음 | `load_duplicate_groups()`, `representative_map()`, `duplicate_exclusions()`, `excluded_stems()` |
| `api/photos.py` | 목록·사진·썸네일 | `dup_rep_ai_excluded()`, `register()` |
| `api/masks.py` | 마스크·판정·확정 | `labeled()`, `register()` |
| `api/boxes.py` | 상자 저장·초벌·YOLO 내보내기 | `team_box_path()`, `read_team_boxes()`, `team_count()`, `export_boxes_to()` |
| `api/instances.py` | 번호 편집·개수 캐시 | `source_of()`, `seed_source_of()`, `source_name()`, `mask_path_of()` |
| `api/counts.py` | 개수 출처·충돌 판정 | `counts_of()`, `register()` |
| `api/export.py` | 내보내기 작업 관리 | `export_module()`, `export_args()`, `export_caps()`, `job_public()` |
| `api/dashboard.py` | 진행 현황 | `register()` |
| `api/dupes.py` | 중복 제외·되돌리기 | `register()` |
| `static/js/state.js` | 상태 S·공용 표현 | `S`·`API`·`UI`를 통해 연결 |
| `static/js/api.js` | 서버 요청·알림 | `S`·`API`·`UI`를 통해 연결 |
| `static/js/view.js` | 화면·확대·보기 전환 | `S`·`API`·`UI`를 통해 연결 |
| `static/js/mask.js` | 붓·지우개·다각형 | `S`·`API`·`UI`를 통해 연결 |
| `static/js/boxes.js` | 상자 편집 | `S`·`API`·`UI`를 통해 연결 |
| `static/js/instances.js` | 번호 편집·PNG 해독 | `S`·`API`·`UI`를 통해 연결 |
| `static/js/counts.js` | 확정·개수 표시 | `S`·`API`·`UI`를 통해 연결 |
| `static/js/list.js` | 목록·사진 열기·현황 | `S`·`API`·`UI`를 통해 연결 |
| `static/js/export.js` | 내보내기 화면 | `S`·`API`·`UI`를 통해 연결 |
| `static/js/tour.js` | 첫 방문 안내 | `S`·`API`·`UI`를 통해 연결 |
| `static/js/keys.js` | 단축키 표·이벤트 등록 | `S`·`API`·`UI`를 통해 연결 |
| `static/js/main.js` | 초기 연결 | `S`·`API`·`UI`를 통해 연결 |

JS 파일은 위 순서대로 로드합니다. 전역 lexical binding은 S/API/UI지만 호환 window 속성 5개가 더 있습니다.
`UI`를 통해 뒤 모듈을 나중에 부르는 연결도 있어 실행 의존이 완전 단방향인 것은 아닙니다.
단축키 표는 keys.js에 있고 실제 분기는 각 handler에 남았습니다. `u7_keys_doc.py`가 표와 도움말을 대조합니다.

## 3. 데이터 파일 형식

`data/<fruit>/status.json`은 사진 이름을 키로 갖는 사전입니다. 옛 판정과 세 종류의 사람 확정을 별도로 보존합니다.

```json
{
  "사진이름": {
    "status": "fixed", "by": "작업자", "at": "<저장시각>", "note": "메모",
    "prev": {"status": "flag", "by": "기존 작성자", "note": "기존 메모"},
    "src": "dup_group",
    "confirmed": {"status": "ok", "by": "작업자", "at": "<확정시각>", "note": ""},
    "confirmed_boxes": {"status": "fixed", "by": "작업자", "at": "<확정시각>", "note": ""},
    "confirmed_instances": {"status": "ok", "by": "작업자", "at": "<확정시각>", "note": ""}
  }
}
```

위는 필드 형식 예시이며 실제 사진 기록이 아닙니다. `prev`와 확정 칸은 없을 수 있습니다.
`src=dup_group/dup_bulk`는 되돌리기의 소유 표식입니다. 무조건 ai/human으로 덮으면 안 됩니다.
확정 상태 중 ok/fixed만 내보내기 대상으로 인정합니다. flag는 확인 필요, exclude는 제외입니다.

| 경로 | 형식·뜻 |
|---|---|
| `boxes/<stem>.json` | fruit, stem, width, height, boxes 배열. 각 상자 id, cls, xyxy, src |
| `masks_fixed/<stem>.png` | 사람 수정 이진본, 8비트 L의 0/255 |
| `instances_fixed/<stem>.png` | 사람 수정 번호본, 16비트 정수 PNG. RGB 변환 금지 |
| `proposals/<stem>.png` | AI 제안 이진 마스크 |
| `duplicates.json` | groups 배열 안에 대표가 앞인 사진 이름 묶음. 기존 순서를 유지 |
| `app/cache/instance_counts/<fruit>.json` | 개수 캐시. 데이터 정답이 아니며 원본·수정본 지문으로 무효화 |
| `exports/<날짜시각>_<과일>/` | 내보낸 이미지·마스크·번호·상자·manifest·선택한 counts.csv |

```json
{"fruit":"peach","stem":"사진이름","width":100,"height":100,
  "boxes":[{"id":1,"cls":"fruit","xyxy":[10,20,40,50],"src":"human"}]}
```

xyxy는 픽셀 좌표이며 오른쪽/아래 끝은 범위의 끝입니다. 2픽셀 미만 상자는 버립니다.
빈 상자 목록 저장은 상자 수정본/확정을 되돌리는 동작입니다. 입력은 있지만 모든 상자가 검증에서 탈락하면 400으로 거절하고 기존 상자·확정을 유지합니다. 사용자가 명시한 빈 목록만 되돌립니다.
상자 cls는 fruit/bunch/other(0/1/2), 원본 modal/amodal 정의는 과일·출처에 따라 다르므로 임의 통일하지 않습니다.

`counts.csv`의 개수는 상자·번호·팀원 출처를 구별합니다. 번호 확정이 우선이며, 양쪽 확정 수가 다르면
사람 개수를 비우고 conflict로 표시합니다. 숫자를 직접 입력하는 별도 확정 칸은 없습니다.
`n_gt`는 확보된 정답만 채웁니다. 블루베리 초벌을 정답이라고 부르면 안 됩니다.

## 4. API 표

아래는 실제 Flask 주소표에서 생성한 37개 주소입니다. 세부 허용값·400/409/413 응답은 해당 함수와 회귀 시험을 함께 봅니다.
모든 쓰기 시험은 모래상자에서 합니다. 동시 편집을 막는 revision/409 계약은 아직 없습니다. 과일·사진 구간을 나눠 작업합니다.

| 주소 | 메서드 | 주요 입력 | 출력 | 구현 |
|---|---|---|---|---|
| `/` | GET | 직접 입력 없음 또는 경로 변수 | HTML·PNG/JPEG·정적 파일 또는 리다이렉트 | `api/photos.py:index` |
| `/api/apply_duplicate_exclusions` | POST | by, fruit | JSON: changed, kept_human, n_pairs, ok, skipped | `api/dupes.py:api_apply_duplicate_exclusions` |
| `/api/boxes` | GET | at, boxes, by, fruit, stem | JSON: at, boxes, by, classes, fruit, height, ok, saved, stem, team, width | `api/boxes.py:api_boxes` |
| `/api/boxes` | POST | boxes, by, fruit, note, stem | JSON: at, boxes, confirmed_cleared, dropped, n_boxes, ok, over, removed | `api/boxes.py:api_boxes_save` |
| `/api/boxes_export` | POST | fruit | JSON, 구성 함수 참조 | `api/boxes.py:api_boxes_export` |
| `/api/boxes_seed` | GET | fruit, source, stem | JSON: boxes, n, ok, seed_source, source | `api/boxes.py:api_boxes_seed` |
| `/api/boxes_stats` | GET | 직접 입력 없음 또는 경로 변수 | JSON: at, ok, stats | `api/boxes.py:api_boxes_stats` |
| `/api/component` | POST | fruit, source, stem, x, y | JSON: n_pixels, ok, png | `api/masks.py:api_component` |
| `/api/duplicate_preview` | GET | fruit | JSON: already_excluded, fruit, kept_human, n_groups, n_other_excludes, n_to_exclude, n_to_exclude_all, n_undoable, n_will_change, outside_dataset, sample | `api/dupes.py:api_duplicate_preview` |
| `/api/exclude_group` | POST | by, fruit, stem | JSON: changed, group, members, ok, rep, skipped | `api/dupes.py:api_exclude_group` |
| `/api/export_excluded` | POST | drop_flag, fruit | JSON: n, ok, path | `api/dupes.py:api_export_excluded` |
| `/api/export_list` | GET | 직접 입력 없음 또는 경로 변수 | JSON: dir, fruits, items, kinds, n_all, ok, running | `api/export.py:api_export_list` |
| `/api/export_plan` | GET | confirmed_only, fruit | JSON, 구성 함수 참조 | `api/export.py:api_export_plan` |
| `/api/export_start` | POST | by, confirmed_only, fruit, kinds | JSON: error, fruit, job, msg, ok, out | `api/export.py:api_export_start` |
| `/api/export_status` | GET | job | JSON, 구성 함수 참조 | `api/export.py:api_export_status` |
| `/api/fruits` | GET | 직접 입력 없음 또는 경로 변수 | JSON: data_root, fruits, statuses | `api/photos.py:api_fruits` |
| `/api/health` | GET | 직접 입력 없음 또는 경로 변수 | JSON, 구성 함수 참조 | `api/dashboard.py:api_health` |
| `/api/instance_errors` | GET | fruit | JSON: by_stem, n, n_stems, ok, rows, source | `api/instances.py:api_instance_errors` |
| `/api/instance_info` | GET | fruit, stem | JSON: cut_px, editable, has, has_fixed, hole_px, max_id, n, ok, source | `api/instances.py:api_instance_info` |
| `/api/instance_stats` | GET | fruit, start | JSON: at, ok, running, started, stats | `api/counts.py:api_instance_stats` |
| `/api/item` | GET | fruit, stem | JSON: ai_boxes_status, ai_status, at, by, confirmed, confirmed_boxes, confirmed_instances, counts, dup_group, dup_member_confirmed, dup_member_status, dup_members, dup_rep, fruit, has_fixed, has_gt, has_proposal, height, inspection, n_boxes, n_inst, note, scores, src, status, stem, width | `api/photos.py:api_item` |
| `/api/list` | GET | by, confirmed, dup, flag, fruit, mode, page, page_size, proposal, q, sort, status, suspect | JSON: features, flag, flag_counts, fruit, items, page, page_size, pages, total | `api/photos.py:api_list` |
| `/api/revert` | POST | by, fruit, stem | JSON: confirmed_cleared, ok, removed, restored, status | `api/masks.py:api_revert` |
| `/api/revert_instances` | POST | by, fruit, stem | JSON: changed, confirmed_cleared, ok, removed, restored, status | `api/instances.py:api_revert_instances` |
| `/api/save` | POST | action, by, fruit, note, png, stem | JSON: fg_pixels, has_fixed, kept_exclude, ok, status, wrote_mask | `api/masks.py:api_save` |
| `/api/save_instances` | POST | by, counts, fruit, note, png, stem | JSON: blocked, error, fg_pixels, hole_px, max_id, msg, n_instances, ok, status | `api/instances.py:api_save_instances` |
| `/api/stats` | GET | 직접 입력 없음 또는 경로 변수 | JSON, 구성 함수 참조 | `api/dashboard.py:api_stats` |
| `/api/status` | POST | by, confirm, fruit, kind, note, status, stem, stems | JSON: confirmed, kind, n, ok, skipped, status | `api/masks.py:api_status` |
| `/api/undo_duplicate_exclusions` | POST | fruit | JSON: backup, changed, kept, kept_other, ok | `api/dupes.py:api_undo_duplicate_exclusions` |
| `/api/undo_exclude_group` | POST | by, fruit, stems | JSON: changed, kept, ok | `api/dupes.py:api_undo_exclude_group` |
| `/box` | GET | 직접 입력 없음 또는 경로 변수 | HTML·PNG/JPEG·정적 파일 또는 리다이렉트 | `api/photos.py:index_box` |
| `/img` | GET | fruit, stem | HTML·PNG/JPEG·정적 파일 또는 리다이렉트 | `api/photos.py:serve_img` |
| `/instances` | GET | fruit, layer, stem | HTML·PNG/JPEG·정적 파일 또는 리다이렉트 | `api/instances.py:serve_instances` |
보안 관련 값·설정 세부는 공개본에서 생략했습니다.
| `/mask` | GET | fruit, layer, stem | HTML·PNG/JPEG·정적 파일 또는 리다이렉트 | `api/photos.py:serve_mask` |
| `/static/<path:fn>` | GET | 직접 입력 없음 또는 경로 변수 | HTML·PNG/JPEG·정적 파일 또는 리다이렉트 | `api/photos.py:static_files` |
| `/thumb` | GET | fruit, stem | HTML·PNG/JPEG·정적 파일 또는 리다이렉트 | `api/photos.py:serve_thumb` |

## 5. 규칙표

**30초 찾기: «이진본이 번호본을 자른다»는 A1, `app/domain/rules.py:cut_by_binary()`, 호출은 `app/api/instances.py:load_inst()`입니다.**
N6는 A3, `keep_numberless_foreground()`입니다. 읽기와 쓰기 규칙을 함께 보세요.
아래 108행은 기존 결정 기록에서 이어받았으며 코드 위치를 새 구조에 맞췄습니다.
근거의 `cycles/`는 툴 폴더, `문서/`는 `/data/project/2026summer/kds0206/문서/` 기준입니다.
시험 칸에 «없음» 또는 «제안»이 있으면 전용 단정까지 갖췄다고 주장하지 않습니다.

| # | 규칙 | 결정 근거 | 현재 코드 | 지키는 시험 |
|---|---|---|---|---|
| A1 | **이진본이 번호본을 자른다** — 이진 마스크가 배경인 자리의 번호는 **읽을 때 버린다**(파일은 안 고친다) | 두 파일이 서로 몰라서 세 갈래로 터졌다: 내보내기에 «없는 번호» **1,034화소** · 브러시로 지운 알이 번호 저장에서 되살아남 · 마스크 되돌리기가 번호 파일을 남김. **규칙 하나로 세 갈래 전부 0.** 2026-09-17 · 상자번호판정 **§2 «사이클 5» 행 · §3 «판정»** | `domain/rules.py:cut_by_binary()` → `api/instances.py:load_inst()` | `tests/api/regress_all.py`(번호 갈래) · `tests/unit/u3_instances_u16.py` |
| A2 | 거꾸로 **이진본은 전경인데 번호가 없는 자리는 채우지 않는다** | 어느 번호인지 툴이 정할 수 없다. 사람이 `N`(새 번호)·`M`(합치기)로 붙일 자리다. 상자번호판정 §3 | `api/instances.py load_inst()` | `manifest.csv` 의 `instances_check hole=` |
| A3 | **N6 쓰기 규칙 — «번호 저장» 은 «번호가 있던 화소만» 이진본에서 뺄 수 있다** | 번호 저장이 **고치지 않아도** 이진 전경 중 번호 없던 자리를 지웠다: 블루베리 초벌 **239장(20%)·61,620화소** · `Camera 1 Video (144)_121` 에서 **아무것도 안 고치고 151화소 소실**. 실제 손실 0(번호 파일 0장)이어서 살았다. 규칙화: «**읽기 규칙을 세우면 쓰기 자리도 같은 문장으로 검사한다**»(상자번호판정 §8-3). 결정 2026-09-17 · 상자번호판정 **§3 «판정»**(코드 6줄) → **2026-09-18 해제**(2차 독립 재현 `cycles/260917_신기능/cycle_6_n6/stage2_review.md` 2026-09-17 19:20 · 상자번호판정 머리말 «후속») | `api/instances.py api_save_instances()` · **`domain/rules.py keep_numberless_foreground()`**(규칙 함수 · 2차 채움) · `domain/maskio.py save_mask_atomic()` | `tests/api/regress_all.py` · (구조4 제안: N6 전용 단위 시험) |
| A4 | **번호를 전부 지운 저장은 400 으로 막는다**(`blocked:"instances_zero"`) · 파일·확정은 한 글자도 바뀌지 않는다 | A1 자르기 규칙 때문에 0개 저장은 **이진 마스크까지 0화소**로 만들고(실측 1,180화소→0), «원본 OK» 로 확정해 둔 사진이 «사람 확정만» 내보내기에 **빈 마스크 PNG** = «열매 없음» 학습 라벨로 나갔다. 화면 확인창은 회귀 시험을 깨므로 **서버에서** 막는다. 2026-09-19 · **paint5 §1 «번호 0개 저장» 행**(전 5/9 → 후 14/0) · 방향전환판정 **§3 #34 · §6** | `api/instances.py api_save_instances()` · **`domain/rules.py zero_instance_save_blocked()`**(규칙 함수 · 2차 채움) | 없음 ⚠ (구조4 제안) |
| A5 | 번호를 고친 사진은 **마스크 «수정본 되돌리기» 가 거절**된다 — «번호 되돌리기» 를 써야 한다 | 이진본만 지우면 번호 파일이 낡아 «없는 번호» 가 된다. 2026-09-17 · 상자번호판정 §3 | `api/masks.py api_revert()` · `api/instances.py api_revert_instances()` | `tests/api/regress_all.py`(되돌리기) |
| A6 | `masks_fixed/*.png` 는 **늘 8비트 L · 0/255** 로 저장한다 · 읽기는 «0보다 크면 전경» | 세그멘테이션 쪽 코드가 그 규격을 가정한다. 라벨값이 1·84 처럼 섞인 원본도 같은 규칙으로 읽는다 | `domain/maskio.py save_mask_atomic()` · `domain/maskio.py load_mask_bool()` | `tests/unit/u2_maskio.py` 단위2-1~2-10 |
| A7 | 번호본은 **16비트 PNG**, 읽은 배열은 **uint32**(8비트로 잘리지 않게) | 한 사진에 번호가 123개까지(사과 최대 실측) · 값은 65535까지 | `domain/maskio.py read_u16()` · `domain/maskio.py write_u16_atomic()` | `tests/unit/u3_instances_u16.py`(1·255·256·257·32768·65535 왕복) |
| A8 | 마스크·번호본·상자·status 는 **임시 파일 → `os.replace`**(원자적)로 쓰고 `.tmp*` 를 남기지 않는다 | 저장 도중 서버가 죽어도 반쪽 파일이 남지 않게 | `domain/maskio.py write_u16_atomic()` · `core/status_store.py write_status()` · `api/boxes.py api_boxes()` | `u2_maskio.py` 단위2-6 · `u3` 단위3-4 |
| A9 | 보낸 마스크·번호 크기가 원본과 다르면 **400** 으로 거절한다 | 크기가 다른 라벨을 받으면 조용히 어긋난 데이터가 쌓인다 | `api/masks.py _decode_png_mask()` · `api/masks.py _size_msg()` · `api/instances.py _decode()` | `tests/api/t1_api.py` |
| B1 | **AI 제안(`status`)과 사람 확정(`confirmed*`)은 다른 칸이다.** 사람이 확정해도 AI 제안은 **지우지 않는다** | 교수님 녹취의 «AI 초벌 → 사람이 맞다/틀리다 → 확실한 데이터셋» 을 **칸부터 갈라야** 사람 판단이 AI 값에 섞이지 않는다. 전에는 `1`·`3`·`4` 가 AI 3회 검수의 `status`·`by`·`note` 를 덮어 «왜 flag 였나» 가 사라졌다. 2026-09-18 · **paint1 §3** · 방향전환판정 §1 | `core/status_store.py confirm_status()` | `tests/browser/t2_ui.py` 가-0b · `regress_all.py` |
| B2 | 확정 칸은 **셋이고 서로 독립**이다(`confirmed`·`confirmed_boxes`·`confirmed_instances`) | 한 칸에 섞으면 상자를 확정할 때 마스크 확정이 지워진다(paint3 2차 §5-2). 2026-09-18 · **paint3 §4 결정 1 → paint4 §1** | `domain/statusfmt.py confirmed_of()` | `t1_api.py` 가-2·가-2b·나-1 · `regress_all.py` Enter확정 |
| B3 | **옛 자료를 고치지 않는다** — 새 칸이 없으면 «미확정» 으로 읽힌다(마이그레이션 0) | 공용 `status.json` 을 일괄 수정하면 그 순간 누른 판정이 사라질 수 있다 | `confirmed_of()` 가 없는 칸을 `None` 으로 | `regress_all.py`(네 과일 실자료) |
| B4 | 확정을 **쓰는 곳은 `confirm_status()` 하나**, **지우는 곳은 `clear_confirm()` 하나** | 종류마다 칸 이름을 따로 적으면 한 군데만 고치고 지나간다. 2026-09-18 · paint4 §1 | `core/status_store.py confirm_status()` · `core/status_store.py clear_confirm()` | `t1_api.py` |
| B5 | **묶음째 확정은 남이 이미 확정한 구성원을 건너뛰고 `skipped` 로 알린다** | 남이 확정한 것을 «제외» 로 덮던 결함(화면·서버 두 층 모두). 화면 필터 + 서버 = **두 겹**. 2026-09-18 · **paint2 §1 «N3» 행** · 방향전환판정 §3 #3·#9 | `confirm_status()` 의 `if i and confirmed_of(...)` | `regress_all.py` 묶음확정 · `t1_api.py` |
| B6 | **«1 원본 OK»·«3 문제»·«4 제외» 는 `confirmed` 칸만 쓴다** («2 AI로 교체»·«Ctrl+S 저장» 은 실제로 그림을 쓰므로 예전대로) | B1 과 같은 까닭. 2026-09-18 · paint2(2차 `s5_live_guard` C-2·C-4) · 사람확인표 «헷갈리기 쉬운 것» | `api/masks.py api_status()` · `api/masks.py api_save()` | `t2_ui.py` 가-0b |
| B7 | **저장 ≠ 확정**(마스크) / **상자·번호 저장 = 그 작업의 «수정함» 확정** · 저장은 자동으로 다음 장으로 넘기지 않는다 | 사람이 결과를 **눈으로 보게** 하는 설계(paint1 §2-3: «저장됨 — . 로 다음»). 상자·번호는 사람이 손대어 저장했으면 «사람이 본 것» 이다. 2026-09-18 · **paint1 §2-3 · paint4 §1 «갈림길 1»** · 사람확인표 C-2·D-2 | `api/boxes.py`·`api/instances.py` 가 `ctx["confirm_status"]`(= `core/status_store.py`) 를 부른다 | `t1_api.py` 가-3·나-1 · `regress_all.py` 저장 |
| B8 | **② 상자의 `Enter` 는 «저장 → 확정» 두 걸음**이고 상자가 0개면 확정하지 않는다 | «초벌» 은 파일이 아니라 **화면에만** 있다. 저장 없이 확정하면 «맞다» 고 해 놓고 내보낼 상자가 하나도 없다. 2026-09-18 · **paint4 §1 «갈림길 1» 행** | `js/counts.js enterConfirmTask()` | `t2_ui.py` 가-2·가-4 · `t1_api.py` 가-1 |
| B9 | **`Enter` 는 안내 창이 닫혀 있고 입력칸에 커서가 없을 때만** 확정이다 · 서버가 확정을 못 받으면 **다음 장으로 넘어가지 않는다** | 옛 서버에서 «Enter 열 번 = 열 장 넘어가고 확정 0» 이었다. 2026-09-18 · **paint1 §3 · paint2 §1 «가드» 행**(`if (!j) return;`). 예외 목록(메모·이름·검색 칸 커서 · Ctrl/Alt/Shift · 다각형 켜짐 · 번호 모드에서 그리다 만 영역)은 사람확인표 «헷갈리기 쉬운 것» | `js/keys.js`(등록) · `js/counts.js onEnterKey()`→`enterConfirm()` | `t2_ui.py` 가-5 |
| B10 | **되돌리기가 성공하면 그 종류의 확정을 지운다**(응답 `confirmed_cleared` · 화면 1초 힌트) | 확정이 «수정함» 으로 남으면 manifest 는 `source=human`·`fixed` 인데 나가는 파일은 **원본**이다 = 내보내기가 거짓말을 한다(소수정이 manifest 한 줄로 실증). «사람은 되돌린 뒤 Enter 한 번». 2026-09-18 · **paint4 §1 «갈림길 4» — 1차 결론을 3차가 뒤집었다** · 방향전환판정 §3 #26·§6 · 사람확인표 C-3 | `core/status_store.py clear_confirm()` | `regress_all.py` 되돌리기 · `t1_api.py` |
| B11 | **`by` 가 «AI» 로 시작하면 `POST /api/status` 는 400** | `src_of()` 가 `by.startswith("AI")` 로 출처를 미루므로 **사람 판정이 «AI 제안» 으로 보인다**(오표시 · 데이터 소실 아님). 사람이 갈 수 있는 길은 이름 칸뿐이고 그 길은 막았다. «AI 3회 검수» 는 HTTP 가 아니라 **파일 직접 쓰기**였다(실측으로 주석 근거를 교체). 2026-09-18 발견(paint2 §1 «N8» 보류) → **paint4 §1 «갈림길 2» 결론 유지**. «400» 숫자는 `cycles/260918_paint/cycle_4/stage2_review.md:192` | `api/masks.py api_status()` · **`domain/rules.py ai_name_rejected()`**(규칙 함수 · 2차 채움) | `t1_api.py` 마-2·마-2b |
| B12 | `src_of()` 는 `by` 로 «사람/AI» 를 **계산**한다 — `src` 칸에 `ai`/`human` 을 **쓰지 않는다** | `status.json` 의 `src` 칸은 **이미 다른 뜻**(어느 단추가 제외했나)이고 **되돌리기가 그 값만 본다**. 적으면 되돌리기가 망가진다. 2026-09-18 · 근거는 3차가 아니라 **`cycles/260918_paint/cycle_2/stage2_review.md:424`**(«server.py 1241·1341·1283·1375행») | `domain/statusfmt.py src_of()` | `t1_api.py`(응답 `src`) |
| C1 | **「일괄 제외 되돌리기」는 `src:"dup_bulk"` 표식이 있는 것만 되돌린다** | 전에는 «메모가 «중복: » 으로 시작하면» 전부 되돌려서, 한 번 누르면 AI 3회 검수의 제외(**사과 572·블루베리 81장**)와 flag 사유(51·4장)가 통째로 날아갔다. 2026-09-17 · 근거 `cycles/260918_paint/cycle_2/stage2_review.md:424` + README §5 | `api/dupes.py api_undo_duplicate_exclusions()` | 없음 ⚠ |
| C2 | **「묶음 되돌리기」는 `src:"dup_group"` + 메모 «중복:» + `by` 가 같은 이름일 때만** | 다른 사람이 제외한 것을 내가 되돌리면 «누가·왜 뺐나» 가 사라진다. 다른 이름이면 한 장도 안 돌아오고 빨간 글씨로 까닭을 말한다. 2026-09-17 사이클3 2차 | `api/dupes.py api_undo_exclude_group()` | 없음 ⚠ |
| C3 | **일괄 제외는 «아직 안 봄» 인 사진만 «제외» 로 바꾼다** — 사람이 판정한 사진은 덮지 않는다 | 확인창이 «N장은 사람이 이미 판정해서 건드리지 않습니다» 라고 알려 준다 | `api/dupes.py api_apply_duplicate_exclusions()` · `api/dupes.py api_exclude_group()` | `regress_all.py` 묶음확정 |
| C4 | **되돌릴 수 없는 일괄 작업 전에는 `_status_backup_<시각>.json` 을 먼저 만든다** | 「일괄 제외 되돌리기」는 되돌릴 수 없다 — 이미 폴더에서 빠진 사진은 복구되지 않는다 | `core/status_store.py backup_status()` | 없음 ⚠ |
| C5 | **되돌릴 것이 0장이면 백업을 만들지 않고 `status.json` 도 건드리지 않는다** | 전에는 0장에도 백업이 하나씩 쌓였다. 2026-09-18 · paint «N10» | `api_undo_duplicate_exclusions()` | 없음 ⚠ |
| C6 | **되돌리기·판정 저장은 이전 판정을 `prev` 로 남긴다** — `unreviewed` 가 아닌 **모든** 판정에서 | ①`1·3·4` 가 AI 판정을 되살릴 수 없게 지우고 있었다(2026-09-18 · **paint2 §1 «N1» 행** — `api_save` 에 `keep_prev=True`) ②그 뒤에도 `flag`·`exclude` 일 때만 남겨서 AI 판정이 `ok`·`fixed` 인 **107장**(복숭아 77+18 · 포도 12)은 붓질 저장 뒤 되돌리면 판정·메모가 사라졌다(그 뒤 `Enter` 도 거부). 2026-09-19 · **paint5 §1** · 방향전환판정 §3 #33 | `core/status_store.py update_status()` | `regress_all.py` 되돌리기 |
| D1 | **상자 0개 저장 = 파일 삭제 + 상자 확정 비움**(저장이 아니라 «그 작업의 되돌리기») | 전에는 빈 파일을 쓰고 «수정함» 으로 확정해서 ㉠확정을 비울 길이 영영 없고(`/api/revert_boxes` 없음) ㉡카드가 «✔ 확정» 이라 말하고 ㉢«사람 확정만» 내보내기가 **0줄 txt** = «이 사진에는 열매가 없다» 는 **학습 라벨**을 냈다(실측 102줄 → 0줄). 종합 리뷰가 «**데이터 소실 가능 1**» 로 분류한 건. 2026-09-19 · **paint5 §1(즉시 수정 3)** · 방향전환판정 **§3 #31·§5 고침 1** | `api/boxes.py api_boxes()` · `core/status_store.py clear_confirm()` · **`domain/rules.py is_box_clear_save()`**(규칙 함수 · 2차 채움) | `t2_ui.py` 가-7 계열 |
| D2 | **상자가 한 줄도 없는 사진은 내보낼 때 txt 를 만들지 않고 건너뛴다** | 0줄 txt 는 검출 학습이 «열매 없음» **정답 라벨**로 읽는다. 시험 잔재였지만 같은 경로로 빈 라벨이 나갈 수 있다. 2026-09-19 · **count4 §1 «0줄 YOLO txt» 행 · §3**(사이클 5 로 넘긴 소수정) | `api/boxes.py export_boxes_to()` | `t1_api.py` 라-2·라-3 |
| D3 | **2픽셀보다 작은 변의 상자는 버린다**(`MIN_SIDE=2`) · 버린 개수를 화면에 알려 준다 | 1픽셀 붕괴·2화소 조각 같은 쓰레기 상자를 막는다. 2026-09-17 · **상자번호판정 §7 «숫자 사전»** | `domain/rules.py clean()` | `tests/unit/u1_boxes_selftest.py` |
| D4 | **한 사진에 3,000개 상한**(`MAX_BOXES`) · 넘으면 그린 순서 앞 3,000개만 저장하고 넘은 개수를 알려 준다 | 3,000개 넘는 상자가 **조용히 사라지던** 결함(사이클 1). 2026-09-17 · **상자번호판정 §7** | `domain/rules.py clean()` · `domain/rules.py boxes_of()` | `u1_boxes_selftest.py`(3,005 → 3,000 · over 5) |
| D5 | **초벌은 4화소 미만 번호를 제외한다**(`min_px=4`) | 2화소짜리 번호가 상자가 되면 쓰레기 라벨이다. 실측 예외 1장: `20150921_131234_image451` 번호 62 ↔ 상자 61. 2026-09-17 · **상자번호판정 §2(사이클 3)·§7** | `domain/rules.py boxes_of()` | `u3_instances_u16.py` 단위3-8·3-9 |
| D6 | **저장 응답의 `boxes` 목록으로 화면이 자기 상태를 덮어쓴다** | 서버가 버린 상자가 화면에만 남아 «저장했는데 아직 있다» 가 되지 않게(D3·D4) | `api/boxes.py api_boxes_save()` 응답 + **화면 — 구조 사이클 3 몫**(2차 채움: 서버 쪽이 빠져 있었다) | `tests/sim/boxsim.js` |
| D7 | **상자 종류는 세 가지뿐** — `fruit`(0)·`bunch`(1)·`other`(2) | 검출 팀 YOLO 번호와 짝을 맞추려는 것. 2026-09-17 · **상자번호판정 §7** | `domain/rules.py CLASSES` | `u1_boxes_selftest.py` |
| D8 | 🔴 **내보낸 YOLO txt 는 교수님 5번(클래스 번호) 결정 전에는 학습에 바로 넣지 않는다** | 우리 송이 = 1, 검출 팀 송이 = 0 — 그대로 학습하면 라벨이 뒤집힌다. 2026-09-17 · **상자번호판정 §1 «상자(네모) 모드» 행 · §5 교수님 5번** · 교수님17건 5번 | (사람 규칙 · 코드가 막지 않는다) | 없음(사람) |
| D9 | **초벌은 저장하지 않는다** — 사람이 고치고 저장할 때 비로소 파일이 된다 | AI 가 잘못 그릴 수 있다. 초벌 속도 기준 **0.5초 미만**(실서버 0.2초 — 옛 7.55초가 사람을 기다리게 했다 · 상자번호판정 §7) | `api/boxes.py api_boxes_seed()` | `t1_api.py` 가-0c · `t2_ui.py` 가-1b |
| D10 | **상자 = 마스크(또는 번호)를 꼭 감싸는 축정렬 최소 상자** — 상자가 규칙을 새로 정하지 않는다 · **과일별 정의를 문장으로 고정** | COCO 관례(`lin2014coco` 인쇄 p.750 — PDF p.11 아님, M19). amodal/modal 여부는 **마스크가 정한다**. 사람이 같은 기준으로 그리게 화면·문서에 과일별 문장을 적는다. 2026-09-19 · **count1 §1(1행) · count2 §2 M4 · count3 §2-4** | `domain/rules.py boxes_of()` | `u3_instances_u16.py` 단위3-8 |
| D11 | **되돌리기 깊이: 번호 40단계 · 상자 30칸**(마스크는 20단계) | 사람이 실수를 되돌릴 수 있는 폭을 숫자로 못 박았다. 2026-09-17 · **상자번호판정 §7 «되돌리기» 행** | `js/instances.js pushNumUndo()`(40) · `js/boxes.js bpush()`(30) · `js/mask.js pushUndo()`(20) | `tests/sim/sim.js` |
| D12 | **상자 저장은 마스크 판정·마스크 확정을 바꾸지 않는다**(`confirmed_boxes` 칸만) | 칸이 따로다(B2). 2026-09-18 · paint4 | `api/boxes.py api_boxes()` | `t1_api.py` 가-3b · `t2_ui.py` 가-7b |
| E1 | **사람 확정 개수를 직접 입력하는 칸은 두지 않는다** — 이미 있는 두 확정에서 **유도**한다 | ㉠숫자 칸은 «세 번째 진실» 을 만든다 ㉡확정·되돌리기 규칙을 네 번째 종류로 또 나눠야 한다 ㉢녹취 0908 «AI 초벌 + 사람이 맞다/틀리다» 흐름에 없는 작업이다. 2026-09-19 · **count1 §1(1행 «숫자만 치는 칸 없음(yagni)»)** | `domain/rules.py human_count()` | `u1_boxes_selftest.py` 단위1-1·1-4·1-5 |
| E2 | 유도 순서: **번호 확정 > 상자 확정 > 없음** | 번호는 알 하나하나에 붙은 라벨이고 상자는 그 번호에서 만든 것이다. 사람이 상자를 합치거나 나눌 수 있어 상자는 «개수의 원본» 이 아니다 | `human_count()` | `u1_boxes_selftest.py` |
| E3 | 🔴 **둘 다 확정인데 수가 다르면 개수를 비운다**(`n_human=None`·`source="conflict"`·`conflict=True`) | 1차는 «어긋나면 번호 수를 쓰고» 있었다(2차가 밝힌 1차 오류 4 중 하나). 툴이 한쪽을 고르면 **사람이 인정하지 않은 수가 논문 표(MAE·RMSE·R²)에 실린다 = 사후 정당화**(2026-08-13 경고). 어긋난 사진은 사람이 고칠 때까지 «사람 확정만» 에서 빠진다. 2026-09-19 · **count1 §1 «결정 1» 행** | `human_count()` | `u1_boxes_selftest.py` 단위1-4 |
| E4 | `flag`·`exclude` 확정은 «확정» 으로 세지 않는다 | flag = 아직 고칠 것 · exclude = 안 쓸 사진. 내보내기가 이미 그 둘을 뺀다 | `human_count()` | `u1_boxes_selftest.py` |
| E5 | **`0` 개도 «값 없음» 이 아니다** — 빈칸 = 셀 수 없다, `0` = 열매가 없다 | 표에서 둘을 섞으면 분모가 달라진다 | `human_count()` · `export_dataset._cell()` | `u1_boxes_selftest.py` |
| E6 | 🔴 **`counts.csv` 는 «그 job 이 나간 사진» 만 담는다** — 같은 job 의 `manifest.csv` 의 «포함» 줄과 **완전히 같다** | manifest 와 개수 표가 서로 다른 사진 집합을 말하면 지표가 어긋난다(분모가 달라진다). 2026-09-19 · **count1 §1 «결정 2» 행** | `export/export_dataset.py included_stems()`·`exclude_reason()` — 빼는 판단 한 군데 | 없음 ⚠ (구조4 제안: manifest↔counts 대조) |
| E7 | `manifest.csv` 와 `counts.csv` 는 **같은 판정 스냅샷**(`st`)으로 센다 | 사과 1,001장 내보내기는 수십 초다. 그 사이에 누가 확정하면 두 표가 어긋났다. 2026-09-19 · count1 2차 검수 B-1 | `export_one(st=…)`·`write_counts_csv(st=…)` | 없음 ⚠ |
| E8 | **개수 캐시는 «지문»(mtime+크기)이 맞을 때만 쓴다** | 캐시 무효화가 없어 **첫 편집부터** 낡은 값을 썼다(번호를 10개로 고쳐 저장했는데 화면·`counts.csv` 는 옛 95개 · 같은 job 의 번호 PNG 는 10개). 속도도 함께 얻었다: 한 장 **218ms → 0.32ms**. 2026-09-19 · **count1 §1 «결정 3» 행 · 2차 즉시 수정 6** | `api/instances.py count_fresh()` · `api/instances.py sig_of()` | `regress_all.py`(번호 갈래) |
| E9 | 번호를 확정했는데 캐시에 없으면 **그 자리에서 세고, 센 값을 캐시에 적는다** — **GET 이 파일을 쓰는 유일한 자리** | 안 세면 «번호로 확정했는데 개수는 상자 수» 라는 조용한 거짓말이 된다. 적는 것은 개수 캐시 하나뿐이고 `status.json`·마스크·번호본은 그대로다. 2026-09-19 · **count1 §1 «결정 3»** | `api/instances.py count_now()` | 없음 ⚠ |
| E10 | **개수 칸은 «사람 확정이 있으면 초록» 이 이긴다** · 어긋남은 `≠` **글자로만** · `?` = «서버가 모른다» ≠ `-` = «없다» | 전에는 노랑이 초록을 덮어 «확정했는데도 초록이 아닌» 칸이 있었고, 화면이 **없는 확정을 말하기도** 했다. 없는 값을 있는 척하지 않는다. 2026-09-19 · **count1 §1 «결정 4» 행 · 2차 즉시 수정 6** | `js/counts.js renderCntChip()` | `t2_ui.py` |
| E11 | **개수 세기 연결성은 4-연결로 고정**(8-연결 경로를 두지 않는다) | 실서버는 `boxes.py` 가 맨 위에서 `from scipy import ndimage` 하므로 **scipy 가 없으면 서버가 아예 뜨지 않는다** → 4/8 갈림이 **불가능**하다. 실측으로도 4-연결이 정답에 더 가까웠다(−16.7 vs −18.2 · 사과 MAE 6.76/R² 0.883 ↔ 7.36/0.863). 2026-09-19 · **count1 §1 «2차가 밝힌 1차 오류 4» 행 · count2 §1 «2차 실측» · count3 §1 «1차 과잉 3»**. ⚠ «4-연결이 더 정확하다» 는 **문서화는 보류**(M2 · count3 §2-10) | `api/masks.py labeled()` | `tests/run_all.sh` 의 `syntax`·`unit` |
| F1 | **초벌은 «이미 있는 것»(박성문 워터셰드 출력)을 먼저 쓰고, 툴이 세는 4-연결 CC 는 마지막 폴백이다** | 같은 것을 두 번 구현한 셈이었고 **나쁜 쪽이 기본값**이었다 — 복숭아 개수 MAE **0.70**(툴 CC) ↔ **0.30**(워터셰드). 이유는 «정확해서» 가 아니라 «**도구 일치를 위해**»(count2 가 문장을 그렇게 고쳤다). 2026-09-19 · **count2 §2 M1 → count3 §2-1 → count4 §1(1차 10항)·§2** | `api/instances.py seed_source_of()` · `api/instances.py source_name()` | `u3_instances_u16.py` 단위3-10 · `t1_api.py` 나-2 |
| F2 | 읽는 우선순위는 **`fixed`(사람이 고친 것) > `seed`(초벌) > `gt`(원본 번호)** | 사람이 고친 것이 늘 먼저다 | `api/instances.py source_of()` | `regress_all.py` |
| F3 | **사과는 `SEED_DIRS` 에 넣지 않는다 — 원본 마스크에 정답 번호가 있다** | 우선순위가 `seed > gt` 이므로 넣으면 **워터셰드가 정답을 덮는다**. 실측 8장 오차 **0 ↔ 20**. 2026-09-19 · **count4 §1 «사과는 team 초벌 제외» 행** | `SEED_DIRS`(사과 없음) · `KIND_SOURCE = {"gt":"gt_numbers"}` | `regress_all.py`(사과) · `t2_ui.py` 나-1 |
| F4 | 사과 ③ 하단 한 줄은 «**원본 정답 번호** N개» 라고 말한다(«AI 초벌» 이라 하지 않는다) | 정답 라벨을 AI 산출물이라고 부르지 않는다. 2026-09-19 · **count4 §1 → 사이클 5 로 넘긴 소수정(count4 §3)** | `js/counts.js taskConfLine()` | `t2_ui.py` 나-1 |
| F5 | ⛔ **포도 번호 초벌은 꺼 둔다 — 교수님 확인 8번 전까지** | 교수님 8번(«포도 송이 번호를 CERTH 원본에서 — **전경 기준을 우리 마스크로 두어도 되는가**»)이 미결이다. 전제 넷 중 셋(N1 재현·화면 문구·N6 재현)은 끝났고 이것만 남았다. 최초 2026-09-17 · **상자번호판정 §1 표 «포도 송이 번호 = 켜지 않음» · §4 «사람 규칙 ③» · §6 «전제 넷·켜기 절차»** → 재확인 2026-09-19 · **count4 §1 «포도 번호 초벌(CERTH)» 행**(1차가 켠 채 넘긴 것을 **2차가 다시 껐다**) | `api/instances.py SEED_DIRS` | `regress_all.py`(포도 = 번호 없음) |
| F6 | 포도를 켤 때는 **절차가 있다** — `SEED_DIRS` 한 줄 되살리기 → **아무도 저장 중이 아닐 때** `run.sh restart` → 10분 확인(포도 `1439`=1개 · `1564`=18개 · 복숭아 패널 없음 · 500 없음) → 되돌리기는 그 한 줄 빼고 재시작 | 남이 쓰는 화면을 바꾸는 일이다. 2026-09-17 · **상자번호판정 §6** | 같음 | 없음(사람 절차) |
| F7 | 팀원 상자 초벌이 그 사진에 없으면 **404 로 끝내지 않고** 번호본 → CC4 로 물러선다(응답 `fallback_from`) | 사람이 «없다» 는 화면만 보고 멈추지 않게. 2026-09-19 · count4(M1) | `api/boxes.py api_boxes_seed()` | `t1_api.py` 가-0c |
| F8 | 🔴 **워터셰드 매개변수의 출처를 문장으로 못 박는다** — «매개변수는 **사과 정답 1,001장으로 골랐고**, 보고 숫자는 **정답 마스크 입력 기준 상한**» | `PEAK_FRAC=1.1`·`RADIUS_PCT=90` 을 «정답으로 튜닝하고 그 정답으로 평가» 한 **순환** 의심. 숫자는 견뎠지만(절반 200회·5-fold 세 seed 모두 +0.59~0.70%, 5폴드 전부 1.1 선택) **절차는 순환**이므로 문장으로 덮는다. 복숭아 최적은 훑은 범위의 끝값(0.7 이하)이다. 2026-09-19 · **count3 §2-7(M15) · §1 «순환 튜닝» 행** | (문서 규칙 — README §20-2 · 대조표 · 계획서) | 없음(사람) |
| G1 | 🔴 **사람 확정이 AI 판정보다 위 — 두 모드(«사람 확정만»·«AI 제안 포함»)가 똑같이 판단한다** | «AI 제안 포함» 이 사람 확정을 **아예 보지 않아서** 사람이 «제외» 로 확정한 **3장이 나가고**(오염) 사람이 «OK» 한 **2장이 빠졌다**(손실). 화면 풍선말이 말한 것과 코드가 달랐다. 방향 문서 §3-1 «사람이 확정하면 그것이 위에 선다» 그대로. 2026-09-18 · **paint3 §1 «2차 즉시 수정 F1» 행 — 이 사이클의 핵심 수정** · 방향전환판정 §3 #12 | `export/export_dataset.py exclude_reason()`(확정이 있으면 AI 의 중복·제외 판단은 더 보지 않는다) | 없음 ⚠ (구조4 제안: 두 모드 × 확정 5가지) |
| G2 | **기본값은 «사람 확정만»** 이고 «지금 확정된 사진 N장 · 나갈 사진 N장» 을 **늘**(경고가 아니라 상시) 보여 준다 | 확정 0장인데 누르면 아무것도 안 나가는 것을 사람이 **미리** 알아야 한다. 2026-09-18 · **paint2 §4 결정 1** · 실측 확인 paint3 §2·§3(화면 숫자 = `export_plan` dry-run 과 같은 코드) | `api/export.py api_export_plan()` + **화면 — 구조 사이클 3 몫**(2차 채움: 서버 쪽이 빠져 있었다) | `t1_api.py` 라-0 |
| G3 | **사람이 «문제 있음(flag)» 으로 확정한 사진은 어느 모드에서도 빠진다**(`confirmed_flag`) · **포함 옵션을 두지 않았다** | 아직 고칠 것이므로 «확실한 데이터셋» 이 아니다(원하면 고쳐서 «수정함» 으로 확정하면 나간다). manifest 에 왜 빠졌는지 남긴다. 2026-09-18 · **paint2 §4 결정 2 → paint3 §1(항목 8)** | (`export/` 는 같은 자리) · 툴 쪽은 **`domain/rules.py goes_out()`·`CONFIRM_OUT`** ← `api/export.py export_caps()`·`api/export.py export_worker()`(2차 채움) | `t1_api.py` 라-0 |
| G4 | 내보내기는 **종류마다 자기 확정**을 본다 — 마스크 `confirmed` · 상자 `confirmed_boxes` · 번호 `confirmed_instances` | 상자·번호에 «확정» 이 없어 상자 YOLO 가 사람 확정을 **전혀 가리지 않고** 저장된 것을 전부 냈다(paint3 §1 «넘긴 것 1»). 2026-09-18 · **paint3 §4 결정 1 → paint4 §1** | `api/boxes.py export_boxes_to()` | `t1_api.py` 라-2·라-3·라-4 |
| G5 | **번호를 «마스크 확정으로 대신하지 않는다»** — 빠진 줄은 `instances_check` 에 «번호 미확정» 이라 적는다 | 번호를 한 번도 보지 않은 사람의 «원본 OK» 가 번호까지 확정한 것처럼 새어 나가면 안 된다. 2026-09-18 · paint4 | `export_dataset.py`(`chk["skip"]`) | `t1_api.py` 나-1 |
| G6 | **빼는 판단은 `exclude_reason()` 한 군데**에 있고 manifest·counts.csv·상자가 그것을 같이 쓴다 | 두 벌로 베끼면 곧 갈라진다(paint3 2차 «의미-1» 이 그런 갈라짐이었다). 2026-09-19 · count1 §1 «결정 2» | `export/export_dataset.py exclude_reason()` | 없음 ⚠ |
| G7 | **`manifest.csv` 앞 9칸은 한 칸도 바꾸지 않는다**(검출 팀이 읽는 표) · 새 칸은 **뒤에 붙인다** | 남의 도구를 깨지 않는다. 2026-09-18 · paint3 §1(«manifest 4칸» 추가 · N6) | `export_dataset.py` 머리줄 · `conf_cells()` | 없음 ⚠ (구조1 기준선 sha256 이 대신 지킨다) |
| G8 | 내보낸 산출물에 **검사 칸을 같이 넣는다** — `instances_check`(`cut=`·`lost_ids=`·`hole=`) | 자르기 규칙(A1)으로 번호가 빠질 수 있으니 **받는 쪽(검출 팀)이 그 수치를 같이 읽어야** 한다. 2026-09-17 · **상자번호판정 §1 마지막 행 · §2(사이클 5) · §11** | `export_dataset.check_cell()` | `regress_all.py` |
| G9 | 내보내는 코드는 **명령줄과 화면이 같은 함수**다(`export_one()`·`export_boxes_to()`) | 규칙이 두 군데로 갈라지지 않게 | `api/export.py export_worker()` | `t1_api.py` 라-1~라-4 |
| G10 | 나가는 곳은 **툴 폴더 안** `exports/<YYMMDD_HHMMSS>_<과일>/` 하나뿐 · 폴더 이름은 **서버가** 정한다(`exist_ok=False`) | 팀 데이터셋(`kds0206/datasets_*`)과 공용 `data/` 를 건드리지 않는다. 기존 폴더를 덮어쓸 수 없다. 2026-09-18 · **paint2 §4 결정 3 → paint3 §1** | `api/export.py api_export_start()` | `t1_api.py` 라-1 |
| G11 | 같은 과일을 두 번 동시에 내보내면 **409**(다른 과일은 동시에 됨) · 스레드가 죽으면 **503 + state error** · 반쪽 폴더는 `job.json running` → `stale` · 몸통이 dict 아니면 **400**(500 아님) · `confirmed_only: null` 은 **True** | 폴더가 섞이지 않게. 전에는 스레드가 죽으면 **영영 409** 였고, `job.json` 을 끝날 때만 써서 목록에도 안 보이는 반쪽 폴더가 남았다. 2026-09-18 · **paint3 §1** | `api/export.py api_export_start()` · `api/export.py write_job_json()` · `api/export.py api_export_status()` | `t1_api.py` 라-3b |
| G12 | **나갈 장수는 «파일이 실제로 있는 사진» 만 센다**(화면 숫자 = 실제 txt 수) | 상자 파일이 없어도 «나갈 상자» 로 세던 것. 2026-09-18 · **paint4 §1 «넘긴 것» 행** · 방향전환판정 §3 #27 | `api/export.py export_caps()` | `t1_api.py` 라-0 |
| G13 | **빈 날짜 폴더는 «만들지 않기» 가 아니라 «표시»** — 표에 «빈 폴더» 로 보여 주고 지우지 않는다 | «**상자만 골라도 저장된다**» 규칙을 깨지 않기 위해. 사이클 4 의 «만들지 않기 우선» 을 **3차가 뒤집었다**. 2026-09-19 · **paint5 §1 · 방향전환판정 §6** · 사람확인표 E-2 | `api/export.py api_export_list()` + **화면 — 구조 사이클 3 몫**(2차 채움: 서버 쪽이 빠져 있었다) | 없음 ⚠ |
| G14 | 🔴 **`LABELTOOL_DATA_ROOT` 를 안 주면 «검수 전 폴더» 에서 내보낸다** — 명령 맨 윗줄의 원본 폴더를 **눈으로 확인**한다 | 장수가 우연히 같게 나와서 숫자만으로는 알아챌 수 없다(포도: 어느 쪽이든 «포함 2,403장») | `core/paths.py dataset_for()` | 없음 ⚠ (사람 절차) |
| H1 | **묶음 대표는 «자기 AI 제안 그대로» 확정한다** — 대표가 `flag` 면 `flag`(큐에 «고칠 것» 으로 남는다) · 나머지는 `exclude` | 전에는 대표를 **무조건 «원본 OK»** 로 확정했다 — flag 인 대표까지 OK 가 됐다. 확인창도 «대표: \<제안\> 으로 확정 · 나머지 N장: 제외로 확정» 으로 고쳤다. 2026-09-18 · **paint2 §1 «N5» 행** · 방향전환판정 §3 #10 | `core/status_store.py confirm_status()` · **`domain/rules.py pick_representative()`**(대표 고르기 · ← `api/dupes.py api_exclude_group()`·`api/photos.py api_item()`) + **화면 — 구조 사이클 3 몫**(2차 채움) | `regress_all.py` 묶음확정 |
| H2 | 근접 중복(대표 아닌 장)은 내보내기에서 **빠진다**(`duplicate_of:<대표>`) · `--keep-duplicates` 로 끌 수 있다 | 거의 같은 사진은 학습에 도움이 안 되고 평가를 부풀린다 | `export_dataset.exclude_reason()`·`representative_map()` | 없음 ⚠ |
| H3 | 표의 «대표 외 장수» 와 「검수자별」 표는 **지금 데이터셋에 있는 사진만** 센다 · 빠진 것은 «데이터셋 밖» 으로 따로 적는다 | 이미 폴더에서 빠진 사진을 세면 단추를 눌러도 안 바뀌는 숫자가 된다 | `api/dupes.py api_duplicate_preview()` · `api/dashboard.py api_stats()` | 없음 ⚠ |
| H4 | 🔴 반영 스크립트 `final/build_reviewed_dataset_260917_v2.py --tool` 은 **다시 돌리지 않는다** | 공용 `status.json` 을 **잠금 없이** 덮어쓴다 — 사람이 검수를 시작한 뒤에 돌리면 그 순간의 판정이 사라진다 | (툴 밖 스크립트) | 없음(사람 규칙) |
| H5 | 사진 이름은 **줄여 쓰지 않고 전체 이름으로** 적는다 | `Camera 4 Video (79)_1` 과 `Camera 1 Video (79)_1` 은 **다른 사진**이다. 화면 하단 줄이 이름을 반쪽으로 자르던 것도 고쳤다(«중복: 20150919_1»). 2026-09-17 · **상자번호판정 §8-9** / 화면: 2026-09-18 · paint2 §1(F5) · 방향전환판정 §3 #6 | `js/counts.js cutNote()`(화면 쪽) | `t2_ui.py` |
| I1 | `status.json` **쓰기는 늘 `status:<과일>` 자물쇠 안에서 임시 파일 → `os.replace`** | 원자적으로 바꿔야 반쪽 파일이 없다 | `core/util.py lock_for()` · `core/status_store.py write_status()` | `regress_all.py` |
| I2 | **임시 파일 이름에 PID + 스레드 번호를 넣는다** | PID 만 쓰던 때 한 서버 안의 두 요청이 같은 임시 파일을 써서, 동시 46요청에서 **판정 40건이 사라지고 500 이 3건** 났다. 2026-09-18 · paint3 2차 | `write_status()`·`backup_status()`·`api_boxes()` | 없음 ⚠ (구조4 제안: 동시 저장 시험) |
| I3 | 상자·번호는 **파일별 자물쇠**(`boxes:<과일>:<stem>`·`inst:<과일>:<stem>`) | 같은 사진을 두 요청이 동시에 쓰지 않게 | `api/boxes.py`·`api/instances.py` | 없음 ⚠ |
| I4 | ⚠ **자물쇠가 작업별로 나뉘어 «번호 저장 ↔ 브러시 저장» 사이는 막히지 않는다** — **마지막 쓴 쪽이 이긴다** | «한 사진에 한 사람이면 무해» 로 두고 최소 수정은 Codex 질문으로 넘겼다. 2026-09-17 · **상자번호판정 §4-(다) · §10-3** → 8절 «알려진 한계» | 같음 | 없음 ⚠ |
| I5 | 요청 크기 상한 **64 MB**(`MAX_CONTENT_LENGTH`) · 넘으면 413 | 2MP 수정본 PNG 는 수백 KB 다. 그보다 훨씬 큰 요청은 사고다 | `app/server.py`(`app.config["MAX_CONTENT_LENGTH"]`) · 값은 `core/paths.py MAX_UPLOAD_BYTES` | 없음 ⚠ |
보안 관련 값·설정 세부는 공개본에서 생략했습니다.
| I7 | **경로 훑기 차단** — `?job=../x` 같은 값은 **404** | 툴 폴더 밖 파일이 열리지 않게. 2026-09-18 · **paint3 §2** | `core/util.py short_path()` · `api/export.py api_export_status()` | `t1_api.py` |
| I8 | `GET /api/health` 는 로그인 없이 열려 있지만 **폴더 경로·PID 는 로그인한 사람에게만** 준다 | 살아 있는지 확인은 누구나, 서버 내부 경로는 아무나 안 된다 | `api/dashboard.py api_health()` | `tests/run_all.sh` |
| J1 | **요소 id 를 지우거나 바꾸지 않는다** — 자리만 옮긴다 | `app.js` 가 id 로 붙고 **회귀 시험이 그 구조를 글자 그대로 잘라 쓴다**. 2026-09-18 · paint1 §3 | `app/static/index.html` — **그대로**. 다만 `<script>` **순서**가 의존 방향이자 시뮬의 입력이 됐다(`tests/sim/lib/load_bundle.js`) | `tests/sim/*.js`(`sim`·`boxsim`·`modesim`) |
| J2 | **`ui.js` 는 상태를 가로채지 않고 0.2초마다 «읽어서» 화면만 맞춘다** | `app.js` 의 단축키·`setNumMode`·`#box-mode onchange` 를 회귀 시험이 글자 그대로 떼어 돌린다. 그 안에 새 호출을 넣으면 시험이 깨진다 | 🔄 **규칙이 바뀐다** — `ui.js` 가 없어졌다. 0.2초마다 읽는 것은 `js/view.js tick()` 이고 등록은 `js/main.js`. «가로채지 않는다» 는 그대로 | `tests/sim/modesim.js`·`boxsim.js` |
| J3 | **상자 모드와 번호 편집 모드는 동시에 켜지지 않는다** · 번호 모드에서는 브러시·다각형이 잠긴다 | 두 편집이 섞이면 저장 규칙이 꼬인다 | `js/instances.js setNumMode()` · `js/boxes.js`(`#box-mode` onchange) | `tests/sim/modesim.js` |
| J4 | **사진 «밖» 회색 여백을 눌러도 «고쳤다» 딱지가 켜지지 않는다** — 한 화소라도 바뀐 뒤에만 | 전에는 여백 클릭으로 **안 고친 마스크가 `masks_fixed` 로 저장되고 판정이 `fixed`** 가 됐다. 2026-09-18 · **paint1 §1(2차가 잡은 것)** | `js/mask.js`(stamp·strokeTo 의 `touched`) · 마우스 손잡이는 `js/main.js` | `tests/sim/sim.js` · `t2_ui.py` |
| J5 | **편집 화면 밖에서는 `Ctrl+S`·`Ctrl+Z`·`Ctrl+Y` 가 먹지 않는다** | 목록·현황 탭에서 눌러 «마지막으로 본 사진» 에 판정이 저장됐다. 2026-09-18 · **paint3 §1(2차가 잡은 것)** | `js/keys.js` 단축키 갈래(`#view-edit` 숨김 검사) | `tests/sim/modesim.js` |
| J6 | **단축키 표는 한 곳에** 있고 화면 단추의 `title` 풍선말과 같은 글자를 쓴다 | 두 군데에 적으면 갈라진다. (구조 사이클 3 이 `keys.js` 로 모은다) | ✅ **한 곳이 됐다** — `js/keys.js` 의 `KEYS` 표. `tests/unit/u7_keys_doc.py` 가 표↔`help.html`↔손잡이 코드를 대조한다(69항목) | `tests/sim/modesim.js` |
| J7 | 서버가 모르는 값은 화면이 **«모른다» 고 말한다** — `개수 ?·?·?` · «서버가 아직 이 기능을 모릅니다» | 정적 파일이 서버보다 먼저 나갈 수 있다. **없는 숫자를 지어내지 않는다.** 2026-09-19 · count1 §1 «결정 4» | `js/counts.js renderCntChip()` · `js/export.js` | `t2_ui.py` |
| J8 | 마스킹 편의 3가지(붓 크기 기억 · 자동 확대 · 기본 도구)는 **전부 브라우저 localStorage** — 서버는 모른다 | 사람마다 다른 취향을 공용 파일에 쓰지 않는다. 2026-09-18 · paint4 | `js/mask.js brushKey()`·`loadBrush()` · `js/list.js openStem()` · `js/view.js`(패널 접기) · `js/boxes.js`(초벌 출처) · `js/tour.js`(안내 본 표시) | `t2_ui.py`(⚠ «창을 완전히 닫았다 열어도 남는가» 는 **사람만** 확인 가능 — paint4 §1) |
| J9 | 긴 설명은 화면에 쓰지 않고 **풍선말(`title`)과 `help.html`** 로 보낸다(편집 화면 글자 1,088자 → 138자) | 1366×768 노트북에서 판정 단추 5개가 **0개 → 5개 전부** 보이게 됐다. 2026-09-18 · **paint1 §1** | `index.html` `title` · `help.html` | `t2_ui.py` |
| K1 | **팀 표준 2MP 규격** — 비율 유지 · 총 화소를 **1440×1440 = 2,073,600** 에 맞춤(±0.15%) · 변은 **8의 배수** → 실제 해상도 **5종**(1440×1440·1920×1080·1080×1920·1664×1248·1248×1664) · 이미지 **LANCZOS** · 마스크·번호 **NEAREST** · 가로세로비가 **0.5% 넘게** 다르면 **채택하지 않는다** | 0806 교수님미팅 지시(`tools/resize_datasets_to_common_pixels.py`). 보간하면 **없는 라벨값이 생긴다**. ⚠ **이 규칙은 툴 사이클 판정서에는 없습니다**(12개 판정서에 «2MP» 문구 0건) — 근거는 코드와 0806 미팅입니다 | `semantic-segmentation/tools/build_merged_dataset.py` `SPEC_*`·`spec_target_size()` | `tools/tests_merged_260918/`(`run_all.sh --only merged`) |
| K2 | 🔴 **확정 없는 툴 상자 json 은 통합본이 채택하지 않는다** — `boxes_source=tool_unconfirmed` 로 **표시만** 한다 | 확정하지 않은 초벌 저장본이 정답 상자를 덮으면 안 된다. 확정이 없으면 채택 순서는 **박성문 gt > 임성후**. 툴과 통합본이 확정을 **같은 규칙으로** 보게 한 것(2026-09-19 02:06 통합 스크립트 수정). 2026-09-19 · **방향전환판정 §6 «3차가 이번에 결정한 것» · §1-3** | `build_merged_dataset.py` 1241~1270행 | `tools/tests_merged_260918/` |
| K3 | 확정된 툴 상자가 **0개(빈 json)** 면 «그대로(상자 0개) 채택» 하고 manifest 에 그 사실을 적는다 | 사람이 «열매 없음» 을 확정한 것과 «아직 안 봄» 을 구별한다 | `build_merged_dataset.py` | `tools/tests_merged_260918/` |
| K4 | 통합 manifest 의 개수 6칸은 **그 폴더에 실제로 나간 파일을 센 값**이다(툴 저장분이 아니라) | 규격을 맞추다 번호가 사라질 수 있다. 세 구현이 갈라지지 않는지 대조한다 | `build_merged_dataset.py` | `tools/tests_merged_260918/counts/test_counts.py`(세 구현 대조) |
| K5 | **통합본은 복숭아 번호본을 «추정» 으로 표기해 넣는다**(`instances_source=psm_watershed` · 블루베리와 같은 취급) | 통합 스크립트가 복숭아 번호본을 몰라 빠져 있었다. 2026-09-19 · **count4 §1 «통합 스크립트가 복숭아 번호본을 모름» 행 · §3**(사이클 5 에서 추가 · 0920 빌드 내용이 바뀜) | `build_merged_dataset.py` | `tools/tests_merged_260918/` |
| K6 | 팀원 산출물은 **읽기 전용**이다 — `bbox_outputs/`·`apple_check/` 에 한 글자도 쓰지 않는다 | 남의 폴더다 | `api/boxes.py TEAM_BOX_DIRS` · `api/instances.py PARK` · `api/instances.py ERROR_CSV` | 없음 ⚠ (`tests/run_all.sh` 가 규칙으로 적어 둠) |
| K7 | 원본 데이터셋(`<데이터 루트>/<과일>/{images,masks}`)은 **읽기만** 한다 | 이 툴의 첫 번째 약속이다 | 전체(쓰기는 `data/`·`app/cache/`·`exports/` 뿐) | `tests/run_all.sh`(모래상자 규칙) |
| L1 | 🔴 **낙과(땅에 떨어진 과실)와 뒷줄 나무 열매는 손대지 않는다** — 칠해져 있으면 지우지 말고, 없으면 새로 칠하지 말라. 상자·번호도 같다 | 원논문 두 편은 «빼라» 고 적었는데(MinneApple p.4 «the ones **on the ground** and trees in the background **were not tagged**» · `seo2024peach` p.5 «except for dropped fruits») **우리 사과 라벨에는 낙과가 남아 있다**(낙과가 보이는 **42장 중 5장**). 규칙이 없는데 사람마다 손대면 **되돌릴 수 없다**. 2026-09-19 · **count2 §2 M7·M11 → count3 §2-4 → count4 §1** · 교수님17건 **10번** | README §10 · `help.html` · 그림 캡션 · 사람확인표 | 없음(사람) |
| L2 | **포도 번호 기능을 켜지 않는다**(교수님 확인 8번 전) | F5·F6 과 같은 까닭 | `api/instances.py` `SEED_DIRS` 주석 | `regress_all.py`(꺼짐 확인) |
| L3 | **상자 «전부 지움» → 저장** 은 확정을 푸는 뜻이다(되돌리기다) — 실수로 누르지 말라 | D1 | README §10 · 화면 1초 힌트 | `t2_ui.py` |
| L4 | **`boxes_yolo/` 의 낡은 txt 는 사람이 지운다** — 툴은 개수만 알려 준다 | 파일 삭제를 툴이 하면 되돌릴 수 없다 | README §10 | 없음(사람) |
| L5 | **시험 잔재 2개**(`data/peach/boxes/210629-t4-17.json` · `data/grape/boxes/740.json`) 삭제는 사람 몫 | 공용 `data/` 에서 지우는 일은 툴이 하지 않는다 | `260917_지울목록_시험잔재.md` · count4 §3 | 없음(사람) |
| L6 | **이름 칸에 «AI…» 로 시작하는 이름을 쓰지 않는다** | `/api/status` 는 400 으로 막지만 `/api/save`·`/api/save_instances` 는 **아직 막지 않는다**(N8 미결 · 오표시 · 데이터 소실 아님). 2026-09-18 · paint4 §1 «갈림길 2» · 상세 `cycles/260918_paint/cycle_5/stage2_review.md:312·640·653` | 8절 «알려진 한계» | `t1_api.py` 마-2(`/api/status` 만) |
| L7 | **블루베리 번호 저장 보류 · 사과에서 브러시로 넓힌 뒤 번호 저장 금지** — ⛔ **이 둘은 폐지된 임시 규칙입니다** | N6 수정 전(2026-09-17)의 임시 사람 규칙이었고, **2026-09-18 N6 2차 독립 재현으로 해제**됐습니다. 지금은 지키지 않아도 됩니다. 남아 있는 것은 «포도 켜지 않기»(L2) 하나입니다. 상자번호판정 **§3 마지막 · 머리말 «후속(2026-09-18)»** | 상자번호판정 · 사람확인표 H | — |

## 6. 시험과 모래상자

```bash
bash tests/run_all.sh                       # syntax·unit·sim·api·merged
bash tests/run_all.sh --browser             # 실제 Firefox까지, 전체 회귀
bash tests/run_all.sh --no-merged --only=syntax,unit,sim,api
bash tests/run_all.sh --only=api             # API만
```

로그는 `tests/_out/logs/`, 표는 `tests/_out/bundles.tsv`, 시험 산출물은 `tests/_sandbox/`입니다.
한 폴더에서 전체 시험을 둘이 동시에 실행하면 같은 산출물이 섞입니다. 각자 별도 복사본을 씁니다.
브라우저는 `scripts/ff.py`입니다. `LABELTOOL_URL`을 생략하면 실행 전에 멈춥니다. 반드시 `LABELTOOL_URL=http://127.0.0.1:<모래상자포트>`를 설정하며
보안 관련 값·설정 세부는 공개본에서 생략했습니다.
보안 관련 값·설정 세부는 공개본에서 생략했습니다.

기준선은 `tests/fixtures/baseline_260920/`입니다. API JSON·내보내기 sha256는 유지해야 합니다.
`--check-baseline`은 HTML/JS 원시 지문까지 엄격 대조하므로, 이번 분리판에서는 알려진 6칸 차이로 rc=1입니다.
그것을 정상 성공으로 적지 마세요. 원래 기준선을 다시 떠서 지우지 말고 구조 5 전환 판정을 확인합니다.
검수한 정적 변경만 고정 해시로 허용하는 별도 관문은 `--structure-baseline`입니다.
이 관문도 원래 API JSON·내보내기 sha256·나머지 라우트는 그대로 대조하고, 임의의 새 정적 변경은 실패합니다.
전체 회귀와 기준선 검증은 서로 다른 결과입니다.

현행 시험 도구에는 임시 폴더 삭제가 들어 있습니다. 이 인수인계 작업에서는 별도 보존 래퍼를 사용해
삭제 대신 `_archive/`로 옮깁니다. `--clean`을 그대로 실행하지 마세요. 보존 목록은
`cycles/260920_structure/codex_resume/_archive/moves.jsonl`입니다.

로컬 자료 의존: `datasets_reviewed_260916`, `datasets_resized_2mp`, 팀원 초벌 파일,
`semantic-segmentation/tools/tests_merged_260918`. 공개 저장소에는 이 데이터가 없습니다.
백업 호환 시험은 `_archive/backups_260920`도 읽습니다. 원본·남의 폴더는 읽기만 합니다.

## 7. 작은 수정 레시피

### 상자 저장 응답에 칸 하나 추가 (인수인계 연습)

1. **연습 복사본**의 `app/api/boxes.py`에서 `api_boxes_save()`를 찾습니다.
2. 상자 저장 성공 응답의 `jsonify({"ok": True, ...})`의 사전에 `"handoff_probe": True`를 추가합니다.
   요청 검증·저장·확정 코드는 바꾸지 않습니다. 빈 목록 응답과 성공 응답은 다릅니다.
3. 별도 API 시험으로 유효한 상자 하나를 저장하고 응답의 새 칸이 true인지 확인합니다.
   저장된 상자 JSON에는 새 칸이 추가되지 않았는지도 확인합니다.
4. `bash tests/run_all.sh --browser`를 다시 실행합니다. 연습은 응답 변경이므로 기존 API 기준선 차이는
   의도된 결과입니다. 연습 파일은 제품 후보에 합치지 않고 따로 보관합니다.

### 그 밖의 수정

| 일 | 고칠 자리·확인할 것 |
|---|---|
| 과일 추가 | core/paths.py FRUITS·dataset_for, domain/dupes/팀원 경로, 화면 state.js FRUIT_KO·목록. 데이터·초벌 출처와 없는 기능 처리를 먼저 정한다 |
| 확정 종류 추가 | domain/statusfmt.py CONFIRM_KINDS, core/status_store의 confirm/clear, API 및 export 필터, 화면 TASKFIELD. 한 칸 추가로 끝나지 않는다 |
| 색 바꾸기 | static/js/state.js COL. 원본/AI/수정본 구분 유지, 브라우저 범례·그림 대조 |
| JS/CSS/HTML 수정 | 정적 파일은 서버 재시작 없이 바로 나간다. **모래상자에서 먼저** 확인 후 전체 파일을 함께 전환한다 |
| Python 수정 | 프로세스는 옛 코드를 유지한다. 검증 후 운영 담당자가 run.sh restart로 한 번 다시 켠다 |

## 8. 한계와 결정 기록

- 사람 확정이 0건이라는 옛 초안은 틀렸습니다. 2026-09-19 22:55 복숭아 flag 확정이 한 건 생겼습니다.
  현재 개수는 운영 데이터에서 다시 세어야 하며, 문서의 고정 숫자를 진행률로 쓰지 않습니다.
- 같은 사진을 여러 탭/사람이 고칠 때 스레드 잠금은 있지만 오래된 화면의 저장을 revision으로 막지는 않습니다. 협업 편집·변경 이력 시스템이 아닙니다.
  과일이나 사진 구간을 나눠 맡으세요. 상태 쓰기 잠금은 한 프로세스 내부 스레드용입니다.
- 포도 번호 초벌은 교수님 확인 전 꺼져 있습니다. 포도 자동 개수를 정답으로 쓰지 않습니다.
  사과의 출처별 modal/amodal·시퀀스 분할·간격 솎기, 낙과 제외 등은 교수님 결정이 남았습니다.
- 공개 함수 타입을 보완했지만 복합값 Any가 남고 타입 검사기로 전체를 검증한 것은 아닙니다.
  긴 함수 3개, JS window 연결 5개·역방향 호출·단축키 표/분기 중복은 미완 목록입니다.
- 일부 오래된 사이클 시험은 백업 이동 후 직접 실행이 깨집니다. 재현할 때 tests/의 정리된 시험을 씁니다.
- sim.js의 손으로 쓴 배율 예제는 현재 boxes.js의 실제 함수를 대체하지 않습니다.
- 데이터 소실 예외 수정 1건: 전부 무효인 상자 요청은 400으로 거절하고 기존 파일·확정을 보존합니다.
  `codex_resume/safety_fix/`에서 잘못된 요청 3종과 명시적 빈 목록 되돌리기를 별도로 검증했습니다.
  이 한 가지 오류 응답은 의도적으로 달라집니다. 원래 고정 표본 API·내보내기 지문도 별도로 대조합니다.
- 논문 근거는 `문서/260919_논문근거_대조표.md`, 카운팅 판정은 `문서/260920_상자카운팅_5회검수_최종판정.md`입니다.
  구조 판정은 `cycles/260920_structure/cycle_1~5/stage3_final.md`에서 완료된 것만 읽습니다.

이전 결과(2026-09-20 03:23, 당시 기록): 새 사람 규칙 찾기7초, 서버+시험8분33초, 응답수정+시험8분11초로 합격했습니다.
최신 전체 단정1,124/0이나 **원래 엄격 기준선 정적6칸/rc1로 운영 코드 전환은 보류**했습니다.
원시 API24응답·내보내기60파일이 같다는 별도 증거도 있습니다. 운영 서버에 후보 보호수정이 적용됐다고 생각하지 마세요.
추가 미결: Infinity/NaN 좌표 요청은 기존·후보 모두500이며 파일은 보존합니다. 이 비소실 오류처리는 후속 목록입니다.
판정: `문서/260920_툴_구조정리_5회검수_최종판정.md`, `문서/260920_Codex검수_최종종합.md`.

## 2026-09-20 마무리 최신 상태

최종전체회귀 1193/0·501초·rc0. 원래기준선은보존했고정적6칸차이는사용자승인으로새기준선에반영했다. Infinity/NaN좌표는이제400과오류메시지이며기존파일을보존한다. 전부무효상자보호·URL누락보호도운영파일에반영했다. 후보타입·설명16파일전부반영했다. 다만실행중PID1467097은옛코드이며전환은사람이한다. cycles/260920_structure/finish_260920/전환하기.md와260920_마무리_보고.md를읽는다.
