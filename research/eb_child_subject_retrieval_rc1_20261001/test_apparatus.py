"""Exposed mechanical controls. No test below qualifies a semantic reviewer."""

from __future__ import annotations

import copy
import subprocess
import sys

import bind
import pytest
import retrieval
import study


def population():
    packets, declarations, corpora = [], [], []
    for packet in range(3):
        parents = []
        for parent in range(4):
            pid = f"p{packet}-{parent}"
            anchor = f"Unit {packet}-{parent}"
            text = f"{anchor} completed cooling and pressure checks."
            children = [
                {"child_id": pid + "/1", "text": "Completed the cooling check.", "sequence": 1},
                {
                    "child_id": pid + "/2",
                    "text": f"{anchor} completed the pressure check.",
                    "sequence": 2,
                },
            ]
            parents.append({"parent_id": pid, "text": text, "children": children})
            for child in children:
                origin = "parent" if child["sequence"] == 1 else "child"
                origin_text = text if origin == "parent" else child["text"]
                declarations.append(
                    {
                        "child_id": child["child_id"],
                        "anchor": anchor,
                        "origin": origin,
                        "span_start": 0,
                        "span_end": len(anchor),
                        "origin_text_sha256": study.digest(origin_text.encode()),
                        "wrong_child_id": f"p{packet}-{(parent + 1) % 4}/{child['sequence']}",
                        "entity_class": "fixture_unit",
                    }
                )
        packets.append(
            {
                "packet_id": f"packet-{packet}",
                "provenance": "SYNTHETIC TEST ONLY",
                "parents": parents,
            }
        )
        content = f"SYNTHETIC packet {packet}: locally distinct source bytes."
        corpora.append(
            {
                "packet_id": f"packet-{packet}",
                "sources": [
                    {
                        "source_id": f"source-{packet}",
                        "media_type": "text/plain; charset=utf-8",
                        "content": content,
                        "content_sha256": study.digest(content.encode()),
                    }
                ],
            }
        )
    return (
        {"schema": "eb-child-subject-claims-v1", "packets": packets},
        {"schema": "eb-child-subject-declarations-v1", "declarations": declarations},
        {"schema": "eb-child-subject-corpus-v1", "packets": corpora},
    )


def result_fixture():
    claims, _, _ = population()
    targets = study.claim_index(claims)
    targets = {
        cid: {key: value[key] for key in ["text", "parent_text", "parent_id", "packet_id"]}
        for cid, value in targets.items()
    }
    pools = {
        cid: [
            {"passage_id": "adequate", "text": "Synthetic adequate local passage."},
            {"passage_id": "topical", "text": "Synthetic topical fragment."},
        ]
        for cid in targets
    }
    selections = {arm: {cid: ["topical"] for cid in targets} for arm in study.policy()["arms"]}
    return {
        "schema": "eb-child-subject-retrieval-v1",
        "binding": {"fixture": True},
        "targets": targets,
        "pools": pools,
        "selections": selections,
    }


def review(packet, rows=None, identity="one"):
    return {
        "reviewer_id": identity,
        "session_id": "session-" + identity,
        "model_id": "fixture-observations-not-live-model",
        "packet_raw_sha256": study.digest(study.canonical(packet)),
        "rows": rows
        if rows is not None
        else [
            {"alias": row["alias"], "decision": "rejected", "reason": "insufficient_context"}
            for row in packet["rows"]
        ],
    }


def weak_accept_all(packet, identity):
    """Intentionally weak evaluator: topical presence treated as adequacy."""
    return review(
        packet,
        [
            {"alias": row["alias"], "decision": "accepted", "reason": "on_target_adequate"}
            for row in packet["rows"]
        ],
        identity,
    )


def weak_topical(packet, identity):
    rows = []
    for row in packet["rows"]:
        uncertain = "fragment ends" in row["passage"]
        rows.append(
            {
                "alias": row["alias"],
                "decision": "needs-review" if uncertain else "accepted",
                "reason": "uncertain" if uncertain else "on_target_adequate",
            }
        )
    return review(packet, rows, identity)


def synthetic_metrics():
    m = {}
    for arm in study.policy()["arms"]:
        covered = 12 if arm != "A3" else 18
        m[arm] = {
            "required_children": covered,
            "complete_parents": 4 if arm != "A3" else 7,
            "wrong_subject": 2,
            "non_useful": 30,
            "accepted_reachable": 50,
            "per_packet": {f"packet-{p}": covered // 3 for p in range(3)},
        }
    return m


def lane():
    return [
        {
            "passage_id": str(n),
            "text": "Unit Birch observation.",
            "owner": "sibling",
            "score": 0.900 - n * 0.001,
        }
        for n in range(5)
    ]


def test_population_binding_and_preformed_contracts():
    claims, subjects, corpus = population()
    assert len(study.check_subjects(claims, subjects)) == 24
    study.check_corpus(claims, corpus)
    contracts = bind.make_contracts(claims, corpus)
    assert len(contracts) == 12
    for contract in contracts.values():
        payload = {k: v for k, v in contract.items() if k != "handoff_sha256"}
        assert study.digest(study.canonical(payload)) == contract["handoff_sha256"]


@pytest.mark.parametrize(
    "mutation",
    [
        "evidence_origin",
        "wrong_span",
        "resealed_origin",
        "missing_child",
        "wrong_same_subject",
        "wrong_packet_donor",
        "automatic_hint",
    ],
)
def test_subject_falsifiers(mutation):
    claims, subjects, _ = population()
    row = subjects["declarations"][0]
    if mutation == "evidence_origin":
        row["origin"] = "evidence"
    elif mutation == "wrong_span":
        row["span_end"] -= 1
    elif mutation == "resealed_origin":
        row["anchor"] = "Invented subject"
        row["origin_text_sha256"] = study.digest(row["anchor"].encode())
    elif mutation == "missing_child":
        subjects["declarations"].pop()
    elif mutation == "wrong_same_subject":
        row["wrong_child_id"] = row["child_id"]
    elif mutation == "wrong_packet_donor":
        row["wrong_child_id"] = "p1-0/1"
    else:
        row["answer_hint"] = "successful pressure check"
    with pytest.raises(study.BoundaryError):
        study.check_subjects(claims, subjects)


@pytest.mark.parametrize(
    "mutation", ["tamper", "cross_packet_duplicate", "known_rc0", "smaller_population"]
)
def test_corpus_and_denominator_controls(mutation):
    claims, _, corpus = population()
    if mutation == "tamper":
        corpus["packets"][0]["sources"][0]["content"] += " changed"
    elif mutation == "cross_packet_duplicate":
        corpus["packets"][1]["sources"] = copy.deepcopy(corpus["packets"][0]["sources"])
    elif mutation == "smaller_population":
        claims["packets"].pop()
    else:
        exclusions = study.load(study.HERE / "PREDECESSOR-EVIDENCE.json")
        claims["packets"][0]["parents"][0]["children"][0]["text"] = "known RC0 injected"
        monkey = exclusions["known_failure_exclusions"]["child_text_sha256"]
        monkey.append(study.digest(b"known RC0 injected"))
        original_load = study.load
        # A declared denial registry is checked independently of input resealing.
        with pytest.MonkeyPatch.context() as patch:
            patch.setattr(
                study,
                "load",
                lambda p: exclusions if p.name == "PREDECESSOR-EVIDENCE.json" else original_load(p),
            )
            with pytest.raises(study.BoundaryError, match="known RC0"):
                study.claim_index(claims)
        return
    with pytest.raises(study.BoundaryError):
        study.check_corpus(claims, corpus)


def test_stage_custody_order_and_raw_byte_binding(tmp_path):
    root = tmp_path / "fresh"
    study.fresh_directory(root)
    bind.snapshot(root, "CLAIMS", {"CLAIMS.PRIVATE.json": b'{"key":1}'})
    bind.snapshot(root, "SUBJECTS", {"SUBJECTS.PRIVATE.json": b'{"subject":1}'})
    bind.verify_chain(root, 2)
    p = root / "CLAIMS.PRIVATE.json"
    p.chmod(0o600)
    p.write_bytes(b'{ "key": 1 }')  # Semantically same; frozen raw bytes differ.
    with pytest.raises(study.BoundaryError, match="byte drift"):
        bind.verify_chain(root, 2)


def test_stage_reordering_and_stale_outputs(tmp_path):
    with pytest.raises(study.BoundaryError):
        study.fresh_directory(tmp_path)
    root = tmp_path / "fresh"
    study.fresh_directory(root)
    with pytest.raises(study.BoundaryError):
        bind.snapshot(root, "SUBJECTS", {})
    bind.snapshot(root, "CLAIMS", {"CLAIMS.PRIVATE.json": b"{}"})
    with pytest.raises(study.BoundaryError, match="already frozen"):
        bind.snapshot(root, "CLAIMS", {})


@pytest.mark.parametrize(
    "text,anchor,expected",
    [
        ("Unit Cedar ran.", "Unit Cedar", True),
        ("unit\nCEDAR ran.", "Unit Cedar", True),
        ("Units Cedar ran.", "Unit Cedar", False),
        ("Unit Cedarwood ran.", "Unit Cedar", False),
        ("Joann ran.", "Ann", False),
    ],
)
def test_exact_anchor_collision_control(text, anchor, expected):
    assert retrieval.anchor_match(text, anchor) is expected


def test_coverage_subject_and_wrong_controls_are_behaviorally_distinct():
    rows = lane()
    rows[3]["owner"] = "child"
    rows[4]["text"] = "Unit Cedar observation."
    rows[4]["owner"] = "child"
    base = retrieval.select_lane(rows, "child", "Unit Cedar", coverage=False, subject=False)
    child = retrieval.select_lane(rows, "child", "Unit Cedar", coverage=True, subject=False)
    subject = retrieval.select_lane(rows, "child", "Unit Cedar", coverage=False, subject=True)
    combined = retrieval.select_lane(rows, "child", "Unit Cedar", coverage=True, subject=True)
    wrong_subj = retrieval.select_lane(rows, "child", "Unit Birch", coverage=True, subject=True)
    wrong_child = retrieval.select_lane(
        rows, "child", "Unit Cedar", coverage=True, subject=False, wrong_child="sibling"
    )
    assert base == ["0", "1", "2"]
    assert "3" in child and "4" in subject and "4" in combined
    assert wrong_subj == child and wrong_child == base
    assert all(len(x) == 3 for x in [base, child, subject, combined, wrong_subj, wrong_child])


def test_no_depth_or_loss_cap_rescue_and_order_determinism():
    rows = lane()
    rows[3]["owner"] = "child"
    rows[3]["score"] = 0.1
    expected = retrieval.select_lane(rows, "child", "Unit Cedar", coverage=True, subject=False)
    assert expected == ["0", "1", "2"]
    assert (
        retrieval.select_lane(
            list(reversed(rows)), "child", "Unit Cedar", coverage=True, subject=False
        )
        == expected
    )
    with pytest.raises(study.BoundaryError, match="depth"):
        retrieval.select_lane(rows * 3, "child", "Unit Cedar", coverage=True, subject=False)


@pytest.mark.parametrize("score", [float("nan"), float("inf"), True])
def test_nonfinite_scores_rejected(score):
    rows = lane()
    rows[0]["score"] = score
    with pytest.raises(study.BoundaryError):
        retrieval.select_lane(rows, "child", "Unit Cedar", coverage=False, subject=False)


def test_model_backend_missing_is_not_a_pass(monkeypatch, tmp_path):
    monkeypatch.setattr(retrieval, "check_runtime", lambda _: {})

    def disconnected(_):
        raise ImportError("backend physically absent")

    monkeypatch.setattr(retrieval.importlib, "import_module", disconnected)
    with pytest.raises(study.BoundaryError, match="no fallback"):
        retrieval.load_model(tmp_path)


def test_cli_missing_freeze_physically_fails_closed(tmp_path):
    p = subprocess.run(
        [
            sys.executable,
            str(study.HERE / "retrieval.py"),
            "--freeze-dir",
            str(tmp_path / "missing"),
            "--model-dir",
            str(tmp_path / "model"),
            "--run-ordinal",
            "1",
        ],
        capture_output=True,
        text=True,
    )
    assert p.returncode == 2 and '"BLOCKED"' in p.stdout
    assert not (tmp_path / "missing").exists()


def test_blinding_preserves_bytes_and_does_not_leak_arm_rank_state():
    result = result_fixture()
    packet, mapping = study.build_packet(result, "opaque-private-salt-" * 3)
    assert len(packet["rows"]) == 48
    assert all(
        set(row) == {"alias", "proposition", "parent_context", "passage"} for row in packet["rows"]
    )
    assert mapping["packet_raw_sha256"] == study.digest(study.canonical(packet))
    for row in packet["rows"]:
        cid, pid = mapping["mapping"][row["alias"]]
        assert row["passage"] == next(
            x["text"] for x in result["pools"][cid] if x["passage_id"] == pid
        )
    contaminated = copy.deepcopy(result)
    next(iter(contaminated["pools"].values()))[0]["nomination_rank"] = 1
    with pytest.raises(study.BoundaryError, match="exact fields"):
        study.build_packet(contaminated, "salt")


@pytest.mark.parametrize(
    "mutation",
    ["third_review", "same_session", "rank_leak", "wrong_reason", "missing_alias", "mapping_swap"],
)
def test_reviewer_and_mapping_fail_closed(mutation):
    result = result_fixture()
    packet, mapping = study.build_packet(result, "frozen-salt")
    a, b = review(packet), review(packet, identity="two")
    if mutation == "third_review":
        with pytest.raises(study.BoundaryError):
            study.tally(result, packet, mapping, [a, b, review(packet, identity="three")], True)
        return
    if mutation == "same_session":
        b["session_id"] = a["session_id"]
    elif mutation == "rank_leak":
        a["rows"][0]["rank"] = 1
    elif mutation == "wrong_reason":
        a["rows"][0]["reason"] = "supports"
    elif mutation == "missing_alias":
        a["rows"].pop()
    else:
        aliases = list(mapping["mapping"])
        mapping["mapping"][aliases[0]], mapping["mapping"][aliases[2]] = (
            mapping["mapping"][aliases[2]],
            mapping["mapping"][aliases[0]],
        )
    with pytest.raises(study.BoundaryError):
        study.tally(result, packet, mapping, [a, b], True)


def test_zero_adequacy_is_negative_not_trigger_for_retry():
    result = result_fixture()
    packet, mapping = study.build_packet(result, "salt")
    output = study.tally(
        result, packet, mapping, [review(packet), review(packet, identity="two")], True
    )
    assert output["primary_disposition"] == "FALSIFIED"
    assert "NO_LOCAL_ADEQUACY_OBSERVED_WITHIN_FROZEN_DEPTH" in output["mechanism_results"]
    assert output["metrics"]["A0"]["recall"] is None


def test_disagreement_and_uncertainty_and_unqualified_evaluator_are_inconclusive():
    result = result_fixture()
    packet, mapping = study.build_packet(result, "salt")
    a, b = review(packet), review(packet, identity="two")
    b["rows"][0].update(decision="accepted", reason="on_target_adequate")
    assert (
        study.tally(result, packet, mapping, [a, b], True)["primary_disposition"] == "INCONCLUSIVE"
    )
    assert (
        study.tally(result, packet, mapping, [a, review(packet, identity="two")], False)[
            "primary_disposition"
        ]
        == "INCONCLUSIVE"
    )
    for r in [a, b]:
        r["rows"][0].update(decision="needs-review", reason="uncertain")
    assert (
        study.tally(result, packet, mapping, [a, b], True)["primary_disposition"] == "INCONCLUSIVE"
    )


def test_partial_all_of_and_recall_denominator_are_not_topical_presence():
    result = result_fixture()
    ids = list(result["targets"])
    result["selections"]["A3"][ids[0]] = ["adequate"]
    values = {
        (cid, row["passage_id"]): ("accepted", "on_target_adequate")
        if row["passage_id"] == "adequate"
        else ("rejected", "insufficient_context")
        for cid, rows in result["pools"].items()
        for row in rows
    }
    m = study.metrics(result, values)["A3"]
    assert m["required_children"] == 1 and m["complete_parents"] == 0
    assert m["accepted_reachable"] == 24 and m["recall"] == 1 / 24


def test_target_calibration_and_intentionally_weak_evaluators_discriminated():
    controls = study.load(study.HERE / "CONTROLS.json")
    packet, gold = controls["packet"], controls["gold"]
    good = [review(packet, copy.deepcopy(gold["rows"]), identity) for identity in ["one", "two"]]
    assert study.calibrate(packet, gold, good)
    for weak in [weak_accept_all, weak_topical]:
        assert not study.calibrate(packet, gold, [weak(packet, "one"), weak(packet, "two")])


def test_numeric_primary_and_both_increments():
    verdict = study.decide(synthetic_metrics())
    assert verdict["primary_disposition"] == "SUPPORTED"
    assert "SUPPORTED_CHILD_AND_SUBJECT" in verdict["mechanism_results"]


@pytest.mark.parametrize("control", ["WS3", "WC3", "L0"])
def test_realistic_controls_reproducing_gain_falsify_combined(control):
    m = synthetic_metrics()
    m[control]["required_children"] = m["A3"]["required_children"] - 1
    assert study.decide(m)["primary_disposition"] == "FALSIFIED"


@pytest.mark.parametrize("reference", ["A0", "S0"])
def test_improvement_over_one_reference_does_not_qualify(reference):
    m = synthetic_metrics()
    m[reference]["required_children"] = m["A3"]["required_children"] - 2
    assert study.decide(m)["primary_disposition"] == "FALSIFIED"


@pytest.mark.parametrize(
    "ref,label",
    [
        ("A2", "CHILD_COVERAGE_INCREMENT_NOT_REPRODUCED"),
        ("A1", "SUBJECT_IDENTITY_INCREMENT_NOT_REPRODUCED"),
    ],
)
def test_mixed_component_evidence_is_not_combined_support(ref, label):
    m = synthetic_metrics()
    m[ref]["required_children"] = m["A3"]["required_children"] - 1
    verdict = study.decide(m)
    assert verdict["primary_threshold_pass"] and verdict["primary_disposition"] == "INCONCLUSIVE"
    assert label in verdict["mechanism_results"]


def test_packet_concentration_and_wrong_subject_regression_fail():
    m = synthetic_metrics()
    m["A3"]["per_packet"] = {"packet-0": 8, "packet-1": 4, "packet-2": 4}
    assert study.decide(m)["primary_disposition"] == "FALSIFIED"
    m = synthetic_metrics()
    m["A3"]["wrong_subject"] += 1
    assert study.decide(m)["primary_disposition"] == "FALSIFIED"


@pytest.mark.parametrize("bytes_", [b'{"x":1,"x":2}', b'{"x":NaN}'])
def test_json_duplicate_and_nonfinite_values_rejected(tmp_path, bytes_):
    p = tmp_path / "input.json"
    p.write_bytes(bytes_)
    with pytest.raises(study.BoundaryError):
        study.load(p)


@pytest.mark.parametrize(
    "mutation", ["top_level_rank", "row_rank", "rubric_drift", "same_model_drift"]
)
def test_frozen_aperture_and_profile_controls(mutation):
    result = result_fixture()
    packet, _ = study.build_packet(result, "salt")
    artifact = review(packet)
    if mutation == "top_level_rank":
        packet["arm"] = "A3"
    elif mutation == "row_rank":
        packet["rows"][0]["score"] = 0.9
    elif mutation == "rubric_drift":
        packet["rubric"]["meaning"] = "Must support the proposition."
    else:
        b = review(packet, identity="two")
        b["model_id"] = "unqualified-different-model"
        controls = study.load(study.HERE / "CONTROLS.json")
        control = controls["packet"]
        a = review(control, controls["gold"]["rows"])
        b = review(control, controls["gold"]["rows"], "two")
        b["model_id"] = "unqualified-different-model"
        with pytest.raises(study.BoundaryError, match="model mismatch"):
            study.calibrate(control, controls["gold"], [a, b])
        return
    artifact["packet_raw_sha256"] = study.digest(study.canonical(packet))
    with pytest.raises(study.BoundaryError):
        study.judgments(artifact, packet)


def replay_fixture(tmp_path):
    first, second = tmp_path / "one", tmp_path / "two"
    first.mkdir()
    second.mkdir()
    result = result_fixture()
    trace = {"test": "SYNTHETIC ARTIFACT-BYTE CONTROL"}
    result["binding"]["nomination_trace_payload_sha256"] = study.digest(study.canonical(trace))
    hashes = {
        "retrieval_output_raw_sha256": study.digest(study.canonical(result)),
        "nomination_trace_raw_sha256": study.digest(study.canonical(trace)),
    }
    for p in range(12):
        hashes[f"baseline-{p}.json"] = study.digest(b"{}")
    for ordinal, root in enumerate([first, second], 1):
        study.write_new(root / "STARTED.PUBLIC.json", {"ordinal": ordinal})
        study.write_new(root / "RETRIEVAL.PRIVATE.json", result)
        study.write_new(root / "NOMINATION-TRACE.PRIVATE.json", trace)
        for p in range(12):
            study.write_new(root / f"baseline-{p}.json", {})
        study.write_new(root / "COMPLETED.PUBLIC.json", {"ordinal": ordinal, "hashes": hashes})
    return first, second


def test_all_research_and_native_replay_bytes_bound(tmp_path):
    first, second = replay_fixture(tmp_path)
    study.compare_replays(first, second)
    file = second / "baseline-2.json"
    file.chmod(0o600)
    file.write_bytes(b"{ }")
    with pytest.raises(study.BoundaryError, match="raw-byte replay drift"):
        study.compare_replays(first, second)


def test_resealed_replay_hashes_do_not_discard_frozen_binding(tmp_path):
    first, second = replay_fixture(tmp_path)
    p = second / "COMPLETED.PUBLIC.json"
    data = study.load(p)
    data["hashes"]["nomination_trace_raw_sha256"] = "sha256:" + "0" * 64
    p.chmod(0o600)
    p.write_bytes(study.canonical(data))
    with pytest.raises(study.BoundaryError, match="hash mismatch"):
        study.compare_replays(first, second)


def test_replay_and_scope_disconnection_not_success(tmp_path):
    with pytest.raises(study.BoundaryError, match="unavailable"):
        study.compare_replays(tmp_path / "missing", tmp_path / "other")


@pytest.mark.parametrize(
    "mutation", ["K_overflow", "missing_arm", "unreachable_passage", "aliased_parent"]
)
def test_retrieval_population_and_budget_mutations(mutation):
    result = result_fixture()
    cid = next(iter(result["targets"]))
    if mutation == "K_overflow":
        result["selections"]["A3"][cid] = ["one", "two", "three", "four"]
    elif mutation == "missing_arm":
        result["selections"].pop("WS3")
    elif mutation == "unreachable_passage":
        result["selections"]["A3"][cid] = ["not-in-the-reachable-world"]
    else:
        result["targets"][cid]["parent_id"] = "unregistered-parent"
    with pytest.raises(study.BoundaryError):
        study.validate_result(result)


def test_subject_span_byte_domain_discriminates_character_offset_control():
    claims, subjects, _ = population()
    parent = claims["packets"][0]["parents"][0]
    row = subjects["declarations"][0]
    parent["text"] = "Å " + parent["text"]
    row["origin_text_sha256"] = study.digest(parent["text"].encode("utf-8"))
    row["span_start"] = len("Å ".encode())
    row["span_end"] = row["span_start"] + len(row["anchor"].encode("utf-8"))
    assert len(study.check_subjects(claims, subjects)) == 24
    row["span_start"] = len("Å ")
    row["span_end"] = row["span_start"] + len(row["anchor"])
    # The weak character-index implementation would accept this wrong byte-domain declaration.
    assert parent["text"][row["span_start"] : row["span_end"]] == row["anchor"]
    with pytest.raises(study.BoundaryError, match="UTF-8 byte span"):
        study.check_subjects(claims, subjects)


def test_unmanifested_replay_artifact_is_not_unchanged_world(tmp_path):
    first, second = replay_fixture(tmp_path)
    (second / "unbound-extra.txt").write_text("SYNTHETIC unexpected drift")
    with pytest.raises(study.BoundaryError, match="unexpected replay artifacts"):
        study.compare_replays(first, second)


def test_weak_any_child_parent_evaluator_is_discriminated():
    result = result_fixture()
    cid = next(iter(result["targets"]))
    result["selections"]["A3"][cid] = ["adequate"]
    values = {
        (child, row["passage_id"]): ("accepted", "on_target_adequate")
        if row["passage_id"] == "adequate"
        else ("rejected", "insufficient_context")
        for child, rows in result["pools"].items()
        for row in rows
    }
    actual = study.metrics(result, values)["A3"]["complete_parents"]
    weak_or_count = 1
    assert actual == 0 and actual != weak_or_count
