from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
from typing import Any

SCHEMA_TOKEN = "contract-a-wire-candidate-rc2"
STRATEGY_ORDER = ("D1", "D2", "D3", "D4", "D5a", "D5b", "D6")
MODEL_STRATEGIES = {"D3", "D4", "D5a", "D5b"}


def canonical_json_bytes(value: Any) -> bytes:
    return json.dumps(
        value,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=False,
        allow_nan=False,
    ).encode("utf-8")


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def text_hash(text: str) -> str:
    return "sha256:" + hashlib.sha256(text.encode("utf-8")).hexdigest()


def compute_handoff_hash(value: dict[str, Any]) -> str:
    payload = dict(value)
    payload.pop("handoff_sha256", None)
    return "sha256:" + hashlib.sha256(canonical_json_bytes(payload)).hexdigest()


def _model_rows(*outputs: dict[str, Any]) -> dict[tuple[str, str], dict[str, Any]]:
    rows: dict[tuple[str, str], dict[str, Any]] = {}
    for output in outputs:
        for row in output["rows"]:
            key = (str(row["original_claim_id"]), str(row["strategy"]))
            if key in rows:
                raise RuntimeError(f"duplicate model-generation row: {key}")
            rows[key] = row
    return rows


def _children_for_strategy(
    *,
    case: dict[str, Any],
    strategy: str,
    model_rows: dict[tuple[str, str], dict[str, Any]],
) -> tuple[str, list[str], str | None]:
    if strategy in case["historical_treatments"]:
        rows = case["historical_treatments"][strategy]["children"]
        return "declared", [str(row["text"]) for row in rows], None
    row = model_rows[(str(case["original_claim_id"]), strategy)]
    if row["status"] != "declared":
        return "failed", [], str(row.get("failure_reason") or "MODEL_ABSTENTION")
    return "declared", [str(value) for value in row["children"]], None


def _contract_a_object(
    *,
    case: dict[str, Any],
    strategy: str,
    state: str,
    children: list[str],
) -> dict[str, Any]:
    claim_id = str(case["original_claim_id"])
    decomposition: dict[str, Any]
    if state == "declared":
        decomposition = {
            "state": "declared",
            "decomposition_id": f"research-{claim_id}-{strategy.lower()}-dev-rc1",
            "operator": "all_of",
            "children": [
                {
                    "proposition_id": f"{claim_id}:{strategy}:child:{index}",
                    "text": text,
                    "text_sha256": text_hash(text),
                    "sequence": index,
                }
                for index, text in enumerate(children, start=1)
            ],
        }
    else:
        decomposition = {"state": "failed"}

    obj: dict[str, Any] = {
        "schema": SCHEMA_TOKEN,
        "handoff_id": f"eb-research-{claim_id}-{strategy.lower()}-dev-rc1",
        "producer": {
            "producer_id": "evidence-bundler-research-fixture-builder",
            "producer_version": "decomposition-parent-child-dev-rc1",
        },
        "work": {"work_id": f"eb-parent-child-{claim_id}-dev-rc1"},
        "root_proposition": {
            "proposition_id": case["root_proposition"]["proposition_id"],
            "text": case["root_proposition"]["text"],
            "text_sha256": case["root_proposition"]["text_sha256"],
        },
        "decomposition": decomposition,
        "sources": [
            {
                "source_id": source["source_id"],
                "media_type": source["media_type"],
                "content": source["content"],
                "content_sha256": source["content_sha256"],
            }
            for source in case["sources"]
        ],
    }
    obj["handoff_sha256"] = compute_handoff_hash(obj)
    return obj


def build(
    *,
    generation_input: Path,
    flan_output: Path,
    smol_output: Path,
    expected_generation_input_sha256: str,
    expected_flan_sha256: str,
    expected_smol_sha256: str,
    output_dir: Path,
) -> dict[str, Any]:
    for path, expected in (
        (generation_input, expected_generation_input_sha256),
        (flan_output, expected_flan_sha256),
        (smol_output, expected_smol_sha256),
    ):
        actual = sha256_bytes(path.read_bytes())
        if actual != expected:
            raise RuntimeError(f"frozen input digest mismatch: {path}: {actual} != {expected}")

    generation = json.loads(generation_input.read_text(encoding="utf-8"))
    flan = json.loads(flan_output.read_text(encoding="utf-8"))
    smol = json.loads(smol_output.read_text(encoding="utf-8"))
    model_rows = _model_rows(flan, smol)

    output_dir.mkdir(parents=True, exist_ok=True)
    manifest_rows: list[dict[str, Any]] = []
    source_array_hashes_by_claim: dict[str, set[str]] = {}
    root_hashes_by_claim: dict[str, set[str]] = {}
    for case in generation["cases"]:
        claim_id = str(case["original_claim_id"])
        source_array_hashes_by_claim[claim_id] = set()
        root_hashes_by_claim[claim_id] = set()
        for strategy in STRATEGY_ORDER:
            state, children, failure_reason = _children_for_strategy(
                case=case,
                strategy=strategy,
                model_rows=model_rows,
            )
            obj = _contract_a_object(
                case=case,
                strategy=strategy,
                state=state,
                children=children,
            )
            path = output_dir / f"{claim_id}-{strategy}.json"
            path.write_text(
                json.dumps(obj, indent=2, ensure_ascii=False, sort_keys=True) + "\n",
                encoding="utf-8",
            )
            source_array_hash = sha256_bytes(canonical_json_bytes(obj["sources"]))
            root_hash = sha256_bytes(canonical_json_bytes(obj["root_proposition"]))
            source_array_hashes_by_claim[claim_id].add(source_array_hash)
            root_hashes_by_claim[claim_id].add(root_hash)
            manifest_rows.append(
                {
                    "original_claim_id": claim_id,
                    "strategy": strategy,
                    "path": path.name,
                    "contract_a_file_sha256": sha256_bytes(path.read_bytes()),
                    "handoff_sha256": obj["handoff_sha256"],
                    "root_proposition_id": obj["root_proposition"]["proposition_id"],
                    "root_text_sha256": obj["root_proposition"]["text_sha256"],
                    "decomposition_state": obj["decomposition"]["state"],
                    "decomposition_id": obj["decomposition"].get("decomposition_id"),
                    "child_count": len(obj["decomposition"].get("children", [])),
                    "source_array_sha256": source_array_hash,
                    "failure_reason": failure_reason,
                }
            )

    invariant_failures = [
        claim_id
        for claim_id in source_array_hashes_by_claim
        if len(source_array_hashes_by_claim[claim_id]) != 1
        or len(root_hashes_by_claim[claim_id]) != 1
    ]
    if invariant_failures:
        raise RuntimeError(
            f"root/source byte invariants failed across treatments: {invariant_failures}"
        )

    manifest = {
        "schema_version": "1.0",
        "experiment": generation["experiment"],
        "generation_input_sha256": expected_generation_input_sha256,
        "flan_output_sha256": expected_flan_sha256,
        "smol_output_sha256": expected_smol_sha256,
        "strategy_order": list(STRATEGY_ORDER),
        "same_root_and_source_bytes_per_case": True,
        "records": manifest_rows,
    }
    manifest_path = output_dir / "MANIFEST.json"
    manifest_path.write_bytes(canonical_json_bytes(manifest) + b"\n")
    return {
        "fixture_count": len(manifest_rows),
        "declared_count": sum(
            row["decomposition_state"] == "declared" for row in manifest_rows
        ),
        "failed_count": sum(
            row["decomposition_state"] == "failed" for row in manifest_rows
        ),
        "manifest_sha256": sha256_bytes(manifest_path.read_bytes()),
        "same_root_and_source_bytes_per_case": True,
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--generation-input", type=Path, required=True)
    parser.add_argument("--flan-output", type=Path, required=True)
    parser.add_argument("--smol-output", type=Path, required=True)
    parser.add_argument("--expected-generation-input-sha256", required=True)
    parser.add_argument("--expected-flan-sha256", required=True)
    parser.add_argument("--expected-smol-sha256", required=True)
    parser.add_argument("--output-dir", type=Path, required=True)
    args = parser.parse_args()
    receipt = build(
        generation_input=args.generation_input,
        flan_output=args.flan_output,
        smol_output=args.smol_output,
        expected_generation_input_sha256=args.expected_generation_input_sha256,
        expected_flan_sha256=args.expected_flan_sha256,
        expected_smol_sha256=args.expected_smol_sha256,
        output_dir=args.output_dir,
    )
    print(json.dumps(receipt, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
