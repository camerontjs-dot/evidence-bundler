from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
from typing import Any

SYSTEMS = ("B0_lexical", "R1_generic", "R2_bidirectional_nli")


def canon(value: Any) -> str:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False)


def sha256_text(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def rank(row: dict[str, Any], system: str) -> list[tuple[float, str]]:
    return sorted(
        ((float(c["scores"][system]), c["candidate_id"]) for c in row["candidates"]),
        key=lambda item: (-item[0], item[1]),
    )


def main() -> int:
    p = argparse.ArgumentParser()
    p.add_argument("--raw", required=True)
    p.add_argument("--gold", required=True)
    p.add_argument("--calibration", required=True)
    p.add_argument("--output", required=True)
    a = p.parse_args()
    raw = json.loads(Path(a.raw).read_text(encoding="utf-8"))
    gold = {x["root_id"]: x for x in map(json.loads, Path(a.gold).read_text(encoding="utf-8").splitlines()) if x}
    calibration = json.loads(Path(a.calibration).read_text(encoding="utf-8"))
    rows = {row["root_id"]: row for row in raw["rows"]}

    summaries: dict[str, Any] = {}
    details: list[dict[str, Any]] = []
    for system in SYSTEMS:
        c = calibration["systems"][system]
        if c["status"] != "CALIBRATED":
            summaries[system] = {"status": c["status"]}
            continue
        floor = float(c["chosen"]["floor"])
        margin_threshold = float(c["chosen"]["margin_threshold"])
        safe_selects = unsafe_selects = correct_abstains = false_abstains = 0
        pairwise_total = pairwise_correct = critical_total = critical_correct = 0
        top1_safe = top1_total_selectable = 0
        for root_id, g in gold.items():
            row = rows[root_id]
            ranking = rank(row, system)
            top_score, top_id = ranking[0]
            second_score = ranking[1][0] if len(ranking) > 1 else 0.0
            margin = top_score - second_score
            selected = top_id if top_score >= floor and margin >= margin_threshold else None
            safe = set(g["safe_candidate_ids"])
            unsafe = {candidate["candidate_id"] for candidate in row["candidates"]} - safe
            critical = set(g.get("critical_unsafe_candidate_ids", []))
            if g["expected"] == "SELECT":
                top1_total_selectable += 1
                if top_id in safe:
                    top1_safe += 1
                for safe_id in safe:
                    safe_score = next(score for score, candidate_id in ranking if candidate_id == safe_id)
                    for unsafe_id in unsafe:
                        unsafe_score = next(score for score, candidate_id in ranking if candidate_id == unsafe_id)
                        pairwise_total += 1
                        if safe_score > unsafe_score:
                            pairwise_correct += 1
                        if unsafe_id in critical:
                            critical_total += 1
                            if safe_score > unsafe_score:
                                critical_correct += 1
            if selected is None:
                if g["expected"] == "ABSTAIN":
                    correct_abstains += 1
                else:
                    false_abstains += 1
            elif g["expected"] == "SELECT" and selected in safe:
                safe_selects += 1
            else:
                unsafe_selects += 1
            details.append({
                "system": system,
                "root_id": root_id,
                "family": g["family"],
                "expected": g["expected"],
                "top_id": top_id,
                "top_score": top_score,
                "margin": margin,
                "selected": selected,
                "selected_safe": selected in safe if selected else None,
            })
        summaries[system] = {
            "status": "CALIBRATED",
            "floor": floor,
            "margin_threshold": margin_threshold,
            "safe_selects": safe_selects,
            "unsafe_selects": unsafe_selects,
            "correct_abstains": correct_abstains,
            "false_abstains": false_abstains,
            "top1_safe_preference_rate": top1_safe / top1_total_selectable if top1_total_selectable else None,
            "pairwise_safe_over_unsafe_rate": pairwise_correct / pairwise_total if pairwise_total else None,
            "critical_pairwise_safe_over_unsafe_rate": critical_correct / critical_total if critical_total else None,
            "pairwise_total": pairwise_total,
            "critical_pairwise_total": critical_total,
        }

    r2 = summaries.get("R2_bidirectional_nli", {})
    b0 = summaries.get("B0_lexical", {})
    if r2.get("status") != "CALIBRATED":
        disposition = "FALSIFIED_AS_JUDGE_REPLACEMENT"
        reason = "R2 could not calibrate a zero-unsafe development rule"
    elif r2["unsafe_selects"] > 0:
        disposition = "FALSIFIED_AS_JUDGE_REPLACEMENT"
        reason = "R2 selected at least one unsafe fresh decomposition"
    elif r2["correct_abstains"] < sum(1 for g in gold.values() if g["expected"] == "ABSTAIN"):
        disposition = "FALSIFIED_AS_JUDGE_REPLACEMENT"
        reason = "R2 collapsed at least one intrinsic ambiguity"
    elif (r2["critical_pairwise_safe_over_unsafe_rate"] or 0.0) < 1.0:
        disposition = "FALSIFIED_AS_JUDGE_REPLACEMENT"
        reason = "R2 failed a critical safe-over-unsafe pairwise ordering"
    elif (r2["pairwise_safe_over_unsafe_rate"] or 0.0) < 0.95:
        disposition = "INCONCLUSIVE"
        reason = "R2 pairwise ordering below preregistered 0.95 gate"
    elif r2["safe_selects"] <= b0.get("safe_selects", 0):
        disposition = "INCONCLUSIVE"
        reason = "R2 did not safely select more fresh roots than lexical baseline"
    else:
        disposition = "SUPPORTED_AS_TRIAGE_LANE"
        reason = "R2 passed all preregistered fresh triage gates"

    result = {
        "schema_version": "pc-rerank-evaluation-rc0.1",
        "summaries": summaries,
        "disposition": disposition,
        "reason": reason,
        "details": details,
    }
    text = canon(result) + "\n"
    Path(a.output).write_text(text, encoding="utf-8")
    print(sha256_text(text))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
