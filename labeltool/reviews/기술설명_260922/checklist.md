작성: 2026-09-22 12:30 · 끝나면 `[x]` + 시각

- [x] (12:33) T1 저장 방식 실측(판정=즉시 서버 저장 · 마스크/상자/번호=Ctrl+S · 1분 브라우저 임시백업) → 답변 + 문서 §2
- [x] (12:32) T2 `문서/260922_툴_기술설명.md` 작성(기술 스택 · 구조 · 저장 경로 · 안전장치 · 시험 · 만든 과정 · 팀원 수정법 · 깃 권한)
- [x] (12:33, 6쪽 261KB, 쪽 그림 `pdf_pages/` 눈 확인) T3 `문서/260922_툴_기술설명.pdf` 생성(`semantic-segmentation/tools/make_tool_tech_pdf_260922.py`, pdfdoc) · 쪽 그림 눈 확인
- [x] (12:33, 모래상자 실측: restart.flag → run.sh restart 호출·플래그 삭제·로그 2줄) T4 팀원 편집: `scripts/watchdog.sh` 에 `restart.flag` 처리 추가 · 문법검사 · 감시자 크론이 그대로 도는지 확인 · 폴더 권한 실측
- [x] (12:37 prepare 481/6/83 · audit failures 0 · push 결과는 작업기록 §2) T5 공개 저장소 동기화(prepare_public → audit_public 비밀검사 → docs/ 에 md·PDF → 커밋 → deploy key push → `log -1 origin/main`)
- [x] (12:39) T6 카톡 초안 `문서/260922_카톡_툴기술설명.txt`(미발송) · 작업기록 갱신
- [x] (12:36) T7 (사용자 12:35 추가) 툴 «사진 한 장 검수하기» 설명 페이지(how_to.html)에서 «발표자 폰 대본» 링크와 시연 문장 2개 제거 · `시연.html`·`시연_PDF원문.html` 을 `_archive/260922_시연대본_static/` 로 옮김(정적 파일만 → 재시작 없음)
- [x] (13:15) T8 (사용자 13:00 보고 «지우개가 안 지워진다») 원인 = 화면 겹침: 지우개는 수정본(S.ed)만 지우는데 원본(빨강)·AI(파랑)·번호(0.6)가 같은 진하기로 밑에 깔려 지운 자리가 그대로 보였다. 모래상자+파이어폭스 실측(데이터 0 · 화면 색 그대로) → `view.js` draw() 에서 수정본이 켜져 있으면 원본·AI·번호(번호 편집 모드 제외)를 0.35배로 흐리게 · 레이어 툴팁 3개 갱신 · 백업 `_backup_260922_eraser_view.js`·`_backup_260922_eraser_index.html`
- [x] (13:45) T9 (사용자 13:30 «검수 전 진짜 원본 레이어» + «전체 회귀») `core/paths.py` orig_gt_path/has_orig_gt · `api/photos.py` /mask?layer=orig + item.has_orig · 화면 `#l-orig` 주황 레이어(있을 때만 칸 표시) · VLAYERS/OFF/CHIP · 밀폐 시험 822/0 · 모래상자 브라우저: 복숭아 has_orig=true·orig 31,505px·gt 와 6,684px 다름·콘솔 오류 0 · 실서버 재시작 1회 · 전체 회귀는 뒤에서 실행(결과는 작업기록)
