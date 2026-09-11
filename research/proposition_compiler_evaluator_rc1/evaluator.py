#!/usr/bin/env python3
from __future__ import annotations
import hashlib,json,re
from dataclasses import asdict,dataclass
from typing import Any

PROFILE_ID="pc-evaluator-rc1-binding-v1"
ART={"the","a","an"}; PRON={"it","they","he","she","them","him","her"}
MOD={"may","might","must","should","can","could","will","would"}; SQ={"each","every","all","some","most","no"}
UNITS={"ms","s","sec","seconds","kg","g","mg","kpa","pa","volts","volt","v","percent","%","units","meters","metres","cm","mm","hours","minutes"}
LEM={
"reviewed":"review","review":"review","reviews":"review","approved":"approve","approve":"approve","approves":"approve",
"acquired":"acquire","acquire":"acquire","acquires":"acquire","notified":"notify","notify":"notify","notifies":"notify",
"logged":"log","log":"log","logs":"log","stored":"store","store":"store","stores":"store","cached":"cache","cache":"cache","caches":"cache",
"recorded":"record","record":"record","records":"record","inspected":"inspect","inspect":"inspect","inspects":"inspect","retested":"retest","retest":"retest","retests":"retest",
"sealed":"seal","seal":"seal","seals":"seal","labeled":"label","labelled":"label","label":"label","labels":"label","encrypted":"encrypt","encrypt":"encrypt","encrypts":"encrypt",
"authenticated":"authenticate","authenticate":"authenticate","authenticates":"authenticate","reduced":"reduce","reduce":"reduce","reduces":"reduce","increased":"increase","increase":"increase","increases":"increase",
"decreased":"decrease","decrease":"decrease","decreases":"decrease","caused":"cause","cause":"cause","causes":"cause","filed":"file","file":"file","files":"file",
"signed":"sign","sign":"sign","signs":"sign","sent":"send","send":"send","sends":"send","shipped":"ship","ship":"ship","ships":"ship","delivered":"deliver","deliver":"deliver","delivers":"deliver",
"transferred":"transfer","transfer":"transfer","transfers":"transfer","sold":"sell","sell":"sell","sells":"sell","bought":"buy","buy":"buy","buys":"buy","preceded":"precede","precede":"precede","precedes":"precede",
"followed":"follow","follow":"follow","follows":"follow","examined":"examine","examine":"examine","examines":"examine","measured":"measure","measure":"measure","measures":"measure","archived":"archive","archive":"archive","archives":"archive",
"processed":"process","process":"process","processes":"process","scanned":"scan","scan":"scan","scans":"scan","restarted":"restart","restart":"restart","restarts":"restart","starts":"start","start":"start","started":"start",
"stops":"stop","stop":"stop","stopped":"stop","sounds":"sound","sound":"sound","sounded":"sound","failed":"fail","fail":"fail","fails":"fail","passed":"pass","pass":"pass","passes":"pass",
"recovered":"recover","recover":"recover","recovers":"recover","rose":"rise","rises":"rise","rise":"rise","fell":"fall","falls":"fall","fall":"fall","changed":"change","change":"change","changes":"change","dimmed":"dim","dim":"dim","dims":"dim",
"arrived":"arrive","arrive":"arrive","arrives":"arrive","departed":"depart","depart":"depart","departs":"depart"}
STATE={"encrypted","authenticated","compliant","ready","active","inactive","sealed","labeled"}; COMP={"faster","slower","higher","lower","greater","less","cheaper","larger","smaller"}
INTR={"restart","start","stop","sound","fail","pass","recover","rise","fall","change","arrive","depart"}
VRE="(?:"+"|".join(sorted(map(re.escape,LEM),key=len,reverse=True))+")"

@dataclass(frozen=True)
class Q: kind:str; value:str
@dataclass(frozen=True)
class F:
    predicate:str; roles:tuple[tuple[str,str],...]; ops:tuple[tuple[str,str],...]=(); qs:tuple[Q,...]=(); ref:str="explicit"
    def key(self): return canon({"p":self.predicate,"r":self.roles,"o":self.ops,"q":[asdict(x) for x in self.qs],"ref":self.ref})
@dataclass(frozen=True)
class P: status:str; frames:tuple[F,...]=(); reason:str=""
@dataclass(frozen=True)
class Finding: dimension:str; status:str; reason_code:str; detail:str

def norm(s): return re.sub(r"\s+"," ",s.replace("’","'").replace("–","-").replace("—","-").strip().lower()).strip(" .")
def art(s):
    t=norm(s).split(); return " ".join(t[1:] if t and t[0] in ART else t)
def canon(x): return json.dumps(x,sort_keys=True,separators=(",",":"),ensure_ascii=False,default=lambda o:asdict(o))
def sha(s): return hashlib.sha256(s.encode()).hexdigest()
def q(k,v): return Q(k,norm(v))
def subj(s):
    t=norm(s).split(); ops=[]
    if t and t[0] in SQ: ops=[("subject_quantifier",t.pop(0))]
    return art(" ".join(t)),tuple(ops)
def qty(s):
    n=norm(s); ops=[]; qs=[]; m=re.match(r"^(at least|at most|more than|less than)\s+(.+)$",n)
    if m: ops=[("quantity_operator",m.group(1))]; n=m.group(2)
    m=re.search(r"\b\d+(?:\.\d+)?\s*([a-z%]+)?\b",n)
    if m and m.group(1) in UNITS: qs=[q("unit",m.group(1))]
    return n,tuple(ops),tuple(qs)
def mk(p,roles,ops=(),qs=(),ref="explicit"): return F(p,tuple((k,art(v)) for k,v in roles),tuple(sorted(ops)),tuple(sorted(qs,key=lambda x:(x.kind,x.value))),ref)

def lead(s):
    m=re.match(r"^([^,]{2,120}),\s*(.+)$",s.strip(),re.I)
    if not m:return s.strip(),()
    n=norm(m.group(1)); z=None
    for pre,k in [("if ","condition"),("except for ","exception"),("among ","population"),("during ","temporal"),("according to ","attribution"),("at ","location")]:
        if n.startswith(pre): z=q(k,n[len(pre):]); break
    if not z and n.startswith("in "):
        v=n[3:]; z=q("temporal" if re.search(r"\b(?:19|20)\d{2}\b|\bq[1-4]\b",v) else "location",v)
    return (m.group(2).strip(),(z,)) if z else (s.strip(),())
def embed(s):
    m=re.match(r"^(.+?)\s+(reported|reports|said|says|recommended|recommends|expects|expected)\s+that\s+(.+)$",s.strip().rstrip("."),re.I)
    return (m.group(3).strip(),(q("attribution",f"{m.group(1)}|{m.group(2)}"),)) if m else (s.strip(),())
def trail(s):
    n=s.strip().rstrip(".")
    pats=[(r"^(.*)\s+if\s+(.+)$","condition"),(r"^(.*)\s+except for\s+(.+)$","exception"),(r"^(.*)\s+during\s+(.+)$","temporal"),(r"^(.*)\s+among\s+(.+)$","population"),(r"^(.*)\s+at\s+((?:the\s+)?(?:north|south|east|west|central|main|remote|local|toronto|boston|ottawa|montreal)[^,]*)$","location"),(r"^(.*)\s+in\s+((?:19|20)\d{2}|q[1-4])$","temporal")]
    for p,k in pats:
        m=re.match(p,n,re.I)
        if m:return m.group(1).strip(),(q(k,m.group(2)),)
    return s.strip(),()
def clue(s):
    n=norm(s); return bool(re.search(rf"\b{VRE}\b|\bassociated\s+with\b|\bstopped\s+transmitting\b|\bshut\s+down\b",n) or re.search(r"\b(?:is|was|are|were|be)\s+(?:not\s+)?(?:"+"|".join(STATE|COMP)+r")\b",n) or re.search(r"\b(?:is|was)\s+(?:probably\s+)?(?:below|above|\d)",n))
def inherit_ok(s): return bool(re.match(rf"^(?:did\s+not\s+|did\s+|(?:{'|'.join(MOD)})\s+)?{VRE}\b",norm(s)) or norm(s) in STATE)
def split_and(s):
    n=s.strip().rstrip(".")
    if re.search(r"\band/or\b",n,re.I):return [n]
    for m in re.finditer(r"\s+and\s+",n,re.I):
        l=n[:m.start()].strip(" ,"); r=n[m.end():].strip(" ,")
        if clue(l) and (clue(r) or inherit_ok(r)): return [l,*split_and(r)]
    return [n]
def refs(f): return list(dict.fromkeys(v for k,v in f.roles if k in {"agent","entity","subject","object","source","destination","buyer","seller","left","right"} and not re.search(r"\d",v)))
def ctxref(c):
    m=re.search(r"\bonly\s+(?:the\s+)?([a-z][a-z0-9 -]*?)(?:\s+was|\s+is|\s+remained|\s+stayed|\s+continued)\b",norm(c)); return art(m.group(1)) if m else None
def resolve(s,c,prior):
    x=art(s)
    if x not in PRON:return x,"explicit",False
    z=ctxref(c)
    if z:return z,"uniquely_resolved",False
    if prior:
        rr=refs(prior)
        if len(rr)==1:return rr[0],"uniquely_resolved",False
    return x,"unresolved",True

def parse_clause(s,context="",insub=None,inops=(),prior=None,inqs=()):
    w,lq=lead(s); w,eq=embed(w); w,tq=trail(w); qs=tuple(sorted((*inqs,*lq,*eq,*tq),key=lambda x:(x.kind,x.value))); n=norm(w)
    if re.search(r"\band/or\b|\bor\b",n):return P("unsupported",reason="DISJUNCTIVE_CLAUSE")
    if insub and inherit_ok(n):
        if n in STATE:n=f"{insub} is {n}"
        else:
            own=re.match(r"^(?:did\s+not\s+|did\s+|(?:"+"|".join(MOD)+r")\s+)",n); pre="" if own else " ".join(v for k,v in inops if k in {"modal","negation"})
            n=f"{insub} {pre+' ' if pre else ''}{n}"
    m=re.match(r"^(.+?)\s+did\s+too$",n)
    if m:
        if not prior:return P("unsupported",reason="ELLIPSIS_WITHOUT_ANTECEDENT")
        ss,op=subj(m.group(1)); ss,rf,amb=resolve(ss,context,prior)
        if amb:return P("ambiguous",reason="ELLIPSIS_SUBJECT_AMBIGUOUS")
        roles=[];done=False
        for k,v in prior.roles:
            if not done and k in {"agent","entity","subject","buyer","seller","source"}:roles.append((k,ss));done=True
            else:roles.append((k,v))
        return P("ok",(mk(prior.predicate,roles,(*prior.ops,*op),qs or prior.qs,rf),))
    for pat,pred in [(r"^(.+?)\s+stopped\s+transmitting$","stop_transmitting"),(r"^(.+?)\s+shut\s+down$","shutdown")]:
        m=re.match(pat,n)
        if m:
            ss,op=subj(m.group(1));ss,rf,amb=resolve(ss,context,prior)
            return P("ambiguous",reason="SUBJECT_REFERENCE_AMBIGUOUS") if amb else P("ok",(mk(pred,(("entity",ss),),op,qs,rf),))
    m=re.match(r"^(.+?)\s+(?:is|was)\s+(faster|slower|higher|lower|greater|less|cheaper|larger|smaller)\s+than\s+(.+)$",n)
    if m:
        a,rel,b=m.groups();a,op=subj(a);a,rf,amb=resolve(a,context,prior)
        return P("ambiguous",reason="COMPARATIVE_SUBJECT_AMBIGUOUS") if amb else P("ok",(mk("compare:"+rel,(("left",a),("right",b)),op,qs,rf),))
    m=re.match(r"^(.+?)\s+(?:was|is)\s+(not\s+)?associated\s+with\s+(.+)$",n)
    if m:
        a,ng,b=m.groups();a,op=subj(a);a,rf,amb=resolve(a,context,prior); op=list(op)+([("negation","not")] if ng else [])
        return P("ambiguous",reason="RELATION_SUBJECT_AMBIGUOUS") if amb else P("ok",(mk("associated_with",(("subject",a),("object",b)),op,qs,rf),))
    m=re.match(r"^(.+?)\s+(?:is|was)\s+(probably\s+)?(below|above)\s+(.+)$",n)
    if m:
        a,pr,rel,b=m.groups();a,op=subj(a);a,rf,amb=resolve(a,context,prior);b,bop,u=qty(b);op=list(op)+list(bop)+([("probability","probably")] if pr else [])
        return P("ambiguous",reason="THRESHOLD_SUBJECT_AMBIGUOUS") if amb else P("ok",(mk(rel,(("subject",a),("threshold",b)),op,(*qs,*u),rf),))
    m=re.match(r"^(.+?)\s+(?:is|was)\s+(\d+(?:\.\d+)?(?:\s+to\s+\d+(?:\.\d+)?)?)(?:\s+([a-z%]+))?$",n)
    if m:
        a,v,u=m.groups();a,op=subj(a);a,rf,amb=resolve(a,context,prior);qq=list(qs)+([q("unit",u)] if u else [])
        return P("ambiguous",reason="VALUE_SUBJECT_AMBIGUOUS") if amb else P("ok",(mk("value",(("subject",a),("value",v)),op,qq,rf),))
    m=re.match(r"^(.+?)\s+(be|is|was|are|were)\s+(not\s+)?([a-z]+)$",n)
    if m:
        a,_,ng,p=m.groups();a,op=subj(a);a,rf,amb=resolve(a,context,prior);op=list(op)+([("negation","not")] if ng else [])
        if amb:return P("ambiguous",reason="STATE_SUBJECT_AMBIGUOUS")
        if p in STATE:return P("ok",(mk("state:"+p,(("entity",a),),op,qs,rf),))
        if p in LEM:return P("ok",(mk(LEM[p],(("patient",a),),op,qs,rf),))
    m=re.match(r"^(.+?)\s+(may|might|must|should|can|could|will|would)\s+be\s+(not\s+)?([a-z]+)$",n)
    if m:
        a,mo,ng,p=m.groups();a,op=subj(a);a,rf,amb=resolve(a,context,prior)
        if amb:return P("ambiguous",reason="PASSIVE_SUBJECT_AMBIGUOUS")
        if p not in LEM:return P("unsupported",reason="UNSUPPORTED_PASSIVE_PREDICATE")
        return P("ok",(mk(LEM[p],(("patient",a),),(*op,("modal",mo),*((["negation","not"],) if False else ())),qs,rf),)) if not ng else P("ok",(mk(LEM[p],(("patient",a),),(*op,("modal",mo),("negation","not")),qs,rf),))
    m=re.match(r"^(.+?)\s+(sent|send|sends|shipped|ship|ships|delivered|deliver|delivers|sold|sell|sells)\s+(.+?)\s+to\s+(.+)$",n)
    if m:
        a,v,t,d=m.groups();a,op=subj(a);a,rf,amb=resolve(a,context,prior);p=LEM[v];r0="seller" if p=="sell" else "source";r3="buyer" if p=="sell" else "destination"
        return P("ambiguous",reason="DIRECTIONAL_SUBJECT_AMBIGUOUS") if amb else P("ok",(mk(p,((r0,a),("theme",t),(r3,d)),op,qs,rf),))
    m=re.match(r"^(.+?)\s+(bought|buy|buys)\s+(.+?)\s+from\s+(.+)$",n)
    if m:
        a,v,t,sr=m.groups();a,op=subj(a);a,rf,amb=resolve(a,context,prior)
        return P("ambiguous",reason="BUY_SUBJECT_AMBIGUOUS") if amb else P("ok",(mk(LEM[v],(("buyer",a),("theme",t),("seller",sr)),op,qs,rf),))
    m=re.match(r"^(.+?)\s+(transferred|transfer|transfers)\s+(.+?)\s+from\s+(.+?)\s+to\s+(.+)$",n)
    if m:
        a,v,t,sr,d=m.groups();a,op=subj(a);a,rf,amb=resolve(a,context,prior)
        return P("ambiguous",reason="TRANSFER_SUBJECT_AMBIGUOUS") if amb else P("ok",(mk(LEM[v],(("agent",a),("theme",t),("source",sr),("destination",d)),op,qs,rf),))
    m=re.match(rf"^(.+?)\s+(?:(did)\s+(not)\s+|(?:(may|might|must|should|can|could|will|would)\s+))?({VRE})(?:\s+(.+))?$",n)
    if m:
        a,_,ng,mo,v,b=m.groups();a,op=subj(a);a,rf,amb=resolve(a,context,prior);op=list(op)+([("negation","not")] if ng else [])+([("modal",mo)] if mo else [])
        if amb:return P("ambiguous",reason="SUBJECT_REFERENCE_AMBIGUOUS")
        p=LEM[v]
        if b:
            b,bop,u=qty(b); return P("ok",(mk(p,(("agent",a),("object",b)),(*op,*bop),(*qs,*u),rf),))
        return P("ok",(mk(p,(("entity",a),),op,qs,rf),)) if p in INTR else P("fragment",reason="MISSING_REQUIRED_OBJECT")
    if re.match(rf"^(?:{VRE})\b",n):return P("fragment",reason="MISSING_SUBJECT")
    return P("unsupported",reason="NO_BOUNDED_FRAME_PARSE")

def parse_root(root,context):
    if re.search(r"\band/or\b|\bor\b",norm(root)):return P("ambiguous",reason="UNSUPPORTED_OR_AMBIGUOUS_CONNECTIVE")
    b,l=lead(root);b,e=embed(b);qs=(*l,*e); parts=split_and(b);fs=[];insub=None;inops=();prior=None
    for i,c in enumerate(parts):
        p=parse_clause(c,context,insub if i else None,inops if i else (),prior,qs)
        if p.status!="ok" or len(p.frames)!=1:return p
        f=p.frames[0];fs.append(f);insub=next((v for k,v in f.roles if k in {"agent","entity","subject","buyer","seller","source","patient","left"}),None);inops=tuple((k,v) for k,v in f.ops if k in {"modal","negation","subject_quantifier"});prior=f
    return P("ok",tuple(fs))
def parse_child(s,context):
    if re.search(r"\band/or\b|\bor\b",norm(s)):return P("unsupported",reason="CHILD_CONNECTIVE_CORRUPTION")
    if len(split_and(s))>1:return P("fragment",reason="CHILD_RETAINS_MULTIPLE_PROPOSITIONS")
    return parse_clause(s,context)
def valid(c):
    miss=[k for k in ("case_id","root_id","root_text","profile_id","candidate_state","children") if k not in c]
    if miss:return ["MISSING_"+x.upper() for x in miss]
    e=[]
    if c["profile_id"]!=PROFILE_ID:e.append("UNSUPPORTED_PROFILE")
    if c["candidate_state"] not in {"NOT_NEEDED","DECLARED","ABSTAINED","FAILED"}:e.append("INVALID_CANDIDATE_STATE")
    if not isinstance(c["children"],list):return e+["CHILDREN_NOT_LIST"]
    if c["candidate_state"]=="DECLARED":
        if c.get("operator")!="all_of":e.append("DECLARED_REQUIRES_ALL_OF")
        if len(c["children"])<2:e.append("DECLARED_REQUIRES_TWO_CHILDREN")
    elif c["children"]:e.append("NON_DECLARED_MUST_NOT_HAVE_CHILDREN")
    ids=set()
    for x in c["children"]:
        if not isinstance(x,dict) or not isinstance(x.get("child_id"),str) or not isinstance(x.get("text"),str):e.append("INVALID_CHILD_SHAPE");continue
        if x["child_id"] in ids:e.append("DUPLICATE_CHILD_ID")
        ids.add(x["child_id"])
        if not x["text"].strip():e.append("EMPTY_CHILD_TEXT")
    return e
def out(c,d,find):
    r={"schema_version":"pc-evaluator-result-rc1.0","profile_id":c.get("profile_id"),"case_id":c.get("case_id"),"root_id":c.get("root_id"),"candidate_state":c.get("candidate_state"),"disposition":d,"findings":[asdict(x) for x in find]};r["canonical_sha256"]=sha(canon(r));return r
def evaluate(c:dict[str,Any]):
    f=[];e=valid(c)
    if e:return out(c,"INVALID_INPUT",[Finding("STRUCTURAL_VALIDITY","FAIL",x,x) for x in e])
    f.append(Finding("STRUCTURAL_VALIDITY","PASS","VALID_SHAPE","valid"));st=c["candidate_state"]
    if st in {"ABSTAINED","FAILED"}:return out(c,"INDETERMINATE",f+[Finding("PROFILE_MEMBERSHIP","INDETERMINATE","UPSTREAM_"+st,"no candidate")])
    rp=parse_root(c["root_text"],c.get("context_text","") or "")
    if rp.status=="ambiguous":return out(c,"INDETERMINATE",f+[Finding("AMBIGUITY_GATE","INDETERMINATE",rp.reason,"root binding ambiguous")])
    if rp.status!="ok":return out(c,"INDETERMINATE",f+[Finding("PROFILE_MEMBERSHIP","INDETERMINATE",rp.reason,"root outside bounded profile")])
    rf=list(rp.frames);f.append(Finding("PROFILE_MEMBERSHIP","PASS","UNIQUE_BOUNDED_ROOT_PARSE",str(len(rf))))
    if st=="NOT_NEEDED":return out(c,"ACCEPTABLE_WITHIN_PROFILE" if len(rf)==1 else "REJECT_UNSAFE",f+[Finding("CORRESPONDENCE","PASS" if len(rf)==1 else "FAIL","SINGLE_FRAME_NOT_NEEDED" if len(rf)==1 else "MULTIPLE_ROOT_FRAMES_NOT_DECLARED","")])
    cf=[]
    for ch in c["children"]:
        p=parse_child(ch["text"],c.get("context_text","") or "")
        if p.status=="fragment":return out(c,"REJECT_UNSAFE",f+[Finding("PROPOSITIONHOOD","FAIL",p.reason,ch["child_id"])])
        if p.status!="ok":
            if p.reason=="CHILD_CONNECTIVE_CORRUPTION":return out(c,"REJECT_UNSAFE",f+[Finding("CONNECTIVE_PRESERVATION","FAIL",p.reason,ch["child_id"])])
            return out(c,"INDETERMINATE",f+[Finding("AMBIGUITY_GATE","INDETERMINATE",p.reason,ch["child_id"])])
        cf.append(p.frames[0])
    rk=sorted(x.key() for x in rf);ck=sorted(x.key() for x in cf)
    if len(rf)!=len(cf):return out(c,"REJECT_UNSAFE",f+[Finding("BIJECTION","FAIL","FRAME_COUNT_MISMATCH","")])
    if len(ck)!=len(set(ck)):return out(c,"REJECT_UNSAFE",f+[Finding("BIJECTION","FAIL","DUPLICATE_CHILD_FRAME","")])
    if rk==ck:return out(c,"ACCEPTABLE_WITHIN_PROFILE",f+[Finding("BIJECTION","PASS","ONE_TO_ONE_FRAME_CORRESPONDENCE",""),Finding("REFERENCE_ARGUMENT_BINDING","PASS","BINDINGS_PRESERVED",""),Finding("OPERATOR_ATTACHMENT","PASS","OPERATORS_PRESERVED",""),Finding("RECONSTRUCTION","PASS","BOUND_FRAMES_RECONSTRUCT_ROOT","")])
    return out(c,"REJECT_UNSAFE",f+[Finding("BIJECTION","FAIL","FRAME_BINDING_MISMATCH","root/child bound frames differ")])
def evaluate_jsonl(path):
    return [evaluate(json.loads(x)) for x in open(path,encoding="utf-8") if x.strip()]
if __name__=="__main__":
    import argparse
    p=argparse.ArgumentParser();p.add_argument("input_jsonl");p.add_argument("output_jsonl");a=p.parse_args()
    with open(a.output_jsonl,"w",encoding="utf-8",newline="\n") as h:
        for r in evaluate_jsonl(a.input_jsonl):h.write(canon(r)+"\n")
