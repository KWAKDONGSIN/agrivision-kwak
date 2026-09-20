# 원격커밋과 공개된최종코드·보고서를실제로대조한다.
"""Verify authorized public repo HEAD, root contents, and three raw files without secrets."""
from pathlib import Path
import subprocess,os,urllib.request,urllib.parse,json,hashlib,datetime,re
R=Path(__file__).resolve().parent;G=Path('/data/project/2026summer/kds0206/_git_agrivision-kwak');env=os.environ.copy();env['GIT_SSH_COMMAND']='ssh -i '+str(Path.home()/'.ssh/agrivision_deploy')+' -o IdentitiesOnly=yes -o BatchMode=yes'
head=subprocess.check_output(['git','rev-parse','HEAD'],cwd=G,text=True).strip();remote=subprocess.check_output(['git','ls-remote','origin','refs/heads/main'],cwd=G,env=env,text=True).split()[0];assert head==remote
base='https://api.github.com/repos/KWAKDONGSIN/agrivision-kwak/contents/'
def get(u):
 with urllib.request.urlopen(urllib.request.Request(u,headers={'User-Agent':'agrivision-handover-verification'}),timeout=60) as r:return r.status,r.read()
code,body=get(base+'?ref='+head);names=[x['name'] for x in json.loads(body)];assert {'labeltool','dataset','scripts','docs','worklog','README.md'}<=set(names)
known=[]
for l in (Path.home()/'.council/labeltool.env').read_text().splitlines():
 if l.startswith('LABELTOOL_PASSWORD='):
  v=l.split('=',1)[1].strip().strip('\"\'')
  if v:known.append(v)
raw={}
for name in ['README.md','labeltool/app/static/시연.html','labeltool/reviews/easy_260921/랩미팅_툴시연_대본.md','labeltool/reviews/easy_260921/demo/DEMO_완료보고.md']:
 code,b=get('https://raw.githubusercontent.com/KWAKDONGSIN/agrivision-kwak/'+head+'/'+urllib.parse.quote(name));assert code==200 and b==(G/name).read_bytes()
 s=b.decode();assert '<서버주소>' not in s and not any(v in s for v in known);assert not re.search(r'AIza[0-9A-Za-z_-]{20,}|sk-[0-9A-Za-z_-]{20,}|ghp_[0-9A-Za-z_]+|github_pat_[0-9A-Za-z_]+|-----BEGIN [A-Z ]*PRIVATE KEY-----',s)
 raw[name]={'http':code,'sha256':hashlib.sha256(b).hexdigest()}
report={'at':datetime.datetime.now().isoformat(),'head':head,'remote_main':remote,'api_http':code,'root':names,'raw':raw};target=R/'evidence'/('github_verified_'+head[:7]+'.json');target.write_text(json.dumps(report,ensure_ascii=False,indent=2));print(json.dumps(report,ensure_ascii=False))
