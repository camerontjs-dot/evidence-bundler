from __future__ import annotations

import hashlib
import json
from copy import deepcopy
from typing import Any


def canonicalize_gold(gold: dict[str, Any]) -> dict[str, Any]:
    obj = deepcopy(gold)
    queries = obj.get("queries", [])
    for query in queries:
        query["judgments"] = sorted(query.get("judgments", []), key=lambda x: x["passage_id"])
        for group in query.get("groups", []):
            group["required_passage_ids"] = sorted(group["required_passage_ids"])
        query["groups"] = sorted(query.get("groups", []), key=lambda x: x["group_id"])
    obj["queries"] = sorted(queries, key=lambda x: x["query_id"])
    return obj


def canonical_bytes(gold: dict[str, Any]) -> bytes:
    normalized = canonicalize_gold(gold)
    text = json.dumps(normalized, sort_keys=True, separators=(",", ":"), ensure_ascii=False)
    return text.encode("utf-8")


def commitment_sha256(gold: dict[str, Any]) -> str:
    return hashlib.sha256(canonical_bytes(gold)).hexdigest()
