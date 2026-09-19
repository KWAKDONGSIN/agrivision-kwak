"""Preserve original behavior baseline; admit only three reviewed static replacements.
작성: 2026-09-20. This does not rebaseline any API response or exported artifact.
"""
import copy,json,sys
from pathlib import Path
import snapshot as S
POLICY=Path(S.FIX)/'structure_transition_260920.json'

def differences(base,now,policy):
    errors=[]
    missing=object()
    for part in ('api','exports'):
        a,b=S.flat(base[part]),S.flat(now[part])
        errors.extend(part+'/'+k for k in sorted(a.keys()|b.keys()) if a.get(k,missing)!=b.get(k,missing))
    old,new=copy.deepcopy(base['routes']),copy.deepcopy(now['routes'])
    for key,allowed in policy['routes'].items():
        if old.get(key)!=allowed['old']:
            errors.append('static/original-baseline-changed/'+key)
        if new.get(key)!=allowed['new']:
            errors.append('static/unreviewed-change/'+key)
        old.pop(key,None);new.pop(key,None)
    a,b=S.flat(old),S.flat(new)
    errors.extend('routes/'+k for k in sorted(a.keys()|b.keys()) if a.get(k,missing)!=b.get(k,missing))
    return errors

def mutation_checks(base,now,policy):
    assert not differences(base,now,policy)
    attacks=[]
    n=copy.deepcopy(now);n['api']['unexpected_field']={'ok':True};attacks.append(n)
    n=copy.deepcopy(now);n['api']['unexpected_null']=None;attacks.append(n)
    n=copy.deepcopy(now);n['exports']['unexpected_file']='sha256-changed';attacks.append(n)
    n=copy.deepcopy(now);n['routes']['r_page_index']['sha256']='unreviewed';attacks.append(n)
    n=copy.deepcopy(now);n['routes']['r_page_box']['http']=404;attacks.append(n)
    n=copy.deepcopy(now);n['routes'].pop('r_static_app_js');attacks.append(n)
    for n in attacks:assert differences(base,n,policy)
    b=copy.deepcopy(base);b['routes']['r_page_index']['bytes']+=1
    assert differences(b,now,policy)
    print('전환 관문 변조 검사: 7/7 거부')

def main():
    base=S.load();now=S.take();policy=json.loads(POLICY.read_text())
    assert set(policy['routes'])=={'r_page_index','r_page_box','r_static_app_js'}
    errors=differences(base,now,policy)
    print('원래 기준선 보존: API JSON·내보내기 sha256·나머지 라우트 전부 대조')
    print('검증된 정적 교체: 3주소, 각 원래 값/새 값 exact match (6칸)')
    if errors:
        print('실패:',json.dumps(errors,ensure_ascii=False));return 1
    if now.get('bundles') and S.diff_bundles(base['bundles'],now['bundles']):return 1
    mutation_checks(base,now,policy)
    out=Path(S.L.OUT_DIR)/'structure_transition_result.json'
    out.write_text(json.dumps({'behavior_differences':errors,'reviewed_static_routes':list(policy['routes']),'mutation_cases_rejected':7},ensure_ascii=False,indent=1))
    print('통과 8 / 실패 0');return 0
if __name__=='__main__':sys.exit(main())
