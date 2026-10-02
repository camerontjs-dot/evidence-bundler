"""Synthetic gate qualification, not model authoring or retrieval evidence."""

import copy
import json
import subprocess
import sys

import population as p
import pytest


def hd(text):
    return p.digest(text.encode())


def inventory():
    provenance = {
        k: hd(k)
        for k in [
            "pool_raw_sha256",
            "custody_manifest_raw_sha256",
            "seal_raw_sha256",
            "pool_construction_raw_sha256",
            "source_manifest_raw_sha256",
        ]
    }
    provenance.update(
        pre_existing_sealed_at="2026-10-02T04:34:27+00:00", fidelity_basis="synthetic test only"
    )
    packets = []
    for packet, size in enumerate([50, 50, 8]):
        source = hd("source" + str(packet))
        roots = []
        for i in range(size):
            text = f"Office {i:03} logs batch {packet}-{i} and archives it."
            roots.append(
                {
                    "root_id": f"p{packet}-r{i}",
                    "text": text,
                    "text_sha256": hd(text),
                    "declared_at": "2026-10-02T02:43:19+00:00",
                    "origin_span": [i * 100, i * 100 + len(text.encode())],
                    "origin_source_sha256": source,
                }
            )
        packets.append(
            {
                "packet_id": f"p{packet}",
                "source_hashes": [source],
                "source_set_sha256": p.source_set_digest([source]),
                "sources": [
                    {
                        "source_id": str(packet),
                        "raw_sha256": source,
                        "locator": "unopened.source",
                        "origin_locator": "archive",
                        "media_type": "text/plain",
                        "sealed_bytes": 10000,
                    }
                ],
                "roots": roots,
            }
        )
    return {"schema": "eb-rc2-root-inventory-v1", "provenance": provenance, "packets": packets}


def proposal(root):
    anchor = root["text"].split(" logs")[0]
    explicit = root["text"].split(" and ")[0] + "."
    sub = {"anchor": anchor, "entity_class": "organization", "root_span": [0, len(anchor.encode())]}
    return {
        "root_alias": p.alias(root),
        "status": "declared",
        "reason": "two_required_conserved",
        "children": [
            {
                "text": explicit,
                "subject": dict(sub, origin="explicit", child_span=[0, len(anchor.encode())]),
            },
            {"text": "Archives it.", "subject": dict(sub, origin="inherited", child_span=None)},
        ],
    }


def checker(proposed):
    checks = {k: True for k in p.load(p.HERE / "AUTHORING-RUBRIC.json")["checks"]}
    return {
        "root_alias": proposed["root_alias"],
        "proposal_sha256": p.digest(p.canonical(proposed)),
        "decision": "accept",
        "reason": "exact_agreement",
        "checks": checks,
    }


def control(profile, session, mode="oracle"):
    rows = []
    for c in p.load(p.HERE / "AUTHORING-CONTROLS.json")["cases"]:
        decision = (
            c["expected_decision"]
            if mode == "oracle"
            else (
                "accept"
                if mode == "accept_all" or (mode == "and_keyword" and " and " in c["root_text"])
                else "reject"
            )
        )
        rows.append({"alias": c["alias"], "decision": decision})
    return {"profile_sha256": profile, "session_id": session, "rows": rows}


def authority():
    profiles = {"primary": hd("primary profile"), "checker": hd("checker profile")}
    return {
        "schema": "eb-rc2-authoring-authority-v1",
        "adapter_sha256": hd("adapter"),
        "adapter_qualification_sha256": hd("synthetic adapter receipt"),
        "destination": "synthetic-control-only",
        "destination_authorization_sha256": hd("auth"),
        "independent_custody_authority_sha256": hd("custody"),
        "profiles": profiles,
        "controls": [control(profiles["primary"], "cal-1"), control(profiles["checker"], "cal-2")],
    }


def trace(root, proposed, output, role, ident, auth):
    return {
        "adapter_sha256": auth["adapter_sha256"],
        "session_id": ident,
        "profile_sha256": auth["profiles"][role],
        "destination": auth["destination"],
        "request": p.capsule(root, role, proposed if role == "checker" else None),
        "output": output,
        "started_at": "2026-10-03T00:01:00+00:00",
        "completed_at": "2026-10-03T00:01:00+00:00",
        "no_history_receipt_sha256": hd(ident),
    }


def attempts(inv, plan, auth):
    roots = {r["root_id"]: r for packet in inv["packets"] for r in packet["roots"]}
    out = []
    for packet in plan["packets"]:
        for rid in packet["initial"]:
            root = roots[rid]
            primary = proposal(root)
            check = checker(primary)
            out.append(
                {
                    "packet_id": packet["packet_id"],
                    "root_id": rid,
                    "primary": {
                        "output": primary,
                        "trace": trace(root, primary, primary, "primary", rid + "p", auth),
                    },
                    "checker": {
                        "output": check,
                        "trace": trace(root, primary, check, "checker", rid + "c", auth),
                    },
                }
            )
    return {"schema": "eb-rc2-declaration-attempts-v1", "attempts": out}


def fixture():
    inv = inventory()
    plan = p.inventory_plan(inv, set())
    auth = authority()
    rows = attempts(inv, plan, auth)
    return inv, plan, auth, rows


def test_inventory_and_complete_prefix():
    inv, plan, auth, rows = fixture()
    result = p.declarations(inv, plan, auth, rows, "2026-10-03T00:00:00+00:00")
    assert sum(len(x["accepted"]) for x in result["packets"]) == 12
    assert len(p.subjects(result)["rows"]) == 24
    assert sum(len(x["reserves"]) for x in plan["packets"]) == 96


@pytest.mark.parametrize(
    "mutation,reason",
    [
        ("root_bytes", "root byte identity"),
        ("source_set", "source set identity"),
        ("late_root", "root postdates"),
        ("late_inventory", "not pre-existing"),
        ("duplicate_id", "duplicate root ID"),
        ("count", "108-root inventory"),
        ("extra_root_field", "schema:root"),
        ("extra_packet", "three source packets"),
        ("bad_span", "root origin span"),
    ],
)
def test_inventory_falsifiers(mutation, reason):
    inv = inventory()
    packet = inv["packets"][0]
    root = packet["roots"][0]
    if mutation == "root_bytes":
        root["text"] += " changed"
    if mutation == "source_set":
        packet["source_set_sha256"] = hd("wrong")
    if mutation == "late_root":
        root["declared_at"] = "2026-10-03T00:00:00+00:00"
    if mutation == "late_inventory":
        inv["provenance"]["pre_existing_sealed_at"] = "2027-01-01T00:00:00+00:00"
    if mutation == "duplicate_id":
        packet["roots"][1]["root_id"] = root["root_id"]
    if mutation == "count":
        packet["roots"].pop()
    if mutation == "extra_root_field":
        root["adequacy"] = True
    if mutation == "extra_packet":
        inv["packets"].append(copy.deepcopy(packet))
    if mutation == "bad_span":
        root["origin_span"] = [True, 4]
    with pytest.raises(p.BoundaryError, match=reason):
        p.inventory_plan(inv, set())


@pytest.mark.parametrize("domain", ["root", "source"])
def test_historical_exclusion(domain):
    inv = inventory()
    banned = (
        inv["packets"][0]["roots"][0]["text_sha256"]
        if domain == "root"
        else inv["packets"][0]["source_hashes"][0]
    )
    with pytest.raises(p.BoundaryError, match="exclusion"):
        p.inventory_plan(inv, {banned})


@pytest.mark.parametrize("mode", ["accept_all", "reject_all", "and_keyword"])
def test_weak_checker_fails_frozen_qualification(mode):
    result = p.calibrate(control(hd("profile"), "fresh-synthetic", mode))
    assert result["total"] == 12
    assert result["correct"] < 12 and not result["qualified_gate"]


def test_oracle_gate_is_not_semantic_authority():
    result = p.calibrate(control(hd("profile"), "synthetic"))
    assert result["correct"] == 12
    assert result["semantic_role_authority"] == "NOT_ESTABLISHED_BY_THIS_FUNCTION"


@pytest.mark.parametrize("mutation", ["missing", "duplicate", "extra", "bad_label"])
def test_control_schema(mutation):
    review = control(hd("profile"), "session")
    if mutation == "missing":
        review["rows"].pop()
    if mutation == "duplicate":
        review["rows"][1] = review["rows"][0]
    if mutation == "extra":
        review["rows"][0]["rank"] = 1
    if mutation == "bad_label":
        review["rows"][0]["decision"] = "supports"
    with pytest.raises(p.BoundaryError):
        p.calibrate(review)


@pytest.mark.parametrize(
    "mutation",
    [
        "rank",
        "duplicate",
        "invented_anchor",
        "bool_span",
        "wrong_child_span",
        "inherited_with_span",
        "changed_alias",
    ],
)
def test_primary_boundary(mutation):
    root = inventory()["packets"][0]["roots"][0]
    proposed = proposal(root)
    subject = proposed["children"][0]["subject"]
    if mutation == "rank":
        proposed["rank"] = 1
    if mutation == "duplicate":
        proposed["children"][1] = copy.deepcopy(proposed["children"][0])
    if mutation == "invented_anchor":
        subject["anchor"] = "South Dock"
    if mutation == "bool_span":
        subject["root_span"] = [False, 10]
    if mutation == "wrong_child_span":
        subject["child_span"][0] = 1
    if mutation == "inherited_with_span":
        subject["origin"] = "inherited"
    if mutation == "changed_alias":
        proposed["root_alias"] += "x"
    with pytest.raises(p.BoundaryError):
        p.check_primary(root, proposed)


def test_multibyte_grounding():
    anchor = "Café Orion"
    p.span_matches(anchor + " logs.", [0, len(anchor.encode())], anchor)
    with pytest.raises(p.BoundaryError):
        p.span_matches(anchor, [0, len(anchor)], anchor)


@pytest.mark.parametrize(
    "mutation",
    ["changed_child", "false_check", "truth_label", "rationale", "boolean_integer", "bad_reason"],
)
def test_checker_exact_binding(mutation):
    proposed = proposal(inventory()["packets"][0]["roots"][0])
    output = checker(proposed)
    if mutation == "changed_child":
        proposed["children"][0]["text"] += " changed"
    if mutation == "false_check":
        output["checks"]["conservation"] = False
    if mutation == "truth_label":
        output["decision"] = "true"
    if mutation == "rationale":
        output["rationale"] = "leak"
    if mutation == "boolean_integer":
        output["checks"]["conservation"] = 1
    if mutation == "bad_reason":
        output["reason"] = "likely"
    with pytest.raises(p.BoundaryError):
        p.check_checker(proposed, output)


@pytest.mark.parametrize(
    "mutation,reason",
    [
        ("skip", "out-of-order"),
        ("short", "AUTHORING_INSUFFICIENT"),
        ("reuse", "reused"),
        ("evidence", "information aperture"),
        ("wrong_profile", "authority identity"),
        ("premature", "chronology"),
        ("third", "schema:attempt"),
    ],
)
def test_declaration_falsifiers(mutation, reason):
    inv, plan, auth, rows = fixture()
    first = rows["attempts"][0]
    if mutation == "skip":
        rows["attempts"][0], rows["attempts"][1] = rows["attempts"][1], first
    if mutation == "short":
        rows["attempts"].pop()
    if mutation == "reuse":
        first["checker"]["trace"]["session_id"] = first["primary"]["trace"]["session_id"]
    if mutation == "evidence":
        first["primary"]["trace"]["request"]["source"] = "secret"
    if mutation == "wrong_profile":
        first["primary"]["trace"]["profile_sha256"] = hd("other")
    if mutation == "premature":
        first["primary"]["trace"]["started_at"] = "2026-10-01T00:00:00+00:00"
    if mutation == "third":
        first["adjudicator"] = {}
    with pytest.raises(p.BoundaryError, match=reason):
        p.declarations(inv, plan, auth, rows, "2026-10-03T00:00:00+00:00")


@pytest.mark.parametrize("mutation", ["unbound", "weak", "reused_calibration", "fresh_boolean"])
def test_unqualified_authority(mutation):
    auth = authority()
    if mutation == "unbound":
        auth["adapter_qualification_sha256"] = "UNBOUND"
    if mutation == "weak":
        auth["controls"][0] = control(auth["profiles"]["primary"], "cal-1", "accept_all")
    if mutation == "reused_calibration":
        auth["controls"][1]["session_id"] = "cal-1"
    if mutation == "fresh_boolean":
        auth["fresh"] = True
    with pytest.raises(p.BoundaryError):
        p.authority_check(auth)


@pytest.mark.parametrize("mutation", ["inherited", "same_anchor", "wrong_class"])
def test_subject_population_falsifiers(mutation):
    inv, plan, auth, rows = fixture()
    declared = p.declarations(inv, plan, auth, rows, "2026-10-03T00:00:00+00:00")
    packet = declared["packets"][0]
    for item in packet["accepted"]:
        for child in item["proposal"]["children"]:
            if mutation == "inherited":
                child["subject"]["origin"] = "explicit"
            if mutation == "same_anchor":
                child["subject"]["anchor"] = "one anchor"
            if mutation == "wrong_class":
                child["subject"]["entity_class"] = item["root_id"]
    with pytest.raises(p.BoundaryError, match="SUBJECT_CONTROL_POPULATION"):
        p.subjects(declared)


def test_rotation_mapping_is_exact_and_within_packet_class():
    inv, plan, auth, rows = fixture()
    declared = p.declarations(inv, plan, auth, rows, "2026-10-03T00:00:00+00:00")
    out = p.subjects(declared)
    lookup = {r["child_id"]: r for r in out["rows"]}
    for row in out["rows"]:
        donor = lookup[row["wrong_subject_child_id"]]
        assert donor["packet_id"] == row["packet_id"]
        assert donor["entity_class"] == row["entity_class"] and donor["anchor"] != row["anchor"]
        assert lookup[row["wrong_child_id"]]["wrong_child_id"] == row["child_id"]
    assert out == p.subjects(declared)


@pytest.mark.parametrize("mutation", ["raw_drift", "extra", "previous", "partial", "stale"])
def test_append_only_chain(tmp_path, mutation):
    root = tmp_path / "freeze"
    p.append(root, "INVENTORY", {"INPUT.PRIVATE.json": b"synthetic"}, {"roots": 108})
    folder = root / "INVENTORY"
    # Deliberately bypass permissions on this disposable fixture to test the hash gate.
    (folder / "INPUT.PRIVATE.json").chmod(0o600)
    (folder / "RECEIPT.PUBLIC.json").chmod(0o600)
    if mutation == "raw_drift":
        (folder / "INPUT.PRIVATE.json").write_bytes(b"changed")
    if mutation == "extra":
        (folder / "extra").write_bytes(b"x")
    if mutation == "previous":
        receipt = p.load(folder / "RECEIPT.PUBLIC.json")
        receipt["previous_receipt_raw_sha256"] = hd("wrong")
        (folder / "RECEIPT.PUBLIC.json").write_bytes(p.canonical(receipt))
    if mutation == "partial":
        (root / "SAMPLE").mkdir()
    if mutation == "stale":
        with pytest.raises(p.BoundaryError):
            p.append(root, "INVENTORY", {}, {})
        return
    with pytest.raises(p.BoundaryError):
        p.chain(root, 1)


def test_hash_linked_stage_receipts(tmp_path):
    root = tmp_path / "freeze"
    first = p.append(root, "INVENTORY", {"input": b"one"}, {})
    second = p.append(root, "SAMPLE", {"input": b"two"}, {})
    assert second["previous_receipt_raw_sha256"] == p.digest(p.canonical(first))
    assert len(p.chain(root, 2)) == 2


def test_duplicate_json_key(tmp_path):
    file = tmp_path / "input.json"
    file.write_text('{"root":1,"root":2}')
    with pytest.raises(p.BoundaryError):
        p.load(file)


def test_control_capsule_has_no_oracle_labels():
    packet = p.control_capsule()
    assert len(packet["rows"]) == 12
    assert all(set(row) == {"alias", "root_text", "proposed_children"} for row in packet["rows"])
    assert "expected_decision" not in json.dumps(packet)


def test_root_capsule_has_only_role_aperture():
    root = inventory()["packets"][0]["roots"][0]
    packet = p.capsule(root, "primary")
    assert set(packet) == {
        "schema",
        "role",
        "root_alias",
        "root_text",
        "rubric",
        "output_schema",
        "proposal",
    }
    assert "launch_trace" not in packet["output_schema"]
    assert "authority" not in packet["output_schema"]
    assert packet["proposal"] is None


@pytest.mark.parametrize("failure", ["primary_ineligible", "checker_rejected"])
def test_next_frozen_reserve_only(failure):
    inv, plan, auth, rows = fixture()
    first = rows["attempts"][0]
    root = next(
        r for packet in inv["packets"] for r in packet["roots"] if r["root_id"] == first["root_id"]
    )
    if failure == "primary_ineligible":
        output = {
            "root_alias": p.alias(root),
            "status": "ineligible",
            "reason": "not_two_required",
            "children": [],
        }
        first["primary"]["output"] = output
        first["primary"]["trace"]["output"] = output
        first["checker"] = None
    else:
        output = first["checker"]["output"]
        output["decision"], output["reason"] = "reject", "not_conserved"
        output["checks"]["conservation"] = False
    donor_plan = copy.deepcopy(plan)
    donor_plan["packets"][0]["initial"] = [plan["packets"][0]["reserves"][0]]
    replacement = attempts(inv, donor_plan, auth)["attempts"][0]
    rows["attempts"].insert(4, replacement)
    bound = p.declarations(inv, plan, auth, rows, "2026-10-03T00:00:00+00:00")
    assert len(bound["exclusions"]) == 1
    assert (
        next(
            packet["consumed"]
            for packet in bound["packets"]
            if packet["packet_id"] == first["packet_id"]
        )
        == 5
    )


@pytest.mark.parametrize("stage", ["authoring_authority", "declarations", "subjects"])
def test_setup_cli_cannot_accept_self_asserted_authority(tmp_path, stage):
    run = subprocess.run(
        [
            sys.executable,
            str(p.HERE / "population.py"),
            stage,
            "--freeze-dir",
            str(tmp_path / "freeze"),
            "--input",
            str(tmp_path / "unopened-private-input"),
        ],
        capture_output=True,
        text=True,
    )
    assert run.returncode == 2
    assert "authoring adapter and authority are unqualified" in run.stdout
    assert not (tmp_path / "freeze").exists()


@pytest.mark.parametrize("stage", ["corpus", "execution"])
def test_unbound_later_adapter_cannot_open_input(tmp_path, stage):
    command = [
        sys.executable,
        str(p.HERE / "population.py"),
        stage,
        "--freeze-dir",
        str(tmp_path / "freeze"),
        "--input",
        str(tmp_path / "nonexistent-secret"),
    ]
    run = subprocess.run(command, capture_output=True, text=True)
    assert run.returncode == 2
    assert "adapter unbound" in json.loads(run.stdout)["reason"]
    assert not (tmp_path / "freeze").exists()


def test_exact_nomination_rejects_substitution_before_freeze(tmp_path):
    file = tmp_path / "synthetic.json"
    file.write_bytes(p.canonical(inventory()))
    command = [
        sys.executable,
        str(p.HERE / "population.py"),
        "inventory",
        "--freeze-dir",
        str(tmp_path / "freeze"),
        "--input",
        str(file),
    ]
    run = subprocess.run(command, capture_output=True, text=True)
    assert run.returncode == 2 and "exact nominated inventory" in run.stdout
    assert not (tmp_path / "freeze").exists()
