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
