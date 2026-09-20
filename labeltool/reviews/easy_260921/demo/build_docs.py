# 검증한 시연 순서를 대본·폰 화면·사용법·PDF 원문으로 만든다.
from pathlib import Path
import json,html,shutil,datetime
R=Path(__file__).resolve().parent;C=R.parent;T=R.parents[2];W=Path('/data/project/2026summer/kds0206');S=R/'static';S.mkdir(exist_ok=True)
first=json.loads((R/'rehearsal1.json').read_text());second=R/'rehearsal2.json'
if second.exists():rows=json.loads(second.read_text())['rows']
else:
 rows=first['rows'];rows[17]['at']='2:55';rows[17:17]=[
 dict(at='2:45',say='기존 빨간 라벨을 끄면 수정한 모양을 볼 수 있습니다.',action='사진 위 원본 클릭',expect='원본 표시 꺼짐'),
 dict(at='2:48',say='AI 표시도 끄고 내가 고친 그림만 확인합니다.',action='사진 위 AI 클릭',expect='지운 줄기와 수정본만 표시')]
for i,r in enumerate(rows,1):r['shot']=f'{i:02d}.png'
(R/'script_rows.json').write_text(json.dumps(rows,ensure_ascii=False,indent=2))
now=datetime.datetime.now().strftime('%Y-%m-%d %H:%M KST');live=json.loads((C/'evidence/live_smoke.json').read_text())
candidates=[('포도','1순위','500','큰 앞 송이 꼭대기 굽은 초록 줄기. 중심(365,490), 지우기(364,470)→(357,515).','직접 비교 확인. 시연 사본에서 줄기 일부만 수정.'),('포도','예비1','2000','오른쪽 송이 안을 세로로 지나는 가는 줄기, 대략(510,880).','원본·이진·겹침 직접 확인. 일부는 이미 빈 틈이므로 칠해진 줄기 부분만 비교.'),('포도','예비2','1000','아래로 길게 이어진 송이 내부 줄기, 대략(530,1290).','직접 비교 확인. 작고 가려져1순위보다 설명이 어려움.'),('사과','1순위','20150921_131453_image1161','번호2. (245,1109)~(317,1178), 중심(280,1140). 잎이 위를 가로지르지만 둥근 라벨이 채움.','직접 비교 확인. 가림 포함 규칙은 미결이므로 수정·확정하지 않고 비교만.'),('사과','예비1','20150921_131234_image406','번호5. (160,475)~(200,518). 얇은 어두운 가림물 포함 후보.','직접 비교. 작고 어두워 낮은 확신. 사본 비교용.'),('사과','예비2','20150921_131234_image6','번호22. (299,481)~(355,543). 오른쪽 위 가림물 위까지 둥근 칠.','직접 비교. 1순위보다 모호하며 사본 비교용.')]
qa=[('이거 왜 만들었나?','❌ 우리 구현·내부 회의 근거. 0915 녹취09:10~09:38에서 편한 검수 툴과 데이터셋 재확인을 요청해, 사진을 보고 고치고 확인하는 흐름을 만들었습니다.'),('몇 장이나 고쳤나?',f"❌ 실제 운영 API {live['at']} 기준 수정본은 복숭아39장·나머지0장, 별도 사람 확인 기록은 이진1장·상자0장·번호0장입니다. 둘을 합산하지 않으며 시연 사본은 실적에서 제외합니다."),('중복 기준이 뭔가?','❌ 내부 실측. 자동은 dHash거리≤10과 상관≥0.9로94그룹192장, 대표 제외98장입니다. 삭제대상202장은 별도 육안 목록99+103입니다. 추가103장 중3장은 이미 자동 그룹 구성원이며, 98+103=202라는 산식은 틀립니다.'),('다른 사람도 쓸 수 있나?','❌ 개발자 인수인계는 위치 찾기7초·실행과시험8분33초·수정과시험8분11초였고, 초보 팀원의5분 사용성 시험은 아직 하지 않았습니다. 오늘 실제 사용 순서를 보여드리고 피드백을 받겠습니다.'),('사과의 가려진 부분도 바로 지우나?','❌ 우리 판단·미결 기준. 사과는 보이는 부분만 칠한 자료와 가려진 부분까지 칠한 자료가 섞여 있어 교수님께 기준을 확인한 뒤 고칩니다. 이 시연에서는 비교만 합니다.')]
failures=[('툴이 안 열린다',f'서버에서 cd {T} 후 bash app/run.sh. 현재 실행 중이면 그대로 두는 동작을 실제 확인했다. 강제 종료하지 않는다.'),('로그인이 안 된다','서버 ~/.council/labeltool.env의 LABELTOOL_PASSWORD를 담당자가 확인한다. 문서·화면 공유에 값은 적지 않는다.'),('사진이 안 뜬다','포도500 대신2000→1000, 사과1161 전체 이름 대신 위 표의image406→image6. 사진 검색은 전체 이름을 붙여 넣는다.'),('저장이 안 된다','초록 저장됨과 수정본 저장 완료 표시를 확인한다. 새로 열어 수정본이 같은지 본 뒤 다 했어요를 누른다. 오류 문구가 있으면 확인을 누르지 말고 화면을 남긴다.'),('전부 안 된다','~/ff_shots/demo_260921/rehearsal2/00_login.png와01.png~31.png를 번호 순서로 설명한다. 오프라인 폴더 복사본은 cycles/260921_쉽게/demo/fallback/, 목록은 index.html이다.')]
md='대행: Codex\n작성: '+now+'\n\n# 랩미팅 툴 시연 대본 — 5분\n\n포도 삭제 결과 발표와 겹치지 않게 **찾기→고치기→확인**만 보여 준다. 아래의 포도 수정·확정은 시연 사본에서만 실행한다. 줄기 한 부분의 사용법 연습을 전체 사진 검수 실적으로 세지 않는다. 사과는 가림 포함 규칙이 미결이므로 비교만 한다. 원본 파일은 고치지 않았다.\n\n## 발표 전 준비\n\n툴 로그인 후 내 이름과 사진 목록이 보이게 준비한다. 처음 안내는 읽고 닫는다. 작업은 칠한 영역·쉬움 모드, 보기와 색 칩은 기본 상태에서 시작한다. 녹화가 아니라 실제 클릭이다. 검증 서버는5791/5792의 격리 사본이며, 실제 운영5111은 읽기 검증만 했다. 무대에서는 연습 사본을 준비하거나 아래 오프라인 화면으로 진행한다. 발표 준비자용 실행·접속은 demo/README.md를 따른다.\n\n## 사진 후보 — 좌표는 원본1080×1920 기준\n\n| 과일 | 순위 | 사진 번호 | 찾을 곳 | 판단과 한계 |\n|---|---|---|---|---|\n'
md+='\n'.join('| '+' | '.join(r)+' |' for r in candidates)+'\n\n포도740은 기존 검수에서 정상 원경 사진으로 기록되어 오류 시연에서 제외했다. 사과 image111은 이미 빈 홈이 있어 둥근 채움의 대표에서 제외했다. 비교 근거는 demo/candidates.md와 실제 Firefox 후보 화면에 있다.\n\n## 진행 — 한 줄에 한 동작\n\n| 시각 | 말할 것 (그대로 읽음) | 누를 것 | 화면에 나와야 할 것 |\n|---|---|---|---|\n'
md+='\n'.join('| '+r['at']+' | “'+r['say']+'” | '+r['action']+' | '+r['expect']+' |' for r in rows)
md+='\n| 4:58 | “여기까지입니다.” | 종료 | 사용법 |\n\n## 사고 대비\n\n| 사고 | 어떻게 |\n|---|---|\n'+'\n'.join('| '+a+' | '+b+' |' for a,b in failures)
md+='\n\n## 예상 질문5개\n\n✅ citekey는 논문 근거일 때만 붙인다. 아래5개는 논문 주장이 아니라 회의·운영 실측·우리 판단이므로 모두❌로 표시한다. 없는 논문 근거를 만들지 않았다.\n\n'+'\n\n'.join('**'+q+'**\n\n'+a for q,a in qa)
md+='\n\n근거. 문서/0915랩미팅.txt09:10~09:38·문서/260917_교수님확인_7건.md17번·cycles/260920_structure/codex_resume/handoff_trial/260920_handoff_trial.md·이번 팀원자료_대조.md·evidence/live_smoke.json. 추가103장 최대상관 구간은 ≥.9=3, .7~.9=63, .65~.7=14, .6~.65=6, .55~.6=4, <.55=13으로,103장을 모두 .55~.9라고 소개하지 않는다.\n'
md+='\n## 실제 리허설\n\n1차 전체 클릭·촬영18.67초. 발화는 측정하지 않았다. 이후 원본·AI 칩을 끄는2동작을 추가했다.\n'
if second.exists():
 j=json.loads(second.read_text());md+=f"최종 대본 그대로2차 {j['elapsed_seconds']}초(4분58초). 실제 클릭·촬영·대본 시각에 맞춘 대기·마지막 팀 설명30초를 포함한다. 자동 음성이나 사람 발화 실측은 아니다. 저장 PNG 픽셀 일치와 확인 fixed를 다시 검사했다.\n"
else:md+='최종 대본의2차 전체 리허설은 문서 완성 후 실행해 실측값을 기록한다.\n'
(C/'랩미팅_툴시연_대본.md').write_text(md)
(R/'candidates.md').write_text('대행: Codex\n작성: '+now+'\n\n# 후보 직접 확인\n\n'+md.split('## 사진 후보')[1].split('## 진행')[0]+'\n\n원본/이진/겹침3열. ~/ff_shots/demo_260921/grape_stems.png 첫 줄, grape_backups.png 첫 두 줄, apple_round.png 세 줄. 포도501·502는 확인 위치에 전경이 없어 제외했다. 사과 후보는 기존 round2_apple_amodal_popsample_verdicts.csv의 좌표를 출발점으로 실제 파일을 다시 확인했다. 후보라는 말은 정답 규칙 확정을 뜻하지 않는다.\n')
css='''*{box-sizing:border-box}body{margin:0;background:#f5f7fa;color:#172d40;font:17px/1.6 system-ui,sans-serif;overflow-wrap:anywhere}main{max-width:650px;margin:auto;padding:18px}header{padding:14px 0}h1{font-size:26px}article{background:white;margin:18px 0;padding:22px 18px;border:1px solid #cfdae5;border-radius:14px;min-height:72svh;display:flex;flex-direction:column;justify-content:center}label{font-size:23px;line-height:1.65;font-weight:700}input{width:24px;height:24px;vertical-align:middle}small,.speech{font-size:17px;color:#43586a}.time{font-size:20px;color:#155ba3}a{color:#155ba3}img{width:100%;height:auto}h2{font-size:23px}@page{size:96mm 172mm;margin:7mm 6mm 8mm}@media print{body{background:white;font-family:'Noto Sans CJK KR',sans-serif}main{padding:0}article{min-height:0;border:0;padding:0;break-after:page;break-inside:avoid}nav,input{display:none}label{font-size:17pt}.speech{font-size:12pt}.time{font-size:13pt}header{break-after:page}article:last-of-type{break-after:auto}section{break-before:page}}'''
cards=''.join('<article><div class="time">'+r['at']+'</div><label><input type="checkbox" data-step="'+str(i)+'"> '+html.escape(r['action'])+'</label><p class="speech">'+html.escape(r['say'])+'</p></article>' for i,r in enumerate(rows))
prompter='<!-- 발표자가 폰에서 다음 동작을 확인하는 시연 대본. 대행: Codex -->\n<!doctype html><html lang="ko"><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>5분 시연</title><style>'+css+'</style><main><header><h1>다음 동작만 보기</h1><p>포도500 → 사과image1161. 연습 사본에서만 저장.</p><nav><a href="how_to.html">사용법</a> · <a href="시연대본.pdf">전체 대본 PDF</a></nav></header>'+cards+'</main><script>document.querySelectorAll("[data-step]").forEach(e=>{const k="demo260921-final-"+e.dataset.step;try{e.checked=localStorage.getItem(k)==="1"}catch(_){}e.onchange=()=>{try{localStorage.setItem(k,e.checked?"1":"0")}catch(_){}}});</script></html>'
(S/'시연.html').write_text(prompter)
# 폰 PDF 원문은 동일96×172mm HTML 인쇄 형식이며 사고 대비와 질문까지 포함한다.
extra='<section><h2>예비 사진</h2>'+''.join('<p>'+html.escape(' · '.join(r))+'</p>' for r in candidates)+'</section><section><h2>사고 대비</h2>'+''.join('<p><b>'+html.escape(a)+'</b><br>'+html.escape(b)+'</p>' for a,b in failures)+'</section><section><h2>예상 질문</h2><p>논문 근거 없음. 모두 내부 기록과 우리 판단(❌)입니다.</p>'+''.join('<p><b>'+html.escape(q)+'</b><br>'+html.escape(a)+'</p>' for q,a in qa)+'</section>'
if second.exists():extra+='<section><h2>검증 기록</h2><p>대행: Codex. 1차 클릭·촬영18.67초, 최종2차는 대본 시각 대기와 마지막 팀 안내 시간을 포함해4분58초입니다. 사람 발화 실측은 아닙니다. 저장 PNG 픽셀 일치·확인 기록 fixed·예비4장 열기를 확인했습니다.</p></section>'
(S/'시연_PDF원문.html').write_text(prompter.replace('</main>',extra+'</main>').replace('다음 동작만 보기','랩미팅 시연 대본').replace('<header>','<header><p>대행: Codex · '+now+'</p>'))
# 실제 리허설 화면으로 기존 여섯 단계 사용법을 맞춘다.
p=T/'_archive/pre_demo_260920/how_to.html';s=p.read_text().replace('포도740번','포도500번');mapping={'09_login.png':'00_login.png','01_list.png':'04.png','10_correct.png':'14.png','04_saved.png':'17.png','05_confirmed.png':'20.png','11_finish.png':'31.png'}
for old,new in mapping.items():s=s.replace('/static/help/easy_260921/'+old,'/static/help/demo_260921/'+new)
s=s.replace('현황에서 사람이 확인한 장수를 봅니다.','시연은 이 사용법 화면으로 돌아와 마칩니다. 실제 작업에서는 현황에서 사람이 확인한 장수를 볼 수 있습니다.')
s=s.replace('팀원은 여기까지 하고 창을 닫으면 됩니다.','팀원은 여기까지 하고 창을 닫으면 됩니다. 시연에서는 사과 후보를 비교한 뒤 이 사용법으로 돌아옵니다.')
s=s.replace('<h1>사진 한 장, 세 걸음</h1>','<h1>사진 한 장, 세 걸음</h1><p><a href="/static/시연.html">발표자 폰 대본</a> · <a href="/static/시연대본.pdf">전체 대본 PDF</a></p>')
s=s.replace('확인 완료로 기록됩니다.','확인 완료로 기록됩니다. 실제 검수에서는 사진 전체를 확인한 뒤 누릅니다.')
(S/'how_to.html').write_text(s)
(R/'카톡_3줄.md').write_text('대행: Codex\n작성: '+now+'\n\n5분 시연은 포도500번의 줄기 표시를 고치고 저장·확인한 뒤 사과의 잎 가림 후보를 비교합니다.\n폰에서는 툴의 /static/시연.html, 오프라인에서는 260921_랩미팅_시연대본.pdf를 보시면 됩니다.\n예비 사진각2장·사고대비·질문5개·전 과정 캡처를 준비했으며, 시연 사본은 실제 검수 실적에 포함하지 않습니다.\n')
print('대본31동작·후보6·질문5·폰화면·사용법 생성')
