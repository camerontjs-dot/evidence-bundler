#!/usr/bin/env python3
from __future__ import annotations
import argparse,json
from pathlib import Path
LOW=('L01','L02','L03','L04')
def main():
    ap=argparse.ArgumentParser(); ap.add_argument('--evaluation',type=Path,required=True); ap.add_argument('--thresholds',type=Path,required=True); ap.add_argument('--output',type=Path,required=True); a=ap.parse_args()
    ev=json.loads(a.evaluation.read_text()); th=json.loads(a.thresholds.read_text()); p=th['apparatus_prerequisites']; tg=th['target_gates']; aa=ev['aggregate']; f=ev['families']; tech=ev['technical']
    family_fail={fam:(f[fam]['case_hit_at_5']<tg['per_low_overlap_family_case_hit_at_5_min'] or f[fam]['decisive_recall_at_5']<tg['per_low_overlap_family_decisive_recall_at_5_min']) for fam in LOW}
    checks={
      'combined_low_overlap_case_hit_weak_enough':aa['combined_l01_l04_case_hit_at_5']<=p['bm25_combined_l01_l04_case_hit_at_5_max'],
      'combined_low_overlap_decisive_recall_weak_enough':aa['combined_l01_l04_decisive_recall_at_5']<=p['bm25_combined_l01_l04_decisive_recall_at_5_max'],
      'minimum_three_low_overlap_families_fail_target_floor':sum(family_fail.values())>=p['bm25_minimum_low_overlap_families_failing_target_floor'],
      'c01_counterevidence_case_hit_strong':f['C01']['counterevidence_case_hit_at_5']>=p['bm25_c01_counterevidence_case_hit_at_5_min'],
      'c01_counterevidence_recall_strong':f['C01']['counterevidence_recall_at_5']>=p['bm25_c01_counterevidence_recall_at_5_min'],
      'c01_first_counterevidence_mrr_strong':f['C01']['first_counterevidence_mrr']>=p['bm25_c01_counterevidence_first_mrr_min'],
      'technical_clean':all(v==0 for v in tech.values()),
    }
    c01_keys=('c01_counterevidence_case_hit_strong','c01_counterevidence_recall_strong','c01_first_counterevidence_mrr_strong')
    c01_stop=not all(checks[k] for k in c01_keys)
    out={'record':'eb-rc4-exact-production-bm25-apparatus-gate','checks':checks,'family_target_floor_failures':family_fail,'evaluation':ev,'all_pass':all(checks.values()),'c01_stop_triggered':c01_stop,'hybrid_sealed_exposed':False,'semantic_sealed_exposed':False}
    a.output.write_text(json.dumps(out,sort_keys=True,indent=2)+'\n'); print(json.dumps(out,sort_keys=True,indent=2)); raise SystemExit(0 if out['all_pass'] else 6)
if __name__=='__main__': main()
