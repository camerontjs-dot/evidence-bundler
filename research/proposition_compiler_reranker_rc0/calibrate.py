from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
from typing import Any

SYSTEMS = ("B0_lexical", "R1_generic", "R2_bidirectional_nli")
FLOORS = (0.0, 0.25, 0.4, 0.5, 0.6, 0.7, 0.8, 0.9)
MARGINS = (0.0, 0.01, 0.025, 0.05, 0.1, 0.15, 0.2)


def canon(value: Any) -> str:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False)


def sha256_text(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def index_raw(raw: dict[str, Any]) -> dict[str, dict[str, Any]]:
    return {row["root_id"]: row for row in raw["rows"]}


def decision(row: dict[str, Any], system: str, floor: float, margin: float) -> dict[str, Any]:
    ranked = sorted(
        ((float(c["scores"][system]), c["candidate_id"]) for c in row["candidates"]),
        key=lambda item: (-item[0], item[1]),
    )
    top_score, top_id = ranked[0]
    second = ranked[1][0] if len(ranked) > 1 else 0.0
    gap = top_score - second
    selected = top_id if top_score >= floor and gap >= margin else None
    return {"selected": selected, "top_score": top_score, "margin": gap, "ranking": ranked}


def metrics(raw: dict[str, Any], gold_rows: list[dict[str, Any]], system: str, floor: float, margin: float) -> dict[str, Any]:
    by_root = index_raw(raw)
    safe_selects = 0
    unsafe_selects = 0
    correct_abstains = 0
    false_abstains = 0
    critical_unsafe_top1 = 0
    details = []
    for gold in gold_rows:
        d = decision(by_root[gold["root_id"]], system, floor, margin)
        safe = set(gold["safe_candidate_ids"])
        critical = set(gold.get("critical_unsafe_candidate_ids", []))
        expected = gold["expected"]
        selected = d["selected"]
        top_id = d["ranking"][0][1]
        if top_id in critical:
            critical_unsafe_top1 += 1
        if selected is None:
            if expected == "ABSTAIN":
                correct_abstains += 1
            else:
                false_abstains += 1
        elif expected == "SELECT" and selected in safe:
            safe_selects += 1
        else:
            unsafe_selects += 1
        details.append(
            {
                "root_id": gold["root_id"],
                "expected": expected,
                "selected": selected,
                "top_score": d["top_score"],
                "margin": d["margin"],
                "top_id": top_id,
            }
        )
    return {
        "system": system,
        "floor": floor,
        "margin_threshold": margin,
        "safe_selects": safe_selects,
        "unsafe_selects": unsafe_selects,
        "correct_abstains": correct_abstains,
        "false_abstains": false_abstains,
        "critical_unsafe_top1": critical_unsafe_top1,
        "details": details,
    }


def choose(raw: dict[str, Any], gold_rows: list[dict[str, Any]], system: str) -> dict[str, Any]:
    candidates = [metrics(raw, gold_rows, system, floor, margin) for floor in FLOORS for margin in MARGINS]
    feasible = [m for m in candidates if m["unsafe_selects"] == 0]
    if not feasible:
        return {
            "system": system,
            "status": "NO_ZERO_UNSAFE_CALIBRATION",
            "chosen": None,
            "best_observed": sorted(
                candidates,
                key=lambda m: (m["unsafe_selects"], -m["safe_selects"], -m["correct_abstains"], -m["floor"], -m["margin_threshold"]),
            )[0],
        }
    chosen = sorted(
        feasible,
        key=lambda m: (-m["safe_selects"], -m["correct_abstains"], -m["floor"], -m["margin_threshold"]),
    )[0]
    return {"system": system, "status": "CALIBRATED", "chosen": chosen}


def main() -> int:
    p = argparse.ArgumentParser()
    p.add_argument("--raw", required=True)
    p.add_argument("--gold", required=True)
    p.add_argument("--output", required=True)
    a = p.parse_args()
    raw = json.loads(Path(a.raw).read_text(encoding="utf-8"))
    gold_rows = [json.loads(x) for x in Path(a.gold).read_text(encoding="utf-8").splitlines() if x.strip()]
    result = {
        "schema_version": "pc-rerank-calibration-rc0.1",
        "grid": {"floors": FLOORS, "margins": MARGINS},
        "systems": {system: choose(raw, gold_rows, system) for system in SYSTEMS},
    }
    text = canon(result) + "\n"
    Path(a.output).write_text(text, encoding="utf-8")
    print(sha256_text(text))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
