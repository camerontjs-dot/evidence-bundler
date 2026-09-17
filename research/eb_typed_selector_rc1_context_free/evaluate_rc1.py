#!/usr/bin/env python3
"""Target-agnostic evaluator for EB typed-selector RC1."""
from __future__ import annotations
import argparse,gzip,hashlib,json
from pathlib import Path
USEFUL={"REQUIRED","USEFUL_DISTINCT"}; NONUSEFUL={"REDUNDANT","DISTRACTOR","UNSAFE_OR_MISLEADING"}
REQUIRED_SYSTEM_GATES=["exact_replay","input_order_permutation_invariant","irrelevant_metadata_invariant","no_duplicate_selection","selection_budget_at_most_3","ids_within_frozen_top10","pool_hash_preserved","no_gold_fields_in_output","runner_has_no_gold_dependency","adapter_source_hashes_recorded"]
THRESHOLDS={"support":{"covered_positive_lane_gain":3,"useful_item_recall_gain":0.08,"unsafe_selected_delta_max":0,"nonuseful_burden_delta_max":3,"ordinary_coverage_loss_vs_best_rank_semantic_max":1,"weak_discrimination_lane_gain":2,"weak_discrimination_recall_gain":0.05},"falsification":{"covered_positive_lane_loss_vs_best_control":2,"useful_item_recall_loss":0.08,"unsafe_selected_delta_min":2,"nonuseful_burden_delta_min":4}}
def read_json(path):
 b=Path(path).read_bytes(); b=gzip.decompress(b) if str(path).endswith('.gz') else b; return json.loads(b)
def canonical_sha(obj): return 'sha256:'+hashlib.sha256(json.dumps(obj,sort_keys=True,separators=(',',':'),ensure_ascii=False).encode()).hexdigest()
def gold_index(g): return {l['lane_id']:{r['candidate_id']:r for r in l['candidates']} for l in g['lanes']}
def pool_index(p): return {l['lane_id']:{c['candidate_id']:c for c in l['candidates']} for l in p['lanes']}
def contains_gold_fields(o):
 forbidden={'class','required_group_ids','redundancy_group_id','reason_code','justification','confidence','gold'}
 if isinstance(o,dict): return bool(forbidden & set(o)) or any(contains_gold_fields(v) for v in o.values())
 if isinstance(o,list): return any(contains_gold_fields(v) for v in o)
 return False
def validate_outputs(pools,out):
 e=[]; pi=pool_index(pools)
 if out.get('pool_canonical_sha256')!=canonical_sha(pools): e.append('pool_hash_mismatch')
 arms=out.get('arms',{})
 if set(arms)!={'ARM_A','ARM_B','ARM_C','ARM_D'}: e.append('opaque_arm_set_must_be_ARM_A_through_D')
 for arm,lanes in arms.items():
  if set(lanes)!=set(pi): e.append(f'{arm}:lane_set_mismatch')
  for lid,sel in lanes.items():
   if not isinstance(sel,list): e.append(f'{arm}/{lid}:selection_not_list'); continue
   if len(sel)>3: e.append(f'{arm}/{lid}:selection_budget_exceeded')
   if len(sel)!=len(set(sel)): e.append(f'{arm}/{lid}:duplicate_selection')
   if any(x not in set(pi.get(lid,{})) for x in sel): e.append(f'{arm}/{lid}:id_outside_pool')
 if contains_gold_fields(out): e.append('gold_field_leak')
 gates=out.get('system_gates',{})
 for g in REQUIRED_SYSTEM_GATES:
  if gates.get(g) is not True: e.append(f'system_gate_not_true:{g}')
 return e
def score_arm(pools,gold,selections):
 gi=gold_index(gold); positive=covered=unsafe=nonuseful=numerator=denominator=0; lane_scores={}
 for lane in pools['lanes']:
  lid=lane['lane_id']; rows=list(gi[lid].values()); req={g for r in rows for g in r.get('required_group_ids',[])}; distinct={r['candidate_id'] for r in rows if r['class']=='USEFUL_DISTINCT'}; units={('req',g) for g in req}|{('distinct',x) for x in distinct}; ispos=bool(units); positive+=ispos; got=set(); lu=ln=0
  for cid in selections.get(lid,[]):
   r=gi[lid][cid]; cl=r['class']
   if cl=='REQUIRED': got|={('req',g) for g in r.get('required_group_ids',[])}
   elif cl=='USEFUL_DISTINCT': got.add(('distinct',cid))
   elif cl=='REDUNDANT' and r.get('redundancy_group_id'): got.add(('req',r['redundancy_group_id']))
   if cl=='UNSAFE_OR_MISLEADING': lu+=1
   if cl in NONUSEFUL: ln+=1
  cov=len(got&units); numerator+=cov; denominator+=len(units); ok=(cov==len(units)); covered+=int(ispos and ok); unsafe+=lu; nonuseful+=ln; lane_scores[lid]={'positive':ispos,'covered':ok if ispos else None,'covered_units':cov,'total_units':len(units),'unsafe_selected':lu,'nonuseful_selected':ln}
 return {'positive_lanes':positive,'covered_positive_lanes':covered,'useful_item_recall':numerator/denominator if denominator else 1.0,'unsafe_selected':unsafe,'nonuseful_burden':nonuseful,'lanes':lane_scores}
def evaluate(pools,gold,out,binding):
 errs=validate_outputs(pools,out)
 if errs: return {'terminal':'BLOCKED_SYSTEM_GATES','errors':errs}
 if set(binding)!={'candidate','rank','semantic','weak'} or set(binding.values())!={'ARM_A','ARM_B','ARM_C','ARM_D'}: return {'terminal':'BLOCKED_BINDING','errors':['binding_invalid']}
 s={r:score_arm(pools,gold,out['arms'][a]) for r,a in binding.items()}; c=s['candidate']; sem=s['semantic']; rank=s['rank']; weak=s['weak']; best=max([sem,rank,weak],key=lambda x:(x['covered_positive_lanes'],x['useful_item_recall'])); brs=max([sem,rank],key=lambda x:(x['covered_positive_lanes'],x['useful_item_recall']))
 support=(c['covered_positive_lanes']-sem['covered_positive_lanes']>=3 and c['useful_item_recall']-sem['useful_item_recall']>=.08 and c['unsafe_selected']<=sem['unsafe_selected'] and c['nonuseful_burden']-sem['nonuseful_burden']<=3 and brs['covered_positive_lanes']-c['covered_positive_lanes']<=1 and (c['covered_positive_lanes']-weak['covered_positive_lanes']>=2 or c['useful_item_recall']-weak['useful_item_recall']>=.05))
 falsified=(best['covered_positive_lanes']-c['covered_positive_lanes']>=2 or best['useful_item_recall']-c['useful_item_recall']>=.08 or c['unsafe_selected']-best['unsafe_selected']>=2 or c['nonuseful_burden']-best['nonuseful_burden']>=4)
 return {'terminal':'EVALUATED','disposition':'SUPPORT_THRESHOLD_MET' if support else ('FALSIFICATION_THRESHOLD_MET' if falsified else 'INCONCLUSIVE'),'scores':s,'thresholds':THRESHOLDS}
def self_test():
 p={'lanes':[{'lane_id':'L','candidates':[{'candidate_id':'a','rank':1},{'candidate_id':'b','rank':2},{'candidate_id':'c','rank':3}]}]}; g={'lanes':[{'lane_id':'L','candidates':[{'candidate_id':'a','class':'REQUIRED','required_group_ids':['G'],'redundancy_group_id':None},{'candidate_id':'b','class':'REDUNDANT','required_group_ids':[],'redundancy_group_id':'G'},{'candidate_id':'c','class':'UNSAFE_OR_MISLEADING','required_group_ids':[],'redundancy_group_id':None}]}]}; o={'pool_canonical_sha256':canonical_sha(p),'arms':{a:{'L':['a']} for a in ['ARM_A','ARM_B','ARM_C','ARM_D']},'system_gates':{x:True for x in REQUIRED_SYSTEM_GATES}}; assert not validate_outputs(p,o); assert score_arm(p,g,{'L':['a']})['useful_item_recall']==1.; b=json.loads(json.dumps(o)); b['arms']['ARM_A']['L']=['a','a']; assert validate_outputs(p,b); print('SELF_TEST_PASS')
def main():
 ap=argparse.ArgumentParser(); ap.add_argument('--pools'); ap.add_argument('--gold'); ap.add_argument('--outputs'); ap.add_argument('--binding'); ap.add_argument('--out'); ap.add_argument('--self-test',action='store_true'); a=ap.parse_args()
 if a.self_test: self_test(); return
 r=evaluate(read_json(a.pools),read_json(a.gold),read_json(a.outputs),read_json(a.binding)); t=json.dumps(r,sort_keys=True,indent=2); Path(a.out).write_text(t+'\n') if a.out else print(t)
if __name__=='__main__': main()
