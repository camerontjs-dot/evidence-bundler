#!/usr/bin/env python3
from __future__ import annotations
import importlib.util,json,os,re,sys
from pathlib import Path
from typing import Any
RC0_PROFILE="pc-evaluator-rc0-explicit-conjunction-v1"
def n(s):return re.sub(r"\s+"," ",s.strip().lower()).strip(" .")
def toks(s):return re.findall(r"[a-zA-Z]+(?:'[a-zA-Z]+)?|\d+(?:\.\d+)?|>=|<=|>|<|%",n(s))
def cset(s):return {x for x in toks(s) if x not in {"the","a","an","and","or","that","to","of","is","was","were","be","are"}}
def base(c,d,r):return {"case_id":c.get("case_id"),"root_id":c.get("root_id"),"disposition":d,"control_reason":r}
def shape(c):
    if not {"case_id","root_id","root_text","profile_id","candidate_state","children"}<=set(c):return False
    return (c.get("operator")=="all_of" and isinstance(c["children"],list) and len(c["children"])>=2) if c["candidate_state"]=="DECLARED" else isinstance(c["children"],list) and not c["children"]
def c0(c):return base(c,"ACCEPTABLE_WITHIN_PROFILE","ACCEPT_ALL")
def c1(c):return base(c,"ACCEPTABLE_WITHIN_PROFILE" if shape(c) else "INVALID_INPUT","SHAPE_ONLY")
def c2(c):
    if not shape(c):return base(c,"INVALID_INPUT","LEXICAL_BAD_SHAPE")
    if c["candidate_state"]!="DECLARED":return base(c,"ACCEPTABLE_WITHIN_PROFILE","LEXICAL_NON_DECLARED")
    r=cset(c["root_text"]);ctx=cset(c.get("context_text",""));u=set().union(*(cset(x["text"]) for x in c["children"]))
    return base(c,"ACCEPTABLE_WITHIN_PROFILE" if u<=r|ctx and r<=u else "REJECT_UNSAFE","LEXICAL_SET_TEST")
def c3(c):
    if not shape(c):return base(c,"INVALID_INPUT","BOW_BAD_SHAPE")
    if c["candidate_state"]!="DECLARED":return base(c,"ACCEPTABLE_WITHIN_PROFILE","BOW_NON_DECLARED")
    r=cset(c["root_text"]);u=set().union(*(cset(x["text"]) for x in c["children"]));sim=len(r&u)/max(1,len(r|u));z=base(c,"ACCEPTABLE_WITHIN_PROFILE" if sim>=.8 else "REJECT_UNSAFE","BOW_JACCARD");z["similarity"]=round(sim,6);return z
_RC0=None
def rc0mod():
    global _RC0
    if _RC0 is None:
        p=os.environ.get("RC0_BASELINE_PATH")
        if not p:raise RuntimeError("RC0_BASELINE_PATH is required for C4")
        spec=importlib.util.spec_from_file_location("pc_rc0_frozen_control",Path(p)); assert spec and spec.loader
        m=importlib.util.module_from_spec(spec);sys.modules[spec.name]=m;spec.loader.exec_module(m);_RC0=m
    return _RC0
def c4(c):
    x=json.loads(json.dumps(c));x["profile_id"]=RC0_PROFILE;r=rc0mod().evaluate(x)
    return {"case_id":c.get("case_id"),"root_id":c.get("root_id"),"disposition":r["disposition"],"control_reason":"FROZEN_RC0_EXACT_BYTES_WITH_PROFILE_ADAPTER","rc0_canonical_sha256":r.get("canonical_sha256")}
CONTROLS={"C0_ACCEPT_ALL":c0,"C1_SHAPE_ONLY":c1,"C2_LEXICAL_CONSERVATION":c2,"C3_BAG_OF_WORDS":c3,"C4_FROZEN_RC0":c4}
def evaluate_control(name,cases):return [CONTROLS[name](c) for c in cases]
