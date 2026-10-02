"""RC2 local artifact gates. No model, retrieval, source reader or semantic author."""

from __future__ import annotations

import argparse
import hashlib
import json
import re
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

HERE = Path(__file__).parent
STAGES = ("INVENTORY", "SAMPLE", "AUTHORING_AUTHORITY", "DECLARATIONS", "SUBJECTS")
HASH = re.compile(r"sha256:[0-9a-f]{64}")


class BoundaryError(ValueError):
    pass


def need(ok: bool, reason: str) -> None:
    if not ok:
        raise BoundaryError(reason)


def canonical(value: Any) -> bytes:
    return (
        json.dumps(value, sort_keys=True, ensure_ascii=False, separators=(",", ":")) + chr(10)
    ).encode()


def digest(data: bytes) -> str:
    return "sha256:" + hashlib.sha256(data).hexdigest()


def source_set_digest(hashes: list[str]) -> str:
    # The nominated inventory binds compact JSON with no trailing newline.
    return digest(
        json.dumps(hashes, sort_keys=True, ensure_ascii=False, separators=(",", ":")).encode()
    )


def exact(value: Any, keys: set[str], label: str) -> None:
    need(isinstance(value, dict) and set(value) == keys, "schema:" + label)


def sha(value: Any) -> None:
    need(isinstance(value, str) and bool(HASH.fullmatch(value)), "invalid SHA-256")
    need(value != "sha256:" + "0" * 64, "unbound zero identity")


def stamp(value: str) -> datetime:
    try:
        time = datetime.fromisoformat(value)
        need(time.tzinfo is not None, "timestamp lacks timezone")
        return time
    except (TypeError, ValueError) as error:
        raise BoundaryError("invalid timestamp") from error


def load(path: Path) -> Any:
    def pairs(items: list[tuple[str, Any]]) -> dict:
        out: dict = {}
        for key, value in items:
            need(key not in out, "duplicate JSON key")
            out[key] = value
        return out

    try:
        return json.loads(path.read_bytes(), object_pairs_hook=pairs)
    except (OSError, ValueError) as error:
        raise BoundaryError("input unreadable or invalid JSON") from error


def inventory_plan(data: dict, forbidden: set[str]) -> dict:
    exact(data, {"schema", "provenance", "packets"}, "inventory")
    need(data["schema"] == "eb-rc2-root-inventory-v1", "inventory schema identity")
    provenance = data["provenance"]
    exact(
        provenance,
        {
            "pool_raw_sha256",
            "custody_manifest_raw_sha256",
            "seal_raw_sha256",
            "pool_construction_raw_sha256",
            "source_manifest_raw_sha256",
            "pre_existing_sealed_at",
            "fidelity_basis",
        },
        "provenance",
    )
    for name in provenance:
        if name.endswith("sha256"):
            sha(provenance[name])
    sealed = stamp(provenance["pre_existing_sealed_at"])
    need(sealed < stamp("2026-10-02T13:46:23.711117+00:00"), "inventory not pre-existing")
    need(len(data["packets"]) == 3, "three source packets required")
    all_roots: set[str] = set()
    all_text: set[str] = set()
    source_hashes: set[str] = set()
    packets: list[dict] = []
    for packet in sorted(data["packets"], key=lambda p: p["source_set_sha256"]):
        exact(
            packet,
            {"packet_id", "source_set_sha256", "source_hashes", "sources", "roots"},
            "packet",
        )
        hashes = packet["source_hashes"]
        need(hashes == sorted(set(hashes)) and bool(hashes), "source identities unique/sorted")
        for value in hashes:
            sha(value)
        need(not (set(hashes) & (source_hashes | forbidden)), "source overlap/exclusion")
        source_hashes.update(hashes)
        need(packet["source_set_sha256"] == source_set_digest(hashes), "source set identity")
        need(sorted(s["raw_sha256"] for s in packet["sources"]) == hashes, "source locators")
        for source in packet["sources"]:
            exact(
                source,
                {
                    "source_id",
                    "raw_sha256",
                    "locator",
                    "origin_locator",
                    "media_type",
                    "sealed_bytes",
                },
                "source locator",
            )
            need(bool(source["locator"]) and bool(source["origin_locator"]), "missing locator")
            need(type(source["sealed_bytes"]) is int and source["sealed_bytes"] > 0, "source size")
        roots = sorted(
            packet["roots"], key=lambda r: (r["declared_at"], r["text_sha256"], r["root_id"])
        )
        for root in roots:
            exact(
                root,
                {
                    "root_id",
                    "text",
                    "text_sha256",
                    "declared_at",
                    "origin_span",
                    "origin_source_sha256",
                },
                "root",
            )
            need(isinstance(root["text"], str) and bool(root["text"].strip()), "empty root")
            need(root["text_sha256"] == digest(root["text"].encode()), "root byte identity")
            need(root["text_sha256"] not in (all_text | forbidden), "root duplicate/exclusion")
            need(root["root_id"] not in all_roots, "duplicate root ID")
            all_roots.add(root["root_id"])
            all_text.add(root["text_sha256"])
            need(stamp(root["declared_at"]) <= sealed, "root postdates prior seal")
            need(root["origin_source_sha256"] in hashes, "root source binding")
            span = root["origin_span"]
            need(
                isinstance(span, list)
                and len(span) == 2
                and all(type(x) is int for x in span)
                and 0 <= span[0] < span[1],
                "root origin span",
            )
        packets.append(
            {
                "packet_id": packet["packet_id"],
                "ordered_roots": [r["root_id"] for r in roots],
                "initial": [r["root_id"] for r in roots[:4]],
                "reserves": [r["root_id"] for r in roots[4:]],
            }
        )
    need(
        sorted(len(p["ordered_roots"]) for p in packets) == [8, 50, 50],
        "frozen complete 108-root inventory",
    )
    need(len({p["packet_id"] for p in packets}) == 3, "duplicate packet ID")
    return {"schema": "eb-rc2-sample-v1", "packets": packets}


def span_matches(text: str, span: Any, anchor: str) -> None:
    need(
        isinstance(span, list) and len(span) == 2 and all(type(x) is int for x in span),
        "span coordinates",
    )
    raw = text.encode()
    need(0 <= span[0] < span[1] <= len(raw), "span bounds")
    need(raw[span[0] : span[1]] == anchor.encode(), "exact UTF-8 subject span")


def check_primary(root: dict, proposal: dict) -> bool:
    exact(proposal, {"root_alias", "status", "reason", "children"}, "primary")
    need(proposal["root_alias"] == alias(root), "primary alias binding")
    if proposal["status"] == "ineligible":
        need(proposal["children"] == [], "ineligible carries children")
        need(
            proposal["reason"] in load(HERE / "AUTHORING-RUBRIC.json")["ineligible_reasons"],
            "ineligibility reason",
        )
        return False
    need(
        proposal["status"] == "declared" and proposal["reason"] == "two_required_conserved",
        "primary disposition",
    )
    children = proposal["children"]
    need(isinstance(children, list) and len(children) == 2, "exact two children")
    texts: set[str] = set()
    for child in children:
        exact(child, {"text", "subject"}, "child")
        need(isinstance(child["text"], str) and bool(child["text"].strip()), "child text")
        need(child["text"] not in texts, "duplicate children")
        texts.add(child["text"])
        sub = child["subject"]
        exact(sub, {"anchor", "entity_class", "root_span", "child_span", "origin"}, "subject")
        need(
            isinstance(sub["anchor"], str)
            and bool(sub["anchor"].strip())
            and isinstance(sub["entity_class"], str)
            and bool(sub["entity_class"].strip()),
            "subject declaration",
        )
        span_matches(root["text"], sub["root_span"], sub["anchor"])
        if sub["origin"] == "explicit":
            span_matches(child["text"], sub["child_span"], sub["anchor"])
        else:
            need(
                sub["origin"] == "inherited" and sub["child_span"] is None,
                "inherited parent anchor",
            )
    return True


def check_checker(proposal: dict, output: dict) -> bool:
    exact(output, {"root_alias", "proposal_sha256", "decision", "reason", "checks"}, "checker")
    need(
        output["root_alias"] == proposal["root_alias"]
        and output["proposal_sha256"] == digest(canonical(proposal)),
        "exact proposal binding",
    )
    keys = set(load(HERE / "AUTHORING-RUBRIC.json")["checks"])
    exact(output["checks"], keys, "checker checks")
    need(all(type(v) is bool for v in output["checks"].values()), "exact Boolean checks")
    need(output["decision"] in {"accept", "reject"}, "checker decision")
    if output["decision"] == "accept":
        need(
            output["reason"] == "exact_agreement" and all(output["checks"].values()),
            "checker acceptance not exact",
        )
        return True
    need(
        output["reason"]
        in set(load(HERE / "AUTHORING-RUBRIC.json")["checker_reasons"]) - {"exact_agreement"},
        "checker rejection reason",
    )
    return False


def calibrate(review: dict) -> dict:
    exact(review, {"profile_sha256", "session_id", "rows"}, "control review")
    sha(review["profile_sha256"])
    need(isinstance(review["session_id"], str) and bool(review["session_id"]), "control session")
    gold = load(HERE / "AUTHORING-CONTROLS.json")["cases"]
    rows = review["rows"]
    need(isinstance(rows, list) and len(rows) == len(gold), "control row count")
    observed: dict[str, str] = {}
    for row in rows:
        exact(row, {"alias", "decision"}, "control row")
        need(row["alias"] not in observed, "duplicate control alias")
        need(row["decision"] in {"accept", "reject"}, "control decision")
        observed[row["alias"]] = row["decision"]
    expected = {g["alias"]: g["expected_decision"] for g in gold}
    need(set(observed) == set(expected), "control aliases")
    correct = sum(observed[a] == expected[a] for a in expected)
    return {
        "correct": correct,
        "total": len(gold),
        "qualified_gate": correct == len(gold),
        "semantic_role_authority": "NOT_ESTABLISHED_BY_THIS_FUNCTION",
    }


def alias(root: dict) -> str:
    return "root-" + digest(canonical([root["root_id"], root["text_sha256"]]))[7:27]


def capsule(root: dict, role: str, proposal: dict | None = None) -> dict:
    need(role in {"primary", "checker"}, "capsule role")
    need((role == "checker") == (proposal is not None), "capsule proposal aperture")
    wire = load(HERE / "SCHEMAS.json")
    fields = ("primary", "child", "subject") if role == "primary" else ("checker",)
    minimal = {name: wire["closed_fields"][name] for name in fields}
    minimal["constraints"] = wire["constraints"]
    return {
        "schema": "eb-rc2-capsule-v1",
        "role": role,
        "root_alias": alias(root),
        "root_text": root["text"],
        "rubric": load(HERE / "AUTHORING-RUBRIC.json"),
        "output_schema": minimal,
        "proposal": proposal,
    }


def control_capsule() -> dict:
    controls = load(HERE / "AUTHORING-CONTROLS.json")
    return {
        "schema": "eb-rc2-authoring-calibration-packet-v1",
        "rubric": load(HERE / "AUTHORING-RUBRIC.json"),
        "rows": [
            {key: case[key] for key in ("alias", "root_text", "proposed_children")}
            for case in controls["cases"]
        ],
        "output_schema": {
            "fields": ["profile_sha256", "session_id", "rows"],
            "row_fields": ["alias", "decision"],
            "decisions": ["accept", "reject"],
        },
    }


def authority_check(value: dict) -> None:
    exact(
        value,
        {
            "schema",
            "adapter_sha256",
            "adapter_qualification_sha256",
            "destination",
            "destination_authorization_sha256",
            "independent_custody_authority_sha256",
            "profiles",
            "controls",
        },
        "authoring authority",
    )
    need(value["schema"] == "eb-rc2-authoring-authority-v1", "authority schema")
    for key in (
        "adapter_sha256",
        "adapter_qualification_sha256",
        "destination_authorization_sha256",
        "independent_custody_authority_sha256",
    ):
        sha(value[key])
    need(bool(value["destination"]), "destination unbound")
    exact(value["profiles"], {"primary", "checker"}, "profiles")
    for profile in value["profiles"].values():
        sha(profile)
    need(len(value["controls"]) == 2, "two role calibrations")
    need(len({c["session_id"] for c in value["controls"]}) == 2, "fresh control sessions")
    need(
        [c["profile_sha256"] for c in value["controls"]]
        == [value["profiles"]["primary"], value["profiles"]["checker"]],
        "control profiles",
    )
    need(all(calibrate(c)["qualified_gate"] for c in value["controls"]), "authoring calibration")


def check_trace(
    trace: dict, request: dict, output: dict, role: str, authority: dict, after: str, seen: set[str]
) -> None:
    exact(trace, set(load(HERE / "SCHEMAS.json")["closed_fields"]["launch_trace"]), "trace")
    need(
        trace["adapter_sha256"] == authority["adapter_sha256"]
        and trace["profile_sha256"] == authority["profiles"][role]
        and trace["destination"] == authority["destination"],
        "launch authority identity",
    )
    need(trace["request"] == request and trace["output"] == output, "exact information aperture")
    sha(trace["no_history_receipt_sha256"])
    session = trace["session_id"]
    need(
        isinstance(session, str) and bool(session) and session not in seen,
        "reused or missing session",
    )
    seen.add(session)
    need(
        stamp(after) <= stamp(trace["started_at"]) <= stamp(trace["completed_at"]),
        "launch chronology",
    )


def declarations(inventory: dict, plan: dict, authority: dict, value: dict, after: str) -> dict:
    exact(value, {"schema", "attempts"}, "declarations")
    need(value["schema"] == "eb-rc2-declaration-attempts-v1", "declaration schema identity")
    authority_check(authority)
    roots = {r["root_id"]: r for p in inventory["packets"] for r in p["roots"]}
    state = {p["packet_id"]: {"cursor": 0, "accepted": []} for p in plan["packets"]}
    plans = {p["packet_id"]: p for p in plan["packets"]}
    seen = {c["session_id"] for c in authority["controls"]}
    exclusions = []
    for attempt in value["attempts"]:
        exact(attempt, {"packet_id", "root_id", "primary", "checker"}, "attempt")
        pid = attempt["packet_id"]
        need(pid in state, "unknown packet")
        s = state[pid]
        order = plans[pid]["ordered_roots"]
        need(len(s["accepted"]) < 4 and s["cursor"] < len(order), "attempt budget exhausted")
        need(attempt["root_id"] == order[s["cursor"]], "out-of-order root or skipped reserve")
        s["cursor"] += 1
        root = roots[attempt["root_id"]]
        exact(attempt["primary"], {"output", "trace"}, "primary attempt")
        proposal = attempt["primary"]["output"]
        check_trace(
            attempt["primary"]["trace"],
            capsule(root, "primary"),
            proposal,
            "primary",
            authority,
            after,
            seen,
        )
        declared = check_primary(root, proposal)
        accepted, reason = False, proposal["reason"]
        if declared:
            exact(attempt["checker"], {"output", "trace"}, "checker attempt")
            output = attempt["checker"]["output"]
            check_trace(
                attempt["checker"]["trace"],
                capsule(root, "checker", proposal),
                output,
                "checker",
                authority,
                attempt["primary"]["trace"]["completed_at"],
                seen,
            )
            accepted = check_checker(proposal, output)
            reason = output["reason"]
        else:
            need(attempt["checker"] is None, "checker after primary ineligibility")
        if accepted:
            s["accepted"].append({"root_id": root["root_id"], "proposal": proposal})
        else:
            exclusions.append({"packet_id": pid, "root_id": root["root_id"], "reason": reason})
    need(
        all(len(s["accepted"]) == 4 for s in state.values()),
        "BLOCKED_POPULATION_AUTHORING_INSUFFICIENT",
    )
    return {
        "schema": "eb-rc2-accepted-declarations-v1",
        "packets": [
            {"packet_id": pid, "accepted": s["accepted"], "consumed": s["cursor"]}
            for pid, s in sorted(state.items())
        ],
        "exclusions": exclusions,
    }


def subjects(declared: dict) -> dict:
    rows = []
    for packet in declared["packets"]:
        local = []
        for item in packet["accepted"]:
            for ordinal, child in enumerate(item["proposal"]["children"], 1):
                local.append(
                    {
                        "child_id": item["root_id"] + ":" + str(ordinal),
                        "root_id": item["root_id"],
                        "packet_id": packet["packet_id"],
                        **child["subject"],
                    }
                )
        need(
            len(local) == 8 and any(s["origin"] == "inherited" for s in local),
            "BLOCKED_SUBJECT_CONTROL_POPULATION: inherited child absent",
        )
        for row in local:
            donors = sorted(
                (s for s in local if s["entity_class"] == row["entity_class"]),
                key=lambda s: (s["anchor"], s["child_id"]),
            )
            anchors = sorted({s["anchor"] for s in donors})
            need(len(anchors) >= 2, "BLOCKED_SUBJECT_CONTROL_POPULATION: plausible rotation")
            next_anchor = anchors[(anchors.index(row["anchor"]) + 1) % len(anchors)]
            row["wrong_subject_child_id"] = next(
                s["child_id"] for s in donors if s["anchor"] == next_anchor
            )
            row["wrong_child_id"] = row["root_id"] + (
                ":2" if row["child_id"].endswith(":1") else ":1"
            )
        rows.extend(local)
    need(len(rows) == 24, "24 subjects required")
    return {
        "schema": "eb-rc2-subject-bindings-v1",
        "rows": rows,
        "mapping_sha256": digest(canonical(rows)),
    }


def chain(root: Path, count: int) -> list[dict]:
    need(not root.is_symlink(), "symlink freeze root")
    need(root.is_dir(), "freeze directory absent")
    need({p.name for p in root.iterdir()} == set(STAGES[:count]), "nonfresh/partial stage tree")
    receipts: list[dict] = []
    previous = None
    for stage in STAGES[:count]:
        folder = root / stage
        need(not folder.is_symlink(), "symlink stage")
        receipt_path = folder / "RECEIPT.PUBLIC.json"
        receipt = load(receipt_path)
        exact(
            receipt,
            {"schema", "stage", "created_at", "previous_receipt_raw_sha256", "files", "counts"},
            "receipt",
        )
        need(
            receipt["stage"] == stage and receipt["previous_receipt_raw_sha256"] == previous,
            "stage chain binding",
        )
        need(
            {p.name for p in folder.iterdir()} == set(receipt["files"]) | {receipt_path.name},
            "unbound stage files",
        )
        for name, expected in receipt["files"].items():
            need(Path(name).name == name and not (folder / name).is_symlink(), "stage path")
            need(digest((folder / name).read_bytes()) == expected, "stage raw-byte drift")
        if receipts:
            need(
                stamp(receipt["created_at"]) >= stamp(receipts[-1]["created_at"]),
                "receipt chronology",
            )
        receipts.append(receipt)
        previous = digest(receipt_path.read_bytes())
    return receipts


def append(root: Path, stage: str, files: dict[str, bytes], counts: dict) -> dict:
    index = STAGES.index(stage)
    if index == 0:
        need(not root.exists(), "fresh private directory required")
        root.mkdir(mode=0o700, parents=False)
        previous = None
    else:
        chain(root, index)
        previous = digest((root / STAGES[index - 1] / "RECEIPT.PUBLIC.json").read_bytes())
    folder = root / stage
    folder.mkdir(mode=0o700)
    for name, data in files.items():
        need(Path(name).name == name, "snapshot filename")
        path = folder / name
        with path.open("xb") as stream:
            stream.write(data)
        path.chmod(0o400)
    receipt = {
        "schema": "eb-rc2-stage-receipt-v1",
        "stage": stage,
        "created_at": datetime.now(UTC).isoformat(),
        "previous_receipt_raw_sha256": previous,
        "files": {name: digest(data) for name, data in files.items()},
        "counts": counts,
    }
    path = folder / "RECEIPT.PUBLIC.json"
    with path.open("xb") as stream:
        stream.write(canonical(receipt))
    path.chmod(0o400)
    return receipt


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("stage", choices=[s.lower() for s in STAGES] + ["corpus", "execution"])
    parser.add_argument("--freeze-dir", required=True, type=Path)
    parser.add_argument("--input", type=Path)
    args = parser.parse_args()
    try:
        stage = args.stage.upper()
        need(stage in STAGES, "BLOCKED: independent corpus/execution adapter unbound")
        need(
            stage in {"INVENTORY", "SAMPLE"},
            "BLOCKED: source-blind authoring adapter and authority are unqualified; "
            "use a separately frozen qualified adapter, not this setup CLI",
        )
        need(args.input is not None, "input required")
        raw, value = args.input.read_bytes(), load(args.input)
        if stage == "INVENTORY":
            expected = load(HERE / "POPULATION-DESIGN.PUBLIC.json")
            need(digest(raw) == expected["inventory_raw_sha256"], "exact nominated inventory")
            plan = inventory_plan(value, set())
            files = {"INPUT.PRIVATE.json": raw, "PLAN.PRIVATE.json": canonical(plan)}
            counts = {"packets": 3, "roots": 108, "initial": 12, "reserves": 96}
        else:
            prior = chain(args.freeze_dir, STAGES.index(stage))
            inventory = load(args.freeze_dir / "INVENTORY" / "INPUT.PRIVATE.json")
            plan = load(args.freeze_dir / "INVENTORY" / "PLAN.PRIVATE.json")
            if stage == "SAMPLE":
                need(value == plan, "exact frozen sample/reserves required")
                result, counts = plan, {"initial_roots": 12, "reserves": 96}
            elif stage == "AUTHORING_AUTHORITY":
                authority_check(value)
                result, counts = value, {"profiles": 2, "control_correct_each": 12}
            elif stage == "DECLARATIONS":
                authority = load(args.freeze_dir / "AUTHORING_AUTHORITY" / "BOUND.PRIVATE.json")
                result = declarations(inventory, plan, authority, value, prior[-1]["created_at"])
                counts = {
                    "packets": 3,
                    "parents": 12,
                    "children": 24,
                    "excluded": len(result["exclusions"]),
                    "attempts": len(value["attempts"]),
                }
            else:
                declared = load(args.freeze_dir / "DECLARATIONS" / "BOUND.PRIVATE.json")
                result = subjects(declared)
                need(value == result, "exact derived subject mapping required")
                counts = {"subjects": 24, "wrong_subject_donors": 24, "wrong_child_pairs": 12}
            files = {"INPUT.PRIVATE.json": raw, "BOUND.PRIVATE.json": canonical(result)}
        receipt = append(args.freeze_dir, stage, files, counts)
        print(
            json.dumps(
                {
                    "stage": stage,
                    "counts": receipt["counts"],
                    "receipt_raw_sha256": digest(canonical(receipt)),
                },
                sort_keys=True,
            )
        )
        return 0
    except (BoundaryError, OSError, KeyError, TypeError) as error:
        # Failed raw inputs stay at their original private path; never print source text.
        print(json.dumps({"disposition": "BLOCKED", "reason": str(error)}, sort_keys=True))
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
