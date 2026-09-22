# Agrivision 작업 기록과 라벨링 툴

작성: 2026-09-20

곽동신의 네 과일 데이터 정리·라벨링 작업 소스와 검수 문서입니다.
2026-09-20 마무리에서 새 기준선과 전체 회귀를 검증했습니다. **정적6칸은 사람이 승인한 변경이며 원래 기준선 통과로 포장하지 않습니다. 파일은 새 구조, 실행 중인 서버는 옛 코드이고 전환은 사람이 합니다.** 최신 기록은 labeltool/reviews/finish_260920/260920_마무리_보고.md입니다.

- `labeltool/`: app·export·tests·scripts와 단계별 검수 보고서.
- `docs/260920_전체정리_폰용.md`: 폰으로 읽는 전체 정리. 같은 이름 PDF도 있습니다.
- `dataset/`: 보존 중인 v3 목록과 출처. 새 시험 재빌드와 구별합니다.
- `scripts/`: 사용자 작성 이력이 확인된 데이터 처리·문서 생성 스크립트.
- `worklog/작업기록.md`: 보안 세부를 가린 작업 이력.
- `NOT_UPLOADED.md`: 공개에서 제외한 항목과 이유.

사진·마스크·번호·상자·체크포인트·논문 원문은 포함하지 않습니다. CERTH·MinneApple 등 데이터의 원출처 및 이용조건은 출처등록표에서 확인하세요. 제3자 자료에 새 재배포 허가를 부여하지 않습니다.

## 실행과 시험

`labeltool/app/README.md`부터 읽으세요. Flask·Pillow·numpy·scipy와 별도 원본 데이터가 필요합니다.
전체 회귀는 기존 서버의 통합 스크립트·팀 자료·아카이브도 참조하므로 이 공개 저장소만으로 재현되지 않습니다.
`tests/run_all.sh --browser --check-baseline`은 승인된 새 기준선으로 통과했습니다. 원래 기준선은 tests/fixtures/baseline_260920_pre_split에 보존했고 BASELINE_CHANGELOG.md에6칸의 이전/새 지문을 기록했습니다.
서버 주소와 비밀값을 가린 공개 사본입니다. 설정값은 자신의 환경으로 정하세요. 데이터 사진이 포함된 도움말 그림은 공개에서 제외돼 일부 예시 이미지가 없습니다.

## 2026-09-20 EASY 갱신

최신 구현·검증은 labeltool/reviews/easy_260921/stage3_final.md와 app/static/how_to.html에 있다. 이번 배포 상태는 그 보고서를 우선한다. 이전 전환 보류 기록은 당시 이력으로 보존한다.

## 2026-09-20 DEMO 갱신

시연 최종 보고는 labeltool/reviews/easy_260921/demo/DEMO_완료보고.md, 실제31동작 대본은 labeltool/reviews/easy_260921/랩미팅_툴시연_대본.md에 있습니다. 사진과 폰PDF는 인증된 내부 운영 환경에서 제공합니다.

## 2026-09-21 MOBILE 갱신

폰 판정·현황·간단 상자/번호 편집을 지원합니다. 정밀 편집은 PC에서 합니다. 최신 검증은 labeltool/reviews/mobile_260921/stage3_final.md, 사용법은 labeltool/app/static/how_to.html입니다. 실기기 검증은 하지 못했습니다.

## 2026-09-21 편의·안정성 갱신

그림판·포토샵·윈도우 관습을 따라 편의 10가지와 안정성 6가지를 더하고, 무채색 토큰 한 벌로
색을 접었습니다. 요소 id·단축키·API 규칙은 바꾸지 않았습니다.
최신 검증은 labeltool/reviews/편의_260921/checklist.md, 결정과 까닭은 같은 폴더
context-notes.md 입니다. 실제 휴대폰 확인은 아직 못 했습니다.

## 2026-09-22 기술설명 갱신

툴을 어떤 기술로 어떻게 만들었는지, 언제 저장되는지, 팀원이 어떻게 고치는지를
docs/260922_툴_기술설명.md (같은 이름 PDF) 에 적었습니다. 감시자(scripts/watchdog.sh)에
팀원용 재시작 신호 `app/logs/restart.flag` 를 더했습니다. 요소 id·단축키·API 규칙은 바꾸지 않았습니다.
