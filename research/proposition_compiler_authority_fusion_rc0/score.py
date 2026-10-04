from __future__ import annotations
import argparse, hashlib, json
from pathlib import Path

SYSTEMS=("A0_AUTHORITY_ONLY","A1_FUSION")

def canon(x): return json.dumps(x,sort_keys=True,separators=(",",":"),ensure_ascii=False)
def sha(s): return hashlib.sha256(s.encode()).hexdigest()

def main():
    p=argparse.ArgumentParser(); p.add_argument('--raw',required=True); p.add_argument('--gold',required=True); p.add_argument('--output',required=True); a=p.parse_args()
    raw=json.loads(Path(a.raw).read_text()); rows={r['root_id']:r for r in raw['rows']}
    gold=[json.loads(x) for x in Path(a.gold).read_text().splitlines() if x.strip()]
    summaries={}; details=[]
    for system in SYSTEMS:
        safe=unsafe=correct_abs=false_abs=0
        for g in gold:
            s=rows[g['root_id']]['systems'][system]; sel=s['selected']; allowed=set(g['safe_candidate_ids']); expected=g['expected']
            if sel is None:
                if expected=='ABSTAIN': correct_abs+=1
                else: false_abs+=1
            elif expected=='SELECT' and sel in allowed: safe+=1
            else: unsafe+=1
            details.append({'system':system,'root_id':g['root_id'],'expected':expected,'selected':sel,'selected_safe':sel in allowed if sel else None,'reason':s.get('reason')})
        summaries[system]={'safe_selects':safe,'unsafe_selects':unsafe,'correct_abstains':correct_abs,'false_abstains':false_abs}
    changed=0
    for g in gold:
        a0=rows[g['root_id']]['systems']['A0_AUTHORITY_ONLY']['selected']; a1=rows[g['root_id']]['systems']['A1_FUSION']['selected']
        if a0!=a1: changed+=1
    summaries['A1_FUSION']['decisions_changed_vs_A0']=changed
    out={'schema_version':'pc-authority-fusion-score-rc0.1','summaries':summaries,'details':details}
    text=canon(out)+'\n'; Path(a.output).write_text(text); print(sha(text))
if __name__=='__main__': main()
