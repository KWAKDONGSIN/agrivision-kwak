작성: 2026-09-19

# «상자 + 개수 세기» 사이클 1 — **3차 판정 전 소수정**(Opus 5)

총괄(Fable)이 채택한 결정 **1~4 만** 최소로 넣었다. 2차 즉시 수정 6건은 **한 글자도 건드리지 않았다.**
2차 보고서 `cycle_1/stage2_review.md` §3(즉시 수정)·§4(3차 이관)·§6(켜기) · 1차 `cycle_1/stage1_work.md`.
작업 시각(실측 `date`): 시작 **16:09:57** · 코드 끝 **16:18:54** · 회귀 끝 **16:38**.
모래상자 `cycle_1/stage2c/{sandbox, sandbox_old, sandbox_guard, c4reg3, sb_chars_cnt1c_*}`
(포트 5371~5378 · 127.0.0.1) · 스크린샷 `~/ff_shots/cnt1/stage2c/`.
**실서버 5111(PID 3915126, 11:57:48 시작)에는 붙지도·켜지도·로그인하지도 않았다**(`ps`·`ss` 로 살아 있는 것만 봤다).

---

## 0. 한눈에

| 결정 | 한 줄 | 고친 파일 | 늘고 줄음 |
|---|---|---|---|
| **1** | 어긋나면 `n_human` 을 **비운다**(`source="conflict"`) | `app/boxes.py` · `tools/build_merged_dataset.py` · 화면·문서 | +16/−8 · +15/−6 |
| **2** | `counts.csv` 는 **그 job 이 나간 사진**만 담는다 | `export/export_dataset.py` | +74/−38 |
| **3** | 센 값을 **캐시에 적는다**(다음 열기 0.32 ms) | `app/instances.py` · `app/server.py` | +19/−0 · +3/−2 |
| **4** | **확정이 있으면 초록이 이긴다** · 옛 서버 가드는 `개수 ?` | `app/static/ui.js` · `help.html` | +21/−11 · +10/−3 |
| 문서·시험 | README §19 · 대조시험 · 2차 공격 스크립트 기대값 | `app/README.md` · `test_counts.py` · `stage2/a1_rules.py` | +44/−13 · +18/−5 · +33/−17 |

새 단정 `stage2c/c1_fix.py` — **전(前) 실패 → 후(後) 통과**를 네 결정마다 한 번씩. **22 / 0.**
백업은 전부 같은 폴더에 `_backup_260919_cnt1c_<파일명>` 으로 남겼다(8개 + 시험 2개).

---

## 1. 항목별 — 무엇을·어디를·전/후

### 1-1. 결정 1 — 어긋나면 `n_human` 을 비운다

규칙이 있는 자리는 **`app/boxes.py human_count()` 한 군데**이고, 통합 스크립트만 같은 규칙을
다시 구현한다(일부러 — 그쪽은 툴 `app/` 을 import 하지 않는다).

```python
# app/boxes.py  (+16 / −8)
    conflict = bool(ok_b and ok_i and n_boxes != n_instances)
    if conflict:
        return None, "conflict", True        # 총괄 결정 1 — 사람이 봐야 한다(툴이 고르지 않는다)
    if ok_i:  return n_instances, "instances", False
    if ok_b:  return n_boxes, "boxes", False
    return None, "", False
```

| 어디 | 전(前) | 후(後) |
|---|---|---|
| `human_count(16, 15, "fixed", "ok")` | `(15, "instances", True)` | **`(None, "conflict", True)`** |
| 화면 `/api/item` 의 `counts` | `human=2 · source=instances · conflict=true` | **`human=null · source=conflict · conflict=true`** |
| `counts.csv` 그 줄 | `n_human=2 · human_source=instances · confirmed_by=<사람>` | **`n_human="" · human_source=conflict · confirmed_by=""`** |
| `counts.csv` «사람 확정만» | 그 사진이 **남는다** | **빠진다**(사람이 고칠 때까지) |
| 통합 `manifest.csv` | `n_count_human=15 · count_source=instances` | **`n_count_human="" · count_source=conflict`**(`count_conflict=1` 은 그대로) |
| 풍선말 | «사람 확정 개수: 2개 (번호 확정에서 나왔습니다)» + «툴은 고르지 않습니다» | **«사람 확정 개수: 비워 둡니다 — …고칠 때까지 counts.csv «사람 확정만» 과 카운팅 지표에서 빠집니다»** |

- 실측 사진: 사과 `20150919_174730_image241`(상자 3 · 번호 2 · 둘 다 확정).
- 같은 문구가 `app/README.md §19-2`·`static/help.html #cnt`·통합 README 생성부에 들어갔다.
- **왜**: 2차 §2-6-가 실측 — 코드는 «툴은 고르지 않습니다» 라고 적어 두고 **번호 쪽을 골라**
  표에 실어 보냈다. 사람이 16과 15 중 어느 쪽인지 고르지 않은 수를 MAE·RMSE·R² 표에 넣으면
  그것이 사후 정당화다(2026-08-13 경고). 문구를 고치는 대신 **코드를 문구에 맞췄다.**

### 1-2. 결정 2 — `counts.csv` 를 «나간 사진» 으로 제한

`export_one()` 안에만 있던 «왜 빼나» 판단을 **`exclude_reason()` 한 함수로 꺼내고**(판단 내용은
한 줄도 바꾸지 않았다 — 옮기기만 했다), 그것을 쓰는 `included_stems()` 를 더했다.

```python
# export/export_dataset.py  (+74 / −38)
def exclude_reason(s, rec, args, rep_of): ...      # manifest 와 counts.csv 가 같이 쓴다
def included_stems(fruit, args, st=None): ...      # 파일을 하나도 읽지·쓰지 않는다
def counts_rows(fruit, confirmed_only=False, st=None, only=None): ...   # only = 나간 사진
def write_counts_csv(fruit, out, args, st=None, only=None):             # 안 주면 스스로 구한다
    if only is None: only = included_stems(fruit, args, st=st)
...
    inc = {r[0] for r in rows if r[1] == "포함"}    # export_one 은 자기가 센 목록을 그대로 넘긴다
```

| 실측(모래상자 · «사람 확정만» + 마스크 + 개수) | 전 | 후 |
|---|---|---|
| `manifest.csv` 의 «포함» | 1장 (`…image251`) | 1장 (같음 — **내보내는 사진은 한 장도 안 바뀌었다**) |
| `counts.csv` 줄 | **4줄** (`image241·246·251·256`) | **1줄** (`image251`) = 포함과 **완전히 같음** |
| 마스크 «제외» 확정 사진(`…image256`) | counts.csv 에 **남았다**(`n_human=5`) | 없다. manifest 에는 «제외 · confirmed_exclude» 로 그대로 남는다 |

- «개수» 만 골라 내보내면 사진은 한 장도 안 나가지만, 표는 **같은 옵션이면 나갈 사진**과 같다
  (`write_counts_csv` 가 `included_stems()` 를 스스로 부른다 — 서버 `export_worker` 의 «개수만» 갈래).
- `only=None` 이면 예전처럼 거르지 않는다 — 규칙만 보는 시험(대조시험 [나2])이 그 길을 쓴다.
- **가정 한 가지**: 총괄 문구 «사람 확정만이면 n_human 있는 사진 / AI 제안 포함이면 그 job 이
  내보낸 사진» 을 **두 모드 모두 «나간 사진» 으로 제한**하고 «사람 확정만» 은 거기에 `n_human`
  조건을 더하는 것으로 읽었다(제목이 «counts.csv 는 «나간 사진» 으로 제한» 이고, 2차 §4-2 의
  문제 자체가 «사람 확정만» 에 «제외» 확정 사진이 남는 것이었다).

### 1-3. 결정 3 — 센 값을 캐시에 적는다

```python
# app/instances.py  (+19 / −0)
def count_now(fruit, stem):
    sig = sig_of(fruit, stem)          # 세기 «전» 의 지문(mtime+크기) — recount() 와 같은 규칙
    n = count_one(fruit, stem)
    cache = dict(load_counts(fruit)); cache[stem] = [n] + sig
    try: save_counts(fruit, cache)     # 원자적 교체. 못 써도 개수는 돌려준다
    except Exception: pass
    return n if n is not None and n >= 0 else None
```
`server.counts_of()` 와 `export counts_rows()` 가 `count_one` 대신 이것을 부른다(+3/−2, +1/−2).

| 실측(사과 한 장) | 전 | 후 |
|---|---|---|
| 캐시 기록 | `None`(아무리 열어도 안 적힌다) | `[2, 1786019007.133, 1786019007.133]` — 지문이 **지금 파일과 같다** |
| `/api/item` 두 번 | **235.0 → 233.1 ms**(두 번 다 다시 센다) | **10.9 → 10.1 ms**(캐시 적중) |
| 한 장 세는 값 ↔ 캐시 적중 | `count_one` **218.1 ms** | `count_fresh` **0.32 ms** |

- 즉 **한 장당 218 ms 를 딱 한 번만** 내고, 그 뒤로는 0.32 ms 다(복숭아 66 ms·블루베리 약 0.6초도 같다).
- ⚠ **GET 이 파일을 쓰는 유일한 자리**다. 쓰는 것은 개수 캐시(`app/cache/instance_counts/<과일>.json`)
  **하나뿐**이고 `status.json`·마스크·번호본은 건드리지 않는다. 2차 [아] 시험(`/api/item` 20번에
  `status.json` 이 한 바이트도 안 바뀐다)은 **그대로 통과**한다.
- 정직하게: 위 «후» 의 첫 호출 10.9 ms 는 이미 캐시가 차 있던 상태다(모래상자를 다시 맞출 때
  `rsync --exclude cache` 라 캐시 폴더가 살아남는다). 캐시가 비어 있으면 첫 호출은 218 ms 를 한 번 낸다.

### 1-4. 결정 4 — 색 우선순위 · 옛 서버 가드 (진짜 파이어폭스 1366×768)

```js
// app/static/ui.js  (+21 / −11)
const hum = c.human !== null && c.human !== undefined;
el.className = "cnts" + (hum ? " hum" : (ne ? " ne" : ""));   // 확정이 있으면 초록이 이긴다
...
el.textContent = m ? "개수 ?·?·?" : "개수 -·-·-";             // 옛 서버는 «?» · 사진 안 고름은 «-»
```

| 사진 | 전 | 후 | 스크린샷 |
|---|---|---|---|
| 상자만 확정(3) · 번호 1 | `개수 3≠1·1` **노랑**(`cnts ne`) — 확정했는데 초록이 아니다 | `개수 3≠1·1` **초록**(`cnts hum`) | `chip_green_ne_{old,new}.png` |
| 둘 다 확정 · 어긋남 | `개수 3≠2·2` 노랑 · 풍선말 «사람 확정 개수: 2개» | `개수 3≠2·2` 노랑 · 풍선말 «**비워 둡니다**» | `chip_conflict_{old,new}.png` |
| 옛 서버(개수 기능 없음) | `개수 -·-·-` (**«다 없는 사진» 과 같은 글자**) | **`개수 ?·?·?`** (8자 ↔ 8자, 글자 수 같음) | `guard_{old,new}_ui.png` |
| 아무 확정 없음 | `개수 -·-·5` 회색 | 같음 | — |

- **글자 예산**: 편집 화면(`#view-edit`) **마스크 +0 · 상자 +0 · 번호 +0자**(`stage2c/t3_chars_cnt1c.py` 6/0,
  전·후 모두 162·253·225자). 개수 칸 글자도 그대로(`개수 -·-·95` 10자). 늘어난 것은 **풍선말뿐**이고
  어긋난 사진에서만 379 → 418자다.
- 눈으로 봤다: `chip_green_ne_new.png` 하단 오른쪽 «개수 3≠1·1» 이 초록 · `guard_new_ui.png` 의
  «개수 ?·?·?» 가 회색 — 1366×768 에서 **줄바꿈·가로 스크롤 0**.

---

## 2. 2차 즉시 수정 6건 — **무변경 확인**

A-1(개수 캐시 지문) · D-1(`cntReload()`) · E-1(0장 폴더) · B-1(같은 스냅샷) · C-1(빈 폴더 딱지) ·
F-1/G-1(문서·기대값)은 **한 줄도 되돌리지 않았다.** 2차의 검증 스크립트 `stage2/a5_fixed.py` 를
그대로 다시 돌려 **8 / 0**(2차와 같은 수). 결정 3 은 A-1 이 만든 `count_fresh()` 위에 얹은 것이고,
결정 2 는 B-1 이 넘기기 시작한 `st` 스냅샷과 같은 자리에 `only` 를 하나 더 넘기는 모양이다.

---

## 3. 회귀 — 돌린 것 전부

| 무엇 | 2차가 적은 값 | 이번 | 판정 |
|---|---|---|---|
| `node --check` 2 · `py_compile` 6 · `python app/boxes.py` | 통과 | **통과** | 같음 |
| `counts/test_counts.py` | 61 / 0 | **62 / 0** | 기대값 갱신(아래) |
| 통합 4묶음 `test_build_merged`·`confirm_kinds`·`spec`·`fix_m5c` | 68·200·106·67 = **441 / 0** | **68·200·106·67 = 441 / 0** | 같음 |
| `build_merged_dataset.py --dry-run`(`-W error::DeprecationWarning`) | exit 0 · 429 / 2,403 / 125 / 1,114 | **exit 0 · 429 / 2,403 / 125 / 1,114** | 같음 |
| 복숭아 부분 빌드 md5 vs v3 | `images dc036154…` · `masks 14e28b7d…` · `boxes 768e1143…` | **셋 다 같은 해시 · 바이트 동일** | 같음 |
| 그 manifest | 125행 `n_boxes`=`n_gt` · 합계 977 · `count_source` 전부 none | **같음**(`n_count_human` 빈칸 125) | 같음 |
| c4 `t1_api` · `t2_ui` · `regress_all` | 34/0 · 27/0(경고1) · 99/0(경고9) | **34/0 · 27/0(경고1) · 99/0(경고9)** | 같음 |
| `sim.js` · `modesim.js` · `boxsim.js` | 통과 · 31/31 · 50/50 | **통과 · 31/31 · 50/50** | 같음 |
| 2차 `a5_fixed.py`(고친 뒤) | 8 / 0 | **8 / 0** | 같음 |
| 2차 `a1_rules.py`(기대값 갱신) | 18 / 2 | **18 / 2** | 같음(아래) |
| 글자 예산 | 마스크 162 · 상자 253 · 번호 225자 | **같음 · 증가 +0자** | 같음 |
| 🆕 `stage2c/c1_fix.py`(전→후) | — | **22 / 0** | 새 단정 |

- **`test_counts.py` 61 → 62**: 기대값을 결정 1 로 갱신하면서 «어긋나면 비운다» 검사를 새로 넣고
  (전 기대값은 주석으로 남겼다), «번호 확정이 먼저다» 를 **수가 같은 짝**으로 다시 물어(출처로 확인)
  둘이 됐다. 결정 2 검사(`only=`)도 하나 더 넣었고, 어긋난 모래상자 사진 `c02_both_diff` 는
  이제 확정 개수가 없어 «confirmed_by·at» 검사가 한 개 줄었다(+2 −1 = +1 → 62). **규칙 격자 1,296
  조합은 그대로 전수 통과**한다(툴 ↔ 통합 두 구현이 갈라지지 않았다).
  덧붙여 [다] 의 «n_human 이 있는 줄만이다» 가 `r[5]`(= `n_gt` 칸)를 보고 있어 이름과 다른 것을
  재고 있었다 — `COUNTS_COLS.index("n_human")` 으로 고쳤다(칸이 늘면서 어긋난 자리다).
- **`a1_rules.py` 18/2 는 2차와 같은 수이고 같은 두 항목**이다([다] 되돌리기 1·2). 원인은 코드가
  아니라 **시험 자료**다 — `server.py:1325` 가 `if os.path.exists(inst_fixed_path(...))` 일 때만
  되돌리므로, 번호 수정본을 한 번도 저장하지 않은 사진에서는 되돌릴 것이 없다(2차 §2-7 이 그
  동작을 «정상 🟢» 으로 적었다). 내가 고친 네 곳과 무관하다.
  ⚠ 그 스크립트를 다시 돌렸으므로 `stage2/a1_rules.json` 은 **지금 값**으로 덮였다(2차의 옛 값은
  `stage2_review.md` §2-1·§4-1 에 글로 남아 있다). 스크립트 자체 백업은 `_backup_260919_cnt1c_a1_rules.py`.

---

## 4. 🔴 켜기 — 순서 · 켠 뒤 GET · 사람 눈으로 볼 것

### 4-1. 지금 실서버가 어떤 상태인가 (켜기 전에 알 것)

- 5111(PID 3915126)은 **11:57:48**에 뜬 서버다 = 사이클1 **이전** 코드. `/api/item` 에 `counts` 칸이 없다.
- 정적 파일(`app/static/*`)은 **다시 켜지 않아도 이미 나가고 있다.** 그래서 지금 실서버 화면은
  옛 서버 + 새 화면이고, 개수 칸이 **`개수 ?·?·?`** 로 보인다(내가 그 조합을 모래상자 5373 에서
  그대로 재현해 확인했다 — `guard_new_ui.png`). 오류가 아니라 «서버가 아직 모른다» 는 뜻이다.
- 2차 §6-1 이 알린 대로 작업 트리에는 **개수 말고 «수정본 색 초록 → 하늘색»** 변경도 들어 있다
  (다른 세션이 15:47:58 에 `ui.js`·`index.html`·`help.html` 을 고쳤다). 다시 켜면 그것도 함께 나간다.

### 4-2. 켜는 순서 (1차 §6 그대로 · `pkill -f` 금지)

```bash
cd /data/project/2026summer/platform/work/kwak_dongsin/260916_라벨링툴/app
bash run.sh restart          # 데이터 루트·포트 유지. 남의 5100·5101·5105 는 건드리지 않는다
tail -20 logs/server.log     # 뜨는 줄에 오류가 없나
```

### 4-3. 켠 뒤 GET (읽기만 · **실제로 있는 경로만**)

```
/api/health                                  # 먼저 이것부터
/api/fruits
/api/list?fruit=apple&page_size=20
/api/item?fruit=apple&stem=<위 목록의 이름>   # ← counts 칸이 **생겼는지**가 이번 확인의 핵심
/api/stats
/api/export_list
/api/export_plan?fruit=apple&confirmed_only=1
/api/boxes?fruit=apple&stem=<이름>
/api/boxes_stats
/api/instance_stats
```

`/api/item` 의 `counts` 가 이렇게 나오면 된다 — 어긋난 사진이면
`"human": null, "source": "conflict", "conflict": true`, 아니면 `"human": 15, "source": "instances"`.
(**켜기 전에는 `counts` 칸이 없는 것이 정상**이고 화면이 `개수 ?·?·?` 로 가려 준다.)

### 4-4. 사람 눈으로 볼 것 (2차 §6 의 다섯 + 이번 넷)

1. 하단 오른쪽 `개수 …` 가 **`?·?·?` 가 아니게** 바뀌었는가(= 서버가 개수를 안다).
2. 「데이터 정리」에 «개수(counts.csv)» 가 있고 그것만 골라도 저장되는가 · 목록에 «빈 폴더» 딱지가 없는가.
3. `/box` 전용 화면에서도 개수 칸이 보이는가.
4. 상자를 저장하면 칸이 **곧 초록**이 되는가 / 🧹 지워 저장하면 **회색**으로 돌아오는가.
5. 🆕 **상자만 확정한 사진에서 `개수 3≠1·1` 이 «초록 + ≠»** 인가(노랑이 아니다).
6. 🆕 **상자·번호를 둘 다 확정해 수가 다른 사진**에서 칸이 **노랑 + ≠** 이고, 마우스를 올리면
   풍선말이 «사람 확정 개수: **비워 둡니다**» 라고 말하는가.
7. 🆕 그 사진을 «사람 확정만» 으로 내보내면 `counts.csv` 에 **그 줄이 없는가**(고치면 다시 생긴다).
8. 🆕 「데이터 정리」에서 «사람 확정만» + 마스크 + 개수를 내보내고 **`counts.csv` 줄 수 =
   `manifest.csv` 의 «포함» 장수**인지 눈으로 맞춰 볼 것(이번 결정 2 의 핵심).
9. 🆕 번호를 확정한 사진을 **두 번째 열 때 눈에 띄게 빠른가**(첫 번째만 세고 캐시에 적는다).

---

## 5. 3차·사이클 4 에 남기는 것

- **사이클 4 로 미룬 셋**(총괄 결정 5): `export_worker` 의 상자 YOLO 갈래가 `read_status` 를 세 번째로
  읽는 것 · `/api/item` 의 옛 `n_inst` 칸(아직 지문을 안 보는 `cached_counts` 값) · `mk_reg_c4.py` 가
  있는 스냅샷을 그대로 다시 쓰는 것(정본에서 다시 복사해야 한다). **이번에 건드리지 않았다.**
- 4↔8 연결(대조표 1-f·M2) · 팀원 상자 좌표 1화소 · 1픽셀 상자가 YOLO 로 나가는 것 — **코드 무변경**.
- `counts.csv` 로 어긋남을 보고 싶으면 «AI 제안 포함» 으로 내보내야 한다(«사람 확정만» 에서는 빠진다).
  화면에서는 노랑 + `≠` 로 늘 보인다.

## 6. 만지지 않은 것

- 실서버 5111 — 붙기·재시작·로그인 **0회**. 교수님 5100·5101·5105 **0회**. `pkill -f` 0. 남의 geckodriver 0.
- 공용 `T/data`·`T/exports` **쓰기 0**(쓰기는 전부 `stage2c/sandbox*` 안) · 팀원 폴더 읽기만 ·
  원본·검수판·`datasets_merged_*` **무변경**(복숭아 재빌드는 `mktemp -d` 안에만) · 삭제 0 · GPU 0 ·
  새 패키지 0 · `작업기록.md` 갱신 0.
- 남의 사이클 폴더: **쓰지 않았다**(사이클4 회귀는 `stage2c/c4reg3/` 사본 · 포트 5374~5376).
  같은 사이클 안 2차 폴더에는 지시대로 `a1_rules.py`(기대값)만 고쳤고 백업을 남겼다.
