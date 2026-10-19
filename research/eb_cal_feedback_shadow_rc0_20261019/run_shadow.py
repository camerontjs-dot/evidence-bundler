#!/usr/bin/env python3
"""Informed, public-kit EB/CAL feedback feasibility; research-only, no contract mutation."""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
from typing import Any

from evidence_bundler.v1 import build_package
from evidence_bundler.v1.package import V1Config
from claim_audit_lab.contracts.factual_context import load_contract_b_intake
from claim_audit_lab.production_v1.semantic.models import FailureCode

CASES = ("p01", "p02", "p03", "p04", "p05", "p06", "p07", "p08")
WINDOWS = (1800, 2400, 8000)
REQUIRED = {
    "clm-p01": ("Procedure Sable-17", "Revision: 4", "Effective date: 3 March 2031"),
    "clm-p02": ("archived samples came from nine sites", "Twelve sites were invited"),
    "clm-p03-1": ("Procedure Wren-4", "two different reviewers", "Before document release"),
    "clm-p03-2": ("Procedure Wren-4", "reconciliation record", "Before document release"),
    "clm-p06-1": ("Halcyon-2 protocol", "sampling log to be signed"),
    "clm-p07": ("Ilex-9 solvent check", "mg/L", "Acceptance ceiling: 0.08."),
}
NO_WITNESS = ("clm-p04", "clm-p05", "clm-p06-2", "clm-p08")
# Oracle-like content markers are public, informed engineering probes only.
# They do not grade semantic sufficiency, which requires independent assessment.

def sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()

def need(cond: bool, msg: str) -> None:
    if not cond:
        raise AssertionError(msg)

def canonical(value: Any) -> bytes:
    return (json.dumps(value, sort_keys=True, ensure_ascii=False,
                       separators=(",", ":"), allow_nan=False) + "\n").encode()

def contents(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))

def record_need(package: dict, target: str, reason: str) -> dict:
    # Illustrative descriptor supplied by experiment, never attributed to actual CAL.
    return {
        "schema": "cal-eb-shadow-evidence-need-v0",
        "producer": "experiment_fixture_not_CAL",
        "upstream_contract_a_sha256": package["contract_a"]["handoff_sha256"],
        "unreviewed_package_sha256": package["package_sha256"],
        "target_id": target,
        "need": reason,
    }

def validate_need(request: dict, package: dict) -> None:
    allowed = {"schema", "producer", "upstream_contract_a_sha256",
               "unreviewed_package_sha256", "target_id", "need"}
    need(set(request) == allowed, "request introduces hidden/routing/verdict fields")
    need(request["schema"] == "cal-eb-shadow-evidence-need-v0", "schema drift")
    need(request["producer"] == "experiment_fixture_not_CAL", "false CAL authority")
    need(request["upstream_contract_a_sha256"] == package["contract_a"]["handoff_sha256"],
         "Contract A binding mismatch")
    need(request["unreviewed_package_sha256"] == package["package_sha256"],
         "native package binding mismatch")
    need(request["target_id"] in {t["proposition_id"] for t in package["primary_targets"]},
         "not an authoritative retrieval target")
    need(request["need"] in {"missing_relationship_context", "unresolved_required_material"},
         "unknown or verdict-directed request")

def analyze_case(name: str, a: dict, max_chars: int) -> tuple[dict, dict]:
    cfg = V1Config(candidate_depth=10, retained_k=3,
                   chunk_max_chars=max_chars, chunk_overlap_chars=80)
    p = build_package(contract_a=a, config=cfg)
    need(p["contract_a"] == a, f"{name}: source/claim rewrote")
    need(p["config_sha256"] == cfg.identity, f"{name}: config identity")
    src = {row["source_id"]:row for row in a["sources"]}
    expected_targets = {row["proposition_id"] for row in p["primary_targets"]}
    found: dict[str, list[dict]] = {t: [] for t in expected_targets}
    for row in p["candidates"]:
        original = src[row["source_id"]]
        actual = original["content"][row["char_start"]:row["char_end"]]
        need(actual == row["text"], "noncontiguous/edited candidate")
        need(row["passage_sha256"] == "sha256:" + sha(actual.encode()), "passage hash drift")
        need(row["source_content_sha256"] == original["content_sha256"], "source hash drift")
        need(row["proposition_id"] in expected_targets, "unexpected target")
        if row["selection_state"] == "retained":
            need(row["admission_state"] == "needs-review", "implicit admission")
            found[row["proposition_id"]].append(row)
    assessments: dict = {}
    for t, rows in found.items():
        markers = REQUIRED.get(t)
        if markers is not None:
            matching = [r for r in rows if all(m.lower() in r["text"].lower()
                                               for m in markers)]
        else:
            matching = []
        assessments[t] = {
            "retained": len(rows),
            "retained_chars": sum(len(r["text"]) for r in rows),
            "witness_marker_in_one_span": bool(matching),
            "marker_satisfying_ids": [r["passage_id"] for r in matching],
            "expected_no_witness_control": t in NO_WITNESS,
            "retained_rows": [
                {"passage_id":r["passage_id"],"source_id":r["source_id"],
                 "start":r["char_start"],"end":r["char_end"],
                 "rank":r["nomination_rank"],"text":r["text"]}
                for r in rows],
        }
    output = {
        "case": name,"chunk_max_chars":max_chars,"candidate_depth":10,"retained_k":3,
        "package_sha256":p["package_sha256"],"config_sha256":p["config_sha256"],
        "candidate_count":len(p["candidates"]),
        "source_hashes":{x["source_id"]:x["content_sha256"] for x in a["sources"]},
        "upstream_handoff_sha256":a["handoff_sha256"],
        "targets":assessments,
    }
    return p, output

def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--kit", type=Path, required=True)
    ap.add_argument("--unreviewed", type=Path, required=True)
    ap.add_argument("--out", type=Path, required=True)
    args=ap.parse_args()
    need(not args.out.exists(), "do not overwrite a result")
    freeze=contents(args.kit/"FREEZE.json")
    need(freeze["closure_sha256"] ==
         "sha256:01cac06293afdb4fd145c3f7b64464799620eac2fcce80ffc2d5bc677553878c",
         "kit closure drift")
    expected={v["path"]:v["sha256"].removeprefix("sha256:")
              for v in freeze["files"]}
    results={};input_digests={}
    for c in CASES:
        src=args.kit/f"inputs/{c}.contract-a.json"
        data=src.read_bytes()
        need(sha(data)==expected[str(src.relative_to(args.kit))],f"{c}: input mismatch")
        a=json.loads(data);input_digests[c]=sha(data)
        runs={}
        for w in WINDOWS:
            pkg, summary=analyze_case(c,a,w)
            runs[str(w)]=summary
            if w==1800:
                original=contents(args.unreviewed/c/"native_eb_v1_package.json")
                need(pkg==original, f"{c}: shadow B0 != exact V1 installed output")
            if w==1800 and c=="p07":
                request=record_need(pkg,"clm-p07","missing_relationship_context")
                validate_need(request,pkg)
                for mutation in (
                    dict(request,target_id="not-an-authoritative-target"),
                    dict(request,unreviewed_package_sha256="sha256:"+"0"*64),
                    dict(request,source_id="invented-source"),
                    dict(request,need="retrieve_supporting_evidence"),
                ):
                    try: validate_need(mutation,pkg)
                    except AssertionError: pass
                    else: raise AssertionError("malicious/misbound request was accepted")
                runs["shadow_request"]=request
        results[c]=runs
    # Mechanical check against actual pinned CAL consumer, not a semantic CAL run.
    view=load_contract_b_intake(args.unreviewed/"p07"/"contract_b")
    claims=view.semantic_context["claims"]
    need(all(len(x["admitted_passages"])==0 for x in claims),
         "unreviewed semantic view unexpectedly admitted evidence")
    need("UPSTREAM_APERTURE_INSUFFICIENT" in {e.value for e in FailureCode},
         "CAL insufficient-aperture code unavailable")
    need("EVIDENCE_NOT_ADMITTED" in {e.value for e in FailureCode},
         "CAL not-admitted code unavailable")
    cal_observation={
        "actual_component":"pinned CAL Contract B intake / semantic FailureCode vocabulary",
        "intake_extension_state":view.extension_state,
        "intake_ledger_keys":sorted(view.intake_ledger),
        "semantic_context_keys":sorted(view.semantic_context),
        "semantic_claims":[{"id":x["claim_id"],"admitted_count":len(x["admitted_passages"])}
                           for x in claims],
        "known_failure_codes":["UPSTREAM_APERTURE_INSUFFICIENT","EVIDENCE_NOT_ADMITTED"],
        "typed_need_request_observed":False,
        "full_semantic_CAL_audit_executed":False,
        "status":"CAL-facing missing-context producer still needs separate qualification",
    }
    out={"schema":"eb-cal-feedback-shadow-rc0-results-v1",
         "cases":results,"source_input_sha256":input_digests,
         "cal_consumer_boundary":cal_observation,
         "limits":{
            "is_blinded":False,"source_world":"synthetic public acceptance kit",
            "actual_CAL_generated_request":False,"changed_V1_config_is_installed_CLI":False,
            "canonical_B_from_rewindowed_candidate":False,
            "marker_check_is_semantic_oracle":False,
            "representative_workload":False,
         }}
    args.out.mkdir(parents=True)
    (args.out/"RESULT.json").write_bytes(json.dumps(out,sort_keys=True,indent=2,ensure_ascii=False).encode()+b"\n")
    for c in CASES:
        initial=results[c]["1800"]
        recovered=results[c]["8000"]
        t="clm-p07" if c=="p07" else "clm-p06-2" if c=="p06" else None
        print(c, "B0",len(initial["targets"]),"targets",
              "R2",len(recovered["targets"]),"targets",
              ("relation_recovered="+str(recovered["targets"][t]["witness_marker_in_one_span"])
               if t else ""))
    print("RESULT_SHA256",sha((args.out/"RESULT.json").read_bytes()))
    return 0

if __name__=="__main__":
    raise SystemExit(main())
