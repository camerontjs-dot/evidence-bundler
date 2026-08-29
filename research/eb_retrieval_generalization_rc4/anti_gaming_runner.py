#!/usr/bin/env python3
from __future__ import annotations
import argparse,json
from pathlib import Path

def main()->None:
    ap=argparse.ArgumentParser(); ap.add_argument('--controls',type=Path,required=True); ap.add_argument('--thresholds',type=Path,required=True); ap.add_argument('--output',type=Path,required=True); a=ap.parse_args()
    rec=json.loads(a.controls.read_text()); th=json.loads(a.thresholds.read_text()); controls=rec['controls']; gates=th['gamer_discrimination']['intended_anti_cue_gates']
    names=['runtime_construction_style_gamer','cue_swap_gamer','runtime_answer_marker_gamer','runtime_sentence_position_gamer','passage_length_heuristic','source_position_heuristic','metadata_identifier_pattern_heuristic']
    result={'systems':{},'all_required_fail':True}
    for n in names:
        c=controls[n]; ev=c['evaluation']; a0=ev['aggregate']; f=ev['families']; vals={'combined_l01_l04_case_hit_at_5':a0['combined_l01_l04_case_hit_at_5'],'combined_l01_l04_decisive_recall_at_5':a0['combined_l01_l04_decisive_recall_at_5'],'l04_case_hit_at_5':f['L04']['case_hit_at_5'],'l04_decisive_recall_at_5':f['L04']['decisive_recall_at_5']}
        # cue_swap_pair_semantic_role_stability is separately tested by metamorphic_runner.
        failed_semantic=not c['qualifies_target_gate']; result['systems'][n]={'qualifies_target_gate':c['qualifies_target_gate'],'failed_intended_semantic_gate':failed_semantic,'values':vals,'qualification_failures':c['qualification_failures']}
        if n in ('runtime_construction_style_gamer','cue_swap_gamer','runtime_answer_marker_gamer','runtime_sentence_position_gamer') and not failed_semantic: result['all_required_fail']=False
    a.output.write_text(json.dumps(result,sort_keys=True,indent=2)+"\n",encoding='utf-8'); print(json.dumps(result,sort_keys=True,indent=2)); raise SystemExit(0 if result['all_required_fail'] else 3)
if __name__=='__main__': main()
