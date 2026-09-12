from __future__ import annotations

import argparse, hashlib, json
from pathlib import Path

SYSTEMS = ("B0_lexical", "R2_bidirectional_nli", "T1_CAL_LINEAR")
FIXED = {"B0_lexical": (0.9, 0.2), "R2_bidirectional_nli": (0.9, 0.01)}


def canon(x):
    return json.dumps(x, sort_keys=True, separators=(",", ":"), ensure_ascii=False)


def sha(s):
    return hashlib.sha256(s.encode()).hexdigest()


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--raw", required=True)
    p.add_argument("--gold", required=True)
    p.add_argument("--model", required=True)
    p.add_argument("--output", required=True)
    a = p.parse_args()

    raw = json.loads(Path(a.raw).read_text())
    model = json.loads(Path(a.model).read_text())
    gold = {g["root_id"]: g for g in map(json.loads, Path(a.gold).read_text().splitlines()) if g}
    rows = {r["root_id"]: r for r in raw["rows"]}
    summaries = {}
    details = []

    for system in SYSTEMS:
        selection_available = True
        calibration_status = "CALIBRATED"
        if system == "T1_CAL_LINEAR":
            cal = model["calibration"]
            calibration_status = cal["status"]
            if cal["status"] == "CALIBRATED":
                floor = float(cal["chosen"]["floor"])
                margin_threshold = float(cal["chosen"]["margin"])
            else:
                selection_available = False
                floor = margin_threshold = None
        else:
            floor, margin_threshold = FIXED[system]

        safe = unsafe = correct_abstains = false_abstains = 0
        pairwise_total = pairwise_correct = critical_total = critical_correct = 0
        top_safe = selectable = 0

        for root_id, g in gold.items():
            candidates = rows[root_id]["candidates"]
            ranked = sorted(
                [(float(c["scores"][system]), c["candidate_id"]) for c in candidates],
                key=lambda x: (-x[0], x[1]),
            )
            top_score, top_id = ranked[0]
            second_score = ranked[1][0]
            gap = top_score - second_score
            selected = (
                top_id
                if selection_available and top_score >= floor and gap >= margin_threshold
                else None
            )
            allowed = set(g["safe_candidate_ids"])
            all_ids = {c["candidate_id"] for c in candidates}
            bad = all_ids - allowed
            critical = set(g.get("critical_unsafe_candidate_ids", []))

            if g["expected"] == "SELECT":
                selectable += 1
                top_safe += int(top_id in allowed)
                score_map = {cid: score for score, cid in ranked}
                for safe_id in allowed:
                    for unsafe_id in bad:
                        pairwise_total += 1
                        pairwise_correct += int(score_map[safe_id] > score_map[unsafe_id])
                        if unsafe_id in critical:
                            critical_total += 1
                            critical_correct += int(score_map[safe_id] > score_map[unsafe_id])

            if selection_available:
                if selected is None:
                    if g["expected"] == "ABSTAIN":
                        correct_abstains += 1
                    else:
                        false_abstains += 1
                elif g["expected"] == "SELECT" and selected in allowed:
                    safe += 1
                else:
                    unsafe += 1

            details.append(
                {
                    "system": system,
                    "root_id": root_id,
                    "expected": g["expected"],
                    "top_id": top_id,
                    "top_score": top_score,
                    "margin": gap,
                    "selected": selected,
                    "selection_available": selection_available,
                }
            )

        summaries[system] = {
            "status": calibration_status,
            "selection_available": selection_available,
            "floor": floor,
            "margin_threshold": margin_threshold,
            "safe_selects": safe if selection_available else None,
            "unsafe_selects": unsafe if selection_available else None,
            "correct_abstains": correct_abstains if selection_available else None,
            "false_abstains": false_abstains if selection_available else None,
            "top1_safe_preference_rate": top_safe / selectable if selectable else None,
            "pairwise_safe_over_unsafe_rate": pairwise_correct / pairwise_total if pairwise_total else None,
            "critical_pairwise_safe_over_unsafe_rate": critical_correct / critical_total if critical_total else None,
            "pairwise_total": pairwise_total,
            "critical_pairwise_total": critical_total,
        }

    out = {
        "schema_version": "pc-cal-linear-evaluation-rc0.2",
        "summaries": summaries,
        "details": details,
    }
    text = canon(out) + "\n"
    Path(a.output).write_text(text)
    print(sha(text))


if __name__ == "__main__":
    main()
