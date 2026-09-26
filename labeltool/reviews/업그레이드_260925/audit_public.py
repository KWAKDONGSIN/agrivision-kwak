# 공개 사본 전체에서 비밀값과 금지 자료를 다시 검사한다.
"""Public-copy secret/data exclusion audit; findings contain no credential values."""
from pathlib import Path
import re,json,subprocess,datetime
W=Path('/data/project/2026summer/kds0206');G=W/'_git_agrivision-kwak';R=Path(__file__).resolve().parent
strong=re.compile(r'AIza[0-9A-Za-z_-]{20,}|sk-[0-9A-Za-z_-]{20,}|ghp_[0-9A-Za-z_]+|github_pat_[0-9A-Za-z_]+|Bearer [0-9A-Za-z._-]{20,}|-----BEGIN [A-Z ]*PRIVATE KEY-----')
words=re.compile(r'password|passwd|secret|token|api[_-]?key',re.I)
known=[]
for l in (Path.home()/'.council/labeltool.env').read_text().splitlines():
 if l.startswith('LABELTOOL_PASSWORD='):
  v=l.split('=',1)[1].strip().strip('\"\'')
  if v:known.append(v)
fail=[];hits=[];pdfs=[];total=0
for p in sorted(G.rglob('*')):
 if not p.is_file() or '.git' in p.parts:continue
 rel=str(p.relative_to(G));total+=p.stat().st_size
 if any(x in ('data','exports','images','masks','instances','boxes','_sandbox','_archive','cache','logs','__pycache__','sandbox') or x.startswith('_backup') for x in p.relative_to(G).parts):fail.append({'file':rel,'reason':'forbidden path'})
 if p.suffix.lower() in ('.png','.jpg','.jpeg','.pt','.pth','.ckpt','.zip'):fail.append({'file':rel,'reason':'forbidden binary'})
 if p.suffix=='.pdf':
  q=subprocess.run(['pdftotext',str(p),'-'],capture_output=True,text=True);s=q.stdout;pdfs.append(rel)
  if q.returncode:fail.append({'file':rel,'reason':'PDF extraction failed'})
 else:
  try:s=p.read_text()
  except UnicodeError:fail.append({'file':rel,'reason':'unscannable binary'});continue
 if '<서버주소>' in s:fail.append({'file':rel,'reason':'server IP'})
 if strong.search(s):fail.append({'file':rel,'reason':'credential pattern'})
 if any(v in s for v in known):fail.append({'file':rel,'reason':'known private credential'})
 for i,l in enumerate(s.splitlines(),1):
  if re.search('claude',l,re.I) and re.search('resume',l,re.I) and re.search(r'[a-f0-9]{8}(?:-[a-f0-9]{4}){3}-[a-f0-9]{12}',l,re.I):fail.append({'file':rel,'line':i,'reason':'session identifier'})
  if words.search(l):
   # Show code structure while suppressing quoted literal values.
   shown=re.sub(r'([\"\'])(?:\\.|(?!\1).)*?\1',lambda m:'<literal>' if not re.fullmatch(r'[\"\'](?:password|passwd|secret|token|api_key)[\"\']',m.group(),re.I) else m.group(),l)
   shown=re.sub(r'(?i)(password|passwd|secret|token|api[_-]?key)(\s*=\s*)[^ ,;\n]+',r'\1\2<value>',shown)
   hits.append({'file':rel,'line':i,'view':shown[:300]})
report={'at':datetime.datetime.now().isoformat(),'files':sum(p.is_file() for p in G.rglob('*') if '.git' not in p.parts),'bytes':total,'pdfs':pdfs,'failures':fail,'keyword_lines':len(hits)}
(R/'evidence/public_secret_audit.json').write_text(json.dumps(report,ensure_ascii=False,indent=2))
(R/'evidence/public_keyword_review.json').write_text(json.dumps(hits,ensure_ascii=False,indent=1))
print(json.dumps(report,ensure_ascii=False,indent=1));assert not fail and total<1024**3
