# 디자인 최종안 — supabase DESIGN.md 를 이 툴에 맞게 옮긴다
작성: 2026-09-21

고른 것과 그 이유는 `design/후보비교.md`, 원본은 `design/DESIGN.md` (getdesign.md → VoltAgent/awesome-design-md).

## 지금 상태의 문제 (측정값)
`app/static/style.css` 에 **서로 다른 색이 133가지** 들어 있다(총 233번 등장). 파랑회색 계열만
`#22303f · #46596e · #3a4a5c · #425060 · #33475d · #35516e · #41566b · #55687d · #56667a …` 처럼
비슷한 것이 열 가지가 넘는다. 손으로 하나씩 고르다 쌓인 것이라, 어디를 고쳐도 옆 칸과 미묘하게 안 맞는다.
supabase 의 처방은 정확히 이 문제를 겨냥한다 — **무채색 계단 하나 + 강조색 하나**.

## 토큰 (이 값을 `:root` 에 선언하고, 앞으로 색은 여기서만 꺼낸다)
| 변수 | 값 | 어디에 |
|---|---|---|
| `--canvas` | `#ffffff` | 카드·패널·단추 바탕 |
| `--canvas-soft` | `#fafafa` | 목록·현황 화면 바탕 (지금 `#eef1f5`) |
| `--canvas-sunken` | `#f4f4f4` | 사진 주변 빈 공간 |
| `--chrome` | `#1c1c1c` | 상단 한 줄 (지금 `#22303f`) |
| `--chrome-soft` | `#202020` | 상단바 안의 눌린 칸 |
| `--chrome-ink` | `#ededed` | 상단바 글씨 |
| `--chrome-mute` | `#9a9a9a` | 상단바 흐린 글씨·구분선 |
| `--hairline` | `#dfdfdf` | 기본 1px 테두리 |
| `--hairline-strong` | `#c7c7c7` | 강조 테두리 |
| `--hairline-cool` | `#ededed` | 아주 옅은 칸 나눔 |
| `--ink` | `#171717` | 본문 글씨 |
| `--ink-mute` | `#707070` | 보조 설명 |
| `--ink-faint` | `#b2b2b2` | 비활성·자리표시 글씨 |
| `--accent` | `#3ecf8e` | **고른 도구 테두리 · 포커스 테두리 · 진행 표시만** |
| `--accent-deep` | `#24b47e` | 눌린 순간 |
| `--accent-wash` | `rgba(62,207,142,.12)` | 고른 도구의 옅은 배경 |
| `--r-xs` `--r-sm` `--r-md` `--r-lg` | `4px` `6px` `8px` `12px` | 입력칸 · 단추 · 카드 · 패널 |
| `--sp-1`…`--sp-5` | `2 4 8 12 16px` | 8px 기준 여백 |
| `--mono` | `ui-monospace, Menlo, Monaco, Consolas, "DejaVu Sans Mono", monospace` | 숫자·좌표·배율·개수 |
| `--shadow-1` | `0 1px 3px rgba(0,0,0,.06)` | 카드 살짝 띄우기 |
| `--shadow-3` | `0 16px 48px rgba(0,0,0,.12)` | 겹창(단축키 표 등) |

## 절대 바꾸지 않는 색 (데이터 의미가 묶여 있다)
- 레이어 4겹 — 빨강(원본) · 파랑(AI) · 초록(내 수정본) · 노랑·분홍(차이)
- 판정 5칸 — 원본 OK(초록) · AI로 교체(파랑) · 저장(진회색) · 문제(주황) · 제외(빨강)
- 목록 카드의 상태 딱지 색과 테두리 색
이 색들은 supabase 팔레트로 «예쁘게» 맞추지 않는다. 의미가 먼저다.

## 파일별로 할 일
1. `app/static/style.css` 맨 위에 `:root` 토큰 선언을 넣는다(주석으로 출처 한 줄).
2. **무채색만** 토큰으로 바꾼다. 파랑회색 10여 가지 → `--chrome*` · `--hairline*` · `--ink*` 로 접는다.
   데이터 색은 그대로 둔다. 한 번에 다 하지 말고 ① 상단바 ② 도구상자·패널 ③ 단추·입력칸 순서로 나눈다.
3. 반지름을 `--r-*` 로 통일한다. 지금 6px·8px 이 섞여 있어 거의 그대로다.
4. 포커스가 보이게 한다 — `:focus-visible { outline: 2px solid var(--accent); outline-offset: 1px; }`.
   지금은 포커스 테두리가 브라우저 기본이라 키보드로 쓰는 사람이 어디 있는지 모른다.
5. 숫자 칸(`#hud` · 배율 · `#cnts` · `#pageinfo` · `#listinfo`)에 `font-variant-numeric: tabular-nums` 와 `--mono` 를 준다.
6. `app/static/mobile.css` 의 `#22303f` 두 곳도 토큰으로.
7. 그림자를 줄인다. supabase 원칙은 «깊이는 1px 실선» 이다. 카드·패널의 그림자는 `--shadow-1` 까지만.

## 하지 않는 것
- Inter·Circular 웹폰트를 받지 않는다(CDN 금지·한국어 주). 지금 글꼴을 유지한다.
- 홍보 사이트 치수(48~64px 제목, 64~96px 여백)를 가져오지 않는다.
- 요소 id·단축키·HTML 구조를 건드리지 않는다. **CSS 만 고친다** → HTML 기준선 차이 0 이어야 한다.
- 에메랄드를 채움 단추로 쓰지 않는다(초록 = 내 수정본).

## 검증
- `bash tests/run_all.sh --check-baseline` → **HTML 기준선 차이 0** (CSS만 고쳤으므로 당연해야 한다)
- `bash tests/run_all.sh --browser` → 통과
- 화면 12장을 다시 뜬 뒤 **사람 눈으로** 대조. 색이 바뀌므로 그림 기준선은 새로 뜬다(그 사실을 기록에 남긴다).
- 폭 360·390 에서 상단바·판정 줄이 깨지지 않는지
- 쉬움 모드에서 «세 걸음» 안내와 판정 5칸이 그대로 잘 보이는지
