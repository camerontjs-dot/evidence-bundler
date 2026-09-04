"""CLI command tests."""

from __future__ import annotations

import json
from collections.abc import Sequence
from pathlib import Path

import pytest
from click.testing import CliRunner

from evidence_bundler.cli import cli
from evidence_bundler.contracts.hashing import compute_bundle_tree_hash
from evidence_bundler.contracts.writer import build_retrieval_bundle, validate_bundle_tree
from evidence_bundler.contracts.yaml_io import dump_yaml, load_model_yaml
from evidence_bundler.models.cb import BundleManifest
from evidence_bundler.models.refinement import ExcerptRefinementFile
from evidence_bundler.models.retrieval import RetrievalConfig
from evidence_bundler.output.finalizer import (
    FinalizeProvenanceFile,
    compute_excerpt_refinement_hash,
)
from evidence_bundler.review import (
    apply_decision_to_annotations,
    compute_review_annotations_hash,
    load_review_annotations,
    write_review_annotations,
)


def test_verify_intake_cli_success(scaffold_run_tmp: Path) -> None:
    result = CliRunner().invoke(cli, ["verify-intake", str(scaffold_run_tmp)])

    assert result.exit_code == 0
    assert "Intake verified" in result.output


def test_verify_intake_cli_failure_writes_deviation(scaffold_run_tmp: Path) -> None:
    content_path = scaffold_run_tmp / "corpus" / "src-001" / "content.md"
    tampered_content = content_path.read_text(encoding="utf-8") + "\nTampered.\n"
    content_path.write_text(tampered_content, encoding="utf-8")

    result = CliRunner().invoke(cli, ["verify-intake", str(scaffold_run_tmp)])

    assert result.exit_code != 0
    assert "Intake verification failed" in result.output
    assert (scaffold_run_tmp / "deviations").exists()


def test_build_fixture_bundle_cli_success(scaffold_run_tmp: Path, tmp_path: Path) -> None:
    output_dir = tmp_path / "evidence-bundle-fixture"
    result = CliRunner().invoke(
        cli,
        ["build-fixture-bundle", str(scaffold_run_tmp), "--output", str(output_dir)],
    )

    assert result.exit_code == 0
    assert "Fixture bundle written" in result.output
    assert (output_dir / "bundle_manifest.yaml").exists()


def test_ingest_cli_dry_run_success(mixed_scaffold_run_tmp: Path, tmp_path: Path) -> None:
    state_path = tmp_path / "ingest-state.json"
    result = CliRunner().invoke(
        cli,
        ["ingest", str(mixed_scaffold_run_tmp), "--dry-run", "--state-path", str(state_path)],
    )

    assert result.exit_code == 0
    assert "Ingest dry run complete" in result.output
    assert "Documents loaded: 4" in result.output
    assert "Chunks emitted:" in result.output
    assert not state_path.exists()


def test_ingest_cli_report_out_success(mixed_scaffold_run_tmp: Path, tmp_path: Path) -> None:
    report_path = tmp_path / "ingest-report.md"
    result = CliRunner().invoke(
        cli,
        [
            "ingest",
            str(mixed_scaffold_run_tmp),
            "--dry-run",
            "--state-path",
            str(tmp_path / "ingest-state.json"),
            "--report-out",
            str(report_path),
        ],
    )

    assert result.exit_code == 0
    assert "Report written" in result.output
    assert report_path.exists()
    assert "# Ingest Report" in report_path.read_text(encoding="utf-8")


def test_ingest_cli_write_state_skips_unchanged_rerun(
    mixed_scaffold_run_tmp: Path,
    tmp_path: Path,
) -> None:
    state_path = tmp_path / "ingest-state.json"
    runner = CliRunner()

    first = runner.invoke(
        cli,
        ["ingest", str(mixed_scaffold_run_tmp), "--write-state", "--state-path", str(state_path)],
    )
    second = runner.invoke(
        cli,
        ["ingest", str(mixed_scaffold_run_tmp), "--write-state", "--state-path", str(state_path)],
    )

    assert first.exit_code == 0
    assert second.exit_code == 0
    assert "Documents skipped: 4" in second.output
    assert "Chunks emitted: 0" in second.output


def test_build_bundle_cli_success(mixed_scaffold_run_tmp: Path, tmp_path: Path) -> None:
    runner = CliRunner()
    output_dir = tmp_path / "evidence-bundle-retrieval"
    report_path = tmp_path / "retrieval-report.md"

    result = runner.invoke(
        cli,
        [
            "build-bundle",
            str(mixed_scaffold_run_tmp),
            "--output",
            str(output_dir),
            "--top-k",
            "1",
            "--child-top-k",
            "5",
            "--report-out",
            str(report_path),
        ],
    )

    assert result.exit_code == 0
    assert "Bundle written:" in result.output
    assert "Claims included: 3" in result.output
    assert (output_dir / "bundle_manifest.yaml").exists()
    assert report_path.exists()


def test_build_bundle_cli_method_bm25_success(
    mixed_scaffold_run_tmp: Path,
    tmp_path: Path,
) -> None:
    output_dir = tmp_path / "evidence-bundle-retrieval"
    result = CliRunner().invoke(
        cli,
        [
            "build-bundle",
            str(mixed_scaffold_run_tmp),
            "--output",
            str(output_dir),
            "--method",
            "bm25",
        ],
    )

    assert result.exit_code == 0
    assert "Bundle written:" in result.output
    assert (output_dir / "bundle_manifest.yaml").exists()


def test_build_bundle_cli_config_loads_and_overrides(
    mixed_scaffold_run_tmp: Path,
    tmp_path: Path,
) -> None:
    config_path = tmp_path / "retrieval-config.yaml"
    report_path = tmp_path / "retrieval-report.md"
    output_dir = tmp_path / "evidence-bundle-retrieval"
    dump_yaml(
        {
            "retrieval_method": "bm25",
            "top_k": 3,
            "child_top_k": 4,
            "semantic_child_top_k": 8,
        },
        config_path,
    )

    result = CliRunner().invoke(
        cli,
        [
            "build-bundle",
            str(mixed_scaffold_run_tmp),
            "--config",
            str(config_path),
            "--output",
            str(output_dir),
            "--top-k",
            "1",
            "--report-out",
            str(report_path),
        ],
    )

    report = report_path.read_text(encoding="utf-8")
    assert result.exit_code == 0
    assert "- Parent top-k: `1`" in report
    assert "- Child top-k: `4`" in report


def test_build_bundle_cli_method_hybrid_success(
    mixed_scaffold_run_tmp: Path,
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(
        "evidence_bundler.contracts.writer.load_embedding_model",
        lambda *_args, **_kwargs: FakeEmbedder(),
    )
    output_dir = tmp_path / "evidence-bundle-hybrid"
    report_path = tmp_path / "hybrid-report.md"
    result = CliRunner().invoke(
        cli,
        [
            "build-bundle",
            str(mixed_scaffold_run_tmp),
            "--output",
            str(output_dir),
            "--method",
            "hybrid",
            "--embedding-model",
            "fake-semantic-model",
            "--report-out",
            str(report_path),
        ],
    )

    assert result.exit_code == 0
    assert "Bundle written:" in result.output
    assert (output_dir / "bundle_manifest.yaml").exists()
    assert "- Retrieval method: `hybrid`" in report_path.read_text(encoding="utf-8")


def test_build_bundle_cli_config_enables_hybrid_rerank(
    mixed_scaffold_run_tmp: Path,
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(
        "evidence_bundler.contracts.writer.load_embedding_model",
        lambda *_args, **_kwargs: FakeEmbedder(),
    )
    monkeypatch.setattr(
        "evidence_bundler.contracts.writer.load_reranker_model",
        lambda *_args, **_kwargs: FakeCrossEncoder(),
    )
    config_path = tmp_path / "retrieval-config.yaml"
    report_path = tmp_path / "hybrid-rerank-report.md"
    output_dir = tmp_path / "evidence-bundle-hybrid-rerank"
    dump_yaml(
        {
            "retrieval_method": "hybrid",
            "embedding_model": "fake-semantic-model",
            "top_k": 1,
            "rrf_candidate_pool": 5,
            "rerank_enabled": True,
            "rerank_model": "fake-reranker",
            "rerank_top_n": 3,
        },
        config_path,
    )

    result = CliRunner().invoke(
        cli,
        [
            "build-bundle",
            str(mixed_scaffold_run_tmp),
            "--config",
            str(config_path),
            "--output",
            str(output_dir),
            "--report-out",
            str(report_path),
        ],
    )

    report = report_path.read_text(encoding="utf-8")
    assert result.exit_code == 0
    assert "Bundle written:" in result.output
    assert "- Rerank enabled: `True`" in report
    assert "- Rerank model: `fake-reranker`" in report


def test_build_bundle_cli_semantic_method_executes_end_to_end(
    mixed_scaffold_run_tmp: Path,
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    class CliFakeEmbedder:
        def encode(self, texts: list[str], **_kwargs: object) -> list[list[float]]:
            return [[1.0, 0.0, 0.0] for _ in texts]

    monkeypatch.setattr(
        "evidence_bundler.contracts.writer.load_embedding_model",
        lambda *_args, **_kwargs: CliFakeEmbedder(),
    )
    output_dir = tmp_path / "evidence-bundle-semantic"
    report_path = tmp_path / "semantic-report.md"
    result = CliRunner().invoke(
        cli,
        [
            "build-bundle",
            str(mixed_scaffold_run_tmp),
            "--output",
            str(output_dir),
            "--report-out",
            str(report_path),
            "--method",
            "semantic",
        ],
    )

    assert result.exit_code == 0
    assert "Bundle written:" in result.output
    assert output_dir.exists()
    assert "- Retrieval method: `semantic`" in report_path.read_text(encoding="utf-8")


def test_review_init_cli_writes_sidecar_outside_draft_bundle(
    mixed_scaffold_run_tmp: Path,
    tmp_path: Path,
) -> None:
    draft_bundle_dir = _build_bm25_draft_bundle(mixed_scaffold_run_tmp, tmp_path)
    annotation_path = tmp_path / "review_annotations.yaml"

    result = CliRunner().invoke(
        cli,
        [
            "review",
            "init",
            str(draft_bundle_dir),
            "--output",
            str(annotation_path),
            "--reviewer",
            "qa-reviewer",
        ],
    )

    loaded = load_review_annotations(annotation_path, draft_bundle_dir)
    assert result.exit_code == 0
    assert "Review annotations written:" in result.output
    assert annotation_path.exists()
    assert loaded.reviewer == "qa-reviewer"
    assert len(loaded.annotations) > 0
    assert all(annotation.decision == "needs-review" for annotation in loaded.annotations)


def test_review_init_cli_refuses_output_inside_draft_bundle(
    mixed_scaffold_run_tmp: Path,
    tmp_path: Path,
) -> None:
    draft_bundle_dir = _build_bm25_draft_bundle(mixed_scaffold_run_tmp, tmp_path)
    annotation_path = draft_bundle_dir / "review_annotations.yaml"

    result = CliRunner().invoke(
        cli,
        ["review", "init", str(draft_bundle_dir), "--output", str(annotation_path)],
    )

    assert result.exit_code != 0
    assert "outside the sealed draft bundle" in result.output
    assert not annotation_path.exists()


def test_review_init_cli_existing_file_requires_force_and_force_replaces(
    mixed_scaffold_run_tmp: Path,
    tmp_path: Path,
) -> None:
    draft_bundle_dir = _build_bm25_draft_bundle(mixed_scaffold_run_tmp, tmp_path)
    annotation_path = tmp_path / "review_annotations.yaml"
    runner = CliRunner()
    runner.invoke(cli, ["review", "init", str(draft_bundle_dir), "--output", str(annotation_path)])
    annotations = load_review_annotations(annotation_path, draft_bundle_dir)
    accepted, _count = apply_decision_to_annotations(
        annotations,
        decision="accepted",
        sample=1,
        decided_at_utc="2026-05-13T01:02:03Z",
    )
    write_review_annotations(accepted, annotation_path)

    without_force = runner.invoke(
        cli,
        ["review", "init", str(draft_bundle_dir), "--output", str(annotation_path)],
    )
    with_force = runner.invoke(
        cli,
        ["review", "init", str(draft_bundle_dir), "--output", str(annotation_path), "--force"],
    )
    replaced = load_review_annotations(annotation_path, draft_bundle_dir)

    assert without_force.exit_code != 0
    assert "Use --force to replace it" in without_force.output
    assert with_force.exit_code == 0
    assert "Review annotations replaced:" in with_force.output
    assert all(annotation.decision == "needs-review" for annotation in replaced.annotations)
    assert all(annotation.decided_at_utc is None for annotation in replaced.annotations)


def test_review_batch_cli_dry_run_does_not_write(
    mixed_scaffold_run_tmp: Path,
    tmp_path: Path,
) -> None:
    draft_bundle_dir, annotation_path = _init_review_annotations(
        mixed_scaffold_run_tmp,
        tmp_path,
    )
    before = annotation_path.read_text(encoding="utf-8")

    result = CliRunner().invoke(
        cli,
        [
            "review",
            "batch",
            str(draft_bundle_dir),
            "--annotations",
            str(annotation_path),
            "--decision",
            "accepted",
            "--sample",
            "1",
            "--dry-run",
        ],
    )

    assert result.exit_code == 0
    assert "Dry run: 1 annotation(s) would be updated to accepted." in result.output
    assert annotation_path.read_text(encoding="utf-8") == before


def test_review_batch_cli_updates_filtered_rows_and_preserves_draft_hash(
    mixed_scaffold_run_tmp: Path,
    tmp_path: Path,
) -> None:
    draft_bundle_dir, annotation_path = _init_review_annotations(
        mixed_scaffold_run_tmp,
        tmp_path,
    )
    draft_hash_before = compute_bundle_tree_hash(draft_bundle_dir)

    result = CliRunner().invoke(
        cli,
        [
            "review",
            "batch",
            str(draft_bundle_dir),
            "--annotations",
            str(annotation_path),
            "--decision",
            "accepted",
            "--role",
            "supporting",
            "--sample",
            "1",
            "--notes",
            "candidate reviewed",
        ],
    )

    loaded = load_review_annotations(annotation_path, draft_bundle_dir)
    accepted = [
        annotation for annotation in loaded.annotations if annotation.decision == "accepted"
    ]
    assert result.exit_code == 0
    assert "Updated 1 annotation(s)" in result.output
    assert len(accepted) == 1
    assert accepted[0].decided_at_utc is not None
    assert accepted[0].reviewer_notes == "candidate reviewed"
    assert compute_bundle_tree_hash(draft_bundle_dir) == draft_hash_before


def test_review_walkthrough_cli_accept_note_skip_and_quit(
    mixed_scaffold_run_tmp: Path,
    tmp_path: Path,
) -> None:
    draft_bundle_dir, annotation_path = _init_review_annotations(
        mixed_scaffold_run_tmp,
        tmp_path,
    )

    result = CliRunner().invoke(
        cli,
        [
            "review",
            "walkthrough",
            str(draft_bundle_dir),
            "--annotations",
            str(annotation_path),
        ],
        input="accept\nnote\ndeferred - compare adjacent claim\nskip\nquit\n",
    )

    loaded = load_review_annotations(annotation_path, draft_bundle_dir)
    assert result.exit_code == 0
    assert "Candidate 1/" in result.output
    assert "Walkthrough updated 2 annotation(s)" in result.output
    assert loaded.annotations[0].decision == "accepted"
    assert loaded.annotations[0].decided_at_utc is not None
    assert loaded.annotations[1].decision == "needs-review"
    assert loaded.annotations[1].reviewer_notes == "deferred - compare adjacent claim"
    assert loaded.annotations[1].decided_at_utc is None
    assert loaded.annotations[2].decision == "needs-review"
    assert loaded.annotations[2].reviewer_notes is None
    assert loaded.annotations[2].decided_at_utc is None


def test_review_batch_cli_surfaces_drift_and_does_not_write(
    mixed_scaffold_run_tmp: Path,
    tmp_path: Path,
) -> None:
    draft_bundle_dir, annotation_path = _init_review_annotations(
        mixed_scaffold_run_tmp,
        tmp_path,
    )
    before = annotation_path.read_text(encoding="utf-8")
    claim_path = next((draft_bundle_dir / "claims").glob("*.yaml"))
    claim_path.write_text(
        claim_path.read_text(encoding="utf-8") + "\n# drift\n",
        encoding="utf-8",
    )

    result = CliRunner().invoke(
        cli,
        [
            "review",
            "batch",
            str(draft_bundle_dir),
            "--annotations",
            str(annotation_path),
            "--decision",
            "accepted",
            "--sample",
            "1",
        ],
    )

    assert result.exit_code != 0
    assert "bundle-hash mismatch" in result.output
    assert annotation_path.read_text(encoding="utf-8") == before


def test_refine_excerpts_cli_writes_sidecar_and_preserves_inputs(
    mixed_scaffold_run_tmp: Path,
    tmp_path: Path,
) -> None:
    draft_bundle_dir, annotation_path = _init_review_annotations(
        mixed_scaffold_run_tmp,
        tmp_path,
    )
    refinement_path = tmp_path / "excerpt_refinement.yaml"
    draft_hash_before = compute_bundle_tree_hash(draft_bundle_dir)
    annotations_before = annotation_path.read_text(encoding="utf-8")

    result = CliRunner().invoke(
        cli,
        [
            "refine-excerpts",
            str(draft_bundle_dir),
            "--annotations",
            str(annotation_path),
            "--output",
            str(refinement_path),
        ],
    )

    refinement = load_model_yaml(ExcerptRefinementFile, refinement_path)
    assert result.exit_code == 0
    assert "Excerpt refinement written:" in result.output
    assert "Candidates considered:" in result.output
    assert refinement.draft_bundle_id
    assert compute_bundle_tree_hash(draft_bundle_dir) == draft_hash_before
    assert annotation_path.read_text(encoding="utf-8") == annotations_before


def test_refine_excerpts_cli_refuses_output_inside_draft_bundle(
    mixed_scaffold_run_tmp: Path,
    tmp_path: Path,
) -> None:
    draft_bundle_dir, annotation_path = _init_review_annotations(
        mixed_scaffold_run_tmp,
        tmp_path,
    )
    refinement_path = draft_bundle_dir / "excerpt_refinement.yaml"

    result = CliRunner().invoke(
        cli,
        [
            "refine-excerpts",
            str(draft_bundle_dir),
            "--annotations",
            str(annotation_path),
            "--output",
            str(refinement_path),
        ],
    )

    assert result.exit_code != 0
    assert "outside the sealed draft bundle" in result.output
    assert not refinement_path.exists()


def test_refine_excerpts_cli_existing_file_requires_force_and_force_replaces(
    mixed_scaffold_run_tmp: Path,
    tmp_path: Path,
) -> None:
    draft_bundle_dir, annotation_path = _init_review_annotations(
        mixed_scaffold_run_tmp,
        tmp_path,
    )
    refinement_path = tmp_path / "excerpt_refinement.yaml"
    refinement_path.write_text("placeholder: true\n", encoding="utf-8")
    runner = CliRunner()

    without_force = runner.invoke(
        cli,
        [
            "refine-excerpts",
            str(draft_bundle_dir),
            "--annotations",
            str(annotation_path),
            "--output",
            str(refinement_path),
        ],
    )
    with_force = runner.invoke(
        cli,
        [
            "refine-excerpts",
            str(draft_bundle_dir),
            "--annotations",
            str(annotation_path),
            "--output",
            str(refinement_path),
            "--force",
        ],
    )

    assert without_force.exit_code != 0
    assert "Use --force to replace it" in without_force.output
    assert with_force.exit_code == 0
    assert "Excerpt refinement replaced:" in with_force.output
    load_model_yaml(ExcerptRefinementFile, refinement_path)


def test_finalize_bundle_cli_writes_final_bundle_and_provenance(
    mixed_scaffold_run_tmp: Path,
    tmp_path: Path,
) -> None:
    draft_bundle_dir, annotation_path = _init_review_annotations(
        mixed_scaffold_run_tmp,
        tmp_path,
    )
    refinement_path = tmp_path / "excerpt_refinement.yaml"
    final_bundle_dir = tmp_path / "final-bundle"
    result_refine = CliRunner().invoke(
        cli,
        [
            "refine-excerpts",
            str(draft_bundle_dir),
            "--annotations",
            str(annotation_path),
            "--output",
            str(refinement_path),
        ],
    )

    result = CliRunner().invoke(
        cli,
        [
            "finalize-bundle",
            str(draft_bundle_dir),
            "--annotations",
            str(annotation_path),
            "--refinement",
            str(refinement_path),
            "--output",
            str(final_bundle_dir),
        ],
    )

    provenance_path = tmp_path / "final-bundle_finalize_provenance.yaml"
    manifest = load_model_yaml(BundleManifest, final_bundle_dir / "bundle_manifest.yaml")
    provenance = load_model_yaml(FinalizeProvenanceFile, provenance_path)
    assert result_refine.exit_code == 0
    assert result.exit_code == 0
    assert "Final bundle written:" in result.output
    assert "Finalize provenance written:" in result.output
    assert validate_bundle_tree(final_bundle_dir) == []
    assert manifest.reviewer_sign_off.required is True
    assert provenance.annotation_hash == compute_review_annotations_hash(annotation_path)
    assert provenance.refinement_hash == compute_excerpt_refinement_hash(refinement_path)
    assert provenance.final_bundle_id == manifest.bundle_id
    assert not (final_bundle_dir / "finalize_provenance.yaml").exists()


def test_finalize_bundle_cli_rejects_output_inside_draft_bundle(
    mixed_scaffold_run_tmp: Path,
    tmp_path: Path,
) -> None:
    draft_bundle_dir, annotation_path = _init_review_annotations(
        mixed_scaffold_run_tmp,
        tmp_path,
    )
    refinement_path = tmp_path / "excerpt_refinement.yaml"
    refine_result = CliRunner().invoke(
        cli,
        [
            "refine-excerpts",
            str(draft_bundle_dir),
            "--annotations",
            str(annotation_path),
            "--output",
            str(refinement_path),
        ],
    )
    final_bundle_dir = draft_bundle_dir / "final-bundle"

    result = CliRunner().invoke(
        cli,
        [
            "finalize-bundle",
            str(draft_bundle_dir),
            "--annotations",
            str(annotation_path),
            "--refinement",
            str(refinement_path),
            "--output",
            str(final_bundle_dir),
        ],
    )

    assert refine_result.exit_code == 0
    assert result.exit_code != 0
    assert "outside the sealed draft bundle" in result.output
    assert not final_bundle_dir.exists()


def test_finalize_bundle_cli_rejects_non_empty_output(
    mixed_scaffold_run_tmp: Path,
    tmp_path: Path,
) -> None:
    draft_bundle_dir, annotation_path = _init_review_annotations(
        mixed_scaffold_run_tmp,
        tmp_path,
    )
    refinement_path = tmp_path / "excerpt_refinement.yaml"
    final_bundle_dir = tmp_path / "final-bundle"
    final_bundle_dir.mkdir()
    (final_bundle_dir / "placeholder.txt").write_text("occupied\n", encoding="utf-8")
    refine_result = CliRunner().invoke(
        cli,
        [
            "refine-excerpts",
            str(draft_bundle_dir),
            "--annotations",
            str(annotation_path),
            "--output",
            str(refinement_path),
        ],
    )

    result = CliRunner().invoke(
        cli,
        [
            "finalize-bundle",
            str(draft_bundle_dir),
            "--annotations",
            str(annotation_path),
            "--refinement",
            str(refinement_path),
            "--output",
            str(final_bundle_dir),
        ],
    )

    assert refine_result.exit_code == 0
    assert result.exit_code != 0
    assert "Output directory is not empty" in result.output
    assert (final_bundle_dir / "placeholder.txt").exists()


def test_finalize_bundle_cli_rejects_annotations_from_different_draft(
    mixed_scaffold_run_tmp: Path,
    tmp_path: Path,
) -> None:
    first_draft_dir, first_annotation_path = _init_review_annotations(
        mixed_scaffold_run_tmp,
        tmp_path / "first",
        top_k=1,
    )
    second_draft_dir, second_annotation_path = _init_review_annotations(
        mixed_scaffold_run_tmp,
        tmp_path / "second",
    )
    del first_draft_dir
    refinement_path = tmp_path / "second" / "excerpt_refinement.yaml"
    final_bundle_dir = tmp_path / "final-bundle"
    refine_result = CliRunner().invoke(
        cli,
        [
            "refine-excerpts",
            str(second_draft_dir),
            "--annotations",
            str(second_annotation_path),
            "--output",
            str(refinement_path),
        ],
    )

    result = CliRunner().invoke(
        cli,
        [
            "finalize-bundle",
            str(second_draft_dir),
            "--annotations",
            str(first_annotation_path),
            "--refinement",
            str(refinement_path),
            "--output",
            str(final_bundle_dir),
        ],
    )

    assert refine_result.exit_code == 0
    assert result.exit_code != 0
    assert "draft bundle-id mismatch" in result.output
    assert not final_bundle_dir.exists()


def test_coverage_report_cli_writes_markdown_and_json(
    mixed_scaffold_run_tmp: Path,
    tmp_path: Path,
) -> None:
    draft_bundle_dir, annotation_path, refinement_path, final_bundle_dir, provenance_path = (
        _finalize_for_coverage_cli(mixed_scaffold_run_tmp, tmp_path)
    )
    markdown_path = tmp_path / "coverage.md"
    json_path = tmp_path / "coverage.json"

    result = CliRunner().invoke(
        cli,
        [
            "coverage-report",
            str(draft_bundle_dir),
            "--annotations",
            str(annotation_path),
            "--refinement",
            str(refinement_path),
            "--final-bundle",
            str(final_bundle_dir),
            "--provenance",
            str(provenance_path),
            "--markdown-out",
            str(markdown_path),
            "--json-out",
            str(json_path),
        ],
    )

    payload = json.loads(json_path.read_text(encoding="utf-8"))
    markdown = markdown_path.read_text(encoding="utf-8")
    assert result.exit_code == 0
    assert "Coverage Markdown written:" in result.output
    assert "Coverage JSON written:" in result.output
    assert payload["anchors"]["final_bundle_id"]
    assert "No counterevidence-candidate claims" in markdown
    assert "Candidate passages are review nominations, not support determinations" in markdown


def test_coverage_report_cli_rejects_outputs_inside_bundles_and_input_overwrite(
    mixed_scaffold_run_tmp: Path,
    tmp_path: Path,
) -> None:
    draft_bundle_dir, annotation_path, refinement_path, final_bundle_dir, provenance_path = (
        _finalize_for_coverage_cli(mixed_scaffold_run_tmp, tmp_path)
    )

    inside_bundle = CliRunner().invoke(
        cli,
        [
            "coverage-report",
            str(draft_bundle_dir),
            "--annotations",
            str(annotation_path),
            "--refinement",
            str(refinement_path),
            "--final-bundle",
            str(final_bundle_dir),
            "--provenance",
            str(provenance_path),
            "--markdown-out",
            str(draft_bundle_dir / "coverage.md"),
            "--json-out",
            str(tmp_path / "coverage.json"),
        ],
    )
    overwrite_input = CliRunner().invoke(
        cli,
        [
            "coverage-report",
            str(draft_bundle_dir),
            "--annotations",
            str(annotation_path),
            "--refinement",
            str(refinement_path),
            "--final-bundle",
            str(final_bundle_dir),
            "--provenance",
            str(provenance_path),
            "--markdown-out",
            str(annotation_path),
            "--json-out",
            str(tmp_path / "coverage.json"),
        ],
    )

    assert inside_bundle.exit_code != 0
    assert "outside the sealed draft bundle" in inside_bundle.output
    assert overwrite_input.exit_code != 0
    assert "must not overwrite an input artifact" in overwrite_input.output


class FakeEmbedder:
    """Deterministic fake embedding model for CLI hybrid tests."""

    def encode(self, texts: Sequence[str], **_kwargs: object) -> list[list[float]]:
        return [_vector_for(text) for text in texts]


def _vector_for(text: str) -> list[float]:
    lowered = text.lower()
    if "submission checklist" in lowered or "audit review" in lowered:
        return [1.0, 0.0, 0.0]
    if "line breaks" in lowered or "plain text" in lowered:
        return [0.0, 1.0, 0.0]
    if "pdf" in lowered or "extraction" in lowered:
        return [0.0, 0.0, 1.0]
    return [0.1, 0.1, 0.1]


class FakeCrossEncoder:
    """Deterministic fake reranker for CLI hybrid+rerank tests."""

    def predict(self, pairs: Sequence[tuple[str, str]], **_kwargs: object) -> list[float]:
        return [1.0 for _pair in pairs]


def _build_bm25_draft_bundle(
    scaffold_run_dir: Path,
    tmp_path: Path,
    *,
    top_k: int = 3,
) -> Path:
    draft_bundle_dir = tmp_path / "phase-3-unit2-draft"
    build_retrieval_bundle(
        scaffold_run_dir,
        draft_bundle_dir,
        config=RetrievalConfig(top_k=top_k, child_top_k=10),
    )
    return draft_bundle_dir


def _init_review_annotations(
    scaffold_run_dir: Path,
    tmp_path: Path,
    *,
    top_k: int = 3,
) -> tuple[Path, Path]:
    draft_bundle_dir = _build_bm25_draft_bundle(scaffold_run_dir, tmp_path, top_k=top_k)
    annotation_path = tmp_path / "review_annotations.yaml"
    result = CliRunner().invoke(
        cli,
        ["review", "init", str(draft_bundle_dir), "--output", str(annotation_path)],
    )
    assert result.exit_code == 0
    return draft_bundle_dir, annotation_path


def _finalize_for_coverage_cli(
    scaffold_run_dir: Path,
    tmp_path: Path,
) -> tuple[Path, Path, Path, Path, Path]:
    draft_bundle_dir, annotation_path = _init_review_annotations(scaffold_run_dir, tmp_path)
    refinement_path = tmp_path / "excerpt_refinement.yaml"
    final_bundle_dir = tmp_path / "final-bundle"
    runner = CliRunner()
    refine_result = runner.invoke(
        cli,
        [
            "refine-excerpts",
            str(draft_bundle_dir),
            "--annotations",
            str(annotation_path),
            "--output",
            str(refinement_path),
        ],
    )
    finalize_result = runner.invoke(
        cli,
        [
            "finalize-bundle",
            str(draft_bundle_dir),
            "--annotations",
            str(annotation_path),
            "--refinement",
            str(refinement_path),
            "--output",
            str(final_bundle_dir),
        ],
    )
    assert refine_result.exit_code == 0
    assert finalize_result.exit_code == 0
    return (
        draft_bundle_dir,
        annotation_path,
        refinement_path,
        final_bundle_dir,
        tmp_path / "final-bundle_finalize_provenance.yaml",
    )
