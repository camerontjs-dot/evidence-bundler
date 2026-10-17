#!/usr/bin/env python3
"""Controller checks on transport-only dummy data; never reads EB review cases."""
import copy
import io
import json
import runpy
import stat
import time
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
m = runpy.run_path(str(ROOT / 'tools/local_review.py'))
rows = []
record = {'schema': 'transport-control-v1', 'bindings': {'input_sha256': 'control-only'},
          'decisions': [{'proposition_id': 'transport-target', 'passage_id': 'transport-span',
                         'decision': 'needs-review', 'reason': ''}]}
files = {'REVIEWER-RULE.md': b'Return JSON matching the supplied output schema. For this transport-only check, preserve identities, fill any permitted decision, a nonblank reason and a target note. No tool use.'}
for case in m['CASES']:
    files[f'{case}/review_context.md'] = b'## Target `transport-target`\n\nTransport readiness control only.\n'
    files[f'{case}/review_record.json'] = m['encode'](record)


def zip_bytes(entries):
    buff = io.BytesIO()
    with zipfile.ZipFile(buff, 'w') as z:
        for name, value in entries:
            z.writestr(name, value)
    return buff.getvalue()


def good(name, fn):
    fn()
    rows.append({'check': name, 'passed': True})


def refuses(name, fn):
    try:
        fn()
    except (ValueError, json.JSONDecodeError):
        rows.append({'check': name, 'passed': True})
        return
    raise AssertionError('Did not refuse: ' + name)


raw = zip_bytes(list(files.items()))
good('exact_member_allowlist', lambda: m['packet'](raw, m['sha'](raw)))
refuses('wrong_zip_identity', lambda: m['packet'](raw, '0'*64))
for name, entries in [
    ('extra_file', list(files.items()) + [('unallowed.txt', b'not allowed')]),
    ('missing_file', list(files.items())[1:]),
    ('duplicate_member', list(files.items()) + [('REVIEWER-RULE.md', b'duplicate')]),
    ('traversal_member', [('../elsewhere', b'outside')] + list(files.items())[1:]),
]:
    mutation = zip_bytes(entries)
    refuses(name, lambda b=mutation: m['packet'](b, m['sha'](b)))
info = zipfile.ZipInfo('REVIEWER-RULE.md')
info.create_system = 3
info.external_attr = (stat.S_IFLNK | 0o777) << 16
mutation = zip_bytes([(info, b'/outside')] + list(files.items())[1:])
refuses('symlink_member', lambda: m['packet'](mutation, m['sha'](mutation)))
refuses('invalid_case', lambda: m['make_request'](files, 'other'))
payload = m['make_request'](files, 'p01')
assert payload['tools'] == [] and len(payload['messages']) == 2
assert [x['role'] for x in payload['messages']] == ['system', 'user']
assert set(json.loads(payload['messages'][1]['content'])['files']) == {'p01/review_context.md', 'p01/review_record.json'}
assert payload['keep_alive'] == 0 and 'context' not in payload
rows.append({'check': 'no_history_tools_other_cases_or_context', 'passed': True})
refuses('unapproved_endpoint', lambda: m['http']('elsewhere'))
refuses('redirect', lambda: m['NoRedirect']().redirect_request(None, None, 302, None, None, 'https://example.test'))
valid = {'review_record': copy.deepcopy(record), 'target_notes': {'transport-target': 'transport only'}}
valid['review_record']['decisions'][0]['reason'] = 'transport control'
for decision in m['STATES']:
    value = copy.deepcopy(valid)
    value['review_record']['decisions'][0]['decision'] = decision
    good('permits_' + decision, lambda v=value: m['validate_return'](v, record, ['transport-target']))
for name, change in [
    ('binding_change', lambda v: v['review_record']['bindings'].update(input_sha256='changed')),
    ('id_change', lambda v: v['review_record']['decisions'][0].update(passage_id='changed')),
    ('blank_reason', lambda v: v['review_record']['decisions'][0].update(reason=' ')),
    ('extra_decision', lambda v: v['review_record']['decisions'].append(copy.deepcopy(v['review_record']['decisions'][0]))),
    ('missing_decision', lambda v: v['review_record'].update(decisions=[])),
    ('illegal_decision', lambda v: v['review_record']['decisions'][0].update(decision='approve')),
    ('missing_target_note', lambda v: v.update(target_notes={})),
    ('extra_field', lambda v: v['review_record'].update(extra='unallowed')),
]:
    value = copy.deepcopy(valid)
    change(value)
    refuses(name, lambda v=value: m['validate_return'](v, record, ['transport-target']))
refuses('duplicate_json_keys', lambda: m['parse']('{"a":1,"a":2}'))
refuses('nonfinite_json', lambda: m['parse']('{"a":NaN}'))
m['save'](ROOT/'preflight/CONTROLLER-TESTS.json', {'passed': True, 'checks': rows,
            'runner_sha256': m['sha']((ROOT/'tools/local_review.py').read_bytes()),
            'scientific_packet_read': False, 'model_inference': False})
print('CONTROLLER TESTS', len(rows), 'PASS', flush=True)
identity = m['identity']()
m['save'](ROOT/'preflight/MODEL-IDENTITY.json', identity)
assert not m['parse'](m['http']('ps'))['models'], 'Provider busy; do not interrupt'
m['save'](ROOT/'preflight/request.json', payload)
tick = time.monotonic()
raw = m['http']('chat', m['encode'](payload), timeout=300)
elapsed = time.monotonic()-tick
m['save'](ROOT/'preflight/response.json', raw)
r = m['parse'](raw)
assert r.get('done') is True and r.get('done_reason') == 'stop'
assert not r['message'].get('tool_calls')
m['validate_return'](m['parse'](r['message']['content']), record, ['transport-target'])
m['save'](ROOT/'preflight/PROVIDER-PREFLIGHT.json', {'passed': True,
          'elapsed_seconds': elapsed, 'at_utc': m['now'](),
          'model': m['MODEL'], 'model_digest': m['MODEL_DIGEST'],
          'request_sha256': m['sha'](m['encode'](payload)), 'response_sha256': m['sha'](raw),
          'scientific_packet_read': False, 'semantic_accuracy_not_tested': True,
          'backend_metrics': {k:v for k,v in r.items() if k != 'message'}})
print('PROVIDER PREFLIGHT PASS', round(elapsed,2), 'seconds; no EB case exposed', flush=True)
