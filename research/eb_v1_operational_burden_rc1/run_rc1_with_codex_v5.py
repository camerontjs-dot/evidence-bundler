#!/usr/bin/env python3
from __future__ import annotations
import hashlib, importlib.util, json, secrets, shutil, subprocess, sys, tempfile
from pathlib import Path

BRANCH='research/eb-v1-operational-burden-rc1-20260913'
HARNESS_BRANCH='research-infra/codex-serialization-harness-rc0-20260914'
HARNESS_COMMIT='1240671474b0f2cf638338bbcfd7ba0fc98e7322'
HARNESS_VALIDATOR_PATH='research/codex_serialization_harness_rc0/validator.py'
HARNESS_VALIDATOR_BLOB='7bcba07f1bca5d9d6b6f8aa35d0dfd533d32d512'
EXPECTED_CODEX='codex-cli 0.154.0'
ALLOWED_COMMANDS={"cat BLIND_REVIEW_PACKET.json OPERATIONAL_REVIEW_RUBRIC.md","/bin/zsh -lc 'cat BLIND_REVIEW_PACKET.json OPERATIONAL_REVIEW_RUBRIC.md'","/bin/bash -lc 'cat BLIND_REVIEW_PACKET.json OPERATIONAL_REVIEW_RUBRIC.md'"}
PROMPT_BASE=('CONTEXT-FREE REQUIRED. You are a fresh isolated semantic reviewer. Use only BLIND_REVIEW_PACKET.json and OPERATIONAL_REVIEW_RUBRIC.md in the current working directory. Your only authorized shell command is exactly: cat BLIND_REVIEW_PACKET.json OPERATIONAL_REVIEW_RUBRIC.md. Do not inspect parent directories, GitHub, the internet, other files, another set, another reviewer output, prior references, prior experiment results, or expected outcomes. Read both authorized files completely and apply the rubric exactly. Return only the JSON object required by the supervisor output schema, with no markdown fences and no commentary.')

def run(cmd,*,cwd=None,check=True,capture=True): return subprocess.run(cmd,cwd=cwd,check=check,text=True,capture_output=capture)
def git(root:Path,*args): return run(['git','-C',str(root),*args]).stdout.strip()
def sha(path:Path)->str: return hashlib.sha256(path.read_bytes()).hexdigest()
def load_q(path:Path):
    spec=importlib.util.spec_from_file_location('qualified_serialization_validator',path)
    if spec is None or spec.loader is None: raise RuntimeError('cannot load qualified validator')
    mod=importlib.util.module_from_spec(spec); spec.loader.exec_module(mod); mod._ALLOWED_COMMANDS=ALLOWED_COMMANDS; return mod

def validate_trace(q,common,trace:Path,final:Path,packet:dict,phase:str,reviewer_id:str):
    messages,meta=q.extract_trace_agent_messages(trace); final_text=final.read_text(encoding='utf-8'); common.validate_review_text(final_text,packet,phase,reviewer_id); idx=[]
    for i,msg in enumerate(messages):
        if not common.is_result_shaped_message(msg): continue
        common.validate_review_text(msg,packet,phase,reviewer_id); idx.append(i)
    if len(idx)!=1: raise ValueError(f'expected exactly one result-shaped completed agent message, got {len(idx)}')
    if idx[0]!=len(messages)-1: raise ValueError('unique result-shaped agent message was not the final agent message')
    if messages[idx[0]].strip()!=final_text.strip(): raise ValueError('trace result agent message differs from --output-last-message file')
    return {**meta,'status_agent_message_count':len(messages)-1,'result_agent_message_count':1,'trace_final_text_equal':True,'trace_final_sha256':hashlib.sha256(messages[idx[0]].strip().encode()).hexdigest(),'output_final_sha256':hashlib.sha256(final_text.strip().encode()).hexdigest()}

def import_common(base:Path):
    p=base/'review_common_v2.py'; spec=importlib.util.spec_from_file_location('review_common_v2',p)
    if spec is None or spec.loader is None: raise RuntimeError('cannot load review_common_v2')
    mod=importlib.util.module_from_spec(spec); sys.modules['review_common_v2']=mod; spec.loader.exec_module(mod); return mod

def preflight(root:Path,base:Path,manifest:dict,tmp:Path):
    if manifest.get('schema')!='eb-v1-operational-burden-rc1-apparatus-manifest-v5': raise RuntimeError('V5 manifest schema mismatch')
    for rel,expected in manifest['git_blob_sha1'].items():
        got=git(root,'hash-object','--',str(base/rel))
        if got!=expected: raise RuntimeError(f'apparatus git blob mismatch {rel}: {got} != {expected}')
    common=import_common(base)
    for rel,expected in manifest['packet_canonical_sha256'].items():
        got=common.canonical_hash(common.load(base/rel))
        if got!=expected: raise RuntimeError(f'packet canonical mismatch {rel}: {got} != {expected}')
    sup=common.load(base/'SUPERVISOR_RELATION_MAP.json'); amber=common.load(base/'BLIND_REVIEW_PACKET_AMBER.json'); cobalt=common.load(base/'BLIND_REVIEW_PACKET_COBALT.json')
    if sup.get('arm_mapping')!={'amber':'5/3','cobalt':'10/7'}: raise RuntimeError('arm mapping mismatch')
    if len(amber.get('lanes',[]))!=18 or len(cobalt.get('lanes',[]))!=18: raise RuntimeError('lane count mismatch')
    a=common.packet_relation_ids(amber); c=common.packet_relation_ids(cobalt); matched=sup.get('matched_relationships',[]); large=sup.get('larger_arm_only_relationships',[])
    if len(a)!=54 or len(c)!=96 or len(matched)!=54 or len(large)!=42: raise RuntimeError('relationship count mismatch')
    if set(a)!={r['amber_relation_id'] for r in matched}: raise RuntimeError('amber relation map mismatch')
    if set(c)!=({r['cobalt_relation_id'] for r in matched}|{r['relation_id'] for r in large}): raise RuntimeError('cobalt relation map mismatch')
    if len({r['proposition_id'] for r in matched})!=18: raise RuntimeError('normative lane count mismatch')
    git(root,'fetch','origin',HARNESS_BRANCH)
    if git(root,'rev-parse',f'{HARNESS_COMMIT}:{HARNESS_VALIDATOR_PATH}')!=HARNESS_VALIDATOR_BLOB: raise RuntimeError('qualified harness validator blob mismatch')
    qpath=tmp/'qualified_validator.py'; qbytes=subprocess.check_output(['git','-C',str(root),'show',f'{HARNESS_COMMIT}:{HARNESS_VALIDATOR_PATH}']); qpath.write_bytes(qbytes)
    if git(root,'hash-object','--',str(qpath))!=HARNESS_VALIDATOR_BLOB: raise RuntimeError('extracted qualified harness validator blob mismatch')
    codex=run(['codex','--version']).stdout.strip().splitlines()[0]
    if codex!=EXPECTED_CODEX: raise RuntimeError(f'codex version mismatch: {codex} != {EXPECTED_CODEX}')
    parsed=json.loads(run([sys.executable,str(base/'selftest_v5.py'),'--qualified-validator',str(qpath)],cwd=base).stdout)
    if parsed.get('pass') is not True: raise RuntimeError('V5 selftest failed')
    return common,load_q(qpath),codex,parsed

def write_receipt(directory:Path,name:str):
    files={p.name:{'sha256':sha(p)} for p in sorted(directory.iterdir()) if p.is_file()}; (directory/name).write_text(json.dumps({'schema':'eb-v1-operational-burden-rc1-v5-file-receipt-v1','files':files},indent=2,sort_keys=True)+'\n')

def main():
    root=Path(git(Path.cwd(),'rev-parse','--show-toplevel')); base=root/'research/eb_v1_operational_burden_rc1'; manifest=json.loads((base/'APPARATUS_MANIFEST_V5.json').read_text())
    git(root,'fetch','origin',BRANCH); start=git(root,'rev-parse','HEAD'); remote=git(root,'rev-parse',f'origin/{BRANCH}')
    if start!=remote: raise RuntimeError(f'execution checkout must equal remote branch: {start} != {remote}')
    if git(root,'status','--porcelain'): raise RuntimeError('working tree must be clean before V5 execution')
    for p in [base/'reference_outputs_v5',base/'test_outputs_v5',base/'TERMINAL_RESULT_V5.json',base/'RESULTS_V5.md']:
        if p.exists(): raise RuntimeError(f'V5 output already exists: {p}')
    tmp=Path(tempfile.mkdtemp(prefix='eb-v1-rc1-v5-supervisor-')); common,q,codex_version,selftest=preflight(root,base,manifest,tmp); print('V5_PREFLIGHT_PASS')
    ref_out=base/'reference_outputs_v5'; test_out=base/'test_outputs_v5'; ref_out.mkdir(); test_out.mkdir(); (ref_out/'CODEX_VERSION.txt').write_text(codex_version+'\n')
    execution_id=__import__('datetime').datetime.now(__import__('datetime').timezone.utc).strftime('%Y%m%dT%H%M%SZ')+'-'+secrets.token_hex(4); used_ids:set[str]=set(); child_receipts=[]
    packets={'amber':base/'BLIND_REVIEW_PACKET_AMBER.json','cobalt':base/'BLIND_REVIEW_PACKET_COBALT.json'}; rubric=base/'OPERATIONAL_REVIEW_RUBRIC_COMMON_V5.md'
    def run_child(arm:str,phase:str,ordinal:int,out_dir:Path):
        work=Path(tempfile.mkdtemp(prefix=f'eb-v1-rc1-v5-{phase}-{arm}-{ordinal}-')); packet_obj=common.load(packets[arm]); reviewer_id=f'{execution_id}-{phase}-{arm}-{ordinal}-{secrets.token_hex(6)}'
        if reviewer_id in used_ids: raise RuntimeError('reviewer id collision')
        shutil.copy2(packets[arm],work/'BLIND_REVIEW_PACKET.json'); shutil.copy2(rubric,work/'OPERATIONAL_REVIEW_RUBRIC.md'); schema=common.output_schema(packet_obj,phase,reviewer_id); schema_path=work/'OUTPUT_SCHEMA.json'; schema_path.write_text(json.dumps(schema,separators=(',',':'),ensure_ascii=False)+'\n')
        stem=f'{phase.upper()}_{arm.upper()}_{ordinal}'; final=out_dir/f'{stem}.json'; trace=out_dir/f'{stem}.trace.jsonl'; stderr=out_dir/f'{stem}.stderr.log'
        for p in (final,trace,stderr):
            if p.exists(): raise RuntimeError(f'child output path already exists: {p}')
        prompt=PROMPT_BASE+f' Set reviewer.reviewer_id exactly to "{reviewer_id}" and reviewer.review_phase exactly to "{phase}". Set packet_canonical_sha256 exactly to "{common.canonical_hash(packet_obj)}". Assert independence fields truthfully as required by the rubric.'
        cmd=['codex','exec','--ephemeral','--ignore-user-config','--ignore-rules','--skip-git-repo-check','--sandbox','read-only','--json','--output-schema',str(schema_path),'--output-last-message',str(final),prompt]
        with trace.open('w') as tout, stderr.open('w') as terr: cp=subprocess.run(cmd,cwd=work,text=True,stdout=tout,stderr=terr)
        if cp.returncode!=0: print(f'PRESERVED_FAILED_WORKSPACE={work}',file=sys.stderr); raise RuntimeError(f'child execution failed {phase} {arm} {ordinal}: rc={cp.returncode}')
        meta=validate_trace(q,common,trace,final,packet_obj,phase,reviewer_id); labels,rid=common.validate_review(final,work/'BLIND_REVIEW_PACKET.json',phase,used_ids,reviewer_id)
        if rid!=reviewer_id or len(labels)!=(54 if arm=='amber' else 96): raise RuntimeError('post-validation child identity/count mismatch')
        child_receipts.append({'arm':arm,'phase':phase,'ordinal':ordinal,'reviewer_id':reviewer_id,'final_sha256':sha(final),'trace_sha256':sha(trace),'stderr_sha256':sha(stderr),'output_schema_sha256':sha(schema_path),**meta}); shutil.rmtree(work)
    for i in (1,2,3): run_child('amber','reference',i,ref_out)
    for i in (1,2,3): run_child('cobalt','reference',i,ref_out)
    args=[sys.executable,str(base/'consolidate_references_v2.py'),'--amber-packet',str(packets['amber']),'--cobalt-packet',str(packets['cobalt'])]
    for arm in ('amber','cobalt'):
        for i in (1,2,3): args += [f'--{arm}-r{i}',str(ref_out/f'REFERENCE_{arm.upper()}_{i}.json')]
    run(args+['--out-dir',str(ref_out)],cwd=base); (ref_out/'V5_STAGE1_CHILD_RECEIPTS.json').write_text(json.dumps({'schema':'eb-v1-operational-burden-rc1-v5-child-receipts-v1','execution_id':execution_id,'children':child_receipts},indent=2,sort_keys=True)+'\n'); write_receipt(ref_out,'STAGE1_FILE_RECEIPT_V5.json')
    run(['git','add',str(ref_out)],cwd=root,capture=False); run(['git','commit','-m','research: freeze RC1 V5 task-aligned reference'],cwd=root,capture=False); reference_commit=git(root,'rev-parse','HEAD'); run(['git','push','origin',f'HEAD:{BRANCH}'],cwd=root,capture=False); print('REFERENCE_FREEZE_COMMIT='+reference_commit)
    (test_out/'CODEX_VERSION.txt').write_text(codex_version+'\n')
    for i in (1,2): run_child('amber','test',i,test_out)
    for i in (1,2): run_child('cobalt','test',i,test_out)
    result=base/'TERMINAL_RESULT_V5.json'; run([sys.executable,str(base/'evaluate_rc1_v2.py'),'--map',str(base/'SUPERVISOR_RELATION_MAP.json'),'--amber-packet',str(packets['amber']),'--cobalt-packet',str(packets['cobalt']),'--amber-reference',str(ref_out/'REFERENCE_AMBER.json'),'--cobalt-reference',str(ref_out/'REFERENCE_COBALT.json'),'--amber-t1',str(test_out/'TEST_AMBER_1.json'),'--amber-t2',str(test_out/'TEST_AMBER_2.json'),'--cobalt-t1',str(test_out/'TEST_COBALT_1.json'),'--cobalt-t2',str(test_out/'TEST_COBALT_2.json'),'--reference-freeze-commit',reference_commit,'--out',str(result)],cwd=base)
    r=json.loads(result.read_text()); (test_out/'V5_ALL_CHILD_RECEIPTS.json').write_text(json.dumps({'schema':'eb-v1-operational-burden-rc1-v5-child-receipts-v1','execution_id':execution_id,'children':child_receipts},indent=2,sort_keys=True)+'\n'); write_receipt(test_out,'STAGE2_FILE_RECEIPT_V5.json')
    (base/'RESULTS_V5.md').write_text(f'# Evidence Bundler V1 — Task-Aligned Operational Burden RC1 V5 Results\n\nPrimary disposition: **{r["primary_disposition"]}**\n\nPrimary conclusion: `{r["primary_conclusion"]}`\n\n- scoreable matched relationships: `{r["scoreable_matched_relationship_count"]} / {r["shared_relationship_count"]}`\n- scoreable normative lanes: `{r["scoreable_lane_count"]} / 18`\n- coverage guard: `{r["coverage_guard_pass"]}`\n- larger-worse flags: `{json.dumps(r["larger_worse_flags"],sort_keys=True)}`\n\nV5 uses the qualified schema-constrained child-output apparatus. The exposed V4 cohort was not reused. No merge, release, tag, production-default change, or V1 promotion is authorized by this record.\n')
    run(['git','add',str(test_out),str(result),str(base/'RESULTS_V5.md')],cwd=root,capture=False); run(['git','commit','-m','research: freeze RC1 V5 operational burden result'],cwd=root,capture=False); final_commit=git(root,'rev-parse','HEAD'); run(['git','push','origin',f'HEAD:{BRANCH}'],cwd=root,capture=False)
    print('RC1_V5_COMPLETE'); print('EXECUTION_ID='+execution_id); print('REFERENCE_FREEZE_COMMIT='+reference_commit); print('FINAL_COMMIT='+final_commit); print('PRIMARY_DISPOSITION='+r['primary_disposition']); print('PRIMARY_CONCLUSION='+r['primary_conclusion']); print('ALL_TEN_FRESH_REVIEWERS_COMPLETED_SUCCESSFULLY=yes')
if __name__=='__main__':
    try: main()
    except Exception as exc:
        print('RC1_V5_EXECUTION_FAILED',file=sys.stderr); print(f'ERROR={type(exc).__name__}: {exc}',file=sys.stderr); raise
