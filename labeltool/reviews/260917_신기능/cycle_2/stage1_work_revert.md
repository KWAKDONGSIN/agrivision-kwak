작성: 2026-09-17

# 0917 새 기능 5회 검수 — 사이클 2 · 1차 작업 (라) 번호 되돌리기 기록 정리

작업자: AI 1차(Opus 5) · 갈래 (라) · 고친 파일: `app/instances.py` **한 개뿐**
고치기 전 사본: `app/_backup_260917_c2d_instances.py`
서버는 재시작하지 않았다(다른 작업자가 `app/boxes.py` 를 고치는 중 — 실제로 시험 도중 14:38 에 그 파일이 바뀌었다).
확인은 전부 Flask `test_client` 로 했다.

## ① 합격 기준 (실행 «전» 에 정한 것)

| # | 기준 | 어떻게 판정하나 |
|---|---|---|
| 1 | 번호를 저장하면 `status.json` 항목에 `instances_edited: true` 와 편집 횟수(`instance_counts`)가 남는다 | 저장 후 `status.json` 을 직접 읽어 두 필드 확인 |
| 2 | 되돌리면 두 필드가 **사라지고** `status` 가 `unreviewed` 로 돌아가며 `instances_fixed/`·`masks_fixed/` 파일이 둘 다 지워진다 | 되돌린 후 `status.json` 에 두 키가 **없음** + 두 경로 `os.path.exists == False` |
| 3 | 번호 편집을 한 적 없는 사진은 되돌리기 호출로 이상해지지 않는다(원래 상태·메모·검수자·시각 유지, 없던 항목을 만들지 않는다) | 호출 전후 항목 **완전 일치**(dict 비교), 항목이 없던 사진은 계속 없음 |
| 4 | 복숭아처럼 번호가 없는 과일에서 기존 0/255 저장·되돌리기 흐름이 전과 같다 | `/api/save`(action=fixed) → `/api/revert` 가 고치기 전(old)·고친 뒤(new) 판에서 **같은 결과**, 그 흐름에 `instances_edited` 가 끼어들지 않음 |
| 5 | 시험은 사과 한 장으로만, 끝나면 되돌리기로 원상복구 | 실제 `data/` 에서는 `20150919_174151_image361` 한 장만 쓰고 파일 0개로 끝맺음 |

추가로 스스로 정한 기준 두 개(지적의 뿌리를 같이 막으려고):
- 6: 파일은 이미 없고 **편집 기록만 남은** 사진(= 고치기 전 판이 만들어 놓은 상태)도 되돌리기로 치워진다.
- 7: 되돌리기 응답의 기존 필드(`ok`·`removed`)가 그대로라 화면(`app/static/app.js`)이 안 깨진다.

## ② 한 줄 결론

`/api/revert_instances` 가 파일만 지우고 남겨 두던 `instances_edited`·`instance_counts` 를 **같이 지우게** 고쳤고,
덤으로 «되돌릴 것이 아무것도 없으면 status 항목을 건드리지 않게» 해서 번호 편집을 한 적 없는 사진의 상태·메모가
`unreviewed`/«번호 편집 되돌림» 으로 덮어써지던 것까지 막았다 — 고친 뒤 판 **28/28 통과**, 고치기 전 판은 같은 시험에서 **6개 실패**.

## ③ 바꾼 것

`app/instances.py` 의 `api_revert_instances` 한 함수만 (26줄 추가, 1줄 교체). `boxes.py`·`server.py`·`static/*`·`export/`·`README.md` 는 손대지 않았다.

1. **편집 기록 삭제** — `update_status(...)` 로 `unreviewed` 를 쓴 뒤 `st.pop("instances_edited")`·`st.pop("instance_counts")` 하고
   `ctx["write_status_entry"]` 로 항목을 통째로 덮어쓴다. 저장 쪽(`api_save_instances`)이 두 필드를 붙이는 것과 정확히 대칭이다.
2. **되돌릴 것이 없으면 아무것도 안 쓴다** — 지운 파일도 없고(`removed == []`) 편집 기록도 없으면
   `{"ok": true, "removed": [], "changed": false, "status": <원래 항목>}` 을 주고 `status.json` 을 **쓰지 않는다**.
   기존 항목을 읽는 데는 `DUP.read_status(fruit)` 를 쓴다(ctx 에 `read_status` 가 없고, 파일 위치는 `DUP.DATA_DIR` 로 이미 같은 값).
3. **파일은 없고 기록만 남은 경우도 치운다** — `instances_edited` 가 참이거나 `instance_counts` 키가 있으면 «되돌릴 것이 있다» 로 본다.
   고치기 전 판이 실제로 남겨 놓은 `data/apple/status.json` 의 잔재(아래 ④-0)가 이번 시험에서 이 규칙으로 정리됐다.
4. 응답에 `changed`(true/false) 를 **추가**만 했다. `app.js` 는 `j.ok` 와 `j.removed` 만 쓰므로(1917~1920줄) 화면은 영향 없다.

### ponytail (의도적 단순화)
- `update_status` 로 한 번 쓰고 곧바로 덮어써 지운다 → 두 번 쓰는 **사이**(같은 `inst:` 자물쇠 안이지만 `status:` 자물쇠는 놓은 상태)에
  다른 요청이 `status.json` 을 읽으면 기록이 아직 보일 수 있다. 저장 쪽도 원래 같은 방식이어서 맞춰 두었다.
  한 번만 쓰려면 `ctx` 에 `read_status`·`now_str` 이 필요해 `server.py` 를 고쳐야 하므로(내 범위 밖) 그대로 뒀다.
- `changed: false` 로 «아무것도 안 했다» 를 알리지만, 화면은 아직 이 필드를 보지 않는다(«되돌릴 것이 없습니다» 안내는 2차/3차에서 붙일 일).

## ④ 실행 증거

파이썬 `/home/kds0206/.conda/envs/kwak/bin/python`, 전부 `test_client`(서버 재시작·GPU 없음).
스크립트·로그: `cycles/260917_신기능/cycle_2/stage1_revert/{scripts,logs}/`

### ④-0 지적이 사실이었다는 증거 (고치기 전 판이 남긴 실물)
시험 시작 시점의 실제 `data/apple/status.json` — 파일은 없는데 기록만 남아 있었다(사이클2 앞 갈래의 시험 자취):
```
"20150919_174151_image361": {"at":"2026-09-17 14:30:45","by":"AI 사이클2 1차 시험",
  "instance_counts":{"add":1,"erase":1,"merge":1,"split":1}, "instances_edited":true,
  "note":"번호 편집 되돌림", "status":"unreviewed"}      <- 되돌렸는데 두 필드가 남아 있다
```

### ④-1 실제 `data/` · 사과 한 장 (기준 1·2·5) — 14개 확인, 실패 0
`logs/real_apple_once.log` / `scripts/real_apple_once.py`, 대상 `apple/20150919_174151_image361`(원본 번호 73개)
- 저장(`/api/save_instances`, 번호 1 지운 마스크 + `counts.erase=1`) → HTTP 200,
  항목 = `{"instances_edited":true,"instance_counts":{"erase":1,...},"note":"번호 편집 erase=1","status":"fixed"}`,
  `instances_fixed/`·`masks_fixed/` 둘 다 생김, 응답 `n_instances=72`(73→72 맞음). **기준 1 통과**
- 되돌리기(`/api/revert_instances`) → HTTP 200, `removed=["instances_fixed","masks_fixed"]`, `changed=true`,
  항목 = `{"at":"2026-09-17 14:41:37","by":"AI 사이클2 1차(라)","note":"번호 편집 되돌림","status":"unreviewed"}`
  → **두 필드 없음**, 파일 둘 다 삭제, 응답 안의 `status` 에도 두 필드 없음. **기준 2 통과**
- 끝맺음: `instances_fixed/`·`masks_fixed/` 모두 **빈 폴더**, `*.tmp*` 잔재 0개. **기준 5 통과**

### ④-2 모래상자 A/B — 고친 뒤(new) **28/28 통과**, 고치기 전(old) **6개 실패**
`logs/sandbox_new.log`·`logs/sandbox_old.log` / `scripts/ab_sandbox_test.py`
실제 `data/peach/status.json`(125항목)을 건드리지 않으려고 `app/`+`data/`(proposals 제외)를 scratchpad 로 복사해
`DUP.DATA_DIR` 이 복사본을 가리키게 만든 뒤(스크립트 첫머리에서 `"scratchpad" in DATA_DIR` 을 확인, 아니면 즉시 중단)
**같은 시험을 두 판에 그대로** 돌렸다. old 판은 `instances.py` 만 백업본으로 바꾼 것이다.

| 시험 | new | old(고치기 전) |
|---|---|---|
| 기준1 저장 후 두 필드 남음 (`apple/…image1`, 95개) | PASS 5/5 | PASS 5/5 |
| 기준2 되돌리기 후 두 필드 사라짐 | **PASS 6/6** | **FAIL 2** (`instances_edited`·`instance_counts` 그대로 남음) |
| 기준3-가 번호 편집 안 한 복숭아 `210629-t1-02`(status `ok`, 메모 «3회 검수 이상 없음») | **PASS** 항목 한 글자도 안 바뀜, `changed=false` | **FAIL 2** 항목이 `unreviewed`/«번호 편집 되돌림»/`by=판시험` 으로 **덮어써짐** |
| 기준3-나 status 항목이 없던 사과 `…image101` | **PASS** 계속 없음 | **FAIL** 없던 항목을 새로 만들어 버림 |
| 기준6 파일 없고 기록만 남은 사과 `…image106`(사람 메모 있는 `ok`) | **PASS** 두 필드만 사라짐 | **FAIL** 두 필드 그대로 |
| 기준4 복숭아 0/255 `/api/save`(fixed)→`/api/revert` (`210629-t1-03`) | **PASS 9/9** | **PASS 9/9** (똑같음) |
| 합계 | **28개 확인, 실패 0** | 28개 확인, **실패 6** |

기준 4 세부(두 판 동일): `instance_info.has=false`·`/instances` 404 (복숭아는 번호 마스크 없음) →
0/255 저장 시 `masks_fixed` 만 생기고 `instances_fixed` 는 안 생김·`status=fixed`·`instances_edited` **안 붙음** →
`/api/revert` 로 `removed=true`·파일 삭제·`status=unreviewed`·메모 «수정본 되돌림»·`instances_edited` 없음. **기준 4 통과**

### ④-3 곁가지 확인
- `python -m py_compile app/instances.py` 통과, `import server` 성공(라우트 `/api/revert_instances`·`/api/save_instances`·`/instances` 등록 확인).
- 두 필드를 쓰거나 읽는 곳은 `app/instances.py` **한 파일뿐**(`server.py`·`boxes.py`·`dupes.py`·`static/app.js`·`export/*.py` 전수 grep). **기준 7 통과**
- `/api/list` 의 항목 키는 `added_frac·at·by·dice·dup_group·has_fixed·missed_frac·note·status·stem·suspect·suspect_flags` 로
  두 필드를 **원래 실어 보내지 않는다**(실제 서버에 읽기 전용 GET 으로 확인). 즉 목록 화면이 틀어지던 경로는
  `/api/list` 가 아니라 **`status.json` 을 직접 읽는 쪽**(집계·내보내기·다음 사이클 스크립트)과 되돌린 뒤에도 남는 기록 그 자체다.

## ⑤ 남은 것

1. **서버 재시작이 필요한 확인은 2차에 위임** — 실제 브라우저에서 «번호 되돌리기» 단추를 눌러 목록 딱지·집계가 제자리로
   돌아오는지는 서버를 다시 띄워야 확인된다. 지금은 `boxes.py` 를 다른 작업자가 고치는 중이라 재시작하지 않았다.
2. **사람이 지울 자취(삭제 명령 금지 규칙에 따라 목록만 남김)** — `data/apple/status.json` 은 원래 없던 파일인데
   지금 항목 1개가 남아 있다:
   `20150919_174151_image361` = `{"at":"2026-09-17 14:41:37","by":"AI 사이클2 1차(라)","note":"번호 편집 되돌림","status":"unreviewed"}`
   시험 자취이므로 **파일째로 지워도 된다**(사과는 아직 사람 검수 기록이 없다). 파일 산출물은 남아 있지 않다(두 폴더 모두 빔).
   ※ 이 항목에 원래 붙어 있던 앞 갈래의 `instances_edited`/`instance_counts` 잔재는 이번 되돌리기로 정리됐다.
3. **`changed: false` 를 화면이 아직 안 쓴다** — «되돌릴 것이 없습니다» 안내를 붙일지는 화면 담당 갈래가 결정할 일.
4. **status 항목을 두 번 쓰는 것**(③ ponytail) 을 한 번으로 줄이려면 `server.py` 의 `ctx` 에 `read_status`·`now_str` 추가가 필요하다 — 서버 파일 담당 갈래에 넘긴다.
5. 모래상자 복사본은 scratchpad 안이라 프로젝트에 남지 않는다(세션이 끝나면 사라진다).

## ⑥ 2차 검수가 재현할 절차

```bash
PY=/home/kds0206/.conda/envs/kwak/bin/python
CY=/data/project/2026summer/platform/work/kwak_dongsin/260916_라벨링툴/cycles/260917_신기능/cycle_2/stage1_revert

# (1) 실제 data/ 에서 사과 한 장 저장→되돌리기 (14개 확인, 실패 0 이어야 한다)
#     data/apple/{instances_fixed,masks_fixed} 에 파일이 생겼다 사라지고, status.json 항목 1개가 남는다
보안 관련 값·설정 세부는 공개본에서 생략했습니다.

# (2) 고친 뒤 / 고치기 전 A/B — 모래상자를 만든 다음 두 판을 돌린다
SP=$(mktemp -d)/ab
$PY - <<'EOF'
import os, shutil
SRC="/data/project/2026summer/platform/work/kwak_dongsin/260916_라벨링툴"
SP=os.environ.get("SPDIR") or os.path.join(os.environ["TMPDIR"] if "TMPDIR" in os.environ else "/tmp", "ab")
for case in ("new","old"):
    root=os.path.join(SP,case); os.makedirs(root, exist_ok=True)
    shutil.copytree(os.path.join(SRC,"app"), os.path.join(root,"app"),
                    ignore=shutil.ignore_patterns("__pycache__","cache","logs"))
    shutil.copytree(os.path.join(SRC,"data"), os.path.join(root,"data"),
                    ignore=shutil.ignore_patterns("proposals"))
    if case=="old":
        shutil.copyfile(os.path.join(root,"app","_backup_260917_c2d_instances.py"),
                        os.path.join(root,"app","instances.py"))
EOF
보안 관련 값·설정 세부는 공개본에서 생략했습니다.
보안 관련 값·설정 세부는 공개본에서 생략했습니다.
```
- `ab_sandbox_test.py` 는 `DATA_DIR` 경로에 `scratchpad`(또는 지정한 모래상자) 가 없으면 `assert` 로 즉시 멈춘다.
  실제 `data/` 에 대고 돌리려면 그 안전장치를 먼저 확인할 것 — 복숭아 `status.json` 125항목이 걸려 있다.
- 되돌리기 응답 규약: `{"ok":true,"removed":[...],"changed":true|false,"status":{...}}`.
  `changed=false` 면 `status.json` 을 **쓰지 않았다**는 뜻이고, 그때 `status` 는 원래 항목(없으면 `{}`)이다.
- 서버를 다시 띄울 수 있게 되면 브라우저에서 사과 한 장을 편집·저장·되돌린 뒤 목록 딱지·`/api/stats` 를 눈으로 볼 것(⑤-1).
