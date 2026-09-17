#!/usr/bin/env python3
"""Prereveal control helpers for EB typed-selector RC1. No selector code is imported."""
from __future__ import annotations
import copy,hashlib,json
REQUIRED_GATES=["exact_replay","input_order_permutation_invariant","irrelevant_metadata_invariant","no_duplicate_selection","selection_budget_at_most_3","ids_within_frozen_top10","pool_hash_preserved","no_gold_fields_in_output","runner_has_no_gold_dependency","adapter_source_hashes_recorded"]
def canonical(obj): return json.dumps(obj,sort_keys=True,separators=(',',':'),ensure_ascii=False)
def sha(obj): return 'sha256:'+hashlib.sha256(canonical(obj).encode()).hexdigest()
def permuted_pool(pools):
 x=copy.deepcopy(pools); x['lanes']=list(reversed(x['lanes']))
 for lane in x['lanes']: lane['candidates']=list(reversed(lane['candidates']))
 return x
def irrelevant_metadata_variant(pools):
 x=copy.deepcopy(pools); x['prereveal_irrelevant_metadata']={'nonce':'RC1_FIXED_METADATA_MUTATION'}; return x
def selections_only(out): return {a:{l:list(v) for l,v in sorted(ls.items())} for a,ls in sorted(out['arms'].items())}
def verify_replay(a,b): return selections_only(a)==selections_only(b)
def verify_permutation(a,b): return selections_only(a)==selections_only(b)
def verify_metadata(a,b): return selections_only(a)==selections_only(b)
def manifest(pools): return {'schema':'eb-typed-selector-rc1-preexecution-controls-v1','pool_canonical_sha256':sha(pools),'mutations':{'permutation':'reverse lane order and candidate order within every lane','irrelevant_metadata':{'nonce':'RC1_FIXED_METADATA_MUTATION'}},'required_system_gates':REQUIRED_GATES}
if __name__=='__main__': print('CONTROL_HELPER_IMPORT_PASS')
