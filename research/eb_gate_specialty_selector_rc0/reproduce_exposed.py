from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
from typing import Any

from selector import select


def sha256_file(path: str | Path) -> str:
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def selected_map(rows: list[dict[str, Any]]) -> dict[str, list[str]]:
    return {
        str(row["lane_id"]): [str(value) for value in row["selected_candidate_ids"]]
        for row in rows
    }


def payload_for_lane(lane_id: str, diag: dict[str, Any]) -> dict[str, Any]:
    return {
        "claim_id": lane_id,
        "expected_evidence_forms": list(diag["expected_forms"]),
        "candidates": [
            {
                "candidate_id": str(row["candidate_id"]),
                "rank": int(row["rank"]),
                "text": str(row["text"]) if "text" in row else "",
                "semantic_score": float(row["semantic_score"]),
            }
            for row in diag["candidates"]
        ],
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--v1-selections", required=True)
    parser.add_argument("--out", required=True)
    args = parser.parse_args()

    path = Path(args.v1_selections)
    source = json.loads(path.read_text(encoding="utf-8"))
    expected = selected_map(
        source["selections"]["gate_fraction_loose_correct_cap_0.010"]
    )

    rows: list[dict[str, Any]] = []
    exact = True
    permutation = True

    for lane_id in sorted(source["diagnostics"]):
        diag = source["diagnostics"][lane_id]
        payload = payload_for_lane(lane_id, diag)

        # The frozen development diagnostics intentionally omit text because the
        # already-derived specialty labels are what were frozen pre-gold. RC0
        # therefore cannot be reclassified from those diagnostics alone.
        # This script reconstructs representative text tokens from the frozen
        # loose-form observations solely to verify the selector decision rule.
        for candidate, frozen in zip(payload["candidates"], diag["candidates"], strict=True):
            forms = set(frozen["loose_forms"])
            tokens: list[str] = []
            if "authoritative_declaration" in forms:
                tokens.append("policy states that")
            if "event_record" in forms:
                tokens.append("incident event record")
            if "registry_entry" in forms:
                tokens.append("registry certificate")
            if not tokens:
                tokens.append("plain narrative")
            candidate["text"] = " ".join(tokens)

        first = select(payload)
        reversed_payload = {
            **payload,
            "candidates": list(reversed(payload["candidates"])),
        }
        second = select(reversed_payload)

        observed = list(first["selected_candidate_ids"])
        lane_exact = observed == expected[lane_id]
        lane_permutation = (
            first["selected_candidate_ids"] == second["selected_candidate_ids"]
        )
        exact = exact and lane_exact
        permutation = permutation and lane_permutation

        rows.append(
            {
                "lane_id": lane_id,
                "expected": expected[lane_id],
                "observed": observed,
                "exact_match": lane_exact,
                "permutation_invariant": lane_permutation,
                "action": first["action"],
                "expected_specialty_forms": first["expected_specialty_forms"],
            }
        )

    report = {
        "schema": "eb-gate-specialty-selector-rc0-development-equivalence",
        "source_v1_selection_sha256": sha256_file(path),
        "target_arm": "gate_fraction_loose_correct_cap_0.010",
        "exact_all_lanes": exact,
        "permutation_all_lanes": permutation,
        "lane_count": len(rows),
        "rows": rows,
        "nonclaims": [
            "this is exposed-development implementation equivalence only",
            "reconstructed form tokens verify decision-rule equivalence, not classifier fidelity",
            "fresh qualification remains required",
        ],
    }
    Path(args.out).write_text(
        json.dumps(report, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    print(json.dumps(report, indent=2, sort_keys=True))
    if not exact or not permutation:
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
