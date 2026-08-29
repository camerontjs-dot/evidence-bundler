#!/usr/bin/env python3
from __future__ import annotations
import argparse, collections, hashlib, json, math, re
from pathlib import Path
from typing import Any, Callable
from evaluator import evaluate, qualify_target, load_apparatus
TOKEN=re.compile(r"\w+")
def toks(s:str)->list[str]: return TOKEN.findall(s.lower())
def dump(path:Path,obj:Any): path.write_text(json.dumps(obj,sort_keys=True,indent=2)+"\n",encoding='utf-8')
def hits(ids:list[str],scores:list[float]|None=None)->list[dict[str,Any]]:
    scores=scores or [float(len(ids)-i) for i in range(len(ids))]
    return [{'passage_id':p,'rank':i+1,'score':float(scores[i])} for i,p in enumerate(ids)]
def runtime(root:Path):
    cases,passages,gold,scopes=load_apparatus(root); by=collections.defaultdict(list)
    for p in passages: by[p['case_id']].append(p)
    for v in by.values(): v.sort(key=lambda p:(p['source_order'],p['passage_order']))
    return cases,by,gold,scopes

def rank_score(case,ps,scorefn):
    vals=[(float(scorefn(case,p)),p['source_order'],p['passage_order'],p['passage_id']) for p in ps]
    vals.sort(key=lambda x:(-x[0],x[1],x[2],x[3])); return hits([x[3] for x in vals[:5]],[x[0] for x in vals[:5]])
def token_overlap(c,p):
    q=set(toks(c['claim_text'])); t=set(toks(p['text'])); return len(q&t)/(len(q) or 1)
def char_ngram(c,p):
    def grams(s):
        s=re.sub(r'\s+',' ',s.lower()); return {s[i:i+3] for i in range(max(0,len(s)-2))}
    a,b=grams(c['claim_text']),grams(p['text']); return len(a&b)/(len(a|b) or 1)
def passage_length(c,p): return float(len(toks(p['text'])))
def source_position(c,p): return float(100-p['source_order']*10-p['passage_order'])
def metadata_pattern(c,p):
    md=p.get('runtime_metadata',{}); return float(len(md)*10 + sum(ch.isdigit() for ch in p['source_id']))
def construction_style(c,p):
    # Plausible runtime-only style gamer: favors semantic-looking presentational frames.
    txt=p['text'].lower(); cues=['policy statement:','technical explanation:','answer:','statement=','conditional summary:']
    return float(sum(3 for x in cues if x in txt) + (2 if len(toks(txt))>35 else 0) + len(p.get('runtime_metadata',{})))
def cue_swap(c,p):
    # Different runtime-only benchmark-aware cue hypothesis, intentionally independent of gold.
    txt=p['text'].lower(); return float((4 if p['source_id'].startswith(('REG.','register-','r-')) else 0)+(3 if any(x in txt for x in ('procedure entry','incident review','question:')) else 0)+(1 if p['passage_order']==2 else 0))
def hard_negative_lexical(c,p): return token_overlap(c,p)*10 + (2 if any(x in p['text'].lower() for x in ('retired','tabletop','questionnaire','alternative profile','historical','test fixture','rejected','troubleshooting')) else 0)
def sentence_position_gamer(c,p):
    txt=p['text'].lower()
    neutral_prefix=('the record was reviewed','this entry uses','the note was retained')
    return 0.0 if txt.startswith(neutral_prefix) else 1.0

def answer_marker_gamer(c,p):
    # Query-independent benchmark-aware surface hypothesis. It tries to identify
    # a direct-looking answer by avoiding contextual markers commonly used in
    # synthetic decoys. Because RC4 declarative distractors share the same
    # surface posture, this should not recover semantic role reliably.
    txt=p['text'].lower()
    markers=('retired','tabletop','questionnaire','alternative profile','historical','test fixture','rejected','troubleshooting','fictional','synthetic')
    return float(-sum(1 for x in markers if x in txt))


def bow_tfidf_rank(case,ps):
    docs=[toks(p['text']) for p in ps]; q=toks(case['claim_text']); n=len(docs); df=collections.Counter(w for d in docs for w in set(d)); qtf=collections.Counter(q)
    def vec(tokens):
        tf=collections.Counter(tokens); return {w:c*math.log((n+1)/(df[w]+1))+c for w,c in tf.items()}
    qv=vec(q); qnorm=math.sqrt(sum(v*v for v in qv.values())) or 1
    vals=[]
    for p,d in zip(ps,docs):
        v=vec(d); norm=math.sqrt(sum(x*x for x in v.values())) or 1; sc=sum(qv.get(w,0)*x for w,x in v.items())/(qnorm*norm); vals.append((sc,p))
    vals.sort(key=lambda x:(-x[0],x[1]['source_order'],x[1]['passage_order'],x[1]['passage_id']))
    return hits([p['passage_id'] for _,p in vals[:5]],[s for s,_ in vals[:5]])

def generate(root:Path,control:str)->list[dict[str,Any]]:
    cases,by,gold,_=runtime(root); gby={g['case_id']:g for g in gold}; out=[]
    if control=='null': return []
    for c in cases:
        ps=by[c['case_id']]
        if control=='oracle': ids=[gby[c['case_id']]['decisive'][0]['passage_id']]+[p['passage_id'] for p in ps if p['passage_id']!=gby[c['case_id']]['decisive'][0]['passage_id']][:4]; h=hits(ids)
        elif control=='first_n_source_order': h=hits([p['passage_id'] for p in ps[:5]])
        elif control=='return_all': h=hits([p['passage_id'] for p in ps])
        elif control=='token_overlap': h=rank_score(c,ps,token_overlap)
        elif control=='bow_tfidf': h=bow_tfidf_rank(c,ps)
        elif control=='character_ngram': h=rank_score(c,ps,char_ngram)
        elif control=='hard_negative_biased_lexical': h=rank_score(c,ps,hard_negative_lexical)
        elif control=='passage_length_heuristic': h=rank_score(c,ps,passage_length)
        elif control=='source_position_heuristic': h=rank_score(c,ps,source_position)
        elif control=='metadata_identifier_pattern_heuristic': h=rank_score(c,ps,metadata_pattern)
        elif control=='runtime_construction_style_gamer': h=rank_score(c,ps,construction_style)
        elif control=='cue_swap_gamer': h=rank_score(c,ps,cue_swap)
        elif control=='runtime_answer_marker_gamer': h=rank_score(c,ps,answer_marker_gamer)
        elif control=='runtime_sentence_position_gamer': h=rank_score(c,ps,sentence_position_gamer)
        elif control=='provenance_corrupt': h=[{'passage_id':'corrupt-'+p['passage_id'],'rank':i+1,'score':1.0} for i,p in enumerate(ps[:5])]
        elif control in ('completeness_aperture_liar','semantic_answerability_liar'):
            # Deliberately attempt an unsupported receipt claim. The frozen result
            # schema forbids these fields, so the evaluator must fail closed.
            h=[]
        else: raise ValueError(control)
        row={'case_id':c['case_id'],'hits':h}
        if control=='completeness_aperture_liar': row['completeness_claim']=True
        if control=='semantic_answerability_liar': row['answerable_claim']=True
        out.append(row)
    return out

def main():
    ap=argparse.ArgumentParser(); ap.add_argument('--benchmark-root',type=Path,required=True); ap.add_argument('--thresholds',type=Path,required=True); ap.add_argument('--output',type=Path,required=True); ap.add_argument('--controls',nargs='+',required=True)
    a=ap.parse_args(); th=json.loads(a.thresholds.read_text()); rec={'controls':{},'hybrid_sealed_exposed':False,'semantic_sealed_exposed':False}
    for name in a.controls:
        raw=generate(a.benchmark_root,name); ev=evaluate(a.benchmark_root,raw); qualifies,failures=qualify_target(ev,th)
        raw_sha=hashlib.sha256(json.dumps(raw,sort_keys=True,separators=(',',':')).encode()).hexdigest()
        rec['controls'][name]={'evaluation':ev,'qualifies_target_gate':qualifies,'qualification_failures':failures,'raw_sha256':raw_sha,'receipt_surface_supported': name not in ('completeness_aperture_liar','semantic_answerability_liar'), 'unsupported_receipt_claim_attempted': name in ('completeness_aperture_liar','semantic_answerability_liar')}
    dump(a.output,rec); print(json.dumps(rec,sort_keys=True,indent=2))
if __name__=='__main__': main()
