from __future__ import annotations
import argparse,hashlib,json
from pathlib import Path
SYSTEMS=("B0_lexical","R2_bidirectional_nli","T1_CAL_LINEAR")
FIXED={"B0_lexical":(0.9,0.2),"R2_bidirectional_nli":(0.9,0.01)}
def canon(x):return json.dumps(x,sort_keys=True,separators=(",",":"),ensure_ascii=False)
def sha(s):return hashlib.sha256(s.encode()).hexdigest()
def main():
 p=argparse.ArgumentParser();p.add_argument('--raw',required=True);p.add_argument('--gold',required=True);p.add_argument('--model',required=True);p.add_argument('--output',required=True);a=p.parse_args()
 raw=json.loads(Path(a.raw).read_text()); model=json.loads(Path(a.model).read_text()); gold={g['root_id']:g for g in map(json.loads,Path(a.gold).read_text().splitlines()) if g}; rows={r['root_id']:r for r in raw['rows']}; summaries={};details=[]
 for sys in SYSTEMS:
  if sys=='T1_CAL_LINEAR':
   cal=model['calibration']
   if cal['status']!='CALIBRATED': summaries[sys]={'status':cal['status']};continue
   floor=float(cal['chosen']['floor']);margin=float(cal['chosen']['margin'])
  else: floor,margin=FIXED[sys]
  safe=unsafe=ca=fa=pt=pc=ct=cc=top_safe=selectable=0
  for rid,g in gold.items():
   cand=rows[rid]['candidates'];ranked=sorted([(float(c['scores'][sys]),c['candidate_id']) for c in cand],key=lambda x:(-x[0],x[1]));top,tid=ranked[0];second=ranked[1][0];gap=top-second;sel=tid if top>=floor and gap>=margin else None;allowed=set(g['safe_candidate_ids']);allids={c['candidate_id'] for c in cand};bad=allids-allowed;crit=set(g.get('critical_unsafe_candidate_ids',[]))
   if g['expected']=='SELECT':
    selectable+=1; top_safe+=int(tid in allowed); sm={cid:score for score,cid in ranked}
    for sid in allowed:
     for uid in bad:
      pt+=1;pc+=int(sm[sid]>sm[uid])
      if uid in crit:ct+=1;cc+=int(sm[sid]>sm[uid])
   if sel is None:
    if g['expected']=='ABSTAIN':ca+=1
    else:fa+=1
   elif g['expected']=='SELECT' and sel in allowed:safe+=1
   else:unsafe+=1
   details.append({'system':sys,'root_id':rid,'selected':sel,'top_id':tid,'top_score':top,'margin':gap,'expected':g['expected']})
  summaries[sys]={'status':'CALIBRATED','floor':floor,'margin_threshold':margin,'safe_selects':safe,'unsafe_selects':unsafe,'correct_abstains':ca,'false_abstains':fa,'top1_safe_preference_rate':top_safe/selectable if selectable else None,'pairwise_safe_over_unsafe_rate':pc/pt if pt else None,'critical_pairwise_safe_over_unsafe_rate':cc/ct if ct else None,'pairwise_total':pt,'critical_pairwise_total':ct}
 out={'schema_version':'pc-cal-linear-evaluation-rc0.1','summaries':summaries,'details':details};text=canon(out)+'\n';Path(a.output).write_text(text);print(sha(text))
if __name__=='__main__':main()
