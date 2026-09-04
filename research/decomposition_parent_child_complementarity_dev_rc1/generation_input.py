from __future__ import annotations

import argparse
import hashlib
import json
import re
from pathlib import Path
from typing import Any

CORPUS_TREE_SHA256 = "eee87cff5e86a3d0a3cdaaa762837ca90ae60f62939309c1dc335a19884c78a8"
DEV_DECOMPOSITION_SHA256 = "2120228c81466471214ca8b56a6eba2fa5bc498cd0b0243ff3b8fe24c9da2144"
SELECTED_CLAIMS = (
    "claim-009",
    "claim-013",
    "claim-017",
    "claim-021",
    "claim-037",
    "claim-049",
)
HISTORICAL_VARIANTS = {"D1": "A1", "D2": "A2", "D6": "A4"}


def canonical_json_bytes(value: Any) -> bytes:
    return (
        json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False)
        + "\n"
    ).encode("utf-8")


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def load_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def load_jsonl(path: Path) -> list[dict[str, Any]]:
    return [
        json.loads(line)
        for line in path.read_text(encoding="utf-8").splitlines()
        if line.strip()
    ]


def paragraph_count(text: str) -> int:
    return len([part for part in re.split(r"\n\s*\n", text) if part.strip()])


def build_generation_input(*, benchmark_root: Path, output: Path) -> dict[str, Any]:
    decomposition_path = benchmark_root / "decompositions" / "dev_decompositions.jsonl"
    if sha256_bytes(decomposition_path.read_bytes()) != DEV_DECOMPOSITION_SHA256:
        raise RuntimeError("frozen dev decomposition hash mismatch")

    cases = load_jsonl(benchmark_root / "cases" / "dev_cases.jsonl")
    case_by_key = {
        (str(row["original_claim_id"]), str(row["variant_id"])): row
        for row in cases
    }
    aperture = load_json(benchmark_root / "aperture" / "subsets.json")
    source_ids_by_subset = {
        str(row["subset_id"]): [str(value) for value in row["source_ids"]]
        for row in aperture["subsets"]
    }

    records: list[dict[str, Any]] = []
    for claim_id in SELECTED_CLAIMS:
        a0 = case_by_key[(claim_id, "A0")]
        subset_id = str(a0["accessible_subset_id"])
        sources: list[dict[str, Any]] = []
        for source_id in source_ids_by_subset[subset_id]:
            content_path = benchmark_root / "sources" / source_id / "content.txt"
            content = content_path.read_text(encoding="utf-8")
            sources.append(
                {
                    "source_id": source_id,
                    "media_type": "text/plain; charset=utf-8",
                    "content": content,
                    "content_sha256": "sha256:" + hashlib.sha256(content.encode("utf-8")).hexdigest(),
                    "paragraph_count": paragraph_count(content),
                }
            )

        historical: dict[str, Any] = {}
        for strategy, variant_id in HISTORICAL_VARIANTS.items():
            variant = case_by_key[(claim_id, variant_id)]
            historical[strategy] = {
                "source_variant_id": variant_id,
                "source_decomposition_id": variant["decomposition_id"],
                "children": [
                    {
                        "sequence": int(child["sequence"]),
                        "text": str(child["text"]),
                    }
                    for child in sorted(
                        variant["propositions"], key=lambda row: int(row["sequence"])
                    )
                ],
            }

        records.append(
            {
                "original_claim_id": claim_id,
                "root_proposition": {
                    "proposition_id": claim_id,
                    "text": str(a0["original_claim_text"]),
                    "text_sha256": "sha256:"
                    + hashlib.sha256(str(a0["original_claim_text"]).encode("utf-8")).hexdigest(),
                },
                "accessible_subset_id": subset_id,
                "k": int(a0["runtime_config"]["maximum_passages"]),
                "sources": sources,
                "historical_treatments": historical,
            }
        )

    result = {
        "schema_version": "1.0",
        "experiment": "decomposition-parent-child-complementarity-dev-rc1",
        "corpus_tree_sha256": CORPUS_TREE_SHA256,
        "dev_decomposition_sha256": DEV_DECOMPOSITION_SHA256,
        "split": "dev",
        "selected_claim_ids": list(SELECTED_CLAIMS),
        "cases": records,
    }
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_bytes(canonical_json_bytes(result))
    return {
        "case_count": len(records),
        "output_sha256": sha256_bytes(output.read_bytes()),
        "source_representation_count": sum(len(row["sources"]) for row in records),
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--benchmark-root", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    receipt = build_generation_input(
        benchmark_root=args.benchmark_root,
        output=args.output,
    )
    print(json.dumps(receipt, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
