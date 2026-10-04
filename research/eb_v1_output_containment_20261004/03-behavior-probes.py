"""Independent portable V1 probes; never executes models or scientific corpora."""
from __future__ import annotations

import copy
import hashlib
import importlib.resources
import json
import os
import shutil
import subprocess
import sys
import traceback
from pathlib import Path

import yaml

import evidence_bundler
from evidence_bundler.contracts.writer import validate_bundle_tree
from evidence_bundler.v1 import build_package, load_package, validate_package
from evidence_bundler.v1.contract_b import (
    INTEGRATION_CONFIG,
    project_contract_b,
    validate_projection_receipt,
)


def digest(data: bytes | str) -> str:
    if isinstance(data, str):
        data = data.encode("utf-8")
    return "sha256:" + hashlib.sha256(data).hexdigest()


def canonical(obj: object, newline: bool = False) -> str:
    return json.dumps(obj, sort_keys=True, separators=(",", ":"), ensure_ascii=False, allow_nan=False) + ("\n" if newline else "")


def seal_wire(obj: dict) -> dict:
    obj.pop("handoff_sha256", None)
    obj["handoff_sha256"] = digest(canonical(obj))
    return obj


def reseal_package(obj: dict) -> dict:
    obj.pop("package_sha256", None)
    obj["package_sha256"] = digest(canonical(obj, True))
    return obj


def fixture() -> dict:
    text = "zinnia marker"
    sources = [
        {"source_id": f"src-{i:02}", "media_type": "text/plain; charset=utf-8", "content": f"zinnia marker calibration record label {i:02}."}
        for i in range(12)
    ]
    sources.extend([
        {"source_id": "src-orchard", "media_type": "text/plain; charset=utf-8", "content": "violet orchard protocol background."},
        {"source_id": "src-quartz", "media_type": "text/markdown; charset=utf-8", "content": "# Quartz beacon\n\nquartz beacon protocol boundary.\n"},
    ])
    for source in sources:
        source["content_sha256"] = digest(source["content"])
    return seal_wire({
        "schema": "contract-a-wire-candidate-rc2",
        "handoff_id": "independent-portable-behavior-v1",
        "producer": {"producer_id": "independent-engineering-probe", "producer_version": "1"},
        "work": {"work_id": "portable-software-properties-only"},
        "root_proposition": {"proposition_id": "claim-zinnia", "text": text, "text_sha256": digest(text)},
        "decomposition": {"state": "not_decomposed"},
        "sources": list(reversed(sources)),
    })


def write_json(path: Path, obj: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(canonical(obj, True), encoding="utf-8")


def tree_hashes(root: Path) -> dict:
    return {str(p.relative_to(root)): digest(p.read_bytes()) for p in sorted(root.rglob("*")) if p.is_file()}


def require(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)


def main() -> None:
    base = Path(sys.argv[1]).resolve()
    base.mkdir(parents=True, exist_ok=False)
    cli = Path(sys.executable).parent / "evidence-bundler-v1"
    env = dict(os.environ, HF_HUB_OFFLINE="1", TRANSFORMERS_OFFLINE="1", EVIDENCE_BUNDLER_RUN_RERANKER_SMOKE="0")
    records = []

    def record(name: str, function, scope: str = "required_property"):
        try:
            details = function()
            row = {"name": name, "scope": scope, "status": "PASS", "details": details}
        except Exception as exc:
            row = {"name": name, "scope": scope, "status": "FAIL", "error_type": type(exc).__name__, "error": str(exc), "traceback": traceback.format_exc()}
        records.append(row)
        write_json(base / "results.json", records)
        print(canonical({key: value for key, value in row.items() if key != "traceback"}), flush=True)
        return row

    def run(name: str, wire: dict, admission: dict | None = None, carrier: dict | None = None):
        case = base / name
        case.mkdir(parents=True, exist_ok=True)
        input_path = case / "contract_a.json"
        write_json(input_path, wire)
        out = case / "output"
        cmd = [str(cli), "run", str(input_path), "--out-dir", str(out)]
        if admission is not None:
            write_json(case / "admission.json", admission)
            cmd += ["--admission", str(case / "admission.json")]
        if carrier is not None:
            write_json(case / "carrier.json", carrier)
            cmd += ["--compatibility-carrier", str(case / "carrier.json")]
        result = subprocess.run(cmd, cwd=case, env=env, capture_output=True, text=True, check=False)
        (case / "stdout.txt").write_text(result.stdout, encoding="utf-8")
        (case / "stderr.txt").write_text(result.stderr, encoding="utf-8")
        write_json(case / "invocation.json", {"command": cmd, "cwd": str(case), "exit_code": result.returncode})
        return result, out

    def invalid(name: str, wire: dict, admission: dict | None = None, carrier: dict | None = None):
        result, out = run(name, wire, admission, carrier)
        require(result.returncode != 0, "invalid input succeeded")
        emitted = tree_hashes(out)
        require(not emitted, "invalid input emitted durable artifacts before rejection")
        return {"exit_code": result.returncode, "files_written": len(emitted), "stderr": result.stderr}

    initial = fixture()
    first_result, first = run("first", initial)
    require(first_result.returncode == 0, first_result.stderr)
    package = json.loads((first / "native_eb_v1_package.json").read_text())
    receipt = json.loads((first / "projection_receipt.json").read_text())
    extension_rel = Path("contract_b/extensions/contract-b-factual-context-v1.json")
    extension = json.loads((first / extension_rel).read_text())
    records.append({"name": "installed_cli_outside_repository", "scope": "required_property", "status": "PASS", "details": {"package_file": evidence_bundler.__file__, "package_version": evidence_bundler.__version__, "cwd": str(first.parent), "exit_code": first_result.returncode, "source_count": len(initial["sources"]), "package_sha256": package["package_sha256"]}})

    def inspect():
        a = subprocess.run([str(cli), "inspect", "--json"], cwd=base, capture_output=True, text=True, check=True)
        b = subprocess.run([str(cli), "inspect", "--json"], cwd=base, capture_output=True, text=True, check=True)
        require(a.stdout == b.stdout, "inspect differs")
        data = json.loads(a.stdout)
        require(data["package_version"] == "0.2.0", "wrong installed version")
        require(data["config"]["candidate_depth"] == 10 and data["config"]["retained_k"] == 3, "wrong profile")
        write_json(base / "inspect.json", data)
        return data
    record("installed_authority_inspect", inspect)

    def custody():
        require(package["contract_a"] == initial, "embedded input drift")
        sources = {s["source_id"]: s for s in initial["sources"]}
        for row in package["candidates"]:
            source = sources[row["source_id"]]
            require(row["text"] == source["content"][row["char_start"]:row["char_end"]], "source span drift")
            require(row["source_content_sha256"] == digest(source["content"]), "source hash drift")
            require(row["passage_sha256"] == digest(row["text"]), "passage digest drift")
        resealed = reseal_package(copy.deepcopy(package))
        require(resealed["package_sha256"] == package["package_sha256"], "whole-package digest mismatch")
        return {"source_count_bound_in_native": len(sources), "candidate_span_checks": len(package["candidates"])}
    record("source_byte_and_native_identity_custody", custody)

    def depth_retention():
        rows = package["candidates"]
        require(len(rows) == 10, "depth is not 10")
        require([r["source_id"] for r in rows] == [f"src-{i:02}" for i in range(10)], "tie order unstable or wrong")
        require([r["nomination_rank"] for r in rows] == list(range(1,11)), "ranks not continuous")
        require([r["admission_state"] for r in rows] == ["needs-review"]*3 + ["not_applicable"]*7, "admission/selection conflation")
        require([r["selection_state"] for r in rows] == ["retained"]*3 + ["not_retained"]*7, "retention drift")
        execution = package["retrieval_executions"][0]
        require(execution["candidate_depth_hit"] is True and execution["aperture_state"] == "bounded_at_limit", "aperture misreported")
        require(execution["searched_source_ids"] == sorted(s["source_id"] for s in initial["sources"]), "source scope drift")
        return {"nominated": len(rows), "retained": 3, "accepted": 0, "depth_limit_hit": True, "tie_break": "source_id", "all_declared_sources_searched": True}
    record("bounded_nomination_retention_and_default_admission", depth_retention)

    def projection():
        require(len(extension["history"]) == len(package["candidates"]), "history incomplete")
        expected = {(r["proposition_id"], r["passage_id"]):r for r in package["candidates"]}
        for h in extension["history"]:
            r = expected[(h["claim_id"],h["passage_id"])]
            require(h["nomination"]["rank"] == r["nomination_rank"], "rank projection drift")
            require(h["review"]["native_admission_state"] == r["admission_state"], "admission state lost")
        require(len(receipt["mappings"]) == len(expected), "receipt mappings incomplete")
        require(not validate_bundle_tree(first/"contract_b"), "bundle invalid")
        claim = yaml.safe_load((first/"contract_b/claims/claim-zinnia.yaml").read_text())
        require(claim["evidence_passages"] == [], "unreviewed candidates leaked to admitted evidence")
        return {"candidate_relationships": len(expected), "accepted_evidence_passages": 0, "history_preserves_native_not_applicable": True, "bundle_validation_errors": []}
    record("nonsemantic_projection_preserves_nomination_history", projection)

    def replay():
        result, second = run("relocated-unrelated-directory/second", initial)
        require(result.returncode == 0, result.stderr)
        require(tree_hashes(first) == tree_hashes(second), "identical inputs differ byte-for-byte under relocation")
        relocated = base/"relocated-package-copy"
        shutil.copytree(first,relocated)
        loaded = load_package(relocated/"native_eb_v1_package.json")
        require(loaded == package, "relocated package identity drift")
        require(not validate_bundle_tree(relocated/"contract_b"), "relocated bundle invalid")
        validate_projection_receipt(json.loads((relocated/"projection_receipt.json").read_text()))
        return {"identical_tree_file_count":len(tree_hashes(first)), "all_file_hashes_equal":True, "copied_package_and_bundle_validate":True}
    record("byte_determinism_and_relocated_replay", replay)

    decisions = {"schema":"evidence-bundler-admission-v1", "decisions":[{"proposition_id":r["proposition_id"],"passage_id":r["passage_id"],"decision":d} for r,d in zip(package["candidates"][:3],["accepted","rejected","needs-review"],strict=True)]}
    def admission():
        result,out=run("explicit-admission",initial,decisions)
        require(result.returncode==0,result.stderr)
        p=json.loads((out/"native_eb_v1_package.json").read_text())
        require([r["admission_state"] for r in p["candidates"][:3]]==["accepted","rejected","needs-review"],"explicit state lost")
        claim=yaml.safe_load((out/"contract_b/claims/claim-zinnia.yaml").read_text())
        require([r["passage_id"] for r in claim["evidence_passages"]]==[package["candidates"][0]["passage_id"]],"wrong accepted projection")
        require(p["package_sha256"]!=package["package_sha256"],"admission is not identity-bound")
        require([r["passage_id"] for r in p["candidates"]]==[r["passage_id"] for r in package["candidates"]],"review changed nominations")
        return {"accepted":1,"rejected":1,"needs_review_retained":1,"all_nominations_preserved":True,"package_identity_changes":True}
    record("explicit_admission_is_separate_and_identity_bound",admission)

    for label,modify in [
        ("source_content_tamper",lambda x:x["sources"][0].update(content="changed source without matching hash")),
        ("claim_text_tamper",lambda x:x["root_proposition"].update(text="changed target without matching hash")),
        ("duplicate_source_id",lambda x:x["sources"].append(copy.deepcopy(x["sources"][0]))),
        ("unsupported_schema",lambda x:x.update(schema="contract-a-unsupported")),
        ("forbidden_source_path",lambda x:x["sources"][0].update(path="outside.txt")),
        ("unsupported_pdf_wire",lambda x:x["sources"][0].update(media_type="application/pdf")),
        ("unknown_decomposition",lambda x:x.update(decomposition={"state":"unknown"})),
        ("failed_decomposition",lambda x:x.update(decomposition={"state":"failed"})),
    ]:
        w=copy.deepcopy(initial); modify(w); seal_wire(w)
        record(label,lambda label=label,w=w:invalid(label,w))

    for label,rows in [
        ("duplicate_admission",[decisions["decisions"][0]]*2),
        ("unknown_admission",[{"proposition_id":"unknown-proposition","passage_id":package["candidates"][0]["passage_id"],"decision":"accepted"}]),
        ("nonretained_admission",[{"proposition_id":package["candidates"][3]["proposition_id"],"passage_id":package["candidates"][3]["passage_id"],"decision":"accepted"}]),
    ]:
        record(label,lambda label=label,rows=rows:invalid(label,initial,{"schema":"evidence-bundler-admission-v1","decisions":rows}))

    def zero_hit():
        w=copy.deepcopy(initial); w["root_proposition"].update(text="unmatchabletoken",text_sha256=digest("unmatchabletoken"));seal_wire(w)
        result,out=run("zero-hit",w);require(result.returncode==0,result.stderr)
        p=json.loads((out/"native_eb_v1_package.json").read_text())
        require(p["execution_state"]=="complete" and p["candidates"]==[],"zero-hit collapsed into not-run or success evidence")
        require(p["retrieval_executions"][0]["aperture_state"]=="bounded_under_limit","zero-hit aperture drift")
        return {"execution_state":p["execution_state"],"candidates":0,"aperture_state":p["retrieval_executions"][0]["aperture_state"]}
    record("completed_zero_hit_is_explicit",zero_hit)

    def decomposition():
        w=copy.deepcopy(initial)
        w["decomposition"]={"state":"declared","decomposition_id":"decomp-1","operator":"all_of","children":[{"proposition_id":"child-zinnia","text":"zinnia marker","text_sha256":digest("zinnia marker"),"sequence":1},{"proposition_id":"child-quartz","text":"quartz beacon","text_sha256":digest("quartz beacon"),"sequence":2}]}
        seal_wire(w);write_json(base/"declared-input.json",w)
        p=build_package(contract_a=w,config=INTEGRATION_CONFIG,not_run_target_ids={"child-quartz"})
        require(p["execution_state"]=="partial","partial execution state lost")
        require([t["proposition_id"] for t in p["primary_targets"]]==["child-zinnia","child-quartz"],"root acquired normative lane")
        require(p["retrieval_executions"][1]["status"]=="not_run" and p["retrieval_executions"][1]["searched_source_ids"]==[],"not-run collapsed into zero-hit")
        write_json(base/"partial-package.json",p)
        return {"primary_targets":[t["proposition_id"] for t in p["primary_targets"]],"execution_state":"partial","explicit_not_run_has_empty_search_scope":True,"surface":"native Python API; fixed production CLI has no not-run option"}
    record("declared_children_and_explicit_not_run_are_distinct",decomposition)

    def unicode():
        w=copy.deepcopy(initial)
        text="# Café calibration\r\n\r\nzinnia marker — naïve μmol 😀.\r\n\r\n| marker | value |\r\n| --- | --- |\r\n| zinnia | 1 |\r\n"
        w["sources"]=[{"source_id":"unicode-source","media_type":"text/markdown; charset=utf-8","content":text,"content_sha256":digest(text)}];seal_wire(w)
        result,out=run("unicode-crlf-markdown",w);require(result.returncode==0,result.stderr)
        p=json.loads((out/"native_eb_v1_package.json").read_text())
        require(p["candidates"],"unicode/CRLF source produced no candidates")
        for r in p["candidates"]:require(text[r["char_start"]:r["char_end"]]==r["text"],"Unicode/CRLF offset mismatch")
        return {"candidate_count":len(p["candidates"]),"exact_character_spans":True,"offset_unit":"Python Unicode code points; original UTF-8 bytes hashed separately"}
    record("unicode_crlf_markdown_source_spans",unicode)

    def tamper(label,change,rehash):
        p=copy.deepcopy(package);change(p)
        if rehash:reseal_package(p)
        write_json(base/"tamper-inputs"/(label+".json"),p)
        try:validate_package(p)
        except Exception as exc:return {"rehashed":rehash,"error_type":type(exc).__name__,"error":str(exc)}
        raise AssertionError("tampered inconsistent package accepted")
    for label,change,rehash in [
        ("raw_admission_state_tamper",lambda p:p["candidates"][0].update(admission_state="accepted"),False),
        ("rehashed_excerpt_substitution",lambda p:p["candidates"][0].update(text="substituted excerpt"),True),
        ("rehashed_source_hash_substitution",lambda p:p["candidates"][0].update(source_content_sha256="sha256:"+"f"*64),True),
        ("rehashed_nonretained_acceptance",lambda p:p["candidates"][3].update(admission_state="accepted"),True),
        ("rehashed_retention_override",lambda p:p["candidates"][3].update(selection_state="retained",admission_state="accepted"),True),
        ("rehashed_rank_gap",lambda p:p["candidates"][0].update(nomination_rank=2),True),
        ("rehashed_searched_scope_substitution",lambda p:p["retrieval_executions"][0].update(searched_source_ids=[]),True),
        ("rehashed_native_authority_substitution",lambda p:p["contract_a_authority"].update(release_commit="0"*40),True),
    ]:
        record(label,lambda label=label,change=change,rehash=rehash:tamper(label,change,rehash))

    carrier=json.loads(importlib.resources.files("evidence_bundler.production_v1").joinpath("data/contract_b_compatibility_carrier.json").read_text())
    weakened=copy.deepcopy(carrier);weakened["authority"]["semantic_use_authorized"]=True
    record("carrier_semantic_authority_rejected",lambda:invalid("weakened-carrier",initial,carrier=weakened))

    def altered_carrier():
        changed=copy.deepcopy(carrier);changed["source_profile"]["title_template"]="Probe compatibility title {source_id}"
        result,out=run("allowed-carrier-override",initial,carrier=changed);require(result.returncode==0,result.stderr)
        p=json.loads((out/"native_eb_v1_package.json").read_text());r=json.loads((out/"projection_receipt.json").read_text())
        require(p==package,"carrier changed native package")
        require(r["mappings"]==receipt["mappings"],"carrier changed candidate mapping")
        require(r["bundle_hash"]!=receipt["bundle_hash"],"carrier change not identity-bound")
        return {"native_package_unchanged":True,"mappings_unchanged":True,"bundle_identity_changes":True}
    record("allowed_carrier_override_is_downstream_and_identity_bound",altered_carrier)

    def bundle_tamper():
        out=base/"tampered-bundle";shutil.copytree(first/"contract_b",out)
        path=next(out.glob("evidence/*/passages/*.yaml"));data=yaml.safe_load(path.read_text());data["passage_text"]="substituted passage";path.write_text(yaml.safe_dump(data),encoding="utf-8")
        errors=validate_bundle_tree(out);require(bool(errors),"bundle passage tamper accepted")
        return {"validation_errors":errors}
    record("projected_bundle_tamper_is_rejected",bundle_tamper)

    def receipt_tamper():
        r=copy.deepcopy(receipt);r["native_package_sha256"]="sha256:"+"a"*64
        try:validate_projection_receipt(r)
        except Exception as exc:return {"error_type":type(exc).__name__,"error":str(exc)}
        raise AssertionError("receipt tamper accepted")
    record("raw_projection_receipt_tamper_is_rejected",receipt_tamper)

    def occupied():
        result=subprocess.run([str(cli),"run",str(first.parent/"contract_a.json"),"--out-dir",str(first)],cwd=base,env=env,capture_output=True,text=True)
        require(result.returncode!=0,"nonempty output reused")
        require("refusing non-empty output" in result.stderr,"wrong refusal")
        return {"exit_code":result.returncode,"refusal":"non-empty output"}
    record("nonempty_output_refused",occupied)

    def stale_admission():
        w=copy.deepcopy(initial);w["root_proposition"]["text"]="zinnia marker revised proposition";w["root_proposition"]["text_sha256"]=digest(w["root_proposition"]["text"]);seal_wire(w)
        result,out=run("same-ids-changed-proposition",w,decisions);require(result.returncode==0,result.stderr)
        p=json.loads((out/"native_eb_v1_package.json").read_text())
        return {"changed_text_same_proposition_id_admission_reused":p["candidates"][0]["admission_state"]=="accepted","query_id_changed":p["candidates"][0]["query_id"]!=package["candidates"][0]["query_id"],"interpretation":"Admission wire binds proposition_id and passage_id, not target text/query/handoff digest. A caller must ensure admission belongs to the intended input revision; this probe does not declare a new admission contract."}
    record("admission_revision_binding_limit",stale_admission,"observed_boundary_not_asserted_defect")

    def ranking_limit():
        p=copy.deepcopy(package);p["candidates"][0]["nomination_rank"],p["candidates"][1]["nomination_rank"]=2,1;reseal_package(p)
        validate_package(p)
        project_contract_b(package=p,compatibility_carrier=carrier,out_dir=base/"rehashed-rank-permutation")
        return {"internally_consistent_rehashed_rank_permutation_accepted":True,"package_identity_changed":p["package_sha256"]!=package["package_sha256"],"interpretation":"Native validation verifies structure, source binding and supplied digest; it does not re-execute BM25 to attest ranking derivation. A trusted original digest plus deterministic replay is a separate check."}
    record("validator_is_not_retrieval_execution_attestation",ranking_limit,"observed_boundary_not_asserted_defect")

    write_json(base/"artifact-hashes.json",tree_hashes(base))
    print(canonical({"summary":{"pass":sum(r["status"]=="PASS" for r in records),"fail":sum(r["status"]=="FAIL" for r in records),"observed_boundaries":sum(r["scope"]!="required_property" for r in records)}}))


if __name__=="__main__":
    main()
