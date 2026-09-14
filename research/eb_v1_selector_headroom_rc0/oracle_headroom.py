#!/usr/bin/env python3
import argparse, hashlib, json, tempfile, zipfile
from collections import Counter
from pathlib import Path
from statistics import mean, median

EXPECTED_ARTIFACT_SHA256 = '3424e70988a2ca878e97f6eeaf855cd5ebbd449413536841872bd485de74819d'
PR63_RUN = 34649326414
PR63_ARTIFACT_ID = 10282804289
PR72_HEAD = '22d83d9af465a026eb58ff64888267c4fce18619'
PR72_CONCLUSION = 'FIXED_K_WIDENING_REJECTED_ON_COMPLETED_QUALIFICATION_GOLD'


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open('rb') as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b''):
            h.update(chunk)
    return h.hexdigest()


def load_inputs(zip_path: Path):
    digest = sha256(zip_path)
    if digest != EXPECTED_ARTIFACT_SHA256:
        raise SystemExit(f'artifact sha256 mismatch: {digest}')
    td = tempfile.TemporaryDirectory()
    with zipfile.ZipFile(zip_path) as z:
        z.extractall(td.name)
    root = Path(td.name) / 'artifacts' / 'k7'
    treatment = json.loads((root / 'TREATMENT_10_7_RECEIPT.json').read_text())
    burden = json.loads((root / 'KNOWN_DISTRACTOR_BURDEN.json').read_text())
    return td, treatment, burden


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--artifact-zip', type=Path, required=True)
    ap.add_argument('--output', type=Path, required=True)
    args = ap.parse_args()
    td, treatment, burden = load_inputs(args.artifact_zip)
    try:
        required = {
            (lane['proposition_id'], row['evidence_id'])
            for lane in burden['lanes']
            for row in lane['relationships']
            if row['classification'] == 'required'
        }
        lanes = {}
        for case in treatment['cases']:
            for row in case['raw_retrieval']:
                lanes.setdefault(row['proposition_id'], []).append(row)
        for rows in lanes.values():
            rows.sort(key=lambda row: row['rank'])
        if set(lanes) != {lane['proposition_id'] for lane in burden['lanes']}:
            raise SystemExit('lane identity mismatch')

        lane_rows = []
        required_rows = []
        for proposition_id, rows in sorted(lanes.items()):
            req = [row for row in rows if (proposition_id, row['evidence_id']) in required]
            if not req:
                raise SystemExit(f'no qualification-required relation in lane {proposition_id}')
            required_rows += [(proposition_id, row) for row in req]
            lane_rows.append({
                'proposition_id': proposition_id,
                'candidate_count': len(rows),
                'required_count': len(req),
                'required_ranks': [row['rank'] for row in req],
                'deepest_required_rank': max(row['rank'] for row in req),
                'oracle_removable_relationships': len(rows) - len(req),
            })

        fixed = []
        for k in range(1, 8):
            retained = required_kept = fully_covered = 0
            for proposition_id, rows in lanes.items():
                selected = rows[:k]
                retained += len(selected)
                selected_ids = {row['evidence_id'] for row in selected}
                req = [row for row in rows if (proposition_id, row['evidence_id']) in required]
                got = sum(row['evidence_id'] in selected_ids for row in req)
                required_kept += got
                fully_covered += int(got == len(req))
            fixed.append({
                'k': k,
                'retained_relationships': retained,
                'required_recall': required_kept / len(required_rows),
                'required_kept': required_kept,
                'fully_covered_lanes': fully_covered,
            })

        required_ratios = [
            row['score'] / lanes[proposition_id][0]['score']
            for proposition_id, row in required_rows
        ]
        lossless_ratio = min(required_ratios)
        threshold_retained = threshold_req = threshold_full = 0
        for proposition_id, rows in lanes.items():
            top = rows[0]['score']
            selected = [row for row in rows if row['score'] / top >= lossless_ratio]
            threshold_retained += len(selected)
            ids = {row['evidence_id'] for row in selected}
            req = [row for row in rows if (proposition_id, row['evidence_id']) in required]
            got = sum(row['evidence_id'] in ids for row in req)
            threshold_req += got
            threshold_full += int(got == len(req))

        gap_retained = gap_req = gap_full = 0
        gap_failures = []
        for proposition_id, rows in lanes.items():
            if len(rows) <= 1:
                cut = len(rows)
            else:
                gaps = [
                    (rows[i]['score'] - rows[i + 1]['score']) / rows[i]['score']
                    for i in range(len(rows) - 1)
                ]
                cut = max(range(len(gaps)), key=lambda i: gaps[i]) + 1
            selected = rows[:cut]
            gap_retained += len(selected)
            ids = {row['evidence_id'] for row in selected}
            req = [row for row in rows if (proposition_id, row['evidence_id']) in required]
            got = sum(row['evidence_id'] in ids for row in req)
            gap_req += got
            gap_full += int(got == len(req))
            if got != len(req):
                gap_failures.append({
                    'proposition_id': proposition_id,
                    'cut_after_rank': cut,
                    'missed_required': [
                        {'evidence_id': row['evidence_id'], 'rank': row['rank'], 'score': row['score']}
                        for row in req if row['evidence_id'] not in ids
                    ],
                })

        oracle_required = len(required_rows)
        total_candidates = sum(len(rows) for rows in lanes.values())
        result = {
            'schema': 'eb-v1-selector-headroom-rc0-result-v1',
            'classification': 'RETROSPECTIVE_HEADROOM_ONLY',
            'authorities': {
                'pr63_run': PR63_RUN,
                'pr63_artifact_id': PR63_ARTIFACT_ID,
                'pr63_artifact_sha256': 'sha256:' + EXPECTED_ARTIFACT_SHA256,
                'pr72_head': PR72_HEAD,
                'pr72_conclusion': PR72_CONCLUSION,
                'gold_interpretation': 'PR72 established all 27 previously unresolved retained relationships as KNOWN_NON_REQUIRED_OR_DISTRACTOR; PR63 explicit required mappings are therefore the conservative qualification-required oracle set.',
            },
            'cohort': {
                'lanes': len(lanes),
                'candidate_relationships': total_candidates,
                'qualification_required_relationships': oracle_required,
                'required_count_distribution': dict(sorted(Counter(row['required_count'] for row in lane_rows).items())),
                'deepest_required_rank_distribution': dict(sorted(Counter(row['deepest_required_rank'] for row in lane_rows).items())),
            },
            'oracle': {
                'retained_relationships': oracle_required,
                'mean_per_lane': mean(row['required_count'] for row in lane_rows),
                'median_per_lane': median(row['required_count'] for row in lane_rows),
                'max_per_lane': max(row['required_count'] for row in lane_rows),
                'removable_relationships_upper_bound': total_candidates - oracle_required,
                'compression_upper_bound_fraction': (total_candidates - oracle_required) / total_candidates,
                'lane_rows': lane_rows,
            },
            'fixed_k_frontier': fixed,
            'simple_score_diagnostics': {
                'lossless_global_top_score_ratio': lossless_ratio,
                'lossless_global_ratio_retained_relationships': threshold_retained,
                'lossless_global_ratio_required_kept': threshold_req,
                'lossless_global_ratio_fully_covered_lanes': threshold_full,
                'largest_relative_gap': {
                    'retained_relationships': gap_retained,
                    'required_kept': gap_req,
                    'required_total': oracle_required,
                    'fully_covered_lanes': gap_full,
                    'failures': gap_failures,
                },
            },
            'rank_gt_3_required': [
                {'proposition_id': proposition_id, 'evidence_id': row['evidence_id'], 'rank': row['rank'], 'score': row['score']}
                for proposition_id, row in required_rows if row['rank'] > 3
            ],
            'nonclaims': [
                'This does not qualify a selector.',
                'This does not prove candidate depth 10 is sufficient on future or naturalistic corpora.',
                'Qualification-required is not identical to the later V5 operational KEEP_DISTINCT construct.',
                'No retrieval or semantic review was rerun.',
            ],
        }
        args.output.write_text(json.dumps(result, indent=2, sort_keys=True) + '\n')
    finally:
        td.cleanup()


if __name__ == '__main__':
    main()
