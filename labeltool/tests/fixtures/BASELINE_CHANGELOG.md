대행: Codex
작성: 2026-09-20

# 기준선 변경 이력

승인자 곽동신. 2026-09-20 08:2x «진행해줘», 마무리 지시 C-9에 명시된 승인이다. 사이클3 화면 분리로 정적3주소의 bytes와 sha256, 총6칸이 바뀌었다. 옛 기준선은 baseline_260920_pre_split/에 원본 그대로 복사 보존했다.

원래 기준선이 통과한 것이 아니다. 정적6칸 차이를 사람이 승인해서 전환 가능 상태로 본다. 12장 스크린샷·36상태·콘솔0·탭8/8은 기존 독립 근거이며 이번12장 재검증은 finish_260920/evidence/에 별도로 남긴다.

새 스냅샷 수집 명령은 bash tests/run_all.sh --only baseline --rebaseline. 이 명령은 회귀 묶음을 실행하지 않으므로 bundles.json의 원래15묶음 기준은 그대로 복원·유지했다. 임계값을 없애거나 완화하지 않았다. API 지문·내보내기·표본은 원본과 바이트 동일. 코드지문은 참고용 변경이며 동작 관문과 구별한다.

| 변경 칸 | 이전 값 | 새 값 | 관련 이전 sha256 | 관련 새 sha256 |
|---|---|---|---|---|
| /r_page_box/bytes | 29900 | 31724 | f515913144feb6d53af9b09f2ff6e23c9b7650f81e87a4ea8e5efb198b333ce7 | 45a680a8f04ab87f3e29d9912eb96eab6694efddf20c17c92ad89c06a9471eb6 |
| /r_page_box/sha256 | f515913144feb6d53af9b09f2ff6e23c9b7650f81e87a4ea8e5efb198b333ce7 | 45a680a8f04ab87f3e29d9912eb96eab6694efddf20c17c92ad89c06a9471eb6 | f515913144feb6d53af9b09f2ff6e23c9b7650f81e87a4ea8e5efb198b333ce7 | 45a680a8f04ab87f3e29d9912eb96eab6694efddf20c17c92ad89c06a9471eb6 |
| /r_page_index/bytes | 29900 | 31724 | f515913144feb6d53af9b09f2ff6e23c9b7650f81e87a4ea8e5efb198b333ce7 | 45a680a8f04ab87f3e29d9912eb96eab6694efddf20c17c92ad89c06a9471eb6 |
| /r_page_index/sha256 | f515913144feb6d53af9b09f2ff6e23c9b7650f81e87a4ea8e5efb198b333ce7 | 45a680a8f04ab87f3e29d9912eb96eab6694efddf20c17c92ad89c06a9471eb6 | f515913144feb6d53af9b09f2ff6e23c9b7650f81e87a4ea8e5efb198b333ce7 | 45a680a8f04ab87f3e29d9912eb96eab6694efddf20c17c92ad89c06a9471eb6 |
| /r_static_app_js/bytes | 145377 | 1578 | 0f58ea45601660c9b9f71e7f6d179f3c7cf52be39065578745c1777819523f4f | 2674b4bf3cad4fa2c95360abe8ad8d7e45b2a0d8dba6d15368bc0d61dec805c9 |
| /r_static_app_js/sha256 | 0f58ea45601660c9b9f71e7f6d179f3c7cf52be39065578745c1777819523f4f | 2674b4bf3cad4fa2c95360abe8ad8d7e45b2a0d8dba6d15368bc0d61dec805c9 | 0f58ea45601660c9b9f71e7f6d179f3c7cf52be39065578745c1777819523f4f | 2674b4bf3cad4fa2c95360abe8ad8d7e45b2a0d8dba6d15368bc0d61dec805c9 |

2026-09-20T13:14:15.240651 최종 보완. 별도검수에서발견한 core/domain8개타입·설명누락을반영한코드로전체1193/0·501초·rc0을확인했다. 그뒤 python tests/baseline/snapshot.py --rebaseline을한번더실행하여참고용코드지문도최종파일로맞췄다. 원래API·산출물·표본동일과정적6칸의전후값을다시확인했고원래15묶음임계값은그대로유지했다.

## 2026-09-20 쉽게 만들기

사용자 요청 문서260920_툴_쉽게만들기_지시.md가 승인한 UI 변경이다. 기존 기준선은 baseline_260920_pre_easy에 원본 그대로 복사했다. API100개와 내보내기119개는 바이트 동일, routes118개 중 아래 정적 응답2개만 bytes·sha256이 바뀌었다. 나머지 쓰기 계약은 동일하다. 기존 전체 시험 묶음 문턱은 유지했다. 원래 기준선 통과라고 주장하지 않는다. u6은 기존37주소를 그대로 검사하며 승인된 GET읽기 주소2개만 추가 허용한다.

| 응답 | 이전 SHA256 | 이후 SHA256 | 이전/이후 바이트 |
|---|---|---|---|
| r_page_box | 45a680a8f04ab87f3e29d9912eb96eab6694efddf20c17c92ad89c06a9471eb6 | a76729de0b889ad210b52f986cc793c33d79b5f27cd773e8121fa302b722d91f | 31724/34604 |
| r_page_index | 45a680a8f04ab87f3e29d9912eb96eab6694efddf20c17c92ad89c06a9471eb6 | a76729de0b889ad210b52f986cc793c33d79b5f27cd773e8121fa302b722d91f | 31724/34604 |

## 2026-09-21 21:22 편의·안정성 사이클 (Z1)

대행: Claude Opus. 근거는 사용자가 2026-09-21 10:45 에 낸 요청이다
(`cycles/260921_편의/plan.md` 「사용자 요청 원문 요약」 — 그림판·포토샵 관습으로 편하게 · 안정성도
같이). 그 요청이 승인한 UI 변경 스물넷(S1~S7 · U1~U10 · G1~G7)을 마치고 뜨는 기준선이다.
옛 기준선은 `--rebaseline` 이 스스로 `_baseline_prev/260921_212202/` 에 옮겨 두었다(지우지 않았다).

**원래 기준선이 통과한 것이 아니다.** 아래 6칸을 한 칸씩 까닭까지 확인한 뒤 전환했다.

- **넷은 index.html 이다.** 34,699 → 36,144 바이트. 늘어난 1,445 바이트는 이 사이클이 넣은
  **다섯 줄**과 정확히 같다 — S5 `js/backup.js` script +139 · U1 `js/dirtymark.js` script +125 ·
  U2 `#zoompct` 두 줄 +313 · U7 단축키 겹창 +828 · U8 슬라이더 풍선말 +40.
  다섯 줄이 지금 파일에 다 있는 것을 세어 확인했다(34,699 + 1,445 = 36,144, 실측 파일 크기와 같다).
  두 주소가 같은 값인 것은 `/` 와 `/box` 가 같은 문서를 보내기 때문이다(전부터 그랬다).
- **둘은 복숭아 마스크다 — 코드가 아니라 사람이 고쳤다.**
  `data/peach/masks_fixed/210629-t2-18.png`(mtime 2026-09-21 12:05:37) ·
  `210629-t2-of11-01.png`(12:05:40). 사람이 그 시각에 실서버에서 판정한 두 장이고,
  라운드 3의 기록과 시각까지 맞는다. ⚠ ⑤ 의 `after_masks_fixed__*` 칸은 **사람 자료를 따라
  흔들린다**(얼린 것은 status.json·duplicates.json 뿐이다) — 다음에 또 붉어지면 먼저 이것을 보라.

**임계값을 없애거나 완화하지 않았다.** 옛 ③ 과 새 ③ 을 칸마다 대어 **내려간 묶음 0개 ·
사라진 묶음 0개**임을 확인했다. 오히려 올랐다 — merged 535/실패1 → **536/실패0** ·
sim/boxsim 50 → 69 · unit/u4 7 → 8 · unit/u5 42 → 43, 그리고 묶음이 15 → **27** 로 늘었다
(새 열둘: api/t3·t4 · sim/backupsim·brushsim·dirtysim·leavesim·locksim ·
unit/u6·u7·u8·u9·u10). 옛 ③ 이 merged 를 «실패 1» 로 적고 있었는데 지금은 0이다 —
그때 로그가 안 남아 있어 무엇이었는지는 단정하지 않는다.

**①·②·표본은 바이트까지 같다** — `api_sha256.txt` 11,012바이트 · `exports.json` 9,058바이트 ·
`stems.json` 313바이트가 옛 사본과 한 글자도 다르지 않다(즉 API 응답 100개와 내보내기 지문
119개는 이 사이클 내내 안 바뀌었다). ④ 코드 지문은 참고용이라 당연히 바뀐다.

**근거로 삼은 실행** — `tests/run_all.sh` 전체를 **세 판** 돌려 전부 `1,358개 단정 0 실패 · rc=0`
(344초 · 357초 · 380초). 새 기준선으로 다시 대조하니 **①②③④⑤ 다섯 칸 모두 0개**다.
진짜 브라우저(`--browser`)는 Z2 몫이라 여기 안 들어 있다 → Z2 가 돌면 browser 묶음 세 줄이
③ 에 «없던 묶음» 경고로 뜬다(실패가 아니다).

| 칸 | 이전 값 | 새 값 |
|---|---|---|
| r_page_index/bytes · r_page_box/bytes | 34699 | 36144 |
| r_page_index/sha256 · r_page_box/sha256 | 259d0d87509cfda657b69379e5ec08259259d12657acd77a778d2ad76dfa25c5 | ecf6ad225dcdf61b447c3043dbab41267ebf8c656b44e86fe6746d1de3653020 |
| after_masks_fixed__peach/210629-t2-18.png | 2c9ce7d458156a6040e0ac8b706658ed28ac899d7cd13608905acd5a75cc14b2 | 811471f38ae7f94f21ec9638e43a565cd44a85d462f0006145f60e716ec8bf14 |
| after_masks_fixed__peach/210629-t2-of11-01.png | c614d7bde29be4c69ea04f8228a6e32e915d8fa03e752c8f1dfd0a1e71dd3f05 | 64b908f9a2ef83daee846f8fdcac5872980d4ad280a20fde4ad323071191cee0 |
