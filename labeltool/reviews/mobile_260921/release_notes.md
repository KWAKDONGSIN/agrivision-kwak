대행: Codex (Claude 한도 초과)
작성: 2026-09-21

# 모바일 배포 검토 자료

폰에서 사진을 보고 판정하는 작업을 먼저 지원한다. 사진·도구·판정 순서로 쌓고 목록은 탭으로 연다. 아래 이전/확정/다음/되돌림은 항상 닿을 수 있다. 기존 상자/번호 편집 처리를 터치에 연결했고, 두 손가락은 확대·이동만 한다. 정밀 마스크 칠하기는 PC 안내와 입력 차단으로 제한한다.

## 변경 범위

- app/static/mobile.css와 js/mobile.js 추가. index.html에는 이 두 파일 참조만 추가했다.
- core/auth.py는 로그인 CSS6줄만 추가했다.
- how_to.html의 폰 사용법과 mobile_done.html 전후 보고를 추가했다.
- tests/fixtures/baseline_260920/routes.json은 HTML5종의 길이/지문만 바뀌었다. 원본은 baseline_pre_mobile_260921에 보존했다.
- API·데이터·기존 저장과 확정 함수는 바꾸지 않았다. 새 의존성은 없다.

## 검증 자료

- evidence/mobile_layout.json. 정확한390×844/360×740,30개 검사.
- evidence/touch.json. 합성 터치24개 검사. 실제 기기 미확인.
- evidence/independent.json. 별도 포인터 경로7개 검사.
- evidence/documents.json. 문서 인증·폰 가독성6개 검사.
- evidence/pc_comparison.json. PC12개 상태 전후 픽셀 동일.
- evidence/html_baseline_changes.json. API와 내보내기 산출물 동일, HTML5종만 의도된 변경.
- evidence/release_full.log와release_full.rc가 최종 전체시험 결과다.0을 확인하기 전 운영에 반영하지 않는다.

## 전환·복구

외부 접속이15분 동안 없고 운영 app/data가 착수 지문과 같은지 다시 확인한다. 검증한 사본만 복사하고 tmux에서 bash app/run.sh restart를 실행한다. 운영에서는 로그인·사진·문서 읽기만 확인한다. 공개 사본은 비밀/데이터 검사 후 본인 저장소에 올린다.

복구가 필요하면 _archive/pre_mobile_260921/app의 기존 파일을 복원하고, 새 파일은 삭제하지 않고 별도 아카이브로 이동한다. 접속 유무를 확인한 뒤 같은 run.sh로 재시작한다. data는 이번 변경 대상이 아니다.
