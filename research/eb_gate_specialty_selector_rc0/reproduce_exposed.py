from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
from typing import Any

from selector import candidate_specialty_forms, select


def sha256_file(path: str | Path) -> str:
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def selected_map(rows: list[dict[str, Any]]) -> dict[str, list[str]]:
    return {
        str(row["lane_id"]): [str(value) for value in row["selected_candidate_ids"]]
        for row in rows
    }


def payload_for_lane(
    lane_id: str,
    diag: dict[str, Any],
    pool_by_id: dict[str, dict[str, Any]],
) -> dict[str, Any]:
    return {
        "claim_id": lane_id,
        "expected_evidence_forms": list(diag["expected_forms"]),
        "candidates": [
            {
                "candidate_id": str(row["candidate_id"]),
                "rank": int(row["rank"]),
                "text": str(pool_by_id[str(row["candidate_id"])]["text"]),
                "semantic_score": float(row["semantic_score"]),
            }
            for row in diag["candidates"]
        ],
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--v1-selections", required=True)
    parser.add_argument("--pools", required=True)
    parser.add_argument("--out", required=True)
    args = parser.parse_args()

    path = Path(args.v1_selections)
    pools_path = Path(args.pools)
    source = json.loads(path.read_text(encoding="utf-8"))
    pools = json.loads(pools_path.read_text(encoding="utf-8"))
    pool_by_lane = {
        str(lane["lane_id"]): {
            str(candidate["candidate_id"]): candidate
            for candidate in lane["candidates"]
        }
        for lane in pools["lanes"]
    }
    expected = selected_map(
        source["selections"]["gate_fraction_loose_correct_cap_0.010"]
    )

    rows: list[dict[str, Any]] = []
    exact = True
    permutation = True
    classifier_exact = True

    for lane_id in sorted(source["diagnostics"]):
        diag = source["diagnostics"][lane_id]
        payload = payload_for_lane(lane_id, diag, pool_by_lane[lane_id])

        lane_classifier_exact = True
        for candidate, frozen in zip(
            payload["candidates"], diag["candidates"], strict=True
        ):
            expected_specialties = sorted(
                set(frozen["loose_forms"])
                & {"authoritative_declaration", "event_record", "registry_entry"}
            )
            observed_specialties = sorted(
                candidate_specialty_forms(str(candidate["text"]))
            )
            if observed_specialties != expected_specialties:
                lane_classifier_exact = False
        classifier_exact = classifier_exact and lane_classifier_exact

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
                "classifier_exact": lane_classifier_exact,
                "action": first["action"],
                "expected_specialty_forms": first["expected_specialty_forms"],
            }
        )

    report = {
        "schema": "eb-gate-specialty-selector-rc0-development-equivalence",
        "source_v1_selection_sha256": sha256_file(path),
        "source_pools_sha256": sha256_file(pools_path),
        "target_arm": "gate_fraction_loose_correct_cap_0.010",
        "classifier_exact_all_lanes": classifier_exact,
        "exact_all_lanes": exact,
        "permutation_all_lanes": permutation,
        "lane_count": len(rows),
        "rows": rows,
        "nonclaims": [
            "this is exposed-development implementation equivalence only",
            "actual frozen passage text is used for classifier and selector equivalence",
            "fresh qualification remains required",
        ],
    }
    Path(args.out).write_text(
        json.dumps(report, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    print(json.dumps(report, indent=2, sort_keys=True))
    if not classifier_exact or not exact or not permutation:
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
