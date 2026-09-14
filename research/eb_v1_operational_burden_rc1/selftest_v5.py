from __future__ import annotations
import argparse, importlib.util, json, tempfile
from pathlib import Path
from review_common_v2 import DuplicateKeyError, REVIEW_SCHEMA, output_schema, validate_review_text, is_result_shaped_message, canonical_hash
ALLOWED={"cat BLIND_REVIEW_PACKET.json OPERATIONAL_REVIEW_RUBRIC.md","/bin/zsh -lc 'cat BLIND_REVIEW_PACKET.json OPERATIONAL_REVIEW_RUBRIC.md'","/bin/bash -lc 'cat BLIND_REVIEW_PACKET.json OPERATIONAL_REVIEW_RUBRIC.md'"}
def load_q(path: Path):
    spec=importlib.util.spec_from_file_location('qualified_serialization_validator',path)
    if spec is None or spec.loader is None: raise RuntimeError('cannot load qualified validator')
    mod=importlib.util.module_from_spec(spec); spec.loader.exec_module(mod); mod._ALLOWED_COMMANDS=ALLOWED; return mod
def validate_trace(q, trace: Path, final_text: str, packet, phase, reviewer_id):
    messages,meta=q.extract_trace_agent_messages(trace); validate_review_text(final_text,packet,phase,reviewer_id); idx=[]
    for i,msg in enumerate(messages):
        if not is_result_shaped_message(msg): continue
        validate_review_text(msg,packet,phase,reviewer_id); idx.append(i)
    if len(idx)!=1: raise ValueError(f'expected one result-shaped message, got {len(idx)}')
    if idx[0] != len(messages)-1: raise ValueError('result not last')
    if messages[idx[0]].strip()!=final_text.strip(): raise ValueError('trace/final mismatch')
    return meta
def must_fail(name, fn, exc=Exception):
    try: fn()
    except exc: return
    raise AssertionError(name)
def main():
    ap=argparse.ArgumentParser(); ap.add_argument('--qualified-validator',type=Path,required=True); args=ap.parse_args(); q=load_q(args.qualified_validator)
    packet={"lanes":[{"passages":[{"relation_id":"a"},{"relation_id":"b"},{"relation_id":"c"},{"relation_id":"d"}]}]}; reviewer_id='fresh-1'; phase='reference'; labels={"a":"KEEP_DISTINCT","b":"DROP_REDUNDANT","c":"DROP_DISTRACTOR","d":"UNRESOLVED"}
    good={"schema":REVIEW_SCHEMA,"reviewer":{"reviewer_id":reviewer_id,"review_phase":phase,"model_or_human":"codex-cli 0.154.0","execution_context":"fresh isolated ephemeral execution","packet_canonical_sha256":canonical_hash(packet),"independent_of_other_reviewers":True,"saw_other_set":False,"saw_prior_reference":False},"labels":labels}
    text=json.dumps(good,separators=(',',':')); out,_=validate_review_text(text,packet,phase,reviewer_id); assert out==labels
    schema=output_schema(packet,phase,reviewer_id); assert schema['properties']['labels']['required']==['a','b','c','d']; assert not is_result_shaped_message('status'); assert is_result_shaped_message(text)
    missing=json.loads(text); del missing['labels']['d']; must_fail('missing',lambda:validate_review_text(json.dumps(missing),packet,phase,reviewer_id))
    extra=json.loads(text); extra['labels']['x']='KEEP_DISTINCT'; must_fail('extra',lambda:validate_review_text(json.dumps(extra),packet,phase,reviewer_id))
    wrongrid=json.loads(text); wrongrid['reviewer']['reviewer_id']='other'; must_fail('reviewer',lambda:validate_review_text(json.dumps(wrongrid),packet,phase,reviewer_id))
    dup=text.replace('"a":"KEEP_DISTINCT"','"a":"KEEP_DISTINCT","a":"KEEP_DISTINCT"'); must_fail('duplicate',lambda:validate_review_text(dup,packet,phase,reviewer_id),DuplicateKeyError)
    with tempfile.TemporaryDirectory() as td:
        td=Path(td)
        def write(name,messages,cmd="cat BLIND_REVIEW_PACKET.json OPERATIONAL_REVIEW_RUBRIC.md"):
            rows=[{"type":"thread.started","thread_id":"t1"},{"type":"item.completed","item":{"type":"command_execution","command":cmd}}]+[{"type":"item.completed","item":{"type":"agent_message","text":m}} for m in messages]
            p=td/name; p.write_text('\n'.join(json.dumps(x) for x in rows)+'\n'); return p
        validate_trace(q,write('good',['status',text]),text,packet,phase,reviewer_id)
        must_fail('duplicate_result',lambda:validate_trace(q,write('dup',['status',text,text]),text,packet,phase,reviewer_id))
        must_fail('result_not_last',lambda:validate_trace(q,write('notlast',[text,'status']),text,packet,phase,reviewer_id))
        malformed='{"schema":"'+REVIEW_SCHEMA+'","labels":{}}'; must_fail('malformed',lambda:validate_trace(q,write('malformed',['status',malformed,text]),text,packet,phase,reviewer_id))
        must_fail('forbidden',lambda:validate_trace(q,write('forbid',['status',text],'ls -la'),text,packet,phase,reviewer_id))
    print(json.dumps({'pass':True,'semantic_correctness_asserted':False},sort_keys=True))
if __name__=='__main__': main()
