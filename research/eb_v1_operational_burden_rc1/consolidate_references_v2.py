#!/usr/bin/env python3
from __future__ import annotations
import argparse, hashlib, json
from collections import Counter
from pathlib import Path
from review_common_v2 import canonical_hash, load, packet_relation_ids, validate_review, LABELS

def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()

def consolidate(packet: Path, reviews: list[Path], used: set[str]) -> dict:
    parsed=[]; reviewer_ids=[]
    for p in reviews:
        labels,rid=validate_review(p,packet,'reference',used)
        parsed.append(labels); reviewer_ids.append(rid)
    packet_obj=load(packet); final=[]
    for relation_id in packet_relation_ids(packet_obj):
        votes=[r[relation_id] for r in parsed]; counts=Counter(votes); winner=None
        for label,count in counts.items():
            if label!='UNRESOLVED' and count>=2:
                winner=label; break
        final.append({'relation_id':relation_id,'label':winner or 'UNRESOLVED','vote_counts':{k:counts.get(k,0) for k in sorted(LABELS)}})
    return {'schema':'eb-v1-operational-burden-rc1-reference-v1','packet_canonical_sha256':canonical_hash(packet_obj),'reviewer_ids':reviewer_ids,'judgments':final,'label_counts':dict(Counter(x['label'] for x in final))}

def main():
    ap=argparse.ArgumentParser(); ap.add_argument('--amber-packet',type=Path,required=True); ap.add_argument('--cobalt-packet',type=Path,required=True)
    for arm in ('amber','cobalt'):
        for i in range(1,4): ap.add_argument(f'--{arm}-r{i}',type=Path,required=True)
    ap.add_argument('--out-dir',type=Path,required=True); args=ap.parse_args(); args.out_dir.mkdir(parents=True,exist_ok=True)
    used=set(); sets={}
    for arm,packet in [('amber',args.amber_packet),('cobalt',args.cobalt_packet)]:
        reviews=[getattr(args,f'{arm}_r{i}') for i in range(1,4)]
        ref=consolidate(packet,reviews,used); out=args.out_dir/f'REFERENCE_{arm.upper()}.json'; out.write_text(json.dumps(ref,indent=2,sort_keys=True)+'\n')
        sets[arm]={'packet_canonical_sha256':ref['packet_canonical_sha256'],'reference_file':out.name,'reference_sha256':sha(out),'review_files':{p.name:sha(p) for p in reviews},'reviewer_ids':ref['reviewer_ids'],'label_counts':ref['label_counts']}
    receipt={'schema':'eb-v1-operational-burden-rc1-reference-freeze-receipt-v1','sets':sets,'reviewer_ids_unique':len(used)==6}
    rp=args.out_dir/'REFERENCE_FREEZE_RECEIPT.json'; rp.write_text(json.dumps(receipt,indent=2,sort_keys=True)+'\n'); print(json.dumps(receipt,indent=2,sort_keys=True))
if __name__=='__main__': main()
