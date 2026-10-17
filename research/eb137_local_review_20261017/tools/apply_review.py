#!/usr/bin/env python3
"""Apply frozen first model decisions through --review; no semantic re-review or repair.

Reuses the exact #134 replay-equality/count functions and consumer check_case.
Standalone adequacy remains the separately recorded informed supervisor check.
"""
from __future__ import annotations
import hashlib
import importlib
import importlib.metadata
import json
import os
import runpy
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PREP = Path.home() / '.mainframe-dev/receipts/eb-137-20261017'
CANDIDATE = Path.home() / 'Desktop/MainFrame/30_projects/evidence-bundler/.worktrees/eb-v1-137-fresh-review-20261016'
CF_SHA = '2f41ded9c12e40ade000ec3082abea468bb3a0ddcf9c2c4f4f331171f4319f90'
CASES = [f'p{i:02d}' for i in range(1, 9)]


def need(value, text):
    if not value:
        raise ValueError(text)


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def read(path):
    return json.loads(path.read_text())


def write(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open('x', encoding='utf-8') as f:
        json.dump(value, f, indent=2, sort_keys=True, ensure_ascii=False, allow_nan=False)
        f.write('\n')


def file_hashes(root):
    return {str(p.relative_to(root)): digest(p) for p in sorted(root.rglob('*')) if p.is_file()}


def main():
    run = ROOT / 'execution'
    frozen = read(run/'REVIEW-FREEZE.json')
    need(all(digest(run/name) == value for name, value in frozen['files'].items()),
         'first decisions or receipts changed')
    cf_path = PREP/'fresh-review/CONTENT-FREEZE.json'
    need(digest(cf_path) == CF_SHA, 'content freeze drift')
    cf = read(cf_path)
    need(Path(sys.prefix).resolve() == (PREP/'venv').resolve(), 'wrong installed environment')
    site = Path(importlib.import_module('evidence_bundler').__file__).parent.parent
    for role in ['candidate', 'contract_b', 'cal']:
        for path, value in cf[role]['member_sha256'].items():
            need(digest(site/path) == value, f'installed member drift: {role}/{path}')
    for path, item in cf['evaluator_files'].items():
        need(digest(CANDIDATE/path) == item['sha256'], 'frozen evaluator drift: '+path)
    need(digest(Path.home()/'.mainframe-dev/receipts/eb-137-20261016/wheels/evidence_bundler-0.3.0.dev0-py3-none-any.whl') == cf['candidate']['wheel_sha256'], 'wheel drift')
    checker = runpy.run_path(str(CANDIDATE/'scripts/qualification/check_v1_workflow_consumers.py'))
    helper = runpy.run_path(str(CANDIDATE/'scripts/qualification/run_v1_workflow_acceptance.py'))
    transport = runpy.run_path(str(ROOT/'tools/local_review.py'))
    canonical = importlib.import_module('validators.verify_contract_integrity')
    consumer = importlib.import_module('claim_audit_lab.contracts.factual_context')
    cli = str(PREP/'venv/bin/evidence-bundler-v1')
    out = ROOT/'application'
    out.mkdir(exist_ok=False)
    rows = []
    env = dict(os.environ)
    env.pop('PYTHONPATH', None)
    env.pop('PYTHONHOME', None)
    env['PYTHONNOUSERSITE'] = '1'
    try:
        for case in CASES:
            input_path = PREP/f'fresh-review/inputs/{case}.contract-a.json'
            before_dir = PREP/f'fresh-review/unreviewed/{case}'
            before = read(before_dir/'native_eb_v1_package.json')
            record_path = run/f'reviews/{case}/review_record.json'
            record = read(record_path)
            template = read(before_dir/'review_record.json')
            notes = read(run/f'reviews/{case}/target_notes.json')
            targets = [x['proposition_id'] for x in before['primary_targets']]
            transport['validate_return']({'review_record': record, 'target_notes': notes}, template, targets)
            for path in [input_path, before_dir/'native_eb_v1_package.json', before_dir/'review_context.md', before_dir/'review_record.json']:
                relative = str(path.relative_to(PREP/'fresh-review'))
                need(digest(path) == cf['packet_file_sha256'][relative], 'input/unreviewed drift')
            destination = out/'outputs'/case
            command = [cli, 'run', str(input_path), '--review', str(record_path), '--out-dir', str(destination)]
            result = subprocess.run(command, cwd=out, env=env, capture_output=True, text=True)
            write(out/f'logs/{case}.json', {'command': command, 'returncode': result.returncode,
                  'stdout': result.stdout, 'stderr': result.stderr})
            need(result.returncode == 0, case+' bound application failed')
            need(read(destination/'applied_review_record.json') == record, 'applied review changed')
            need(not (destination/'review_record.json').exists(), 'applied run created another template')
            after = helper['check_outputs'](destination, read(input_path))
            decisions = {(r['proposition_id'], r['passage_id']): r['decision'] for r in record['decisions']}
            helper['check_replay'](before, after, decisions)
            reviewed = sorted(k for k,v in decisions.items() if v == 'accepted')
            native = sorted((r['proposition_id'], r['passage_id']) for r in after['candidates']
                            if r['selection_state'] == 'retained' and r['admission_state'] == 'accepted')
            need(reviewed == native, 'review-to-native identity mismatch')
            hashes_before = file_hashes(destination)
            row = checker['check_case'](case, destination, out/'cal-deviations', canonical, consumer)
            need(row['passed'], case+' actual canonical/CAL check failed')
            need(hashes_before == file_hashes(destination), 'consumer mutated evidence')
            row['review_to_native_pairs_equal'] = reviewed == native
            row['first_decision_counts'] = {s: sum(r['decision']==s for r in record['decisions'])
                                           for s in transport['STATES']}
            rows.append(row)
            write(out/f'consumers/{case}.json', row)
            print(case+': bound review/native/B/CAL equality PASS', flush=True)
        expected = read(CANDIDATE/'research/eb_v1_workflow_acceptance_20261004/EXPECTED-OPPORTUNITIES.json')
        counts = {}
        parent = {}
        for case in CASES:
            after = read(out/f'outputs/{case}/native_eb_v1_package.json')
            for target in after['primary_targets']:
                t = target['proposition_id']
                counts[t] = sum(r['selection_state']=='retained' and r['admission_state']=='accepted'
                                and r['proposition_id']==t for r in after['candidates'])
            parent[case] = all(counts[t['proposition_id']]>0 for t in after['primary_targets'])
        gate = helper['gate'](counts, expected)
        reject = helper['gate']({t:0 for t in counts}, expected)
        accept = helper['gate']({t:int(t!='clm-p08') for t in counts}, expected)
        need(not reject['passed'] and not accept['passed'], 'weak count control passed')
        result = {'schema': 'eb137-bound-local-model-review-application-v1',
                  'at_utc': datetime.now(timezone.utc).isoformat(),
                  'review_freeze_sha256': digest(run/'REVIEW-FREEZE.json'),
                  'mechanical_passed': all(r['passed'] for r in rows), 'cases': rows,
                  'count_gate': gate, 'counts': counts,
                  'parent_boundaries': parent['p03'] and not parent['p06'],
                  'p07_zero_admitted': counts.get('clm-p07', 0)==0,
                  'weak_controls': {'always_reject': reject, 'always_accept': accept},
                  'standalone_adequacy': 'PENDING_INFORMED_SUPERVISOR_ASSESSMENT',
                  'output_file_hashes': file_hashes(out/'outputs')}
        write(out/'RESULT.json', result)
        need(all(digest(run/name) == value for name,value in frozen['files'].items()), 'decisions changed during application')
        print('APPLICATION_RECORDED; standalone adequacy review still required', flush=True)
    except Exception as exc:
        write(out/'FIRST-FAILURE.json', {'type': type(exc).__name__, 'error': str(exc),
              'completed_cases': [r['case_id'] for r in rows], 'repair': 'NONE'})
        raise


if __name__ == '__main__':
    main()
