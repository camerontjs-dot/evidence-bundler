#!/usr/bin/env python3
from __future__ import annotations
import argparse,json
from pathlib import Path
LEXICAL=('token_overlap','bow_tfidf','character_ngram','hard_negative_biased_lexical')
HEURISTICS=('passage_length_heuristic','source_position_heuristic','metadata_identifier_pattern_heuristic')
GAMERS=('runtime_construction_style_gamer','cue_swap_gamer','runtime_answer_marker_gamer','runtime_sentence_position_gamer')
def main():
    ap=argparse.ArgumentParser(); ap.add_argument('--controls',type=Path,required=True); ap.add_argument('--thresholds',type=Path,required=True); ap.add_argument('--output',type=Path,required=True); a=ap.parse_args()
    rec=json.loads(a.controls.read_text()); th=json.loads(a.thresholds.read_text()); c=rec['controls']; t=th['target_gates']; checks={}; details={}
    checks['oracle_ceiling_qualifies']=c['oracle']['qualifies_target_gate'] and all(v==0 for v in c['oracle']['evaluation']['technical'].values())
    for n in LEXICAL:
        tech=c[n]['evaluation']['technical']; checks[f'{n}_does_not_qualify']=not c[n]['qualifies_target_gate'] and all(v==0 for v in tech.values())
    checks['first_n_fails']=not c['first_n_source_order']['qualifies_target_gate'] and all(v==0 for v in c['first_n_source_order']['evaluation']['technical'].values())
    checks['return_all_fails_budget']=not c['return_all']['qualifies_target_gate'] and c['return_all']['evaluation']['technical']['budget_violations']>0
    checks['null_fails_coverage']=not c['null']['qualifies_target_gate'] and c['null']['evaluation']['technical']['coverage_errors']>0
    checks['provenance_corrupt_fails']=not c['provenance_corrupt']['qualifies_target_gate'] and c['provenance_corrupt']['evaluation']['technical']['invalid_provenance_hits']>0
    for n in HEURISTICS:
        checks[f'{n}_does_not_qualify']=not c[n]['qualifies_target_gate'] and all(v==0 for v in c[n]['evaluation']['technical'].values())
    for n in GAMERS:
        ev=c[n]['evaluation']; aa=ev['aggregate']; l4=ev['families']['L04']; tech=ev['technical']
        intended_fail=(aa['combined_l01_l04_case_hit_at_5']<t['combined_l01_l04_case_hit_at_5_min'] or aa['combined_l01_l04_decisive_recall_at_5']<t['combined_l01_l04_decisive_recall_at_5_min'] or l4['case_hit_at_5']<t['per_low_overlap_family_case_hit_at_5_min'] or l4['decisive_recall_at_5']<t['per_low_overlap_family_decisive_recall_at_5_min'])
        checks[f'{n}_fails_intended_anti_cue_gate']=not c[n]['qualifies_target_gate'] and intended_fail and all(v==0 for v in tech.values())
        details[n]={'intended_semantic_failure':intended_fail,'technical':tech,'qualification_failures':c[n]['qualification_failures']}
    comp=c['completeness_aperture_liar']; ans=c['semantic_answerability_liar']
    checks['completeness_liar_fails_closed']=not comp['qualifies_target_gate'] and comp['unsupported_receipt_claim_attempted'] and comp['evaluation']['technical']['false_completeness_claims']>0 and comp['evaluation']['technical']['shape_errors']>0
    checks['answerability_liar_fails_closed']=not ans['qualifies_target_gate'] and ans['unsupported_receipt_claim_attempted'] and ans['evaluation']['technical']['answerability_overclaims']>0 and ans['evaluation']['technical']['shape_errors']>0
    out={'record':'eb-rc4-weak-and-gaming-control-gate','checks':checks,'gamer_details':details,'all_pass':all(checks.values()),'hybrid_sealed_exposed':False,'semantic_sealed_exposed':False}
    a.output.write_text(json.dumps(out,sort_keys=True,indent=2)+'\n'); print(json.dumps(out,sort_keys=True,indent=2)); raise SystemExit(0 if out['all_pass'] else 7)
if __name__=='__main__': main()
