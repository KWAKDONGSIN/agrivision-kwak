작성: 2026-09-22 12:30 · 끝나면 `[x]` + 시각

- [x] (12:33) T1 저장 방식 실측(판정=즉시 서버 저장 · 마스크/상자/번호=Ctrl+S · 1분 브라우저 임시백업) → 답변 + 문서 §2
- [x] (12:32) T2 `문서/260922_툴_기술설명.md` 작성(기술 스택 · 구조 · 저장 경로 · 안전장치 · 시험 · 만든 과정 · 팀원 수정법 · 깃 권한)
- [x] (12:33, 6쪽 261KB, 쪽 그림 `pdf_pages/` 눈 확인) T3 `문서/260922_툴_기술설명.pdf` 생성(`semantic-segmentation/tools/make_tool_tech_pdf_260922.py`, pdfdoc) · 쪽 그림 눈 확인
- [x] (12:33, 모래상자 실측: restart.flag → run.sh restart 호출·플래그 삭제·로그 2줄) T4 팀원 편집: `scripts/watchdog.sh` 에 `restart.flag` 처리 추가 · 문법검사 · 감시자 크론이 그대로 도는지 확인 · 폴더 권한 실측
- [x] (12:37 prepare 481/6/83 · audit failures 0 · push 결과는 작업기록 §2) T5 공개 저장소 동기화(prepare_public → audit_public 비밀검사 → docs/ 에 md·PDF → 커밋 → deploy key push → `log -1 origin/main`)
- [x] (12:39) T6 카톡 초안 `문서/260922_카톡_툴기술설명.txt`(미발송) · 작업기록 갱신
- [x] (12:36) T7 (사용자 12:35 추가) 툴 «사진 한 장 검수하기» 설명 페이지(how_to.html)에서 «발표자 폰 대본» 링크와 시연 문장 2개 제거 · `시연.html`·`시연_PDF원문.html` 을 `_archive/260922_시연대본_static/` 로 옮김(정적 파일만 → 재시작 없음)
