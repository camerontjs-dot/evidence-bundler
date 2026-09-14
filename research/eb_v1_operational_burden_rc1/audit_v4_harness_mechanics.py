#!/usr/bin/env python3
from __future__ import annotations

import argparse
import hashlib
import json
import re
import subprocess
import tempfile
from collections import Counter
from pathlib import Path

HERE = Path(__file__).resolve().parent
REPO = HERE.parents[2]


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def canonical_hash(path: Path) -> str:
    obj = json.loads(path.read_text(encoding='utf-8'))
    raw = json.dumps(obj, sort_keys=True, separators=(',', ':'), ensure_ascii=False).encode('utf-8')
    return sha256_bytes(raw)


def packet_ids(path: Path) -> list[str]:
    obj = json.loads(path.read_text(encoding='utf-8'))
    out: list[str] = []
    for lane in obj.get('lanes', []):
        for passage in lane.get('passages', []):
            rid = passage.get('relation_id')
            if not isinstance(rid, str):
                raise SystemExit(f'missing relation_id in {path}')
            out.append(rid)
    if len(out) != len(set(out)):
        raise SystemExit(f'packet itself contains duplicate relation_id: {path}')
    return out


def git_blob(path: Path) -> str:
    return subprocess.check_output(['git', '-C', str(REPO), 'hash-object', '--', str(path)], text=True).strip()


def relation_ids_from_review_text(text: str) -> list[str]:
    # Parse JSON only to establish structural validity; intentionally do not read label values.
    obj = json.loads(text)
    judgments = obj.get('judgments')
    if not isinstance(judgments, list):
        raise ValueError('judgments missing')
    ids: list[str] = []
    for row in judgments:
        if not isinstance(row, dict) or not isinstance(row.get('relation_id'), str):
            raise ValueError('relation_id missing')
        ids.append(row['relation_id'])
    return ids


def final_agent_text_from_trace(path: Path) -> tuple[str, int]:
    messages: list[str] = []
    for line in path.read_text(encoding='utf-8').splitlines():
        if not line.strip():
            continue
        obj = json.loads(line)
        if obj.get('type') != 'item.completed':
            continue
        item = obj.get('item') or {}
        if item.get('type') in {'agent_message', 'assistant_message'} and isinstance(item.get('text'), str):
            messages.append(item['text'])
    if not messages:
        raise ValueError('no completed agent/assistant message in trace')
    return messages[-1], len(messages)


def inventory(path: Path) -> list[dict]:
    rows = []
    if not path.is_dir():
        return rows
    for p in sorted(path.iterdir()):
        if p.is_file():
            data = p.read_bytes()
            rows.append({'name': p.name, 'size': len(data), 'sha256': sha256_bytes(data)})
    return rows


def structural_selftest() -> dict:
    import sys
    sys.path.insert(0, str(HERE))
    from review_common import validate_review

    with tempfile.TemporaryDirectory(prefix='eb-rc1-harness-selftest-') as td:
        td = Path(td)
        packet = {
            'schema': 'synthetic-nonsemantic-packet-v1',
            'set_id': 'synthetic',
            'lanes': [{'lane_id': 'L', 'proposition_text': 'synthetic', 'passages': [
                {'relation_id': 'r1', 'passage_text': 'x'},
                {'relation_id': 'r2', 'passage_text': 'y'},
                {'relation_id': 'r3', 'passage_text': 'z'},
            ]}],
        }
        pp = td / 'packet.json'
        pp.write_text(json.dumps(packet), encoding='utf-8')
        ph = canonical_hash(pp)

        def review(rows):
            return {
                'schema': 'eb-v1-operational-burden-rc1-review-v1',
                'reviewer': {
                    'reviewer_id': 'synthetic-reviewer',
                    'review_phase': 'reference',
                    'model_or_human': 'synthetic',
                    'execution_context': 'synthetic non-semantic structural self-test',
                    'packet_canonical_sha256': ph,
                    'independent_of_other_reviewers': True,
                    'saw_other_set': False,
                    'saw_prior_reference': False,
                },
                'judgments': rows,
            }

        valid = td / 'valid.json'
        valid.write_text(json.dumps(review([
            {'relation_id': 'r1', 'label': 'KEEP_DISTINCT'},
            {'relation_id': 'r2', 'label': 'DROP_REDUNDANT'},
            {'relation_id': 'r3', 'label': 'DROP_DISTRACTOR'},
        ])), encoding='utf-8')
        validate_review(valid, pp, 'reference', set())

        cases = {
            'duplicate': [
                {'relation_id': 'r1', 'label': 'KEEP_DISTINCT'},
                {'relation_id': 'r1', 'label': 'DROP_DISTRACTOR'},
                {'relation_id': 'r2', 'label': 'DROP_REDUNDANT'},
                {'relation_id': 'r3', 'label': 'DROP_DISTRACTOR'},
            ],
            'missing': [
                {'relation_id': 'r1', 'label': 'KEEP_DISTINCT'},
                {'relation_id': 'r2', 'label': 'DROP_REDUNDANT'},
            ],
            'unknown': [
                {'relation_id': 'r1', 'label': 'KEEP_DISTINCT'},
                {'relation_id': 'r2', 'label': 'DROP_REDUNDANT'},
                {'relation_id': 'rx', 'label': 'DROP_DISTRACTOR'},
            ],
        }
        rejected = {}
        for name, rows in cases.items():
            p = td / f'{name}.json'
            p.write_text(json.dumps(review(rows)), encoding='utf-8')
            try:
                validate_review(p, pp, 'reference', set())
            except Exception as exc:
                rejected[name] = type(exc).__name__
            else:
                rejected[name] = 'NOT_REJECTED'
        return {'valid_passed': True, 'rejected': rejected}


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument('--failed-worktree', type=Path, required=True)
    ap.add_argument('--report', type=Path)
    args = ap.parse_args()

    status = subprocess.check_output(['git', '-C', str(REPO), 'status', '--porcelain'], text=True)
    if status.strip():
        raise SystemExit('audit worktree must be clean before audit')

    manifest = json.loads((HERE / 'APPARATUS_MANIFEST_V3.json').read_text(encoding='utf-8'))
    blob_checks = {}
    for rel, expected in manifest['git_blob_sha1'].items():
        got = git_blob(HERE / rel)
        blob_checks[rel] = {'expected': expected, 'actual': got, 'pass': got == expected}
        if got != expected:
            raise SystemExit(f'git blob mismatch: {rel}')

    canonical_checks = {}
    for rel, expected in manifest['packet_canonical_sha256'].items():
        got = canonical_hash(HERE / rel)
        canonical_checks[rel] = {'expected': expected, 'actual': got, 'pass': got == expected}
        if got != expected:
            raise SystemExit(f'packet canonical mismatch: {rel}')

    a_ids = packet_ids(HERE / 'BLIND_REVIEW_PACKET_AMBER.json')
    c_ids = packet_ids(HERE / 'BLIND_REVIEW_PACKET_COBALT.json')
    sup = json.loads((HERE / 'SUPERVISOR_RELATION_MAP.json').read_text(encoding='utf-8'))
    matched = sup['matched_relationships']
    larger = sup['larger_arm_only_relationships']
    structure = {
        'amber_count': len(a_ids),
        'cobalt_count': len(c_ids),
        'matched_count': len(matched),
        'larger_only_count': len(larger),
        'matched_lane_count': len({r['proposition_id'] for r in matched}),
        'amber_map_exact': set(a_ids) == {r['amber_relation_id'] for r in matched},
        'cobalt_map_exact': set(c_ids) == ({r['cobalt_relation_id'] for r in matched} | {r['relation_id'] for r in larger}),
    }
    if structure != {
        'amber_count': 54, 'cobalt_count': 96, 'matched_count': 54, 'larger_only_count': 42,
        'matched_lane_count': 18, 'amber_map_exact': True, 'cobalt_map_exact': True,
    }:
        raise SystemExit(f'structure mismatch: {structure}')

    runner = (HERE / 'run_rc1_with_codex.sh').read_text(encoding='utf-8')
    v4 = (HERE / 'run_rc1_with_codex_v4.sh').read_text(encoding='utf-8')
    static = {
        'fresh_child_mktemp_present': 'work="$(mktemp -d' in runner,
        'direct_output_last_message_to_final': '--output-last-message "$final"' in runner,
        'trace_uses_truncating_redirect': '> "$trace"' in runner and '>> "$trace"' not in runner,
        'validator_call_count_in_run_child_source': runner.count('validate_one "$work/BLIND_REVIEW_PACKET.json" "$final" "$phase" "$ids_file"'),
        'v4_bash_parse_gate_present': 'bash -n "$TMP_RUNNER"' in v4,
        'v4_forbids_old_uppercase_expansions': "if '${phase^^}' in text or '${set_name^^}' in text" in v4,
    }
    if not all([static['fresh_child_mktemp_present'], static['direct_output_last_message_to_final'], static['trace_uses_truncating_redirect'], static['v4_bash_parse_gate_present'], static['v4_forbids_old_uppercase_expansions']]) or static['validator_call_count_in_run_child_source'] != 1:
        raise SystemExit(f'runner static audit failed: {static}')

    planned = []
    for phase, outdir, n in [('reference', 'reference_outputs', 3), ('test', 'test_outputs', 2)]:
        for set_name in ('amber', 'cobalt'):
            for ordinal in range(1, n + 1):
                stem = f'{phase.upper()}_{set_name.upper()}_{ordinal}'
                planned.extend([f'{outdir}/{stem}.json', f'{outdir}/{stem}.trace.jsonl'])
    output_paths = {
        'planned_count': len(planned),
        'unique_count': len(set(planned)),
        'all_unique': len(planned) == len(set(planned)),
    }

    ignored = []
    for rel in ['research/eb_v1_operational_burden_rc1/reference_outputs/REFERENCE_COBALT_1.json', 'research/eb_v1_operational_burden_rc1/test_outputs/TEST_COBALT_1.json']:
        cp = subprocess.run(['git', '-C', str(REPO), 'check-ignore', '-q', rel])
        if cp.returncode == 0:
            ignored.append(rel)

    failed_base = args.failed_worktree.resolve() / 'research/eb_v1_operational_burden_rc1'
    failed_output = failed_base / 'reference_outputs/REFERENCE_COBALT_1.json'
    failed_trace = failed_base / 'reference_outputs/REFERENCE_COBALT_1.trace.jsonl'
    failed_packet = failed_base / 'BLIND_REVIEW_PACKET_COBALT.json'
    for p in (failed_output, failed_trace, failed_packet):
        if not p.is_file():
            raise SystemExit(f'preserved V4 artifact missing: {p}')

    final_raw = failed_output.read_text(encoding='utf-8')
    trace_text, trace_message_count = final_agent_text_from_trace(failed_trace)
    final_ids = relation_ids_from_review_text(final_raw)
    trace_ids = relation_ids_from_review_text(trace_text)
    expected_ids = packet_ids(failed_packet)
    final_counts = Counter(final_ids)
    trace_counts = Counter(trace_ids)
    final_dupes = sorted(k for k, v in final_counts.items() if v > 1)
    trace_dupes = sorted(k for k, v in trace_counts.items() if v > 1)

    if final_ids == trace_ids and final_dupes:
        attribution = 'CHILD_AGENT_MESSAGE_ALREADY_CONTAINED_DUPLICATE_RELATION_ID'
    elif final_dupes and not trace_dupes:
        attribution = 'OUTPUT_LAST_MESSAGE_FILE_DIVERGED_FROM_TRACE_AGENT_MESSAGE'
    else:
        attribution = 'INDETERMINATE'

    failed = {
        'failed_output_sha256': sha256_bytes(failed_output.read_bytes()),
        'failed_trace_sha256': sha256_bytes(failed_trace.read_bytes()),
        'packet_sha256': sha256_bytes(failed_packet.read_bytes()),
        'expected_relation_count': len(expected_ids),
        'failed_output_relation_count': len(final_ids),
        'failed_output_unique_relation_count': len(set(final_ids)),
        'failed_output_duplicate_relation_ids': final_dupes,
        'trace_completed_agent_message_count': trace_message_count,
        'trace_final_relation_count': len(trace_ids),
        'trace_final_unique_relation_count': len(set(trace_ids)),
        'trace_final_duplicate_relation_ids': trace_dupes,
        'final_and_trace_relation_id_sequence_equal': final_ids == trace_ids,
        'final_and_trace_text_sha256_equal_after_strip': sha256_bytes(final_raw.strip().encode()) == sha256_bytes(trace_text.strip().encode()),
        'failed_output_relation_set_matches_packet': set(final_ids) == set(expected_ids),
        'attribution': attribution,
    }

    report = {
        'schema': 'eb-v1-operational-burden-rc1-v4-harness-audit-v1',
        'scientific_result': False,
        'real_reviewer_launched_by_audit': False,
        'audit_repo_head': subprocess.check_output(['git', '-C', str(REPO), 'rev-parse', 'HEAD'], text=True).strip(),
        'failed_worktree_head': subprocess.check_output(['git', '-C', str(args.failed_worktree), 'rev-parse', 'HEAD'], text=True).strip(),
        'codex_version_file': (failed_base / 'reference_outputs/CODEX_VERSION.txt').read_text(encoding='utf-8').strip() if (failed_base / 'reference_outputs/CODEX_VERSION.txt').is_file() else None,
        'apparatus_git_blob_checks': blob_checks,
        'packet_canonical_checks': canonical_checks,
        'packet_and_supervisor_structure': structure,
        'runner_static_mechanics': static,
        'planned_output_paths': output_paths,
        'planned_output_paths_ignored_by_git': ignored,
        'preserved_reference_output_inventory': inventory(failed_base / 'reference_outputs'),
        'failed_cobalt_1_structural_comparison': failed,
        'synthetic_validator_selftest': structural_selftest(),
        'stop_boundary': 'HARNESS_AUDIT_ONLY_NO_RETRY_AUTHORIZED',
    }

    text = json.dumps(report, indent=2, sort_keys=True) + '\n'
    if args.report:
        args.report.write_text(text, encoding='utf-8')
    print(text, end='')


if __name__ == '__main__':
    main()
