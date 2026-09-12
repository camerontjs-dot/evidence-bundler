from __future__ import annotations

import argparse, hashlib, json, math, re
from pathlib import Path
from typing import Any

FEATURES = (
    "r2", "nli_forward", "nli_reverse", "generic", "lexical", "nli_asymmetry",
    "threshold_mismatch", "unit_mismatch", "negation_mismatch", "modal_mismatch",
    "disjunction_root", "shared_scope_missing_fraction", "pronoun_ambiguity_root",
    "attribution_mismatch", "number_set_mismatch", "child_count", "candidate_token_ratio",
    "duplicate_children", "comparison_operator_mismatch",
)
TRAIN_IDS = tuple([f"D{i:02d}" for i in range(1,13)] + [f"F{i:02d}" for i in range(1,17)])
CAL_IDS = tuple(f"F{i:02d}" for i in range(17,25))
EPOCHS = 4000
LEARNING_RATE = 0.08
L2 = 0.02
FLOORS = (-3.0,-2.0,-1.0,-0.5,0.0,0.5,1.0,1.5,2.0,3.0)
MARGINS = (0.0,0.1,0.25,0.5,0.75,1.0,1.5,2.0)

THRESHOLD_RE=re.compile(r"\b(at least|at most|more than|less than)\b",re.I)
MODAL_RE=re.compile(r"\b(may|might|must|should|can|could|will|would)\b",re.I)
UNIT_RE=re.compile(r"\b(ms|sec|seconds|kg|mg|kpa|pa|volts?|percent|%|units?|meters?|metres?|cm|mm|hours?|minutes?)\b",re.I)
PRON_RE=re.compile(r"\b(it|they|them|he|she|him|her)\b",re.I)
SHARED_PREFIX_RE=re.compile(r"^(?P<prefix>(?:during|among|at|in|if|except for|according to|under|within|for)\s+[^,]{1,100}),\s*",re.I)
ATTR_RE=re.compile(r"\b(?:reported\s+that|reports\s+that|said\s+that|says\s+that|according\s+to|recommended\s+that|recommends\s+that)\b",re.I)
COMP_RE=re.compile(r"\b(faster|slower|higher|lower|greater|less|cheaper|larger|smaller)\b",re.I)


def canon(x: Any) -> str:
    return json.dumps(x,sort_keys=True,separators=(",",":"),ensure_ascii=False)

def sha(s: str) -> str:
    return hashlib.sha256(s.encode()).hexdigest()

def norm(s: str) -> str:
    return re.sub(r"\s+"," ",s.lower().strip().rstrip("."))

def toks(s: str) -> list[str]:
    return re.findall(r"[A-Za-z0-9%'-]+",s.lower())

def neg_count(s: str) -> int:
    return len(re.findall(r"\b(?:not|never|no)\b",s,re.I))

def multiset(pattern: re.Pattern, s: str) -> tuple[str,...]:
    return tuple(sorted(x.lower() if isinstance(x,str) else str(x).lower() for x in pattern.findall(s)))

def numbers(s: str) -> tuple[str,...]:
    return tuple(sorted(set(re.findall(r"\b\d+(?:\.\d+)?\b",s))))

def context_unique_reference(context: str) -> bool:
    return bool(re.search(r"\bonly\s+(?:the\s+)?[A-Za-z][A-Za-z0-9 -]*?(?:\s+was|\s+is|\s+remained|\s+stayed|\s+continued)\b",context,re.I))

def joined(children: list[str]) -> str:
    return " ".join(children)

def feature_dict(case: dict[str,Any], row: dict[str,Any]) -> dict[str,float]:
    root=str(case["root_text"]); context=str(case.get("context_text","") or ""); children=[str(x) for x in row["children"]]; cand=joined(children)
    m=SHARED_PREFIX_RE.match(root.strip().rstrip(".")); miss=0.0
    if m and children:
        p=norm(m.group("prefix")); miss=sum(1 for c in children if p not in norm(c))/len(children)
    fwd=float(row["nli_forward_entailment"]); rev=float(row["nli_reverse_entailment"])
    return {
        "r2":float(row["scores"]["R2_bidirectional_nli"]),
        "nli_forward":fwd,
        "nli_reverse":rev,
        "generic":float(row["scores"]["R1_generic"]),
        "lexical":float(row["scores"]["B0_lexical"]),
        "nli_asymmetry":abs(fwd-rev),
        "threshold_mismatch":float(multiset(THRESHOLD_RE,root)!=multiset(THRESHOLD_RE,cand)),
        "unit_mismatch":float(set(x.lower() for x in UNIT_RE.findall(root))!=set(x.lower() for x in UNIT_RE.findall(cand))),
        "negation_mismatch":float(abs(neg_count(root)-neg_count(cand))),
        "modal_mismatch":float(multiset(MODAL_RE,root)!=multiset(MODAL_RE,cand)),
        "disjunction_root":float(bool(re.search(r"\b(?:or|and/or)\b",root,re.I))),
        "shared_scope_missing_fraction":miss,
        "pronoun_ambiguity_root":float(bool(PRON_RE.search(root)) and not context_unique_reference(context)),
        "attribution_mismatch":float(len(ATTR_RE.findall(root))!=len(ATTR_RE.findall(cand))),
        "number_set_mismatch":float(numbers(root)!=numbers(cand)),
        "child_count":float(len(children)),
        "candidate_token_ratio":min(3.0,len(toks(cand))/max(1,len(toks(root)))),
        "duplicate_children":float(len({norm(c) for c in children})<len(children)),
        "comparison_operator_mismatch":float(multiset(COMP_RE,root)!=multiset(COMP_RE,cand)),
    }

def vector(case,row):
    d=feature_dict(case,row); return [d[k] for k in FEATURES]

def sigmoid(z: float) -> float:
    if z>=0:
        e=math.exp(-z); return 1/(1+e)
    e=math.exp(z); return e/(1+e)

def standardize(x,mean,std): return [(v-m)/s for v,m,s in zip(x,mean,std)]
def dot(a,b): return sum(x*y for x,y in zip(a,b))

def train(cases,raw,gold):
    by_case={c["root_id"]:c for c in cases}; by_raw={r["root_id"]:r for r in raw["rows"]}; by_gold={g["root_id"]:g for g in gold}
    cand=[]
    for rid in TRAIN_IDS:
        case=by_case[rid]
        for row in by_raw[rid]["candidates"]: cand.append(vector(case,row))
    mean=[sum(x[j] for x in cand)/len(cand) for j in range(len(FEATURES))]
    std=[]
    for j,m in enumerate(mean):
        v=sum((x[j]-m)**2 for x in cand)/len(cand); std.append(max(math.sqrt(v),1e-9))
    pairs=[]
    for rid in TRAIN_IDS:
        case=by_case[rid]; rows={r["candidate_id"]:r for r in by_raw[rid]["candidates"]}; safe=set(by_gold[rid]["safe_candidate_ids"])
        if not safe: continue
        unsafe=set(rows)-safe
        for sid in sorted(safe):
            sx=standardize(vector(case,rows[sid]),mean,std)
            for uid in sorted(unsafe):
                ux=standardize(vector(case,rows[uid]),mean,std)
                d=[a-b for a,b in zip(sx,ux)]
                pairs.append((d,1.0)); pairs.append(([-v for v in d],0.0))
    w=[0.0]*len(FEATURES)
    for _ in range(EPOCHS):
        grad=[L2*v for v in w]
        for x,y in pairs:
            e=sigmoid(dot(w,x))-y
            for j,v in enumerate(x): grad[j]+=e*v/len(pairs)
        for j in range(len(w)): w[j]-=LEARNING_RATE*grad[j]
    return mean,std,w,len(pairs)

def score_row(case,row,model):
    z=standardize(vector(case,row),model["mean"],model["std"]); return dot(model["weights"],z)

def cal_metrics(cases,raw,gold,model,floor,margin):
    bc={c["root_id"]:c for c in cases}; br={r["root_id"]:r for r in raw["rows"]}; bg={g["root_id"]:g for g in gold}
    safe_n=unsafe_n=correct_abs=false_abs=0
    for rid in CAL_IDS:
        scores=sorted([(score_row(bc[rid],r,model),r["candidate_id"]) for r in br[rid]["candidates"]],key=lambda x:(-x[0],x[1]))
        top,tid=scores[0]; second=scores[1][0]; sel=tid if top>=floor and top-second>=margin else None; g=bg[rid]; safe=set(g["safe_candidate_ids"])
        if sel is None:
            if g["expected"]=="ABSTAIN": correct_abs+=1
            else:false_abs+=1
        elif g["expected"]=="SELECT" and sel in safe:safe_n+=1
        else:unsafe_n+=1
    return {"floor":floor,"margin":margin,"safe_selects":safe_n,"unsafe_selects":unsafe_n,"correct_abstains":correct_abs,"false_abstains":false_abs}

def calibrate(cases,raw,gold,model):
    opts=[cal_metrics(cases,raw,gold,model,f,m) for f in FLOORS for m in MARGINS]
    feasible=[x for x in opts if x["unsafe_selects"]==0]
    if not feasible:return {"status":"NO_ZERO_UNSAFE_CALIBRATION","chosen":None,"best":sorted(opts,key=lambda x:(x["unsafe_selects"],-x["safe_selects"],-x["correct_abstains"],-x["floor"],-x["margin"]))[0]}
    chosen=sorted(feasible,key=lambda x:(-x["safe_selects"],-x["correct_abstains"],-x["floor"],-x["margin"]))[0]
    return {"status":"CALIBRATED","chosen":chosen}

def load_inputs(cases_path,raw_path,gold_path=None):
    cases=[json.loads(x) for x in Path(cases_path).read_text().splitlines() if x.strip()]; raw=json.loads(Path(raw_path).read_text()); gold=None
    if gold_path: gold=[json.loads(x) for x in Path(gold_path).read_text().splitlines() if x.strip()]
    return cases,raw,gold

def cmd_train(a):
    cases,raw,gold=load_inputs(a.cases,a.raw,a.gold); mean,std,w,n=train(cases,raw,gold)
    model={"schema_version":"pc-cal-linear-reranker-rc0.1","features":FEATURES,"mean":mean,"std":std,"weights":w,"training_root_ids":TRAIN_IDS,"calibration_root_ids":CAL_IDS,"optimizer":{"epochs":EPOCHS,"learning_rate":LEARNING_RATE,"l2":L2,"pair_rows":n}}
    model["calibration"]=calibrate(cases,raw,gold,model)
    text=canon(model)+"\n"; Path(a.model).write_text(text); print(sha(text))

def cmd_score(a):
    cases,raw,_=load_inputs(a.cases,a.raw); model=json.loads(Path(a.model).read_text()); bc={c["root_id"]:c for c in cases}
    out=json.loads(canon(raw))
    for r in out["rows"]:
        for c in r["candidates"]: c["scores"]["T1_CAL_LINEAR"]=score_row(bc[r["root_id"]],c,model)
    out["learned_model_sha256"]=hashlib.sha256(Path(a.model).read_bytes()).hexdigest()
    text=canon(out)+"\n"; Path(a.output).write_text(text); print(sha(text))

def main():
    p=argparse.ArgumentParser(); sp=p.add_subparsers(dest='cmd',required=True)
    t=sp.add_parser('train'); t.add_argument('--cases',required=True);t.add_argument('--raw',required=True);t.add_argument('--gold',required=True);t.add_argument('--model',required=True);t.set_defaults(fn=cmd_train)
    s=sp.add_parser('score');s.add_argument('--cases',required=True);s.add_argument('--raw',required=True);s.add_argument('--model',required=True);s.add_argument('--output',required=True);s.set_defaults(fn=cmd_score)
    a=p.parse_args();a.fn(a)
if __name__=='__main__':main()
