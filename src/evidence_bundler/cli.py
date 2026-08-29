"""Command-line interface for Evidence Bundler."""

from __future__ import annotations

from pathlib import Path

import click
from pydantic import ValidationError

from evidence_bundler import __version__
from evidence_bundler.contracts.hashing import compute_bundle_tree_hash
from evidence_bundler.contracts.intake import verify_intake
from evidence_bundler.contracts.writer import (
    BundleWriterError,
    build_fixture_bundle,
    build_retrieval_bundle,
)
from evidence_bundler.contracts.yaml_io import load_model_yaml, load_yaml
from evidence_bundler.ingest.dedup import IngestStateError, run_ingest
from evidence_bundler.ingest.loader import SourceDocumentLoadError
from evidence_bundler.models.cb import ClaimAuditUnit
from evidence_bundler.models.retrieval import EvidenceRole, RetrievalConfig
from evidence_bundler.models.review import ReviewAnnotation, ReviewAnnotationFile, ReviewDecision
from evidence_bundler.output.finalizer import FinalizeBundleError, finalize_bundle
from evidence_bundler.output.refiner import (
    ExcerptRefinerDriftError,
    ExcerptRefinerError,
    refine_excerpts,
    write_excerpt_refinement,
)
from evidence_bundler.reports.coverage import (
    CoverageReportError,
    build_coverage_report,
    write_coverage_report_json,
    write_coverage_report_markdown,
)
from evidence_bundler.review.annotator import (
    apply_decision,
    apply_decision_to_annotations,
    filter_annotations,
    summarize_review_annotations,
    update_notes,
)
from evidence_bundler.review.io import (
    ReviewAnnotationDriftError,
    load_review_annotations,
    scaffold_annotations_from_bundle,
    write_review_annotations,
)


@click.group()
@click.version_option(version=__version__, prog_name="evidence-bundler")
def cli() -> None:
    """Validate C-A artifacts, ingest sources, and build C-B bundles."""


REVIEW_DECISIONS = ("accepted", "rejected", "needs-review", "insufficient-excerpt")
EVIDENCE_ROLES = ("supporting", "contradicting", "conditional", "insufficient")


@cli.command("verify-intake")
@click.argument(
    "scaffold_run_dir",
    type=click.Path(exists=True, file_okay=False, dir_okay=True, path_type=Path),
)
@click.option(
    "--deviation-dir",
    type=click.Path(file_okay=False, dir_okay=True, path_type=Path),
    default=None,
    help="Optional directory for intake deviation records.",
)
def verify_intake_command(scaffold_run_dir: Path, deviation_dir: Path | None) -> None:
    """Verify a C-A scaffold-run directory before bundle production."""
    result = verify_intake(scaffold_run_dir, deviation_dir=deviation_dir)
    if result.valid:
        click.echo(f"Intake verified: {scaffold_run_dir}")
        return

    click.echo("Intake verification failed:", err=True)
    for error in result.errors:
        click.echo(f"- {error}", err=True)
    if result.deviation_path is not None:
        click.echo(f"Deviation written: {result.deviation_path}", err=True)
    raise click.ClickException("C-A intake failed")


@cli.command("build-fixture-bundle")
@click.argument(
    "scaffold_run_dir",
    type=click.Path(exists=True, file_okay=False, dir_okay=True, path_type=Path),
)
@click.option(
    "--output",
    "output_dir",
    required=True,
    type=click.Path(file_okay=False, dir_okay=True, path_type=Path),
    help="Output directory for the C-B fixture bundle tree.",
)
def build_fixture_bundle_command(scaffold_run_dir: Path, output_dir: Path) -> None:
    """Build a Phase 0 fixture-only C-B bundle from a valid C-A artifact."""
    try:
        result = build_fixture_bundle(scaffold_run_dir, output_dir)
    except BundleWriterError as exc:
        raise click.ClickException(str(exc)) from exc
    click.echo(f"Fixture bundle written: {result.bundle_dir}")
    click.echo(f"Bundle id: {result.manifest.bundle_id}")


@cli.command("build-bundle")
@click.argument(
    "scaffold_run_dir",
    type=click.Path(exists=True, file_okay=False, dir_okay=True, path_type=Path),
)
@click.option(
    "--output",
    "output_dir",
    required=True,
    type=click.Path(file_okay=False, dir_okay=True, path_type=Path),
    help="Output directory for the retrieval-derived C-B bundle tree.",
)
@click.option(
    "--config",
    "config_path",
    type=click.Path(exists=True, file_okay=True, dir_okay=False, path_type=Path),
    default=None,
    help="Optional retrieval config YAML. CLI flags override file values.",
)
@click.option(
    "--method",
    "retrieval_method",
    type=click.Choice(["bm25", "semantic", "hybrid"]),
    default=None,
    help="Retrieval method. BM25, semantic, and hybrid execute through the normal bundle path.",
)
@click.option(
    "--top-k",
    default=None,
    type=click.IntRange(min=1),
    help="Override number of parent candidate passages to keep per claim.",
)
@click.option(
    "--child-top-k",
    default=None,
    type=click.IntRange(min=1),
    help="Override BM25-only child/leaf candidate budget per claim.",
)
@click.option(
    "--semantic-child-top-k",
    default=None,
    type=click.IntRange(min=1),
    help="Override semantic child/leaf candidate budget for semantic and hybrid retrieval.",
)
@click.option(
    "--embedding-model",
    default=None,
    help="Override semantic embedding model name.",
)
@click.option(
    "--semantic-index-path",
    default=None,
    type=click.Path(file_okay=False, dir_okay=True, path_type=Path),
    help="Override C-A-specific semantic index directory.",
)
@click.option(
    "--embedding-model-cache-dir",
    default=None,
    type=click.Path(file_okay=False, dir_okay=True, path_type=Path),
    help="Override SentenceTransformer model cache directory.",
)
@click.option(
    "--report-out",
    type=click.Path(file_okay=True, dir_okay=False, path_type=Path),
    default=None,
    help="Optional Markdown retrieval run report path outside the sealed bundle.",
)
def build_bundle_command(
    scaffold_run_dir: Path,
    output_dir: Path,
    config_path: Path | None,
    retrieval_method: str | None,
    top_k: int | None,
    child_top_k: int | None,
    semantic_child_top_k: int | None,
    embedding_model: str | None,
    semantic_index_path: Path | None,
    embedding_model_cache_dir: Path | None,
    report_out: Path | None,
) -> None:
    """Build a retrieval-derived C-B bundle."""
    try:
        config = _load_retrieval_config(
            config_path,
            retrieval_method=retrieval_method,
            top_k=top_k,
            child_top_k=child_top_k,
            semantic_child_top_k=semantic_child_top_k,
            embedding_model=embedding_model,
            semantic_index_path=semantic_index_path,
            embedding_model_cache_dir=embedding_model_cache_dir,
        )
    except (ValueError, ValidationError) as exc:
        raise click.ClickException(str(exc)) from exc
    try:
        result = build_retrieval_bundle(
            scaffold_run_dir,
            output_dir,
            config=config,
            report_out=report_out,
        )
    except BundleWriterError as exc:
        raise click.ClickException(str(exc)) from exc
    click.echo(f"Bundle written: {result.bundle_dir}")
    click.echo(f"Bundle id: {result.manifest.bundle_id}")
    if result.retrieval_report is not None:
        no_candidate_count = len(result.retrieval_report.no_candidate_claim_ids)
        click.echo(f"Claims included: {result.retrieval_report.claims_included}")
        click.echo(f"No-candidate claims: {no_candidate_count}")
        if result.retrieval_report.retrieval_config.contradiction_enabled:
            no_countercandidate_count = len(
                result.retrieval_report.no_countercandidate_claim_ids
            )
            click.echo(f"No counter-candidate claims: {no_countercandidate_count}")
    if report_out is not None:
        click.echo(f"Retrieval report written: {report_out}")


def _load_retrieval_config(config_path: Path | None, **overrides: object) -> RetrievalConfig:
    data = load_yaml(config_path) if config_path is not None else {}
    data.update({key: value for key, value in overrides.items() if value is not None})
    return RetrievalConfig.model_validate(data)


@cli.group("review")
def review_group() -> None:
    """Create and update review annotation sidecars for draft bundles."""


@review_group.command("init")
@click.argument(
    "draft_bundle_dir",
    type=click.Path(exists=True, file_okay=False, dir_okay=True, path_type=Path),
)
@click.option(
    "--output",
    "annotation_path",
    required=True,
    type=click.Path(file_okay=True, dir_okay=False, path_type=Path),
    help="Sidecar review_annotations.yaml path outside the sealed draft bundle.",
)
@click.option("--reviewer", default=None, help="Optional reviewer label to record.")
@click.option(
    "--force",
    is_flag=True,
    help="Re-scaffold and fully replace an existing annotation file.",
)
def review_init_command(
    draft_bundle_dir: Path,
    annotation_path: Path,
    reviewer: str | None,
    force: bool,
) -> None:
    """Scaffold review_annotations.yaml for a draft retrieval bundle."""
    _assert_sidecar_path_outside_bundle(draft_bundle_dir, annotation_path, "Review annotations")
    existed_before = annotation_path.exists()
    if existed_before and not force:
        raise click.ClickException(
            f"Annotation file already exists: {annotation_path}. Use --force to replace it."
        )

    before_hash = compute_bundle_tree_hash(draft_bundle_dir)
    try:
        annotation_file = scaffold_annotations_from_bundle(draft_bundle_dir)
    except (ValueError, ValidationError) as exc:
        raise click.ClickException(str(exc)) from exc
    if reviewer is not None:
        annotation_file = annotation_file.model_copy(update={"reviewer": reviewer})
    write_review_annotations(annotation_file, annotation_path)
    _assert_draft_hash_unchanged(draft_bundle_dir, before_hash)

    action = "replaced" if force and existed_before else "written"
    click.echo(f"Review annotations {action}: {annotation_path}")
    click.echo(f"Annotations scaffolded: {len(annotation_file.annotations)}")


@review_group.command("batch")
@click.argument(
    "draft_bundle_dir",
    type=click.Path(exists=True, file_okay=False, dir_okay=True, path_type=Path),
)
@click.option(
    "--annotations",
    "annotation_path",
    required=True,
    type=click.Path(exists=True, file_okay=True, dir_okay=False, path_type=Path),
    help="Existing review_annotations.yaml sidecar outside the sealed draft bundle.",
)
@click.option(
    "--decision",
    required=True,
    type=click.Choice(REVIEW_DECISIONS),
    help="Decision to apply to matching annotation rows.",
)
@click.option("--role", type=click.Choice(EVIDENCE_ROLES), default=None)
@click.option("--claim-id", default=None, help="Only update annotations for this claim id.")
@click.option("--source-id", default=None, help="Only update annotations for this source id.")
@click.option(
    "--sample",
    type=click.IntRange(min=1),
    default=None,
    help="Deterministically update the first N matching annotations.",
)
@click.option("--notes", default=None, help="Optional notes to write on each updated row.")
@click.option("--dry-run", is_flag=True, help="Preview matching rows without writing.")
def review_batch_command(
    draft_bundle_dir: Path,
    annotation_path: Path,
    decision: ReviewDecision,
    role: EvidenceRole | None,
    claim_id: str | None,
    source_id: str | None,
    sample: int | None,
    notes: str | None,
    dry_run: bool,
) -> None:
    """Apply one review decision to a filtered batch of annotations."""
    _assert_sidecar_path_outside_bundle(draft_bundle_dir, annotation_path, "Review annotations")
    before_hash = compute_bundle_tree_hash(draft_bundle_dir)
    try:
        annotation_file = load_review_annotations(annotation_path, draft_bundle_dir)
    except (ReviewAnnotationDriftError, ValueError, ValidationError) as exc:
        raise click.ClickException(str(exc)) from exc

    updated_file, count = apply_decision_to_annotations(
        annotation_file,
        decision=decision,
        role=role,
        claim_id=claim_id,
        source_id=source_id,
        sample=sample,
        notes=notes,
    )
    if dry_run:
        _assert_draft_hash_unchanged(draft_bundle_dir, before_hash)
        click.echo(f"Dry run: {count} annotation(s) would be updated to {decision}.")
        return

    if count == 0:
        _assert_draft_hash_unchanged(draft_bundle_dir, before_hash)
        click.echo("No matching annotations found; no changes written.")
        return

    write_review_annotations(updated_file, annotation_path)
    _assert_draft_hash_unchanged(draft_bundle_dir, before_hash)
    click.echo(f"Updated {count} annotation(s): {annotation_path}")
    _echo_review_summary(updated_file)


@review_group.command("walkthrough")
@click.argument(
    "draft_bundle_dir",
    type=click.Path(exists=True, file_okay=False, dir_okay=True, path_type=Path),
)
@click.option(
    "--annotations",
    "annotation_path",
    required=True,
    type=click.Path(exists=True, file_okay=True, dir_okay=False, path_type=Path),
    help="Existing review_annotations.yaml sidecar outside the sealed draft bundle.",
)
@click.option("--role", type=click.Choice(EVIDENCE_ROLES), default=None)
@click.option("--claim-id", default=None, help="Only walk annotations for this claim id.")
@click.option("--source-id", default=None, help="Only walk annotations for this source id.")
def review_walkthrough_command(
    draft_bundle_dir: Path,
    annotation_path: Path,
    role: EvidenceRole | None,
    claim_id: str | None,
    source_id: str | None,
) -> None:
    """Walk through matching annotations one candidate at a time."""
    _assert_sidecar_path_outside_bundle(draft_bundle_dir, annotation_path, "Review annotations")
    before_hash = compute_bundle_tree_hash(draft_bundle_dir)
    try:
        annotation_file = load_review_annotations(annotation_path, draft_bundle_dir)
    except (ReviewAnnotationDriftError, ValueError, ValidationError) as exc:
        raise click.ClickException(str(exc)) from exc

    indexes = filter_annotations(
        annotation_file.annotations,
        role=role,
        claim_id=claim_id,
        source_id=source_id,
    )
    if not indexes:
        _assert_draft_hash_unchanged(draft_bundle_dir, before_hash)
        click.echo("No matching annotations found.")
        return

    annotations = list(annotation_file.annotations)
    claim_cache: dict[str, ClaimAuditUnit] = {}
    changes = 0
    for position, index in enumerate(indexes, start=1):
        annotation = annotations[index]
        _echo_annotation_for_review(
            draft_bundle_dir,
            claim_cache,
            annotation,
            position=position,
            total=len(indexes),
        )
        while True:
            raw_command = click.prompt(
                "Command [accept/reject/needs-review/insufficient-excerpt/note/skip/quit]",
                default="skip",
                show_default=True,
            )
            command = raw_command.strip().lower()
            decision = _decision_from_walkthrough_command(command)
            if command in {"skip", "s"}:
                break
            if command in {"quit", "q"}:
                indexes = []
                break
            if command == "note":
                notes = click.prompt("Note", default="", show_default=False)
                annotations[index] = update_notes(annotation, notes=notes)
                changes += 1
                break
            if decision is None:
                click.echo("Unknown command.")
                continue
            annotations[index] = apply_decision(annotation, decision=decision)
            changes += 1
            break
        if not indexes:
            break

    if changes == 0:
        _assert_draft_hash_unchanged(draft_bundle_dir, before_hash)
        click.echo("No changes written.")
        return

    updated_file = annotation_file.model_copy(update={"annotations": annotations})
    write_review_annotations(updated_file, annotation_path)
    _assert_draft_hash_unchanged(draft_bundle_dir, before_hash)
    click.echo(f"Walkthrough updated {changes} annotation(s): {annotation_path}")
    _echo_review_summary(updated_file)


@cli.command("refine-excerpts")
@click.argument(
    "draft_bundle_dir",
    type=click.Path(exists=True, file_okay=False, dir_okay=True, path_type=Path),
)
@click.option(
    "--annotations",
    "annotation_path",
    required=True,
    type=click.Path(exists=True, file_okay=True, dir_okay=False, path_type=Path),
    help="Existing review_annotations.yaml sidecar outside the sealed draft bundle.",
)
@click.option(
    "--output",
    "refinement_path",
    required=True,
    type=click.Path(file_okay=True, dir_okay=False, path_type=Path),
    help="excerpt_refinement.yaml transformation-log path outside the sealed draft bundle.",
)
@click.option(
    "--force",
    is_flag=True,
    help="Fully replace an existing excerpt refinement sidecar after drift checks pass.",
)
def refine_excerpts_command(
    draft_bundle_dir: Path,
    annotation_path: Path,
    refinement_path: Path,
    force: bool,
) -> None:
    """Write ADR-011's narrow excerpt-refinement transformation log."""
    _assert_sidecar_path_outside_bundle(draft_bundle_dir, annotation_path, "Review annotations")
    _assert_sidecar_path_outside_bundle(draft_bundle_dir, refinement_path, "Excerpt refinement")
    existed_before = refinement_path.exists()
    if existed_before and not force:
        raise click.ClickException(
            f"Excerpt refinement file already exists: {refinement_path}. "
            "Use --force to replace it."
        )

    before_draft_hash = compute_bundle_tree_hash(draft_bundle_dir)
    before_annotations = annotation_path.read_text(encoding="utf-8")
    try:
        refinement_file, summary = refine_excerpts(draft_bundle_dir, annotation_path)
    except (ExcerptRefinerError, ReviewAnnotationDriftError, ValueError, ValidationError) as exc:
        raise click.ClickException(str(exc)) from exc

    write_excerpt_refinement(refinement_file, refinement_path)
    _assert_draft_hash_unchanged(draft_bundle_dir, before_draft_hash)
    if annotation_path.read_text(encoding="utf-8") != before_annotations:
        raise click.ClickException("Review annotations changed while writing excerpt refinement.")

    action = "replaced" if force and existed_before else "written"
    click.echo(f"Excerpt refinement {action}: {refinement_path}")
    click.echo(f"Candidates considered: {summary.candidates}")
    click.echo(f"Clusters written: {summary.clusters}")
    click.echo(f"Cluster members: {summary.members}")
    click.echo(f"Collapsed members: {summary.collapsed_members}")
    click.echo(f"Decision conflicts: {summary.decision_conflicts}")


@cli.command("finalize-bundle")
@click.argument(
    "draft_bundle_dir",
    type=click.Path(exists=True, file_okay=False, dir_okay=True, path_type=Path),
)
@click.option(
    "--annotations",
    "annotation_path",
    required=True,
    type=click.Path(exists=True, file_okay=True, dir_okay=False, path_type=Path),
    help="Existing review_annotations.yaml sidecar outside the sealed draft bundle.",
)
@click.option(
    "--refinement",
    "refinement_path",
    required=True,
    type=click.Path(exists=True, file_okay=True, dir_okay=False, path_type=Path),
    help="Existing excerpt_refinement.yaml sidecar outside the sealed draft bundle.",
)
@click.option(
    "--output",
    "output_dir",
    required=True,
    type=click.Path(file_okay=False, dir_okay=True, path_type=Path),
    help="Output directory for the final reviewed C-B bundle.",
)
@click.option(
    "--provenance-output",
    "provenance_path",
    type=click.Path(file_okay=True, dir_okay=False, path_type=Path),
    default=None,
    help="Optional finalize_provenance.yaml sidecar path outside sealed bundles.",
)
def finalize_bundle_command(
    draft_bundle_dir: Path,
    annotation_path: Path,
    refinement_path: Path,
    output_dir: Path,
    provenance_path: Path | None,
) -> None:
    """Finalize a reviewed C-B bundle from draft, annotation, and refinement sidecars."""
    try:
        result = finalize_bundle(
            draft_bundle_dir,
            annotation_path,
            refinement_path,
            output_dir,
            provenance_path=provenance_path,
        )
    except (
        ExcerptRefinerDriftError,
        ExcerptRefinerError,
        FinalizeBundleError,
        ReviewAnnotationDriftError,
        ValueError,
        ValidationError,
    ) as exc:
        raise click.ClickException(str(exc)) from exc

    click.echo(f"Final bundle written: {result.bundle_dir}")
    click.echo(f"Bundle id: {result.manifest.bundle_id}")
    click.echo(f"Finalize provenance written: {result.provenance_path}")
    click.echo(f"Reviewer sign-off required: {result.manifest.reviewer_sign_off.required}")


@cli.command("coverage-report")
@click.argument(
    "draft_bundle_dir",
    type=click.Path(exists=True, file_okay=False, dir_okay=True, path_type=Path),
)
@click.option(
    "--annotations",
    "annotation_path",
    required=True,
    type=click.Path(exists=True, file_okay=True, dir_okay=False, path_type=Path),
    help="Existing review_annotations.yaml sidecar outside the sealed draft bundle.",
)
@click.option(
    "--refinement",
    "refinement_path",
    required=True,
    type=click.Path(exists=True, file_okay=True, dir_okay=False, path_type=Path),
    help="Existing excerpt_refinement.yaml sidecar outside the sealed draft bundle.",
)
@click.option(
    "--final-bundle",
    "final_bundle_dir",
    required=True,
    type=click.Path(exists=True, file_okay=False, dir_okay=True, path_type=Path),
    help="Final reviewed C-B bundle directory.",
)
@click.option(
    "--provenance",
    "provenance_path",
    required=True,
    type=click.Path(exists=True, file_okay=True, dir_okay=False, path_type=Path),
    help="Finalize provenance sidecar written by finalize-bundle.",
)
@click.option(
    "--markdown-out",
    "markdown_out",
    required=True,
    type=click.Path(file_okay=True, dir_okay=False, path_type=Path),
    help="Markdown coverage report path outside sealed bundles.",
)
@click.option(
    "--json-out",
    "json_out",
    required=True,
    type=click.Path(file_okay=True, dir_okay=False, path_type=Path),
    help="JSON coverage report path outside sealed bundles.",
)
def coverage_report_command(
    draft_bundle_dir: Path,
    annotation_path: Path,
    refinement_path: Path,
    final_bundle_dir: Path,
    provenance_path: Path,
    markdown_out: Path,
    json_out: Path,
) -> None:
    """Write read-only review coverage reports for a finalized bundle."""
    _assert_report_output_path(
        markdown_out,
        draft_bundle_dir=draft_bundle_dir,
        final_bundle_dir=final_bundle_dir,
        input_paths=[annotation_path, refinement_path, provenance_path, json_out],
        artifact_label="Markdown coverage report",
    )
    _assert_report_output_path(
        json_out,
        draft_bundle_dir=draft_bundle_dir,
        final_bundle_dir=final_bundle_dir,
        input_paths=[annotation_path, refinement_path, provenance_path, markdown_out],
        artifact_label="JSON coverage report",
    )
    try:
        report = build_coverage_report(
            draft_bundle_dir,
            annotation_path,
            refinement_path,
            final_bundle_dir,
            provenance_path,
        )
    except (
        CoverageReportError,
        ExcerptRefinerDriftError,
        ReviewAnnotationDriftError,
        ValueError,
        ValidationError,
    ) as exc:
        raise click.ClickException(str(exc)) from exc

    write_coverage_report_markdown(report, markdown_out)
    write_coverage_report_json(report, json_out)
    click.echo(f"Coverage Markdown written: {markdown_out}")
    click.echo(f"Coverage JSON written: {json_out}")
    click.echo(f"Coverage inconsistencies: {len(report.inconsistencies)}")


def _assert_sidecar_path_outside_bundle(
    draft_bundle_dir: Path,
    sidecar_path: Path,
    artifact_label: str,
) -> None:
    draft_root = draft_bundle_dir.resolve()
    target = sidecar_path.resolve(strict=False)
    if target == draft_root or target.is_relative_to(draft_root):
        raise click.ClickException(
            f"{artifact_label} must be written outside the sealed draft bundle."
        )


def _assert_report_output_path(
    output_path: Path,
    *,
    draft_bundle_dir: Path,
    final_bundle_dir: Path,
    input_paths: list[Path],
    artifact_label: str,
) -> None:
    output = output_path.resolve(strict=False)
    for bundle_dir, label in (
        (draft_bundle_dir.resolve(), "draft bundle"),
        (final_bundle_dir.resolve(), "final bundle"),
    ):
        if output == bundle_dir or output.is_relative_to(bundle_dir):
            raise click.ClickException(
                f"{artifact_label} must be written outside the sealed {label}."
            )
    for input_path in input_paths:
        if output == input_path.resolve(strict=False):
            raise click.ClickException(f"{artifact_label} must not overwrite an input artifact.")


def _assert_draft_hash_unchanged(draft_bundle_dir: Path, before_hash: str) -> None:
    after_hash = compute_bundle_tree_hash(draft_bundle_dir)
    if after_hash != before_hash:
        raise click.ClickException("Draft bundle changed while writing review annotations.")


def _echo_review_summary(annotation_file: ReviewAnnotationFile) -> None:
    summary = summarize_review_annotations(annotation_file)
    click.echo(f"Annotations total: {summary.total}")
    for decision in REVIEW_DECISIONS:
        click.echo(f"{decision}: {summary.by_decision.get(decision, 0)}")


def _echo_annotation_for_review(
    draft_bundle_dir: Path,
    claim_cache: dict[str, ClaimAuditUnit],
    annotation: ReviewAnnotation,
    *,
    position: int,
    total: int,
) -> None:
    click.echo("")
    click.echo(f"Candidate {position}/{total}")
    click.echo(f"Claim: {annotation.claim_id}")
    click.echo(f"Role: {annotation.evidence_role}")
    click.echo(f"Source: {annotation.source_id}")
    click.echo(f"Passage: {annotation.passage_id}")
    click.echo(f"Current decision: {annotation.decision}")
    click.echo(f"Notes: {annotation.reviewer_notes or ''}")
    click.echo("Passage text:")
    click.echo(_passage_text_for_annotation(draft_bundle_dir, claim_cache, annotation))


def _passage_text_for_annotation(
    draft_bundle_dir: Path,
    claim_cache: dict[str, ClaimAuditUnit],
    annotation: ReviewAnnotation,
) -> str:
    claim = claim_cache.get(annotation.claim_id)
    if claim is None:
        claim = load_model_yaml(
            ClaimAuditUnit,
            draft_bundle_dir / "claims" / f"{annotation.claim_id}.yaml",
        )
        claim_cache[annotation.claim_id] = claim
    passages = claim.evidence_passages + claim.counterevidence_passages
    for passage in passages:
        if (
            passage.source_id == annotation.source_id
            and passage.passage_id == annotation.passage_id
        ):
            return passage.passage_text
    return "[passage text unavailable]"


def _decision_from_walkthrough_command(command: str) -> ReviewDecision | None:
    if command in {"accept", "accepted", "a"}:
        return "accepted"
    if command in {"reject", "rejected", "r"}:
        return "rejected"
    if command in {"needs-review", "needs", "n"}:
        return "needs-review"
    if command in {"insufficient-excerpt", "insufficient", "i"}:
        return "insufficient-excerpt"
    return None


@cli.command("ingest")
@click.argument(
    "scaffold_run_dir",
    type=click.Path(exists=True, file_okay=False, dir_okay=True, path_type=Path),
)
@click.option(
    "--dry-run/--write-state",
    default=True,
    show_default=True,
    help="Report ingest outcomes without writing state, or persist incremental state.",
)
@click.option(
    "--state-path",
    type=click.Path(file_okay=True, dir_okay=False, path_type=Path),
    default=None,
    help="Optional JSON state file for incremental ingest decisions.",
)
@click.option(
    "--report-out",
    type=click.Path(file_okay=True, dir_okay=False, path_type=Path),
    default=None,
    help="Optional Markdown report path.",
)
def ingest_command(
    scaffold_run_dir: Path,
    dry_run: bool,
    state_path: Path | None,
    report_out: Path | None,
) -> None:
    """Run loader and chunker with per-source incremental dedup."""
    try:
        report = run_ingest(
            scaffold_run_dir,
            state_path=state_path,
            dry_run=dry_run,
            report_out=report_out,
        )
    except (IngestStateError, SourceDocumentLoadError) as exc:
        raise click.ClickException(str(exc)) from exc

    action = "dry run" if report.dry_run else "state update"
    click.echo(f"Ingest {action} complete: {report.scaffold_run_dir}")
    click.echo(f"Documents loaded: {report.documents_loaded}")
    click.echo(f"Documents chunked: {report.documents_chunked}")
    click.echo(f"Documents skipped: {report.documents_skipped}")
    click.echo(f"Documents removed: {report.documents_removed}")
    click.echo(f"Chunks emitted: {report.chunks_emitted}")
    if report_out is not None:
        click.echo(f"Report written: {report_out}")


if __name__ == "__main__":
    cli()
