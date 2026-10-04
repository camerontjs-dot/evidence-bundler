from __future__ import annotations

import json
from hashlib import sha256
from pathlib import Path
from typing import Any

from click.testing import CliRunner

from evidence_bundler.production_v1.cli import cli
from evidence_bundler.production_v1.review_cycle import (
    DISPLAY_LIMIT,
    GAP_NO_NOMINATIONS,
    GAP_NO_SOURCES,
    GAP_NONE_ACCEPTED,
    GAP_NOT_RETAINED,
    GAP_NOT_RUN,
    display_bridge,
    gap_sentence,
)
from evidence_bundler.v1.contract_a import compute_handoff_sha256

REASON = "REASON-TOKEN-the passage states the retained claim and was read in place."


def _hash_text(value: str) -> str:
    return "sha256:" + sha256(value.encode("utf-8")).hexdigest()


def _contract(root_text: str, sources: list[tuple[str, str, str]]) -> dict[str, Any]:
    value: dict[str, Any] = {
        "schema": "contract-a-wire-candidate-rc2",
        "handoff_id": "handoff-review-cycle",
        "producer": {"producer_id": "test", "producer_version": "1"},
        "work": {"work_id": "work-review-cycle"},
        "root_proposition": {
            "proposition_id": "ROOT",
            "text": root_text,
            "text_sha256": _hash_text(root_text),
        },
        "decomposition": {"state": "not_decomposed"},
        "sources": [
            {
                "source_id": source_id,
                "media_type": media_type,
                "content": content,
                "content_sha256": _hash_text(content),
            }
            for source_id, media_type, content in sources
        ],
        "handoff_sha256": "sha256:" + "0" * 64,
    }
    value["handoff_sha256"] = compute_handoff_sha256(value)
    return value


def _write(path: Path, value: dict[str, Any]) -> None:
    path.write_text(json.dumps(value, sort_keys=True) + "\n", encoding="utf-8")


def _run(contract_path: Path, out_dir: Path, *extra: str) -> dict[str, Any]:
    result = CliRunner().invoke(cli, ["run", str(contract_path), "--out-dir", str(out_dir), *extra])
    assert result.exit_code == 0, result.output
    return json.loads(result.output)


def _fill(record: dict[str, Any], decision: str = "accepted") -> dict[str, Any]:
    for row in record["decisions"]:
        row["decision"] = decision
        row["reason"] = REASON
    return record


def test_matching_review_applies_without_putting_reasons_on_the_wire(tmp_path: Path) -> None:
    root = "alpha beta gamma delta appears in the calibration note"
    source = "alpha beta gamma delta appears in the calibration note A."
    contract_path = tmp_path / "contract_a.json"
    _write(contract_path, _contract(root, [("note-a", "text/plain; charset=utf-8", source)]))
    draft = _run(contract_path, tmp_path / "draft")
    record = _fill(json.loads((tmp_path / "draft" / "review_record.json").read_text()))
    review_path = tmp_path / "review.json"
    _write(review_path, record)

    applied = _run(contract_path, tmp_path / "applied", "--review", str(review_path))
    native = json.loads((tmp_path / "applied" / "native_eb_v1_package.json").read_text())
    retained = [row for row in native["candidates"] if row["selection_state"] == "retained"]
    assert retained
    assert {row["admission_state"] for row in retained} == {"accepted"}
    assert REASON not in (tmp_path / "applied" / "native_eb_v1_package.json").read_text()
    bundle = "\n".join(
        path.read_text(encoding="utf-8")
        for path in (tmp_path / "applied" / "contract_b").rglob("*")
        if path.is_file()
    )
    assert REASON not in bundle
    saved = json.loads((tmp_path / "applied" / "applied_review_record.json").read_text())
    assert saved["bindings"] == record["bindings"]
    assert saved["decisions"] == record["decisions"]
    assert REASON in (tmp_path / "applied" / "applied_review_record.json").read_text()
    assert applied["unreviewed_native_package_sha256"] == draft["unreviewed_native_package_sha256"]
    assert applied["native_package_sha256"] != draft["native_package_sha256"]
    assert "review_record" not in applied


def test_stale_review_writes_nothing(tmp_path: Path) -> None:
    root = "alpha beta gamma delta appears in the calibration note"
    source = "alpha beta gamma delta appears in the calibration note A."
    contract_path = tmp_path / "contract_a.json"
    _write(contract_path, _contract(root, [("note-a", "text/plain; charset=utf-8", source)]))
    _run(contract_path, tmp_path / "draft")
    record = _fill(json.loads((tmp_path / "draft" / "review_record.json").read_text()))
    record["bindings"]["input_sha256"] = "sha256:" + "ab" * 32
    review_path = tmp_path / "stale.json"
    _write(review_path, record)
    sentinel = tmp_path / "sentinel.txt"
    sentinel.write_text("keep", encoding="utf-8")
    out_dir = tmp_path / "refused"
    result = CliRunner().invoke(
        cli, ["run", str(contract_path), "--out-dir", str(out_dir), "--review", str(review_path)]
    )
    assert result.exit_code != 0
    assert "refusing stale review" in result.output
    assert "input_sha256" in result.output
    assert not out_dir.exists()
    assert sentinel.read_text(encoding="utf-8") == "keep"

    record = _fill(json.loads((tmp_path / "draft" / "review_record.json").read_text()))
    record["bindings"]["unreviewed_native_package_sha256"] = "sha256:" + "cd" * 32
    _write(review_path, record)
    result = CliRunner().invoke(
        cli, ["run", str(contract_path), "--out-dir", str(out_dir), "--review", str(review_path)]
    )
    assert result.exit_code != 0
    assert "unreviewed_native_package_sha256" in result.output
    assert not out_dir.exists()


def test_changed_contract_reusing_ids_requires_a_new_review(tmp_path: Path) -> None:
    source = "alpha beta gamma delta appears in the calibration note A."
    original = _contract(
        "alpha beta gamma delta appears in the calibration note",
        [("note-a", "text/plain; charset=utf-8", source)],
    )
    changed = _contract(
        "alpha beta gamma delta appears in the revised calibration note",
        [("note-a", "text/plain; charset=utf-8", source)],
    )
    assert original["root_proposition"]["proposition_id"] == "ROOT"
    assert changed["root_proposition"]["proposition_id"] == "ROOT"
    assert original["sources"][0]["source_id"] == changed["sources"][0]["source_id"]
    original_path = tmp_path / "original.json"
    changed_path = tmp_path / "changed.json"
    _write(original_path, original)
    _write(changed_path, changed)
    _run(original_path, tmp_path / "draft")
    stale = _fill(json.loads((tmp_path / "draft" / "review_record.json").read_text()))
    stale_path = tmp_path / "stale.json"
    _write(stale_path, stale)
    refused = tmp_path / "refused"
    result = CliRunner().invoke(
        cli, ["run", str(changed_path), "--out-dir", str(refused), "--review", str(stale_path)]
    )
    assert result.exit_code != 0
    assert "refusing stale review" in result.output
    assert not refused.exists()

    fresh = _run(changed_path, tmp_path / "fresh-draft")
    filled = _fill(json.loads((tmp_path / "fresh-draft" / "review_record.json").read_text()))
    fresh_review = tmp_path / "fresh-review.json"
    _write(fresh_review, filled)
    applied = _run(changed_path, tmp_path / "fresh-applied", "--review", str(fresh_review))
    assert applied["input_sha256"] == fresh["input_sha256"]
    native = json.loads((tmp_path / "fresh-applied" / "native_eb_v1_package.json").read_text())
    assert any(row["admission_state"] == "accepted" for row in native["candidates"])


def test_blank_template_and_mixed_inputs_write_nothing(tmp_path: Path) -> None:
    root = "alpha beta gamma delta appears in the calibration note"
    source = "alpha beta gamma delta appears in the calibration note A."
    contract_path = tmp_path / "contract_a.json"
    _write(contract_path, _contract(root, [("note-a", "text/plain; charset=utf-8", source)]))
    draft = tmp_path / "draft"
    _run(contract_path, draft)
    blank_out = tmp_path / "blank"
    result = CliRunner().invoke(
        cli,
        [
            "run",
            str(contract_path),
            "--out-dir",
            str(blank_out),
            "--review",
            str(draft / "review_record.json"),
        ],
    )
    assert result.exit_code != 0
    assert "empty reason" in result.output
    assert not blank_out.exists()

    admission = tmp_path / "admission.json"
    _write(admission, {"schema": "evidence-bundler-admission-v1", "decisions": []})
    mixed_out = tmp_path / "mixed"
    result = CliRunner().invoke(
        cli,
        [
            "run",
            str(contract_path),
            "--out-dir",
            str(mixed_out),
            "--admission",
            str(admission),
            "--review",
            str(draft / "review_record.json"),
        ],
    )
    assert result.exit_code != 0
    assert "mixed review inputs" in result.output
    assert not mixed_out.exists()


def test_header_and_table_context_stays_outside_the_passage_span(tmp_path: Path) -> None:
    heading = "# Subject ceiling"
    source = (
        f"{heading}\n\n"
        "| subject | unit | ceiling |\n"
        "| --- | --- | --- |\n"
        "| alpha | meter | 12 |\n"
    )
    claim = "alpha meter ceiling"
    contract_path = tmp_path / "contract_a.json"
    _write(
        contract_path,
        _contract(claim, [("table-note", "text/markdown; charset=utf-8", source)]),
    )
    out_dir = tmp_path / "out"
    _run(contract_path, out_dir)
    native = json.loads((out_dir / "native_eb_v1_package.json").read_text())
    for row in native["candidates"]:
        assert row["text"] == source[row["char_start"] : row["char_end"]]
    detached = [
        row
        for row in native["candidates"]
        if row["selection_state"] == "retained"
        and heading not in row["text"]
        and "|" in row["text"]
    ]
    assert detached, [row["text"] for row in native["candidates"]]
    context = (out_dir / "review_context.md").read_text(encoding="utf-8")
    assert "Display context (not admitted text):" in context
    assert heading in context
    for row in detached:
        assert heading not in row["text"]
        assert f"### Passage `{row['passage_id']}`" in context


def test_empty_sources_and_no_hits_explain_different_gaps(tmp_path: Path) -> None:
    empty_path = tmp_path / "empty.json"
    _write(empty_path, _contract("alpha ceiling", []))
    empty_out = tmp_path / "empty-out"
    _run(empty_path, empty_out)
    empty_context = (empty_out / "review_context.md").read_text(encoding="utf-8")
    assert f"Gap: {GAP_NO_SOURCES}" in empty_context

    miss_path = tmp_path / "miss.json"
    _write(
        miss_path,
        _contract(
            "alpha ceiling",
            [("other", "text/plain; charset=utf-8", "unrelated quartz orchard material")],
        ),
    )
    miss_out = tmp_path / "miss-out"
    _run(miss_path, miss_out)
    miss_context = (miss_out / "review_context.md").read_text(encoding="utf-8")
    assert f"Gap: {GAP_NO_NOMINATIONS}" in miss_context
    assert GAP_NO_SOURCES not in miss_context


def test_mechanical_admission_does_not_pretend_to_bind_a_snapshot(tmp_path: Path) -> None:
    root = "alpha beta gamma delta appears in the calibration note"
    source = "alpha beta gamma delta appears in the calibration note A."
    contract_path = tmp_path / "contract_a.json"
    _write(contract_path, _contract(root, [("note-a", "text/plain; charset=utf-8", source)]))
    draft = tmp_path / "draft"
    _run(contract_path, draft)
    template = json.loads((draft / "review_record.json").read_text())
    admission = {
        "schema": "evidence-bundler-admission-v1",
        "decisions": [
            {
                "proposition_id": row["proposition_id"],
                "passage_id": row["passage_id"],
                "decision": "accepted",
            }
            for row in template["decisions"]
        ],
    }
    admission_path = tmp_path / "admission.json"
    _write(admission_path, admission)
    out_dir = tmp_path / "mechanical"
    summary = _run(contract_path, out_dir, "--admission", str(admission_path))
    assert summary["review_binding"] == "mechanical_admission_unbound"
    assert not (out_dir / "review_record.json").exists()
    assert not (out_dir / "applied_review_record.json").exists()
    context = (out_dir / "review_context.md").read_text(encoding="utf-8")
    assert "does not bind the input file bytes" in context
    native = json.loads((out_dir / "native_eb_v1_package.json").read_text())
    assert any(row["admission_state"] == "accepted" for row in native["candidates"])


def test_gap_sentences_distinguish_not_run_retention_and_rejection() -> None:
    def package(execution: dict[str, Any], candidates: list[dict[str, Any]]) -> dict[str, Any]:
        return {
            "contract_a": {"sources": [{"source_id": "S", "content": "alpha"}]},
            "retrieval_plans": [{"proposition_id": "P", "retrieval_id": "R"}],
            "retrieval_executions": [execution],
            "candidates": candidates,
        }

    not_run = package(
        {"retrieval_id": "R", "status": "not_run", "searched_source_ids": [], "returned_count": 0},
        [],
    )
    assert gap_sentence(not_run, "P") == GAP_NOT_RUN
    nominated = package(
        {
            "retrieval_id": "R",
            "status": "completed",
            "searched_source_ids": ["S"],
            "returned_count": 1,
        },
        [
            {
                "proposition_id": "P",
                "selection_state": "not_retained",
                "admission_state": "not_applicable",
            }
        ],
    )
    assert gap_sentence(nominated, "P") == GAP_NOT_RETAINED
    rejected = package(
        {
            "retrieval_id": "R",
            "status": "completed",
            "searched_source_ids": ["S"],
            "returned_count": 1,
        },
        [{"proposition_id": "P", "selection_state": "retained", "admission_state": "rejected"}],
    )
    assert gap_sentence(rejected, "P") == GAP_NONE_ACCEPTED
    waiting = package(
        {
            "retrieval_id": "R",
            "status": "completed",
            "searched_source_ids": ["S"],
            "returned_count": 1,
        },
        [{"proposition_id": "P", "selection_state": "retained", "admission_state": "needs-review"}],
    )
    assert gap_sentence(waiting, "P") is None


def test_display_bridge_keeps_the_heading_when_the_body_is_long() -> None:
    heading = "# Subject ceiling"
    source = heading + "\n" + ("bridge " * 400) + "\n| subject | unit |\n| alpha | meter |\n"
    passage = "| alpha | meter |"
    start = source.rfind(passage)
    bridge, heading_at = display_bridge(source, start, start + len(passage))
    assert heading_at == 0
    assert bridge is not None
    assert bridge.startswith(heading)
    assert len(bridge) <= DISPLAY_LIMIT
    assert "..." in bridge
    assert bridge not in source[start : start + len(passage)]
