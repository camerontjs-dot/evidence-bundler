#!/usr/bin/env python3
from __future__ import annotations

import argparse
import hashlib
import json
from collections import Counter
from pathlib import Path

from review_common import ACTION, load, validate_review


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def ref_labels(path: Path) -> dict[str, str]:
    obj = load(path)
    if obj.get('schema') != 'eb-v1-operational-burden-rc1-reference-v1':
        raise ValueError(f'{path}: reference schema')
    out = {}
    for j in obj.get('judgments', []):
        rid = j.get('relation_id')
        label = j.get('label')
        if rid in out:
            raise ValueError(f'{path}: duplicate reference relation')
        out[rid] = label
    return out


def mapped(label: str) -> str:
    return ACTION[label]


def reviewer_counts(review: dict[str, str], reference: dict[str, str], ids: list[str]) -> dict[str, int]:
    out = {'false_keep': 0, 'false_drop': 0, 'unresolved': 0, 'exact_label_error': 0}
    for rid in ids:
        gold = reference[rid]
        got = review[rid]
        if got != gold:
            out['exact_label_error'] += 1
        ga, ra = mapped(gold), mapped(got)
        if ra == 'UNRESOLVED':
            out['unresolved'] += 1
        elif ga == 'DROP' and ra == 'KEEP':
            out['false_keep'] += 1
        elif ga == 'KEEP' and ra == 'DROP':
            out['false_drop'] += 1
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--map', type=Path, required=True)
    ap.add_argument('--amber-packet', type=Path, required=True)
    ap.add_argument('--cobalt-packet', type=Path, required=True)
    ap.add_argument('--amber-reference', type=Path, required=True)
    ap.add_argument('--cobalt-reference', type=Path, required=True)
    for arm in ('amber', 'cobalt'):
        for i in (1, 2):
            ap.add_argument(f'--{arm}-t{i}', type=Path, required=True)
    ap.add_argument('--reference-freeze-commit', required=True)
    ap.add_argument('--out', type=Path, required=True)
    args = ap.parse_args()

    sup = load(args.map)
    if sup.get('schema') != 'eb-v1-operational-burden-rc1-supervisor-map-v1':
        raise ValueError('supervisor map schema')
    refs = {
        'amber': ref_labels(args.amber_reference),
        'cobalt': ref_labels(args.cobalt_reference),
    }

    used = set()
    receipt_path = args.amber_reference.parent / 'REFERENCE_FREEZE_RECEIPT.json'
    receipt = load(receipt_path)
    for info in receipt['sets'].values():
        used.update(info['reviewer_ids'])
    if len(used) != 6:
        raise ValueError('reference reviewer IDs not unique')

    tests = {}
    packets = {'amber': args.amber_packet, 'cobalt': args.cobalt_packet}
    for arm in ('amber', 'cobalt'):
        tests[arm] = []
        for i in (1, 2):
            p = getattr(args, f'{arm}_t{i}')
            labels, _ = validate_review(p, packets[arm], 'test', used)
            tests[arm].append(labels)
    if len(used) != 10:
        raise ValueError('all RC1 reviewer IDs must be unique')

    scoreable = []
    unresolved_shared = []
    for row in sup['matched_relationships']:
        a_id = row['amber_relation_id']
        c_id = row['cobalt_relation_id']
        a_lab = refs['amber'][a_id]
        c_lab = refs['cobalt'][c_id]
        if a_lab != 'UNRESOLVED' and c_lab != 'UNRESOLVED':
            scoreable.append(row)
        else:
            unresolved_shared.append({
                'semantic_key': row['semantic_key'],
                'proposition_id': row['proposition_id'],
                'amber_reference': a_lab,
                'cobalt_reference': c_lab,
            })

    lane_count = len({x['proposition_id'] for x in scoreable})
    coverage_ok = len(scoreable) >= 49 and lane_count == 18

    primary = {}
    arm_field = {'amber': 'amber_relation_id', 'cobalt': 'cobalt_relation_id'}
    for arm in ('amber', 'cobalt'):
        ids = [x[arm_field[arm]] for x in scoreable]
        per = [reviewer_counts(r, refs[arm], ids) for r in tests[arm]]
        pooled = {k: sum(x[k] for x in per) for k in per[0]}
        action_disagreement = sum(
            1 for rid in ids if mapped(tests[arm][0][rid]) != mapped(tests[arm][1][rid])
        )
        exact_disagreement = sum(1 for rid in ids if tests[arm][0][rid] != tests[arm][1][rid])
        primary[arm] = {
            'per_reviewer': per,
            'pooled': pooled,
            'inter_reviewer_action_disagreement': action_disagreement,
            'inter_reviewer_exact_label_disagreement': exact_disagreement,
        }

    larger = next(k for k, v in sup['arm_mapping'].items() if v == '10/7')
    smaller = next(k for k, v in sup['arm_mapping'].items() if v == '5/3')
    worse = {
        'false_keep': primary[larger]['pooled']['false_keep'] > primary[smaller]['pooled']['false_keep'],
        'false_drop': primary[larger]['pooled']['false_drop'] > primary[smaller]['pooled']['false_drop'],
        'unresolved': primary[larger]['pooled']['unresolved'] > primary[smaller]['pooled']['unresolved'],
        'action_disagreement': primary[larger]['inter_reviewer_action_disagreement'] > primary[smaller]['inter_reviewer_action_disagreement'],
    }

    if not coverage_ok:
        disposition = 'INCONCLUSIVE'
        conclusion = 'REFERENCE_COVERAGE_GUARD_FAILED'
    elif any(worse.values()):
        disposition = 'FALSIFIED'
        conclusion = 'OPERATIONAL_DECISION_HARM_OBSERVED'
    else:
        disposition = 'SUPPORTED FOR PROMOTION'
        conclusion = 'NO_OBSERVED_OPERATIONAL_DECISION_HARM'

    ref_flips = []
    for row in sup['matched_relationships']:
        al = refs['amber'][row['amber_relation_id']]
        cl = refs['cobalt'][row['cobalt_relation_id']]
        if al != cl:
            ref_flips.append({
                'semantic_key': row['semantic_key'],
                'proposition_id': row['proposition_id'],
                'amber_reference': al,
                'cobalt_reference': cl,
            })

    larger_only = sup['larger_arm_only_relationships']
    lo_resolved = [x for x in larger_only if refs[larger][x['relation_id']] != 'UNRESOLVED']
    lo_stats = []
    for review in tests[larger]:
        lo_stats.append(reviewer_counts(review, refs[larger], [x['relation_id'] for x in lo_resolved]))

    out = {
        'schema': 'eb-v1-operational-burden-rc1-result-v1',
        'reference_freeze_commit': args.reference_freeze_commit,
        'arm_mapping': sup['arm_mapping'],
        'shared_relationship_count': len(sup['matched_relationships']),
        'scoreable_matched_relationship_count': len(scoreable),
        'scoreable_lane_count': lane_count,
        'coverage_guard_pass': coverage_ok,
        'unresolved_shared_reference_relationships': unresolved_shared,
        'primary': primary,
        'larger_arm': larger,
        'smaller_arm': smaller,
        'larger_worse_flags': worse,
        'primary_conclusion': conclusion,
        'primary_disposition': disposition,
        'reference_label_counts': {
            arm: dict(Counter(refs[arm].values())) for arm in ('amber', 'cobalt')
        },
        'shared_reference_label_flips': ref_flips,
        'larger_arm_only': {
            'relationship_count': len(larger_only),
            'resolved_reference_count': len(lo_resolved),
            'reference_label_counts': dict(Counter(refs[larger][x['relation_id']] for x in larger_only)),
            'per_reviewer': lo_stats,
        },
        'input_hashes': {
            'map_sha256': sha(args.map),
            'amber_reference_sha256': sha(args.amber_reference),
            'cobalt_reference_sha256': sha(args.cobalt_reference),
            'amber_test_1_sha256': sha(args.amber_t1),
            'amber_test_2_sha256': sha(args.amber_t2),
            'cobalt_test_1_sha256': sha(args.cobalt_t1),
            'cobalt_test_2_sha256': sha(args.cobalt_t2),
        },
        'stop_boundary': True,
    }
    args.out.write_text(json.dumps(out, indent=2, sort_keys=True) + '\n', encoding='utf-8')
    print(json.dumps({
        'primary_disposition': disposition,
        'primary_conclusion': conclusion,
        'scoreable_matched_relationship_count': len(scoreable),
        'scoreable_lane_count': lane_count,
        'larger_worse_flags': worse,
    }, indent=2, sort_keys=True))


if __name__ == '__main__':
    main()
