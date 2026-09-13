#!/usr/bin/env python3
from __future__ import annotations
import hashlib, json, random
from pathlib import Path

ROOT=Path('/mnt/data/k7op/artifacts/k7')
OUT=Path('/mnt/data/operational_burden_rc0')
OUT.mkdir(exist_ok=True)

BASE=json.loads((ROOT/'BASELINE_5_3_RECEIPT.json').read_text())
TREAT=json.loads((ROOT/'TREATMENT_10_7_RECEIPT.json').read_text())
BURDEN=json.loads((ROOT/'KNOWN_DISTRACTOR_BURDEN.json').read_text())

assert BASE['retained_relationship_count']==54
assert TREAT['retained_relationship_count']==96
assert BASE['normative_lane_count']==TREAT['normative_lane_count']==18

# Gold from predecessor burden + PR72 terminal fact that every unresolved relation was resolved nonmaterial.
gold={}
for lane in BURDEN['lanes']:
    pid=lane['proposition_id']
    for r in lane['relationships']:
        cls=r['classification']
        if cls=='required': label='MATERIAL_FOR_PROPOSITION'
        elif cls in {'known_non_required_or_distractor','unresolved_not_safely_classifiable'}:
            label='NONMATERIAL_FOR_PROPOSITION'
        else: raise ValueError(cls)
        gold[(pid,r['evidence_id'])]=label

# proposition text and retained rows
prop_text={}
for case in TREAT['cases']:
    for t in case['primary_targets']:
        prop_text[t['proposition_id']]=t['text']

def retained(profile):
    by_lane={}
    for case in profile['cases']:
        for row in case['candidate_rows']:
            if row['selection_state']!='retained': continue
            key=(row['proposition_id'],row['evidence_id'])
            by_lane.setdefault(row['proposition_id'],[]).append({
                'semantic_key': key,
                'source_id': row['source_id'],
                'passage_id': row['passage_id'],
                'passage_sha256': row['passage_sha256'],
                'text': row['text'],
            })
    return by_lane

b=retained(BASE); t=retained(TREAT)
BSET={x['semantic_key'] for xs in b.values() for x in xs}
TSET={x['semantic_key'] for xs in t.values() for x in xs}
assert len(BSET)==54 and len(TSET)==96 and BSET <= TSET

arms={'amber':('5/3',b,15485863),'cobalt':('10/7',t,32452843)}
answer={'schema':'eb-v1-operational-burden-answer-key-v1','arm_mapping':{},'shared_semantic_relationship_count':len(BSET),'arms':{}}
exposure={'schema':'eb-v1-operational-burden-exposure-v1','arms':{}}

def opaque(prefix,*parts,n=16):
    raw='|'.join((prefix,*parts)).encode()
    return hashlib.sha256(raw).hexdigest()[:n]

def canonical_hash(obj):
    raw=json.dumps(obj,sort_keys=True,separators=(',',':'),ensure_ascii=False).encode()
    return hashlib.sha256(raw).hexdigest()

for arm,(profile,lanes,seed) in arms.items():
    rng=random.Random(seed)
    lane_items=[]
    ans_rel={}
    semantic_to_opaque={}
    pids=list(lanes)
    rng.shuffle(pids)
    for pid in pids:
        lid=opaque('lane',arm,pid)
        rels=list(lanes[pid])
        rng.shuffle(rels)
        passages=[]
        for rel in rels:
            spid,eid=rel['semantic_key']
            rid=opaque('relation',arm,spid,eid)
            semantic_to_opaque[f'{spid}|{eid}']=rid
            passages.append({'relation_id':rid,'passage_text':rel['text']})
            ans_rel[rid]={
                'semantic_key':f'{spid}|{eid}',
                'gold_label':gold[(spid,eid)],
                'shared_with_other_arm':(spid,eid) in BSET,
                'source_id':rel['source_id'],
                'passage_id':rel['passage_id'],
                'passage_sha256':rel['passage_sha256'],
            }
        lane_items.append({'lane_id':lid,'proposition_text':prop_text[pid],'passages':passages})
    packet={
        'schema':'eb-v1-operational-blind-review-packet-v1',
        'set_id':arm,
        'instructions_ref':'REVIEWER_RUBRIC.md',
        'lanes':lane_items,
    }
    ph=canonical_hash(packet)
    (OUT/f'BLIND_REVIEW_PACKET_{arm.upper()}.json').write_text(json.dumps(packet,indent=2,ensure_ascii=False)+'\n')
    answer['arm_mapping'][arm]=profile
    answer['arms'][arm]={
        'packet_canonical_sha256':ph,
        'profile':profile,
        'relationship_count':sum(len(x['passages']) for x in lane_items),
        'relations':ans_rel,
        'semantic_to_opaque':semantic_to_opaque,
    }
    # exposure metrics
    all_text=[p['passage_text'] for l in lane_items for p in l['passages']]
    unique_physical={}
    unique_content={}
    for xs in lanes.values():
        for rel in xs:
            unique_physical.setdefault((rel['source_id'],rel['passage_id']),rel['text'])
            unique_content.setdefault(rel['passage_sha256'],rel['text'])
    uniq=list(unique_physical.values())
    uniq_content=list(unique_content.values())
    exposure['arms'][arm]={
        'profile_hidden_from_reviewers':profile,
        'lane_count':len(lane_items),
        'relationship_count':len(all_text),
        'unique_physical_passage_count':len(uniq),
        'unique_content_passage_count':len(uniq_content),
        'presented_passage_characters':sum(len(x) for x in all_text),
        'presented_passage_whitespace_tokens':sum(len(x.split()) for x in all_text),
        'unique_passage_characters':sum(len(x) for x in uniq),
        'unique_passage_whitespace_tokens':sum(len(x.split()) for x in uniq),
        'packet_canonical_sha256':ph,
    }

# exact matched cross-arm mapping by semantic key
answer['matched_relationships']=[]
for pid,eid in sorted(BSET):
    sk=f'{pid}|{eid}'
    answer['matched_relationships'].append({
        'semantic_key':sk,
        'gold_label':gold[(pid,eid)],
        'amber_relation_id':answer['arms']['amber']['semantic_to_opaque'][sk],
        'cobalt_relation_id':answer['arms']['cobalt']['semantic_to_opaque'][sk],
    })

# treatment-only mapping
answer['larger_arm_only_relationships']=[]
for pid,eid in sorted(TSET-BSET):
    sk=f'{pid}|{eid}'
    answer['larger_arm_only_relationships'].append({
        'semantic_key':sk,
        'gold_label':gold[(pid,eid)],
        'relation_id':answer['arms']['cobalt']['semantic_to_opaque'][sk],
    })

# remove helper mapping from final answer key duplicated under arm
for arm in answer['arms']:
    answer['arms'][arm].pop('semantic_to_opaque')

(OUT/'SUPERVISOR_ANSWER_KEY.json').write_text(json.dumps(answer,indent=2,sort_keys=True)+'\n')
(OUT/'EXPOSURE_METRICS.json').write_text(json.dumps(exposure,indent=2,sort_keys=True)+'\n')

for arm in arms:
    print(arm, answer['arm_mapping'][arm], exposure['arms'][arm])
print('shared',len(answer['matched_relationships']),'larger-only',len(answer['larger_arm_only_relationships']))
print('larger-only material',sum(x['gold_label']=='MATERIAL_FOR_PROPOSITION' for x in answer['larger_arm_only_relationships']))
