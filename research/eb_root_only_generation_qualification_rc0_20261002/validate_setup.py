"""Mechanical packaging checks only; no model execution or semantic qualification."""
from __future__ import annotations

import hashlib
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent


def need(condition: bool, message: str) -> None:
    if not condition:
        raise ValueError(message)


def read(name: str) -> dict:
    def unique(items):
        result = {}
        for key, value in items:
            need(key not in result, "duplicate JSON key")
            result[key] = value
        return result

    def nonfinite(value):
        raise ValueError("nonfinite JSON value: " + value)

    return json.loads(
        (HERE / name).read_text(encoding="utf-8"),
        object_pairs_hook=unique,
        parse_constant=nonfinite,
    )


def primary_capsule(row: dict, rubric: dict, wire: dict) -> dict:
    need(set(row) == {"alias", "root_text"}, "root-only row fields")
    return {
        "schema": "eb-rc2-capsule-v1",
        "role": "primary",
        "root_alias": row["alias"],
        "root_text": row["root_text"],
        "rubric": rubric,
        "output_schema": {
            **{key: wire["closed_fields"][key] for key in ("primary", "child", "subject")},
            "constraints": wire["constraints"],
        },
        "proposal": None,
    }


def check_design(roots: dict, oracle: dict, metamorphic: dict) -> dict:
    need(roots["schema"] == "eb-root-generation-public-roots-v1", "roots schema")
    need(oracle["schema"] == "eb-root-generation-oracle-v1", "oracle schema")
    need(metamorphic["schema"] == "eb-root-generation-metamorphic-v1", "pair schema")
    rows = roots["rows"]
    need(len(rows) == 12, "twelve roots")
    need(all(set(row) == {"alias", "root_text"} for row in rows), "oracle leaked into roots")
    aliases = [row["alias"] for row in rows]
    need(len(set(aliases)) == 12, "unique aliases")
    need(all(isinstance(row["root_text"], str) and row["root_text"] for row in rows), "root text")
    gold = oracle["rows"]
    need(len(gold) == 12 and {row["alias"] for row in gold} == set(aliases), "gold coverage")
    need(len({row["alias"] for row in gold}) == 12, "duplicate oracle alias")
    eligible = {row["alias"] for row in gold if row["expected_status"] == "declared"}
    ineligible = {row["alias"] for row in gold if row["expected_status"] == "ineligible"}
    need(len(eligible) == 8 and len(ineligible) == 4, "8/4 population")
    roots_by_alias = {row["alias"]: row["root_text"] for row in rows}
    for row in gold:
        if row["alias"] in eligible:
            need(len(row["obligation_inventory"]) == 2, "eligible obligation inventory")
            need(len(set(row["obligation_inventory"])) == 2, "duplicate oracle obligation")
            need(row["subject_anchor"] in roots_by_alias[row["alias"]], "literal oracle anchor")
            need(bool(row["entity_class"]), "oracle entity class")
        else:
            need(row["obligation_inventory"] == [] and row["subject_anchor"] is None, "ineligible oracle")
    pairs = metamorphic["pairs"]
    need(len(pairs) == 4 and len({row["pair_id"] for row in pairs}) == 4, "four pairs")
    paired = [alias for pair in pairs for alias in pair["aliases"]]
    need(len(paired) == 8 and set(paired) == eligible, "each eligible case paired exactly once")
    need(all(len(pair["aliases"]) == 2 and pair["change"] and pair["invariants"] for pair in pairs), "pair fields")
    for pair in pairs:
        first, second = pair["aliases"]
        need(roots_by_alias[first] != roots_by_alias[second], "changed pair root")
    return {"roots": 12, "eligible": 8, "ineligible": 4, "metamorphic_pairs": 4}


def validate() -> dict:
    manifest = read("SETUP-MANIFEST.json")
    need(manifest["schema"] == "eb-root-generation-setup-manifest-v1", "manifest schema")
    for relative, expected in manifest["raw_sha256"].items():
        candidate = Path(relative)
        need(not candidate.is_absolute() and ".." not in candidate.parts, "unsafe closure path")
        source = HERE / candidate
        need(source.is_file() and not source.is_symlink(), "missing/symlink closure file")
        actual = "sha256:" + hashlib.sha256(source.read_bytes()).hexdigest()
        need(actual == expected, "raw hash drift: " + relative)
    roots, oracle, pairs = (
        read("ROOTS.PUBLIC.json"),
        read("ORACLE.PUBLIC.json"),
        read("METAMORPHIC.PUBLIC.json"),
    )
    counts = check_design(roots, oracle, pairs)
    rubric, wire = read("AUTHORING-RUBRIC.json"), read("SCHEMAS.json")
    for row in roots["rows"]:
        capsule = primary_capsule(row, rubric, wire)
        need(set(capsule) == set(wire["closed_fields"]["capsule"]), "inherited capsule fields")
        need(capsule["proposal"] is None, "supplied proposal in generation capsule")
        need(set(capsule["output_schema"]) == {"primary", "child", "subject", "constraints"}, "minimal wire schema")
        need(capsule["root_text"] == row["root_text"], "root fidelity")
    controls = read("REVIEWER-CALIBRATION.PUBLIC.json")
    need(len(controls["cases"]) == 12 and controls["required_correct"] == 12, "unchanged judgment control gate")
    need(sum(case["expected_decision"] == "accept" for case in controls["cases"]) == 6, "judgment oracle balance")
    bootstrap = read("BOOTSTRAP-MANIFEST.json")
    allow = set(bootstrap["pre_freeze_allowlist"])
    deny = set(bootstrap["pre_freeze_denylist"])
    need(not allow.intersection(deny), "aperture allow/deny collision")
    need({"ROOTS.PUBLIC.json", "ORACLE.PUBLIC.json", "METAMORPHIC.PUBLIC.json", "REVIEWER-CALIBRATION.PUBLIC.json"} <= deny, "profile writer answer denial")
    status = read("LAUNCH-STATUS.json")
    need(status["execution"] == "NOT_RUN" and status["target_calls"] == 0, "setup cannot assert execution")
    need(not status["private_transmission_authorized"] and not status["population_construction_authorized"], "private authority leak")

    # Mutation controls exercise the boundary, without executing or simulating a role.
    mutations = 0
    bad_roots = json.loads(json.dumps(roots))
    bad_roots["rows"][0]["proposed_children"] = ["answer-bearing material"]
    try:
        check_design(bad_roots, oracle, pairs)
    except ValueError:
        mutations += 1
    bad_pairs = json.loads(json.dumps(pairs))
    bad_pairs["pairs"][0]["aliases"][1] = bad_pairs["pairs"][0]["aliases"][0]
    try:
        check_design(roots, oracle, bad_pairs)
    except ValueError:
        mutations += 1
    need(mutations == 2, "mutation controls must be rejected")
    return {
        "mechanical_setup": "PASS",
        **counts,
        "root_only_capsules_checked": 12,
        "boundary_mutations_rejected": mutations,
        "target_execution": "NOT_RUN",
        "semantic_evaluator": "NOT_RUN",
        "semantic_generation": "UNKNOWN",
        "isolation": "UNBOUND",
    }


if __name__ == "__main__":
    print(json.dumps(validate(), sort_keys=True))
