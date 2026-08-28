#!/usr/bin/env python3
from __future__ import annotations
import argparse, copy, hashlib, json, math, re
from collections import Counter
from pathlib import Path
from typing import Any
import evaluator

TOKEN_RE=re.compile(r"[a-z0-9]+")
LEXICAL_CONTROLS=("token_overlap","tfidf_cosine","char_trigram")


def tok(s:str)->list[str]: return TOKEN_RE.findall(s.lower())
def trigrams(s:str)->set[str]:
    x=" ".join(tok(s)); return {x[i:i+3] for i in range(max(0,len(x)-2))}
def load_json(p:Path): return json.loads(p.read_text(encoding="utf-8"))
def canonical(v:Any)->bytes: return (json.dumps(v,sort_keys=True,separators=(",",":"),ensure_ascii=False)+"\n").encode()
def sha_bytes(b:bytes)->str: return hashlib.sha256(b).hexdigest()

def candidate_passages(case, passages, subsets):
    srcs=set(subsets[case["accessible_subset_id"]]["source_ids"])
    return [p for p in passages.values() if p["source_id"] in srcs]

def make_hit(p,rank,score):
    return {"rank":rank,"source_id":p["source_id"],"passage_id":p["passage_id"],"score":float(score),"text":p["text"]}
def base_result(case,hits,retriever_id, completeness="not_established", answerability="not_established"):
    sid=case["accessible_subset_id"]
    return {"schema_version":"1.0","case_id":case["case_id"],"hits":hits,
            "search_scope":{"actual_searchable_subset_id":sid,"observed_scope":{"subset_id":sid}},
            "completeness_claim":{"status":completeness},"answerability_claim":{"status":answerability},
            "run_identity":{"retriever_id":retriever_id,"configuration_id":"rc2-control-v1","run_id":f"{retriever_id}-{case['case_id']}"}}

def ranked(strategy,case,cands,gold_rows):
    q=case["claim_text"]; k=int(case["runtime_config"]["maximum_passages"])
    if strategy=="first_n":
        rows=sorted(cands,key=lambda p:(p["source_order"],p["passage_order"],p["source_id"],p["passage_id"])); return [(p,0.0) for p in rows[:k]]
    if strategy=="token_overlap":
        qset=set(tok(q)); scored=[]
        for p in cands:
            ps=set(tok(p["text"])); score=len(qset & ps)/(len(qset) or 1); scored.append((p,score))
        scored.sort(key=lambda x:(-x[1],x[0]["source_order"],x[0]["passage_order"],x[0]["passage_id"])); return scored[:k]
    if strategy=="char_trigram":
        qg=trigrams(q); scored=[]
        for p in cands:
            pg=trigrams(p["text"]); score=len(qg&pg)/(len(qg|pg) or 1); scored.append((p,score))
        scored.sort(key=lambda x:(-x[1],x[0]["source_order"],x[0]["passage_id"])); return scored[:k]
    if strategy=="tfidf_cosine":
        docs=[tok(p["text"]) for p in cands]; qtokens=tok(q); n=len(docs)
        df=Counter()
        for d in docs: df.update(set(d))
        def vec(tokens):
            tf=Counter(tokens); return {t:c*(math.log((n+1)/(df.get(t,0)+1))+1.0) for t,c in tf.items()}
        qv=vec(qtokens); qn=math.sqrt(sum(v*v for v in qv.values())) or 1.0; scored=[]
        for p,d in zip(cands,docs):
            dv=vec(d); dn=math.sqrt(sum(v*v for v in dv.values())) or 1.0; dot=sum(qv.get(t,0.0)*v for t,v in dv.items()); scored.append((p,dot/(qn*dn)))
        scored.sort(key=lambda x:(-x[1],x[0]["source_order"],x[0]["passage_id"])); return scored[:k]
    if strategy=="hard_negative_biased":
        hard={(r["source_id"],r["passage_id"]) for r in gold_rows if r["relevance_class"]=="hard_negative"}
        rows=sorted(cands,key=lambda p:(0 if (p["source_id"],p["passage_id"]) in hard else 1,p["source_order"],p["passage_id"])); return [(p,1.0) for p in rows[:k]]
    raise ValueError(strategy)

def produce(strategy,case,passages,gold_rows,subsets):
    cands=candidate_passages(case,passages,subsets); k=int(case["runtime_config"]["maximum_passages"])
    if strategy=="null": return base_result(case,[],strategy)
    if strategy=="oracle":
        accessible=set(subsets[case["accessible_subset_id"]]["source_ids"])
        ids=[(r["source_id"],r["passage_id"]) for r in gold_rows if r["decisive"] and r["source_id"] in accessible]
        hits=[make_hit(passages[i],rank,100-rank) for rank,i in enumerate(ids[:k],1)]
        return base_result(case,hits,strategy)
    if strategy=="return_all":
        rows=sorted(cands,key=lambda p:(p["source_order"],p["passage_order"],p["passage_id"])); hits=[make_hit(p,i,0.0) for i,p in enumerate(rows,1)]; return base_result(case,hits,strategy)
    if strategy in {"first_n","token_overlap","char_trigram","tfidf_cosine","hard_negative_biased"}:
        rows=ranked(strategy,case,cands,gold_rows); return base_result(case,[make_hit(p,i,s) for i,(p,s) in enumerate(rows,1)],strategy)
    if strategy=="provenance_corrupt":
        r=produce("oracle",case,passages,gold_rows,subsets)
        for h in r["hits"]: h["text"] += " [corrupted]"
        r["run_identity"]["retriever_id"]=strategy; return r
    if strategy=="aperture_liar":
        r=produce("oracle",case,passages,gold_rows,subsets); r["completeness_claim"]["status"]="comprehensive"; r["run_identity"]["retriever_id"]=strategy; return r
    if strategy=="answerability_liar":
        r=produce("oracle",case,passages,gold_rows,subsets); r["answerability_claim"]["status"]="answer_present" if case["expected_answerability"]=="answerable" else "no_answer"; r["run_identity"]["retriever_id"]=strategy; return r
    raise ValueError(strategy)

def failure_categories(failures:list[str])->set[str]:
    cats=set()
    for f in failures:
        if "counterevidence" in f: cats.add("counterevidence")
        elif "qualifier_exception" in f: cats.add("qualifier_exception")
        elif "joint_group" in f: cats.add("joint_group")
        elif "case_hit" in f or "decisive_annotation" in f: cats.add("coverage")
        elif "budget" in f: cats.add("budget")
        elif "provenance" in f: cats.add("provenance")
        elif "completeness" in f or "scope" in f: cats.add("aperture")
        elif "answerability" in f: cats.add("answerability")
        else: cats.add("other")
    return cats

def run_controls(root:Path,split:str,thresholds_path:Path):
    passages,cases,gold,subsets=evaluator.load_benchmark(root,split); thresholds=load_json(thresholds_path)
    strategies=["oracle","null","first_n","token_overlap","tfidf_cosine","char_trigram","return_all","provenance_corrupt","aperture_liar","answerability_liar","hard_negative_biased"]
    controls={}
    for strategy in strategies:
        results=[produce(strategy,cases[cid],passages,gold[cid],subsets) for cid in sorted(cases)]
        case_metrics=[evaluator.evaluate_case(cases[r["case_id"]],gold[r["case_id"]],r,passages,subsets) for r in results]
        summary=evaluator.aggregate(case_metrics,thresholds)
        controls[strategy]={"summary":summary,"results_sha256":sha_bytes(canonical(results))}
    replay={}
    for strategy in strategies:
        results=[produce(strategy,cases[cid],passages,gold[cid],subsets) for cid in sorted(cases)]
        replay[strategy]=sha_bytes(canonical(results))
    deterministic=all(replay[s]==controls[s]["results_sha256"] for s in strategies)

    probes={}
    r03=next(c for c in cases.values() if c["family"]=="R03" and c["expected_answerability"]=="answerable")
    rows=gold[r03["case_id"]]; one=produce("oracle",r03,passages,rows,subsets); one["hits"]=one["hits"][:1]
    before=evaluator.evaluate_case(r03,rows,one,passages,subsets)
    mutated=copy.deepcopy(rows); second=next(r for r in mutated if r.get("joint_group_id") and (r["source_id"],r["passage_id"]) != (one["hits"][0]["source_id"],one["hits"][0]["passage_id"])); second["joint_group_id"]=None
    after=evaluator.evaluate_case(r03,mutated,one,passages,subsets)
    probes["joint_group_membership"]={"before_partial":before["partial_joint_groups"],"after_partial":after["partial_joint_groups"],"sensitive":before["partial_joint_groups"]!=after["partial_joint_groups"]}

    any_case=next(c for c in cases.values() if c["expected_answerability"]=="answerable")
    orr=produce("oracle",any_case,passages,gold[any_case["case_id"]],subsets); corrupt=copy.deepcopy(orr); corrupt["hits"][0]["text"] += "x"
    b=evaluator.evaluate_case(any_case,gold[any_case["case_id"]],orr,passages,subsets); a=evaluator.evaluate_case(any_case,gold[any_case["case_id"]],corrupt,passages,subsets)
    probes["provenance_text"]={"before":b["invalid_provenance_hits"],"after":a["invalid_provenance_hits"],"sensitive":a["invalid_provenance_hits"]>b["invalid_provenance_hits"]}

    identity_case=next(c for c in cases.values() if c["expected_answerability"]=="answerable" and any(r["relevance_class"]=="hard_negative" for r in gold[c["case_id"]]))
    identity_rows=gold[identity_case["case_id"]]; identity_oracle=produce("oracle",identity_case,passages,identity_rows,subsets)
    identity_before=evaluator.evaluate_case(identity_case,identity_rows,identity_oracle,passages,subsets)
    identity_mutated=copy.deepcopy(identity_rows); target=next(r for r in identity_mutated if r["decisive"] is True); hard=next(r for r in identity_mutated if r["relevance_class"]=="hard_negative")
    target["source_id"], target["passage_id"] = hard["source_id"], hard["passage_id"]
    identity_after=evaluator.evaluate_case(identity_case,identity_mutated,identity_oracle,passages,subsets)
    probes["gold_decisive_identity"]={"before_found":identity_before["found_decisive"],"after_found":identity_after["found_decisive"],"sensitive":identity_after["found_decisive"]<identity_before["found_decisive"]}

    r07=next(c for c in cases.values() if c["family"]=="R07"); honest=produce("oracle",r07,passages,gold[r07["case_id"]],subsets); liar=copy.deepcopy(honest); liar["completeness_claim"]["status"]="full_corpus"
    b=evaluator.evaluate_case(r07,gold[r07["case_id"]],honest,passages,subsets); a=evaluator.evaluate_case(r07,gold[r07["case_id"]],liar,passages,subsets)
    probes["aperture_completeness"]={"before":b["false_completeness_claims"],"after":a["false_completeness_claims"],"sensitive":a["false_completeness_claims"]>b["false_completeness_claims"]}

    oracle_summary=controls["oracle"]["summary"]
    perm_passages=dict(reversed(list(passages.items()))); perm_subsets=copy.deepcopy(subsets)
    for s in perm_subsets.values(): s["source_ids"]=list(reversed(s["source_ids"]))
    perm_results=[produce("oracle",cases[cid],perm_passages,gold[cid],perm_subsets) for cid in sorted(cases)]
    perm_metrics=[evaluator.evaluate_case(cases[r["case_id"]],gold[r["case_id"]],r,perm_passages,perm_subsets) for r in perm_results]
    perm_summary=evaluator.aggregate(perm_metrics,thresholds)
    keys=["qualified","case_hit_at_k","decisive_annotation_recall_at_k","counterevidence_recall_at_k","qualifier_exception_recall_at_k","complete_joint_group_coverage_at_k","budget_violations","invalid_provenance_hits","out_of_scope_hits","false_completeness_claims","answerability_overclaims"]
    invariant=all(oracle_summary[k]==perm_summary[k] for k in keys)

    lexical_nonqual=[s for s in LEXICAL_CONTROLS if not controls[s]["summary"]["qualified"]]
    cats=set()
    for s in lexical_nonqual: cats |= failure_categories(controls[s]["summary"]["qualification_failures"])
    gate_checks={
        "oracle_qualified":controls["oracle"]["summary"]["qualified"],
        "null_fails":not controls["null"]["summary"]["qualified"],
        "return_all_fails":not controls["return_all"]["summary"]["qualified"] and controls["return_all"]["summary"]["budget_violations"]>0,
        "provenance_corrupt_fails":not controls["provenance_corrupt"]["summary"]["qualified"] and controls["provenance_corrupt"]["summary"]["invalid_provenance_hits"]>0,
        "aperture_liar_fails":not controls["aperture_liar"]["summary"]["qualified"] and controls["aperture_liar"]["summary"]["false_completeness_claims"]>0,
        "answerability_liar_fails":not controls["answerability_liar"]["summary"]["qualified"] and controls["answerability_liar"]["summary"]["answerability_overclaims"]>0,
        "lexical_discrimination":len(lexical_nonqual)>=thresholds["weak_control_min_nonqualifying_lexical_strategies"],
        "lexical_failure_diversity":len(cats)>=thresholds["weak_control_min_distinct_failure_categories"],
        "deterministic_replay":deterministic,
        "metamorphic_source_order_invariance":invariant,
        "mutation_sensitivity":all(p["sensitive"] for p in probes.values()),
    }
    return {"schema_version":"1.0","split":split,"gate_pass":all(gate_checks.values()),"gate_checks":gate_checks,"lexical_nonqualifying":lexical_nonqual,"lexical_failure_categories":sorted(cats),"controls":controls,"sensitivity_probes":probes,"metamorphic":{"source_order_invariant":invariant}}

def main():
    ap=argparse.ArgumentParser(); ap.add_argument("--benchmark-root",required=True,type=Path); ap.add_argument("--split",required=True,choices=["dev","sealed"]); ap.add_argument("--thresholds",required=True,type=Path); ap.add_argument("--output",required=True,type=Path)
    a=ap.parse_args(); out=run_controls(a.benchmark_root,a.split,a.thresholds); a.output.parent.mkdir(parents=True,exist_ok=True); a.output.write_text(json.dumps(out,indent=2,sort_keys=True)+"\n",encoding="utf-8"); print(json.dumps({"gate_pass":out["gate_pass"],"gate_checks":out["gate_checks"],"lexical_nonqualifying":out["lexical_nonqualifying"],"lexical_failure_categories":out["lexical_failure_categories"],"control_summaries":{k:v["summary"] for k,v in out["controls"].items()}},indent=2,sort_keys=True))
    raise SystemExit(0 if out["gate_pass"] else 2)
if __name__=="__main__": main()
