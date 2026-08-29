#!/usr/bin/env python3
from __future__ import annotations
import argparse, hashlib, json
from pathlib import Path
from typing import Any
from evaluator import load_apparatus, evaluate

def main()->None:
    ap=argparse.ArgumentParser(); ap.add_argument('--benchmark-root',type=Path,required=True); ap.add_argument('--raw-output',type=Path,required=True); ap.add_argument('--evaluation-output',type=Path,required=True)
    a=ap.parse_args()
    from evidence_bundler.models.document import DocumentChunk
    from evidence_bundler.retrieval.bm25_retriever import BM25Retriever
    cases,passages,_,_=load_apparatus(a.benchmark_root); by={}
    for p in passages: by.setdefault(p['case_id'],[]).append(p)
    out=[]
    for c in cases:
        chunks=[]
        for p in sorted(by[c['case_id']],key=lambda x:(x['source_order'],x['passage_order'])):
            text=p['text']; start=(p['source_order']-1)*10000+(p['passage_order']-1)*4000
            chunks.append(DocumentChunk(chunk_id=p['passage_id'],source_id=p['source_id'],source_path=Path(p['source_id']+'.txt'),title=None,chunk_level='paragraph',parent_chunk_id=None,heading_path=[],section_tag=None,char_start=start,char_end=start+len(text),chunk_hash='sha256:'+hashlib.sha256(text.encode()).hexdigest(),excerpt=text,text=text))
        r=BM25Retriever(chunks); hs=r.query(c['claim_text'],top_k=5,score_floor=0.0)
        out.append({'case_id':c['case_id'],'hits':[{'passage_id':h.chunk.chunk_id,'rank':h.rank,'score':h.score} for h in hs]})
    raw=json.dumps(out,sort_keys=True,indent=2)+"\n"; a.raw_output.write_text(raw,encoding='utf-8')
    ev=evaluate(a.benchmark_root,out); a.evaluation_output.write_text(json.dumps(ev,sort_keys=True,indent=2)+"\n",encoding='utf-8')
    print(json.dumps({'raw_sha256':hashlib.sha256(raw.encode()).hexdigest(),'evaluation':ev},sort_keys=True,indent=2))
if __name__=='__main__': main()
