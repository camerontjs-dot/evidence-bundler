from __future__ import annotations

import hashlib
import importlib.util
import json
import sys
from pathlib import Path
from typing import Any

from proposers import PROPOSERS

SYSTEMS = {
    "S1_P1": ("P1",),
    "S2_P2": ("P2",),
    "S3_P3": ("P3",),
    "S4_POOL": ("P1", "P2", "P3"),
}


def canon(value: Any) -> str:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False)


def sha(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


def load_authority(path: str):
    spec = importlib.util.spec_from_file_location("frozen_rc1_authority", path)
    if spec is None or spec.loader is None:
        raise RuntimeError("cannot load frozen RC1 authority")
    mod = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = mod
    spec.loader.exec_module(mod)
    return mod


def authority_candidate(candidate: dict) -> dict:
    return {k: v for k, v in candidate.items() if k != "proposal_meta"}


def cluster_key(authority, candidate: dict) -> str:
    frames: list[str] = []
    for child in candidate["children"]:
        parsed = authority.parse_child(child["text"], candidate.get("context_text", "") or "")
        if parsed.status != "ok" or len(parsed.frames) != 1:
            raise RuntimeError("accepted candidate did not reparse to one child frame")
        frames.append(parsed.frames[0].key())
    return sha(canon(sorted(frames)))


def proposals_for(root: dict) -> dict[str, list[dict]]:
    return {name: fn(root) for name, fn in PROPOSERS.items()}


def resolve_system(authority, root: dict, proposer_names: tuple[str, ...]) -> dict:
    all_by_proposer = proposals_for(root)
    candidates: list[dict] = []
    for name in proposer_names:
        candidates.extend(all_by_proposer[name])

    evaluations: list[dict] = []
    clusters: dict[str, list[dict]] = {}
    for candidate in candidates:
        clean = authority_candidate(candidate)
        result = authority.evaluate(clean)
        row = {
            "candidate_id": candidate["case_id"],
            "proposer": candidate["proposal_meta"]["proposer"],
            "variant": candidate["proposal_meta"]["variant"],
            "children": [x["text"] for x in candidate["children"]],
            "authority_disposition": result["disposition"],
            "authority_sha256": result["canonical_sha256"],
        }
        if result["disposition"] == "ACCEPTABLE_WITHIN_PROFILE":
            key = cluster_key(authority, clean)
            row["semantic_cluster"] = key
            clusters.setdefault(key, []).append(row)
        evaluations.append(row)

    if not clusters:
        state = "UNRESOLVED"
        selected = None
    elif len(clusters) == 1:
        state = "RESOLVED"
        selected = sorted(clusters)[0]
    else:
        state = "INDETERMINATE"
        selected = None

    return {
        "root_id": root["root_id"],
        "family": root["family"],
        "state": state,
        "semantic_cluster": selected,
        "surviving_cluster_count": len(clusters),
        "surviving_candidate_ids": sorted(
            row["candidate_id"] for rows in clusters.values() for row in rows
        ),
        "evaluations": evaluations,
    }


def run_root(authority, root: dict) -> dict:
    systems = {
        name: resolve_system(authority, root, proposers)
        for name, proposers in SYSTEMS.items()
    }
    return {"root_id": root["root_id"], "family": root["family"], "systems": systems}


def run_jsonl(authority_path: str, roots_path: str) -> list[dict]:
    authority = load_authority(authority_path)
    roots = [
        json.loads(line)
        for line in Path(roots_path).read_text(encoding="utf-8").splitlines()
        if line.strip()
    ]
    return [run_root(authority, root) for root in roots]


def main() -> None:
    import argparse

    parser = argparse.ArgumentParser()
    parser.add_argument("--authority", required=True)
    parser.add_argument("--roots", required=True)
    parser.add_argument("--output", required=True)
    args = parser.parse_args()
    rows = run_jsonl(args.authority, args.roots)
    text = "".join(canon(row) + "\n" for row in rows)
    Path(args.output).write_text(text, encoding="utf-8")
    print(hashlib.sha256(text.encode("utf-8")).hexdigest())


if __name__ == "__main__":
    main()
