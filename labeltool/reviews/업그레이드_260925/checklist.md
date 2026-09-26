작성: 2026-09-25

# 체크리스트 — 260925 업그레이드
형식: `- [ ] 태그 ID 내용 {after:태그,태그}` · 진행 중은 `[~레인]` · 끝은 `[x]`.
`{after:...}` 가 있으면 그 태그들이 모두 끝난 뒤에만 시작한다. 새 항목은 **해당 구역 맨 아래**에 추가.

## 조사·수집 (지금 바로 병렬)
- [x] 팀원 T01 팀원 작업환경 전수 확인 — `platform/work/{choi_inhun,im_seonghu,park_seongmoon}` 와 `/data/project/2026summer/{jjw0602,lsh0616,nsm0404,plant,dup_review,defect-seg-benchmark}` (읽기만). 09-22 이후 바뀐 것 · 우리 툴/초벌/데이터에 가져올 만한 코드·결과·아이디어 목록 → `문서/260925_팀원작업환경_조사.md`, 가져올 것은 `코드` 항목으로 추가(최대 6). (대화 세션 09-25, 결과 문서 있음 — 상위 6개 중 열매번호 편집 기능은 이미 그림판 K·나누기에 일부 있는지 w1 이 확인 후 코드 항목화)
- [x] 녹취 N01 녹음 txt 전부(`platform/00_meetings/*.txt`, `연구실 블루베리/06_교수님미팅_기록/*.txt`) 에서 툴·라벨·데이터셋·논문에 관한 지시를 날짜별로 뽑아 지금 툴과 대조 → `문서/260925_녹취지시_툴대조.md`, 빠진 것은 `코드` 항목으로(최대 5). (r1 09-25)
- [x] 조사 R01 논문(`연구실 블루베리/01_*`, `03_*`) + 인터넷(2024~2026 라벨링 도구·SAM2/대화형 분할·CVAT·Label Studio·과일 인스턴스) 조사 → 우리 그림판에 넣을 기능 순위(jev 로 점수 매기기) → `문서/260925_라벨링툴_리서치.md`, 상위는 `코드` 항목으로(최대 6). (r1 09-25)
- [x] 설계 F01 실제 브라우저(Playwright)로 그림판 전체 UX·속도·접근성 감사(스킬 make-interfaces-feel-better·accessibility·performance-optimization 참고) → `문서/260925_그림판_감사.md`, 고칠 것은 `코드` 항목으로(최대 8). (f1 09-25) — 파이어폭스·크로미움 오류 0 · 코드 C06~C13 추가 · 재기: `auto/f1_sandbox.sh` + `auto/f1_audit.mjs`
- [x] 데이터 D01 `datasets_merged_260924`(후보) 와 정본 `datasets_merged_260918_v3` 비교(장수·번호·바뀐 사진 목록) → `문서/260925_데이터셋0924_비교.md`. 정본 전환은 사람 몫이라 권고만. (r1 09-25)
- [x] 제미나이 M01 `연구실 블루베리/03_참고논문_리뷰` 를 훑어 라벨링 도구·인스턴스 분할·SAM 관련 내용만 요약. (r1 09-25)
- [x] 문서 S01 지금 사용법 문서(`문서/260923_그림판툴_사용법.md`)가 실제 화면·단축키와 맞는지 점검 → 틀린 곳 목록(`auto/S01_사용법점검.md`). (r1 09-25)

## 코드 (w1 만 고침) — 기준선 먼저
- [x] 코드 C00 기준선 측정 — `tests/run_all.sh --only unit,api` · `tests/browser/run_paint_e2e.sh <레인포트>` 통과 확인 + 성능(첫 화면 로드 ms · 사진 넘김 ms · ✨ 첫 클릭 ms)을 `auto/baseline_260925.md` 에 기록. (w1 09-25)
- [x] 코드 C01 카운팅 100장 표본 모드 — 과일별 결정적 표본 100장 목록과 «n/100 확정» 진행률을 그림판에 (녹취 09-08 G74) (근거: 문서/260925_녹취지시_툴대조.md · app/static/paint/paint.js renderList/#only-todo) (w1 09-25)
- [x] 코드 C02 그림판에서 닮은 사진 표시·«대표만 남기기» — 현재 사진이 중복 묶음이면 이름표+단추, 옛 툴 API 재사용 (녹취 09-15 G78) (근거: app/api/dupes 의 /api/duplicate_preview · 문서/260925_녹취지시_툴대조.md) (w1 09-25)
- [x] 코드 C03 사람 확정 수·마지막 내보내기 시각 표시와 내보내기 링크(재학습 고리의 첫 단계) (녹취 09-08 G73) (근거: app/api/export.py /api/export_list · 문서/260925_녹취지시_툴대조.md) (w1 09-25)
- [x] 코드 C04 512 크롭 박스 표시 토글 — 낮은 우선순위 (녹취 08-10 G42) (근거: app/static/paint/paint.js · 문서/260925_녹취지시_툴대조.md) (w1 09-25)
- [x] 코드 C05 사과·포도 규칙 한 줄 도움말(교수님 답 나오기 전엔 «미정» 표기) — 낮은 우선순위 (녹취 09-15 G78) (근거: 문서/260917_교수님확인_7건.md · 문서/260925_녹취지시_툴대조.md) (w1 09-25)
- [x] 코드 C06 다음·이전 사진 미리 받기(/img·/mask·/instances) — 넘김 0.4~1.1초(로컬)를 0 에 가깝게 (근거: 문서/260925_그림판_감사.md §2 · cycles/260925_업그레이드/auto/f1_audit/*.json · app/static/paint/paint.js openPhoto) (w1 09-25) — 1.5초 본 뒤 넘김 크로미움 0.13~0.16초 · 파이어폭스 복숭아 0.18 · 사과 0.45초(전 0.53~0.97) · C19 의 화면 쪽 조건 포함
- [x] 코드 C07 /instances 응답 캐시(파일 지문) 또는 ETag/304 — 매 사진 서버 0.2~0.3초 (근거: app/api/instances.py serve_instances · 문서/260925_그림판_감사.md §2) (w1 09-25)
- [x] 코드 C08 팔레트 색 칸 .sw·#curbox·#who 를 키보드로(button 또는 tabindex+Enter/Space) — 지금 17개가 Tab 으로 못 감 (근거: 문서/260925_그림판_감사.md §3 · app/static/paint/paint.js renderPalette · index.html) (w1 09-25)
- [x] 코드 C09 보조기기 알림·상태: #msg/#loading aria-live · 도구·원본보기 aria-pressed · 메뉴 aria-haspopup/expanded · 과일·사진·찾기 aria-label · 탭 제목에 사진 이름 (근거: 문서/260925_그림판_감사.md §3 · app/static/paint/index.html · paint.js setTool/applyView/openPhoto) (w1 09-25)
- [x] 코드 C10 메뉴 키보드: 열린 메뉴 ↑↓ 이동 · Esc/선택 뒤 초점을 메뉴 단추로 되돌리기(지금 body 로 사라짐) (근거: 문서/260925_그림판_감사.md §3 · app/static/paint/paint.js keydown Escape) (w1 09-25)
- [x] 코드 C11 글자 대비 AA: #msg.err 4.06 · #msg.ok 4.32 · 제목줄 «저장 안 됨» 2.9 → 4.5 이상 · 도구 이름 11px→12px (근거: 문서/260925_그림판_감사.md §3 · app/static/paint/paint.css) (w1 09-25)
- [x] 코드 C12 작은 화면: #msg 두 줄 허용 또는 잘릴 때 title 로 전체 · 1024×640 이하 도구 옵션 설명 접기 (근거: 문서/260925_그림판_감사.md §4 · auto/f1_audit/*_5_800x600.png · paint.css #statusbar>div, #toolbox) (w1 09-25)
- [x] 코드 C13 붓질 끝 긴 작업 117ms 줄이기(changed 의 computeCenters·팔레트를 바뀐 네모만 갱신 또는 requestIdleCallback) · ✨ 계산 중 커서 progress (근거: 문서/260925_그림판_감사.md §2 · auto/f1_audit/chromium.json perf.longtasks_ms · paint.js pushUndo/changed/samClick) (w1 09-25) — changed() 12~30ms→2~9ms(CR)·19~43→6~15ms(FF) · 재기: `tests/browser/perf_stroke.mjs`
- [x] 코드 C14 «비슷한 열매 한꺼번에 찾기» — 열매 하나를 누르면 SAM 자동 마스크 중 크기·둥근 정도·색이 비슷한 것을 후보로 보이고 «모두 받기» (리서치 1위 3.75) (근거: ai_helper/sam_server.py · app/static/paint/paint.js /api/sam 호출 · 문서/260925_라벨링툴_리서치.md) (w1 09-25)
- [x] 코드 C15 사진 목록 «불확실한 순서» 정렬 — 사람 미확정 + 초벌 열매 수와 원 라벨 수 차이 큰 순 (리서치 2위 2.78) (근거: app/static/paint/paint.js renderList · 문서/260925_라벨링툴_리서치.md) (w1 09-25)
- [x] 코드 C16 저장 뒤 의심 열매 표시 — 넓이·둥근 정도·겹침이 튀는 열매 (리서치 3위 2.65) (근거: app/api/instances.py · 문서/260925_라벨링툴_리서치.md) (w1 09-25)
- [x] 코드 C17 ✨ 결과가 잎·가지처럼 길쭉하거나 너무 크면 경고 (리서치 4위 2.35, 확신 낮음) (근거: app/static/paint/paint.js · 문서/260925_라벨링툴_리서치.md) (w1 09-25)
- [x] 코드 C18 사진당 작업 시간·수정 횟수 기록(app/logs 에만) — 논문에 «라벨링 시간 절감» 을 쓰기 위한 측정 (리서치 5위 1.93) (근거: app/api/instances.py · 문서/260925_라벨링툴_리서치.md) (w1 09-25)
- [x] 코드 C19 C06·C07 안전조건 — 미리 받은 /mask·/instances 는 저장 성공 때 그 사진 항목 삭제·layer/fromOriginal 별 키, 서버 캐시 지문은 고친 번호·초벌·원본·이진 마스크 mtime+size 전부, 저장 경로 load_inst 는 캐시 안 씀 (근거: 문서/260925_그림판_감사_두번째의견.md §2-1 · app/api/instances.py serve_instances/load_inst) (w1 09-25) — 서버·화면 조건 확인 + /api/item file_sig 추가(같은 초 저장도 잡음)
- [x] 코드 C20 키보드로 «비슷한 열매» 받기 막힘 — 팔레트 색 칸(role=button)에 초점이 있으면 G 뒤 Enter 가 «모두 받기»(simAccept) 대신 그 색 칸을 다시 눌러 도구가 붓으로 바뀐다(Tab→색 칸→Enter→G→Enter 순서 그대로, 파이어폭스·크로미움 둘 다). S.sim 이 있을 때는 색 칸 Enter 보다 simAccept 를 먼저 하거나, G 뒤 초점을 «모두 받기» 단추로 옮기기 (근거: tests/browser/e01_sam_neg_keyboard.mjs «B 색 칸에 초점이 있어도 Enter = 모두 받기» · tests/_out/e01/e01_*_result.json · app/static/paint/paint.js keydown 1432줄 role=button 분기가 1445줄 S.sim Enter 보다 앞) (w1 09-25)
- [x] 코드 C21 목록 다시 그리기가 저장 확인 없이 사진을 바꿈 — «안 한 것만» 이 켜진 채 저장(✓)한 뒤 다시 칠하고 «이름 순/헷갈리는 순» 을 바꾸면(또는 «안 한 것만» 을 켜거나 이름 찾기 Enter) renderList 가 지금 사진을 목록에서 빼고 첫 사진을 openPhoto 로 열어 안 저장한 칠이 사라진다. openPhoto 는 dirty 를 안 본다. 1384줄 주석(«순서만 바뀌고 지금 사진은 그대로») 은 필터가 있을 때 틀림. renderList 안에서 want≠S.stem 이고 S.dirty 면 leaveOk 를 거치거나(취소 = 정렬·체크 되돌리기), dirty 인 지금 사진은 필터에서 빼지 않게 (X01 높음 1 확인) (근거: app/static/paint/paint.js renderList 203~204줄 · 1383~1385줄 · openPhoto 268줄) (w1 09-26)
- [x] 코드 C22 저장 중 편집이 막히지 않아 파일 넷이 서로 다른 상태를 담음 — save() 는 /api/save(이진, 호출 때 계산)→/api/status→/api/save_instances(번호, 두 번 기다린 뒤 계산)→/api/boxes(상자, 세 번 기다린 뒤 계산) 순서인데, 그 사이 Ctrl+Z/Y(undo·redo)·Enter «모두 받기»(simAccept)·N(newNumber)·초벌 더하기(loadDraft)·번호 나누기(splitBy)·전부 지우기 는 S.busy 를 안 봐서 L 이 바뀐다(붓·채우기는 mousedown 1094줄에서 막힘). 결과 ① 이진 마스크와 번호 PNG 불일치 ② 저장 끝의 setDirty(false) 가 그새 한 편집을 «저장됨» 으로 가림. 고침: 첫 await 앞에서 encodeBinary·encodeInstances·boxesNow 를 한 번에 만들고, 위 진입점에 S.busy 검사 (X01 높음 2 «추정» → 코드로 확인) (근거: app/static/paint/paint.js save 1199~1224줄 · undo/redo 544~545줄 · simAccept 868줄 · loadDraft 896줄 · splitBy 928줄 · newNumber 985줄) (w1 09-26)
- [x] 코드 C23 ✨ «비슷한 열매» 본보기의 바깥 네모가 칸 T 보다 크면 도우미가 400 — 같은 번호가 멀리 떨어진 두 조각이면(C16 이 «떨어진 조각» 으로 잡는 경우) exemplarOf 의 네모 높이가 10·d 를 넘어 fy>ey0 이 되고, `big[ey0-fy: …] = em[:T-(ey0-fy), …]` 의 음수 슬라이스로 «could not broadcast (639,60) into (161,60)» → 사용자에겐 «비슷한 열매 찾기 실패». numpy 로 재현함(H1500·W2000·본보기 60×800·조각 30×30 둘). 양쪽 좌표의 교집합만 복사하고, 본보기가 칸보다 크면 잘라 쓰기 (X01 중간 4 확인) (근거: ai_helper/sam_server.py _similar 152~156줄 · app/static/paint/paint.js exemplarOf 795줄) (w1 09-26)
- [x] 코드 C24 /api/worklog 가 "NaN" 을 못 거름 — `min(max(float("NaN"),0),1e6)` 은 NaN 그대로이고 int(NaN) 은 try 밖에서 ValueError → 500, `_s` 칸은 round(NaN,1) 이 worklog.jsonl 에 비표준 `NaN` 으로 적힘. Infinity 는 1e6 으로 잘려 괜찮음. float 변환 뒤 math.isfinite 검사, 아니면 0 (X01 중간 5 확인, 낮음 — 화면은 숫자만 보내고 실패도 알리지 않음) (근거: app/api/instances.py api_worklog 680~685줄) (w1 09-26)
- [x] 코드 C25 작업 시간(worklog active_s)이 긴 드래그를 못 잰다 — wlTick 은 pointerdown·keydown·wheel 만 듣고(paint.js 571줄) 한 간격을 60초까지만 더하므로, 붓·올가미로 60초 넘게 끌면 다음 입력에서 60초만 합산된다. pointermove(또는 붓질 중 changed 호출)도 활동으로 세되 100ms 이하로 묶어 부하를 막기. 로그 정확도만의 문제라 화면 기능은 그대로 (X02 지적 2 확인 — f1 09-26, Z01 뒤 등록이라 다음 사이클 몫. X02 지적 1 «번호 65535» 은 F02 에서 이미 뺀 것과 같음) (근거: auto/X02_codex.md · app/static/paint/paint.js wlTick 562·571줄) (w1 09-26)

## 시험
- [x] 시험 E01 ✨ Shift+클릭(떼어 내기)·키보드만으로 한 장 끝내기 자동 시험을 `tests/browser/` 에 추가(모래상자에서만). 실패하면 `코드` 항목으로 버그 등록. {after:팀원} (w1 09-25) — `tests/browser/run_e01.sh [5441]` · 파이어폭스·크로미움 각 27/28, 못 넘은 1개 = C20 등록
- [x] 시험 E02 코드 항목 전부 끝난 뒤 전체 회귀(`tests/run_all.sh` · `--browser` · paint e2e) 다시 돌려 결과 기록. {after:코드} (w1 09-25) — 그림판 e2e 138×2·E01 27×2·run_all 브라우저 전 전부 통과. --browser 실패 4(b1 자료 바뀜·b15 가끔·b24⑩·t2_ui 다-3·마-1 은 사이클 전 코드도 같음) → `auto/E02_회귀_260925.md`

## 교차 검토
- [x] 제미나이 M02 `문서/260925_그림판_감사.md` 에 대한 두 번째 의견(빠진 것·과한 것). {after:설계} (r1 09-25) → 문서/260925_그림판_감사_두번째의견.md
- [x] 코덱스 X01 (공격적 검토) `cycles/260925_업그레이드/snapshot_before/` 와 지금 `app/`·`ai_helper/` 코드의 차이를 읽고 버그·회귀·보안 문제를 찾아라. {after:코드}
- [x] 검수 F02 X01 지적 + 직접 검토 → 진짜인 것만 `코드` 항목으로(최대 5). {after:코드} (f1 09-26) — 5건 중 4건 진짜 → C21~C24 등록, «번호 65535 도달» 은 뺌(한 사진에서 새 번호 6만 개는 불가능·components 는 이미 HOLE-1 로 막음)
- [x] 코덱스 X02 (보통 검토) 최종 코드 차이를 다시 읽고 남은 문제만. {after:검수}

## 문서·마무리
- [x] 문서 S02 사용법 문서 갱신(바뀐 기능 반영, `최종 수정:` 갱신) (카톡 초안은 쓰지 않음 — 사용자 09-26 지시). {after:코드,검수} (r1 09-26) → 문서/260923_그림판툴_사용법.md 갱신(S01 틀린 곳 A1~A4 고침·A5 숫자는 근거 없어 뺌·빠진 단축키·C01~C24 기능 반영)
- [x] 마무리 Z01 전체 회귀 통과 확인 → 공개 저장소 반영·push(force 금지, 비밀검사 `audit_public.py`) → `작업기록.md` 갱신 → `auto/ALL_DONE`. {after:코드,시험,문서,코덱스,검수,조사,녹취,팀원,데이터,제미나이,설계} (f1 09-26) — C25 뒤 최종 코드로 회귀 다시 돌림(`tests/_out/z01_2/`): run_all --browser 2,344/7(실패 7 = E02 기준선과 같은 b1×4·b24⑩·t2_ui 다-3·마-1, 사이클 전 코드도 같음) · 그림판 e2e 파폭·크로미움 286/0 + 디스크 대조 통과 · E01 27/27×2. 공개 사본 `prepare_public.py` 545 파일 → `audit_public.py` 통과 → 커밋·push(해시는 auto/STATUS.md 마지막 줄)
