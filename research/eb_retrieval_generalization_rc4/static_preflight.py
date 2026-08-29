#!/usr/bin/env python3
from __future__ import annotations
import hashlib,json
from pathlib import Path
ROOT=Path(__file__).resolve().parent
EXPECTED_TARGET='65c671e25dfd998350cfdb6d2a84c4a46d4db7e867827dd99fd4e57a8003f60e'
def main():
    target=json.loads((ROOT/'target_identity.json').read_text()); digest=hashlib.sha256(json.dumps(target,sort_keys=True,separators=(',',':')).encode()).hexdigest()
    assert digest==EXPECTED_TARGET
    controls=json.loads((ROOT/'control_plan.json').read_text())['controls']; add=json.loads((ROOT/'additional_control_plan.json').read_text())['controls']
    source=(ROOT/'control_runner.py').read_text()
    missing=[x['id'] for x in controls+add if f"'{x['id']}'" not in source]
    assert not missing, missing
    plan=json.loads((ROOT/'metamorphic_plan.json').read_text())['transformations']; msrc=(ROOT/'metamorphic_runner.py').read_text()
    mm=[x['id'] for x in plan if x['id'] not in msrc]; assert not mm,mm
    assert target['exposure']=={'hybrid_sealed_exposed':False,'semantic_sealed_exposed':False}
    print(json.dumps({'target_config_sha256':digest,'control_ids':[x['id'] for x in controls+add],'metamorphic_ids':[x['id'] for x in plan],'hybrid_sealed_exposed':False,'semantic_sealed_exposed':False},indent=2,sort_keys=True))
if __name__=='__main__': main()
