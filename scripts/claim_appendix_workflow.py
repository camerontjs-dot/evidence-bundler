"""Shared helpers for the claim verification appendix workflow scripts."""

from __future__ import annotations

import argparse
import json
import os
import re
import shutil
import subprocess
import sys
import time
import unicodedata
import urllib.error
import urllib.parse
import urllib.request
from collections import Counter, defaultdict
from dataclasses import asdict, dataclass
from datetime import UTC, datetime
from html.parser import HTMLParser
from pathlib import Path
from typing import Any

from pdfminer.high_level import extract_text

from evidence_bundler.contracts.discovery import resolve_claim_audit_lab_root
from evidence_bundler.contracts.hashing import (
    compute_corpus_hash,
    hash_file,
    hash_text,
    sha256_hexdigest,
    write_sha256sums,
)
from evidence_bundler.contracts.yaml_io import dump_yaml, load_yaml
from evidence_bundler.models.common import CONTRACT_VERSION
from evidence_bundler.review.annotator import apply_decision, summarize_review_annotations
from evidence_bundler.review.io import load_review_annotations, write_review_annotations

REPO_ROOT = Path(__file__).resolve().parents[1]
MAINFRAME_PROJECTS_ROOT = REPO_ROOT.parents[1]

DEFAULT_OUTPUT_ROOT = REPO_ROOT / "build" / "claim-verification-appendix-workflow"
EVIDENCE_BUNDLER_CLI = REPO_ROOT / ".venv" / "bin" / "evidence-bundler"


APPENDIX_LABELS = (
    "EXTRACTED CLAIM",
    "CLAIM TYPE",
    "SOURCE CITED BY SITE",
    "VERIFICATION STATUS",
    "VERIFIED EVIDENCE",
    "PRIMARY SOURCE URL",
    "EPISTEMOLOGICAL GAP",
)

ALIGNMENT_POSITIVE = {"supported", "partially_supported"}
ALIGNMENT_NEGATIVE = {"needs_source", "unsupported", "overstated"}


@dataclass(frozen=True)
class AppendixClaimRecord:
    """One normalized claim parsed from the PDF appendix."""

    claim_number: int
    claim_id: str
    source_name: str
    source_site_url: str
    source_domain_or_sector: str
    claim_text: str
    appendix_claim_type: str
    source_cited_by_site: str
    appendix_verification_status: str
    verified_evidence: str
    primary_source_url: str
    epistemological_gap: str
    source_id: str


@dataclass(frozen=True)
class SourceAcquisitionRecord:
    """One unique primary-source URL acquisition result."""

    source_id: str
    primary_source_url: str
    normalized_url: str
    tier: str
    content_type: str | None
    content_path: str | None
    sha256: str | None
    extracted_text_chars: int
    retrieved_at_utc: str
    retrieved_for_claim_ids: list[str]
    duplicate_claim_numbers: list[int]
    failure_reason: str | None
    title: str | None


@dataclass(frozen=True)
class WorkflowPaths:
    """Filesystem paths for one workflow run."""

    root: Path
    claims_json: Path
    source_records_json: Path
    sources_dir: Path
    scaffold: Path
    retrieval_config: Path
    draft: Path
    retrieval_report: Path
    blind_annotations: Path
    blind_refinement: Path
    blind_final: Path
    blind_provenance: Path
    blind_coverage_md: Path
    blind_coverage_json: Path
    blind_cal_dir: Path
    blind_comparison_md: Path
    blind_comparison_json: Path
    guided_annotations: Path
    guided_refinement: Path
    guided_final: Path
    guided_provenance: Path
    guided_coverage_md: Path
    guided_coverage_json: Path
    guided_cal_dir: Path
    guided_comparison_md: Path
    guided_comparison_json: Path
    workflow_summary_md: Path
    workflow_summary_json: Path

    @classmethod
    def from_root(cls, root: Path) -> WorkflowPaths:
        return cls(
            root=root,
            claims_json=root / "appendix_claims.json",
            source_records_json=root / "source_records.json",
            sources_dir=root / "sources",
            scaffold=root / "scaffold-run-claim-verification-appendix",
            retrieval_config=root / "retrieval-config.yaml",
            draft=root / "draft-bundle",
            retrieval_report=root / "retrieval-report.md",
            blind_annotations=root / "blind_review_annotations.yaml",
            blind_refinement=root / "blind_excerpt_refinement.yaml",
            blind_final=root / "blind-final-bundle",
            blind_provenance=root / "blind-final-bundle_finalize_provenance.yaml",
            blind_coverage_md=root / "blind_coverage_report.md",
            blind_coverage_json=root / "blind_coverage_report.json",
            blind_cal_dir=root / "blind-cal-audited",
            blind_comparison_md=root / "blind_comparison.md",
            blind_comparison_json=root / "blind_comparison.json",
            guided_annotations=root / "guided_review_annotations.yaml",
            guided_refinement=root / "guided_excerpt_refinement.yaml",
            guided_final=root / "guided-final-bundle",
            guided_provenance=root / "guided-final-bundle_finalize_provenance.yaml",
            guided_coverage_md=root / "guided_coverage_report.md",
            guided_coverage_json=root / "guided_coverage_report.json",
            guided_cal_dir=root / "guided-cal-audited",
            guided_comparison_md=root / "guided_comparison.md",
            guided_comparison_json=root / "guided_comparison.json",
            workflow_summary_md=root / "workflow_summary.md",
            workflow_summary_json=root / "workflow_summary.json",
        )

    def pass_paths(self, pass_name: str) -> dict[str, Path]:
        if pass_name == "blind":
            return {
                "annotations": self.blind_annotations,
                "refinement": self.blind_refinement,
                "final": self.blind_final,
                "provenance": self.blind_provenance,
                "coverage_md": self.blind_coverage_md,
                "coverage_json": self.blind_coverage_json,
                "cal_dir": self.blind_cal_dir,
                "comparison_md": self.blind_comparison_md,
                "comparison_json": self.blind_comparison_json,
            }
        if pass_name == "guided":
            return {
                "annotations": self.guided_annotations,
                "refinement": self.guided_refinement,
                "final": self.guided_final,
                "provenance": self.guided_provenance,
                "coverage_md": self.guided_coverage_md,
                "coverage_json": self.guided_coverage_json,
                "cal_dir": self.guided_cal_dir,
                "comparison_md": self.guided_comparison_md,
                "comparison_json": self.guided_comparison_json,
            }
        raise ValueError(f"Unknown pass name: {pass_name}")


def parse_appendix_pdf(pdf_path: Path) -> tuple[list[AppendixClaimRecord], dict[str, Any]]:
    """Parse the PDF appendix into 30 deduplicated claim records."""
    text = extract_text(str(pdf_path))
    blocks = _numbered_blocks(text)
    if len(blocks) != 30:
        raise SystemExit(f"Expected 30 numbered appendix blocks, found {len(blocks)}")

    records: list[AppendixClaimRecord] = []
    duplicate_field_sets = 0
    for block in blocks:
        duplicate_field_sets += max(0, _field_set_count(block) - 1)
        records.append(_parse_block(block))

    deduped = _dedupe_records(records)
    if len(deduped) != 30:
        raise SystemExit(f"Expected 30 unique appendix claims, found {len(deduped)}")

    report = {
        "schema_version": "claim-appendix-parse-report-v1",
        "pdf_path": str(pdf_path),
        "parsed_at_utc": utc_now(),
        "numbered_blocks": len(blocks),
        "unique_claims": len(deduped),
        "duplicate_field_sets_detected": duplicate_field_sets,
        "source_count": len({record.primary_source_url for record in deduped}),
        "claims_by_source_name": dict(Counter(record.source_name for record in deduped)),
    }
    return deduped, report


def write_parse_outputs(
    records: list[AppendixClaimRecord],
    report: dict[str, Any],
    *,
    claims_out: Path,
    report_json_out: Path,
    report_md_out: Path,
) -> None:
    """Write parser artifacts."""
    write_json([asdict(record) for record in records], claims_out)
    write_json(report, report_json_out)
    report_md_out.parent.mkdir(parents=True, exist_ok=True)
    report_md_out.write_text(render_parse_report(report), encoding="utf-8")


def render_parse_report(report: dict[str, Any]) -> str:
    """Render a compact Markdown parser report."""
    source_lines = [
        f"- {source}: `{count}`"
        for source, count in sorted(report["claims_by_source_name"].items())
    ]
    return "\n".join(
        [
            "# Claim Verification Appendix Parse Report",
            "",
            f"- PDF path: `{report['pdf_path']}`",
            f"- Parsed at UTC: `{report['parsed_at_utc']}`",
            f"- Numbered blocks: `{report['numbered_blocks']}`",
            f"- Unique claims: `{report['unique_claims']}`",
            f"- Duplicate field sets detected: `{report['duplicate_field_sets_detected']}`",
            f"- Unique primary-source URLs: `{report['source_count']}`",
            "",
            "## Claims By Source",
            "",
            *source_lines,
            "",
        ]
    )


def acquire_sources(
    claims: list[AppendixClaimRecord],
    *,
    sources_dir: Path,
    timeout_seconds: int = 45,
    url_overrides: dict[str, str] | None = None,
) -> tuple[list[SourceAcquisitionRecord], dict[str, Any]]:
    """Fetch unique primary-source URLs and classify source availability."""
    url_overrides = url_overrides or {}
    sources_dir.mkdir(parents=True, exist_ok=True)
    by_url: dict[str, list[AppendixClaimRecord]] = defaultdict(list)
    for claim in claims:
        by_url[claim.primary_source_url].append(claim)

    records: list[SourceAcquisitionRecord] = []
    for rank, (raw_url, grouped_claims) in enumerate(sorted(by_url.items()), start=1):
        source_id = grouped_claims[0].source_id
        override_url = url_overrides.get(raw_url)
        normalized_url = normalize_url(override_url or raw_url)
        ambiguous_reason = classify_ambiguous_url(raw_url, normalized_url, override_url)
        if ambiguous_reason is not None:
            records.append(
                _source_record(
                    source_id=source_id,
                    raw_url=raw_url,
                    normalized_url=normalized_url,
                    grouped_claims=grouped_claims,
                    tier="ambiguous_url",
                    retrieved_at_utc=utc_now(),
                    failure_reason=ambiguous_reason,
                )
            )
            continue

        started = time.monotonic()
        try:
            fetched = fetch_url(normalized_url, timeout_seconds=timeout_seconds)
        except (urllib.error.URLError, TimeoutError, OSError, ValueError) as exc:
            records.append(
                _source_record(
                    source_id=source_id,
                    raw_url=raw_url,
                    normalized_url=normalized_url,
                    grouped_claims=grouped_claims,
                    tier="unavailable",
                    retrieved_at_utc=utc_now(),
                    failure_reason=f"{type(exc).__name__}: {exc}",
                )
            )
            continue

        content_suffix = ".pdf" if fetched["kind"] == "pdf" else ".txt"
        source_dir = sources_dir / f"{rank:02d}-{source_id}"
        source_dir.mkdir(parents=True, exist_ok=True)
        content_path = source_dir / f"content{content_suffix}"
        if fetched["kind"] == "pdf":
            content_path.write_bytes(fetched["body"])
            extracted_text = extract_pdf_text_best_effort(content_path)
        else:
            content_path.write_text(str(fetched["text"]), encoding="utf-8")
            extracted_text = str(fetched["text"])

        extracted_len = len(extracted_text.strip())
        tier = source_tier_from_text(extracted_text, elapsed_seconds=time.monotonic() - started)
        records.append(
            _source_record(
                source_id=source_id,
                raw_url=raw_url,
                normalized_url=normalized_url,
                grouped_claims=grouped_claims,
                tier=tier,
                content_type=str(fetched["content_type"]),
                content_path=content_path,
                sha256=sha256_hexdigest(content_path.read_bytes()),
                extracted_text_chars=extracted_len,
                retrieved_at_utc=utc_now(),
                failure_reason=None if tier != "unavailable" else "No usable text extracted.",
                title=str(fetched.get("title") or "") or None,
            )
        )
    report = build_source_acquisition_report(records)
    return records, report


def write_acquisition_outputs(
    records: list[SourceAcquisitionRecord],
    report: dict[str, Any],
    *,
    records_out: Path,
    report_json_out: Path,
    report_md_out: Path,
) -> None:
    """Write acquisition artifacts."""
    write_json([asdict(record) for record in records], records_out)
    write_json(report, report_json_out)
    report_md_out.parent.mkdir(parents=True, exist_ok=True)
    report_md_out.write_text(render_source_acquisition_report(report, records), encoding="utf-8")


def build_scaffold(
    claims: list[AppendixClaimRecord],
    sources: list[SourceAcquisitionRecord],
    *,
    sources_dir: Path,
    scaffold_dir: Path,
) -> None:
    """Build a runtime C-A v1.0.0 scaffold-run from staged appendix inputs."""
    if scaffold_dir.exists():
        shutil.rmtree(scaffold_dir)
    corpus_dir = scaffold_dir / "corpus"
    corpus_dir.mkdir(parents=True)

    available_sources = {
        source.source_id: source
        for source in sources
        if source.tier in {"available_exact", "available_limited"} and source.content_path
    }
    run_id = "appendix-claim-verification-20260514"
    generated_at = utc_now()

    claims_payload = {
        "schema_version": CONTRACT_VERSION,
        "run_id": run_id,
        "generated_at_utc": generated_at,
        "claims": [
            _ca_claim_payload(claim, available_sources)
            for claim in sorted(claims, key=lambda item: item.claim_number)
        ],
    }
    dump_yaml(claims_payload, scaffold_dir / "claims.yaml")
    (scaffold_dir / "CONTRACT_VERSION").write_text(f"{CONTRACT_VERSION}\n", encoding="utf-8")

    source_rank = 0
    for source in sorted(available_sources.values(), key=lambda item: item.source_id):
        source_rank += 1
        source_dir = corpus_dir / source.source_id
        source_dir.mkdir(parents=True)
        staged_path = Path(source.content_path or "")
        suffix = staged_path.suffix if staged_path.suffix in {".pdf", ".txt", ".md"} else ".txt"
        content_path = source_dir / f"content{suffix}"
        shutil.copy2(staged_path, content_path)
        source_claims = [claim for claim in claims if claim.source_id == source.source_id]
        source_text = _read_content_text(content_path)
        dump_yaml(
            _ca_source_metadata(source, content_path, source_claims, source_rank),
            source_dir / "metadata.yaml",
        )
        dump_yaml(
            _ca_source_passages(source.source_id, source_text, source_claims),
            source_dir / "passages.yaml",
        )

    scaffold_run = {
        "run_id": run_id,
        "task_id": "claim-verification-appendix-real-workflow",
        "workflow_condition": "full_scaffold",
        "timestamp_utc": generated_at,
        "scaffold": {
            "version": "manual-appendix-parser-v1",
            "prompt_template_id": "manual-claim-verification-appendix",
            "prompt_template_hash": hash_text("manual-claim-verification-appendix"),
            "config_hash": hash_text(
                json.dumps([asdict(claim) for claim in claims], sort_keys=True)
            ),
        },
        "model": {
            "model_id": "manual-appendix-extraction",
            "model_version": "2026-05-14",
            "api_endpoint": "local-file",
            "temperature": 0.0,
            "max_tokens": 1,
        },
        "task": {
            "research_question": (
                "Can the Bundler to CAL workflow audit AI-generated regulated-industry "
                "website claims against the appendix primary-source corpus?"
            ),
            "domain": "regulated_industries",
            "expert_checkable": True,
            "ground_truth_ref": "claim_verification_appendix.pdf",
        },
        "corpus": {
            "total_sources": len(available_sources),
            "corpus_hash": compute_corpus_hash(corpus_dir),
            "retrieval_strategy": "appendix_primary_source_urls",
            "retrieval_timestamp_utc": generated_at,
        },
        "intermediates_present": False,
        "run_metadata": {
            "operator": "cameron",
            "environment": "local-dev",
            "notes": (
                "Runtime scaffold generated from the claim verification appendix. Appendix "
                "statuses remain in sidecar JSON and are not written into C-A support_status."
            ),
        },
    }
    dump_yaml(scaffold_run, scaffold_dir / "scaffold_run.yaml")
    write_sha256sums(scaffold_dir)


def run_workflow(
    paths: WorkflowPaths,
    *,
    claim_audit_cli: Path,
    cal_root: Path,
    force: bool = False,
) -> dict[str, Any]:
    """Run C-A -> Bundler -> blind/guided finalization -> CAL."""
    if force:
        _remove_workflow_outputs(paths)
    claims = load_claim_records(paths.claims_json)
    sources = load_source_records(paths.source_records_json)

    build_scaffold(claims, sources, sources_dir=paths.sources_dir, scaffold_dir=paths.scaffold)
    _write_retrieval_config(paths)
    run_command([EVIDENCE_BUNDLER_CLI, "verify-intake", paths.scaffold], cwd=REPO_ROOT)
    run_command(
        [
            EVIDENCE_BUNDLER_CLI,
            "build-bundle",
            paths.scaffold,
            "--config",
            paths.retrieval_config,
            "--output",
            paths.draft,
            "--report-out",
            paths.retrieval_report,
        ],
        cwd=REPO_ROOT,
    )

    pass_summaries = {}
    for pass_name in ("blind", "guided"):
        pass_summaries[pass_name] = _run_review_pass(
            pass_name,
            paths,
            claims=claims,
            sources=sources,
            claim_audit_cli=claim_audit_cli,
            cal_root=cal_root,
        )


    summary = {
        "schema_version": "claim-appendix-workflow-summary-v1",
        "generated_at_utc": utc_now(),
        "paths": {
            "root": rel(paths.root),
            "scaffold": rel(paths.scaffold),
            "draft_bundle": rel(paths.draft),
            "retrieval_report": rel(paths.retrieval_report),
            "blind_comparison": rel(paths.blind_comparison_md),
            "guided_comparison": rel(paths.guided_comparison_md),
        },
        "claim_count": len(claims),
        "source_record_count": len(sources),
        "source_tiers": dict(Counter(source.tier for source in sources)),
        "passes": pass_summaries,
    }
    write_json(summary, paths.workflow_summary_json)
    paths.workflow_summary_md.write_text(render_workflow_summary(summary), encoding="utf-8")
    return summary


def load_claim_records(path: Path) -> list[AppendixClaimRecord]:
    data = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(data, list):
        raise ValueError(f"Expected list of claim records: {path}")
    return [AppendixClaimRecord(**item) for item in data]


def load_source_records(path: Path) -> list[SourceAcquisitionRecord]:
    data = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(data, list):
        raise ValueError(f"Expected list of source records: {path}")
    return [SourceAcquisitionRecord(**item) for item in data]


def alignment_for(appendix_status: str, cal_verdict: str | None) -> str:
    """Return a coarse consistency label between appendix status and CAL verdict."""
    if cal_verdict is None:
        return "missing_cal_verdict"
    normalized_status = normalize_text(appendix_status).lower()
    if any(token in normalized_status for token in ("verified", "verifiable")) and not any(
        token in normalized_status for token in ("partially", "unverified")
    ):
        return "aligned" if cal_verdict in ALIGNMENT_POSITIVE else "diverged"
    if any(
        token in normalized_status
        for token in (
            "partially",
            "plausible",
            "broadly supported",
            "corroborated",
            "directionally supported",
            "supported by vendor",
        )
    ):
        return (
            "aligned"
            if cal_verdict in {"supported", "partially_supported", *ALIGNMENT_NEGATIVE}
            else "diverged"
        )
    if any(
        token in normalized_status
        for token in ("unverified", "speculative", "opinion-as-fact", "aspirational")
    ):
        return "aligned" if cal_verdict in ALIGNMENT_NEGATIVE else "diverged"
    return "uncategorized"


def normalize_url(url: str) -> str:
    """Normalize PDF line-wrap whitespace without guessing missing URL tails."""
    normalized = normalize_text(url).replace(" ", "")
    parsed = urllib.parse.urlparse(normalized)
    if parsed.scheme and parsed.netloc:
        return urllib.parse.urlunparse(parsed)
    return normalized


def classify_ambiguous_url(
    raw_url: str,
    normalized_url: str,
    override_url: str | None,
) -> str | None:
    """Return a reason when a URL should not be fetched without an explicit override."""
    if override_url:
        return None
    parsed = urllib.parse.urlparse(normalized_url)
    if parsed.scheme not in {"http", "https"} or not parsed.netloc:
        return "URL is not an absolute HTTP(S) URL."
    if parsed.path in {"", "/"}:
        return "Domain-level URL requires an explicit override before acquisition."
    lower = normalized_url.lower()
    known_truncated_endings = (
        "cost-of-qual",
        "5th-consecut",
        "productivity-innovation-and",
    )
    if any(lower.endswith(ending) for ending in known_truncated_endings):
        return "URL appears truncated in the PDF extraction; no silent repair applied."
    return None


def source_tier_from_text(text: str, *, elapsed_seconds: float) -> str:
    """Classify fetched content into the planned availability tiers."""
    stripped = normalize_text(text)
    if len(stripped) < 200:
        return "unavailable"
    limited_markers = (
        "access denied",
        "enable javascript",
        "subscribe",
        "forbidden",
        "checking your browser",
        "captcha",
        "not found",
    )
    lowered = stripped.lower()
    if len(stripped) < 1200 or any(marker in lowered for marker in limited_markers):
        return "available_limited"
    return "available_exact"


def write_json(data: Any, path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def run_command(command: list[object], *, cwd: Path) -> None:
    printable = " ".join(str(part) for part in command)
    print(f"$ {printable}")
    result = subprocess.run(
        [str(part) for part in command],
        cwd=cwd,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        check=False,
    )
    if result.stdout:
        print(result.stdout, end="" if result.stdout.endswith("\n") else "\n")
    if result.returncode != 0:
        raise SystemExit(result.returncode)


def utc_now() -> str:
    return datetime.now(UTC).strftime("%Y-%m-%dT%H:%M:%SZ")


def rel(path: Path) -> str:
    try:
        return path.resolve().relative_to(MAINFRAME_PROJECTS_ROOT.resolve()).as_posix()
    except ValueError:
        return str(path.resolve())



def normalize_text(value: str) -> str:
    normalized = unicodedata.normalize("NFKC", value)
    return " ".join(normalized.split())


def load_url_overrides(path: Path | None) -> dict[str, str]:
    if path is None:
        return {}
    data = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(data, dict) or not all(
        isinstance(key, str) and isinstance(value, str) for key, value in data.items()
    ):
        raise ValueError("URL override file must be a JSON object of string to string")
    return data


def add_common_output_arg(parser: argparse.ArgumentParser) -> None:
    parser.add_argument(
        "--output-root",
        type=Path,
        default=DEFAULT_OUTPUT_ROOT,
        help="Workflow output root.",
    )


def _numbered_blocks(text: str) -> list[str]:
    matches = list(re.finditer(r"(?:^|\f)#\d+\b[^\n]*", text, re.MULTILINE))
    starts = [match.start() + (1 if text[match.start()] == "\f" else 0) for match in matches]
    starts.append(len(text))
    return [text[starts[index] : starts[index + 1]] for index in range(len(starts) - 1)]


def _field_set_count(block: str) -> int:
    return block.count("EXTRACTED CLAIM")


def _parse_block(block: str) -> AppendixClaimRecord:
    lines = [line.strip() for line in block.splitlines() if line.strip()]
    if not lines:
        raise ValueError("Empty appendix block")
    heading = normalize_text(lines[0])
    heading_match = re.match(r"#(?P<number>\d+)\s+(?P<source>.+)", heading)
    if not heading_match:
        raise ValueError(f"Cannot parse appendix heading: {heading!r}")
    claim_number = int(heading_match.group("number"))
    source_name = heading_match.group("source")
    label_index = next(
        (index for index, line in enumerate(lines) if line == "EXTRACTED CLAIM"),
        None,
    )
    source_site_url = lines[1] if len(lines) > 1 and lines[1].startswith("http") else ""
    source_domain_or_sector = (
        lines[label_index - 1] if label_index is not None and label_index >= 3 else ""
    )
    fields = _extract_first_field_set(block)
    primary_url = normalize_url(fields["PRIMARY SOURCE URL"])
    return AppendixClaimRecord(
        claim_number=claim_number,
        claim_id=f"clm-appendix-{claim_number:03d}",
        source_name=source_name,
        source_site_url=source_site_url,
        source_domain_or_sector=source_domain_or_sector,
        claim_text=fields["EXTRACTED CLAIM"],
        appendix_claim_type=fields["CLAIM TYPE"],
        source_cited_by_site=fields["SOURCE CITED BY SITE"],
        appendix_verification_status=fields["VERIFICATION STATUS"],
        verified_evidence=fields["VERIFIED EVIDENCE"],
        primary_source_url=primary_url,
        epistemological_gap=fields["EPISTEMOLOGICAL GAP"],
        source_id=f"src-{sha256_hexdigest(primary_url.encode('utf-8'))[:12]}",
    )


def _extract_first_field_set(block: str) -> dict[str, str]:
    positions: list[tuple[str, int, int]] = []
    for label in APPENDIX_LABELS:
        match = re.search(rf"(?m)^[\f\s]*{re.escape(label)}\s*$", block)
        if match is None:
            raise ValueError(f"Missing appendix field label {label!r}")
        positions.append((label, match.start(), match.end()))

    fields: dict[str, str] = {}
    for index, (label, _start, end) in enumerate(positions):
        next_start = positions[index + 1][1] if index + 1 < len(positions) else len(block)
        raw_value = block[end:next_start]
        if label == "EPISTEMOLOGICAL GAP":
            duplicate_start = raw_value.find("\nEXTRACTED CLAIM")
            if duplicate_start >= 0:
                raw_value = raw_value[:duplicate_start]
            summary_start = raw_value.find("Verification Summary")
            if summary_start >= 0:
                raw_value = raw_value[:summary_start]
            source_url_start = re.search(r"\n\s*https?://", raw_value)
            if source_url_start is not None:
                raw_value = raw_value[: source_url_start.start()]
        fields[label] = normalize_text(raw_value)

    missing = [label for label in APPENDIX_LABELS if not fields.get(label)]
    if missing:
        raise ValueError(f"Empty appendix field(s): {', '.join(missing)}")
    return fields


def _dedupe_records(records: list[AppendixClaimRecord]) -> list[AppendixClaimRecord]:
    deduped: dict[tuple[int, str, str], AppendixClaimRecord] = {}
    for record in records:
        key = (
            record.claim_number,
            normalize_text(record.claim_text).lower(),
            record.primary_source_url.lower(),
        )
        deduped.setdefault(key, record)
    return sorted(deduped.values(), key=lambda item: item.claim_number)


def fetch_url(url: str, *, timeout_seconds: int) -> dict[str, object]:
    request = urllib.request.Request(
        url,
        headers={
            "User-Agent": (
                "Mozilla/5.0 claim-verification-workflow/0.1 "
                "(portfolio local reproducibility test)"
            )
        },
    )
    with urllib.request.urlopen(request, timeout=timeout_seconds) as response:
        body = response.read()
        content_type = response.headers.get("content-type", "application/octet-stream")
        kind = "pdf" if "pdf" in content_type.lower() or url.lower().endswith(".pdf") else "text"
        if kind == "pdf":
            return {"kind": "pdf", "body": body, "content_type": content_type}
        charset = response.headers.get_content_charset() or "utf-8"
        html = body.decode(charset, errors="replace")
        parser = _ReadableHTMLParser()
        parser.feed(html)
        text = parser.text()
        title = parser.title
        return {
            "kind": "text",
            "body": body,
            "text": text,
            "title": title,
            "content_type": content_type,
        }


def extract_pdf_text_best_effort(path: Path) -> str:
    try:
        return extract_text(str(path))
    except Exception:
        return ""


def build_source_acquisition_report(records: list[SourceAcquisitionRecord]) -> dict[str, Any]:
    return {
        "schema_version": "claim-appendix-source-acquisition-report-v1",
        "generated_at_utc": utc_now(),
        "source_count": len(records),
        "tier_counts": dict(Counter(record.tier for record in records)),
        "claim_count": sum(len(record.retrieved_for_claim_ids) for record in records),
        "unavailable_claim_ids": sorted(
            claim_id
            for record in records
            if record.tier in {"unavailable", "ambiguous_url"}
            for claim_id in record.retrieved_for_claim_ids
        ),
    }


def render_source_acquisition_report(
    report: dict[str, Any],
    records: list[SourceAcquisitionRecord],
) -> str:
    tier_lines = [
        f"- `{tier}`: `{count}`" for tier, count in sorted(report["tier_counts"].items())
    ]
    rows = [
        "| Source | Tier | Claims | Chars | URL | Failure |",
        "| --- | --- | ---: | ---: | --- | --- |",
    ]
    for record in sorted(records, key=lambda item: item.source_id):
        rows.append(
            "| "
            f"`{record.source_id}` | `{record.tier}` | "
            f"{len(record.retrieved_for_claim_ids)} | {record.extracted_text_chars} | "
            f"{record.normalized_url} | {record.failure_reason or ''} |"
        )
    return "\n".join(
        [
            "# Source Acquisition Report",
            "",
            "This report classifies primary-source URL availability for the appendix workflow.",
            "",
            f"- Generated at UTC: `{report['generated_at_utc']}`",
            f"- Unique source URLs: `{report['source_count']}`",
            f"- Claim-source links: `{report['claim_count']}`",
            "",
            "## Tier Counts",
            "",
            *tier_lines,
            "",
            "## Sources",
            "",
            *rows,
            "",
        ]
    )


def _source_record(
    *,
    source_id: str,
    raw_url: str,
    normalized_url: str,
    grouped_claims: list[AppendixClaimRecord],
    tier: str,
    retrieved_at_utc: str,
    content_type: str | None = None,
    content_path: Path | None = None,
    sha256: str | None = None,
    extracted_text_chars: int = 0,
    failure_reason: str | None = None,
    title: str | None = None,
) -> SourceAcquisitionRecord:
    return SourceAcquisitionRecord(
        source_id=source_id,
        primary_source_url=raw_url,
        normalized_url=normalized_url,
        tier=tier,
        content_type=content_type,
        content_path=str(content_path) if content_path is not None else None,
        sha256=sha256,
        extracted_text_chars=extracted_text_chars,
        retrieved_at_utc=retrieved_at_utc,
        retrieved_for_claim_ids=sorted(claim.claim_id for claim in grouped_claims),
        duplicate_claim_numbers=sorted(claim.claim_number for claim in grouped_claims),
        failure_reason=failure_reason,
        title=title,
    )


def _ca_claim_payload(
    claim: AppendixClaimRecord,
    available_sources: dict[str, SourceAcquisitionRecord],
) -> dict[str, Any]:
    source_refs = []
    if claim.source_id in available_sources:
        source_refs.append(
            {
                "source_id": claim.source_id,
                "passage_id": f"pass-{claim.claim_id}",
            }
        )
    return {
        "claim_id": claim.claim_id,
        "claim_type": "extracted_claim",
        "claim_text": claim.claim_text,
        "support_status": "uncertain",
        "claim_strength": 0.5,
        "extraction_fidelity": 0.8,
        "source_refs": source_refs,
        "counterevidence_checked": False,
        "counterevidence_found": False,
        "downgraded": False,
        "downgrade_reason": None,
        "scaffold_notes": (
            f"Appendix claim type: {claim.appendix_claim_type}; "
            f"source cited by site: {claim.source_cited_by_site}"
        ),
    }


def _ca_source_metadata(
    source: SourceAcquisitionRecord,
    content_path: Path,
    claims: list[AppendixClaimRecord],
    rank: int,
) -> dict[str, Any]:
    return {
        "source_id": source.source_id,
        "schema_version": CONTRACT_VERSION,
        "bibliographic": {
            "source_type": _source_type(source.normalized_url),
            "title": source.title or source.normalized_url,
            "authors": [],
            "publication_date": None,
            "pmid": None,
            "doi": None,
            "url": source.normalized_url,
            "access_date_utc": source.retrieved_at_utc,
        },
        "trust_level": "primary",
        "content_hash": hash_file(content_path),
        "retrieval": {
            "retrieved_for": sorted(claim.claim_id for claim in claims),
            "retrieval_query": "primary source URL supplied by claim verification appendix",
            "retrieval_rank": rank,
        },
        "notes": f"Acquisition tier: {source.tier}",
    }


def _ca_source_passages(
    source_id: str,
    source_text: str,
    claims: list[AppendixClaimRecord],
) -> dict[str, Any]:
    excerpt = normalize_text(source_text)[:900] or "No extractable text found."
    return {
        "source_id": source_id,
        "schema_version": CONTRACT_VERSION,
        "passages": [
            {
                "passage_id": f"pass-{claim.claim_id}",
                "section": "Appendix primary-source corpus",
                "paragraph_index": index,
                "char_start": 0,
                "char_end": max(1, len(excerpt)),
                "text_preview": excerpt,
                "used_for_claims": [claim.claim_id],
                "extraction_method": "scaffold_inferred",
            }
            for index, claim in enumerate(sorted(claims, key=lambda item: item.claim_id), start=1)
        ],
    }


def _source_type(url: str) -> str:
    lowered = url.lower()
    if "arxiv.org" in lowered:
        return "preprint"
    if any(
        domain in lowered
        for domain in ("pmc.ncbi.nlm.nih.gov", "science.org", "frontiersin.org", "mdpi.com")
    ):
        return "journal_article"
    if any(domain in lowered for domain in ("fda.gov", "iea.org", "oecd.org")):
        return "regulatory_guidance"
    return "web_page"


def _read_content_text(path: Path) -> str:
    if path.suffix == ".pdf":
        return extract_pdf_text_best_effort(path)
    return path.read_text(encoding="utf-8", errors="replace")


def _write_retrieval_config(paths: WorkflowPaths) -> None:
    config = {
        "retrieval_method": "hybrid",
        "top_k": 5,
        "child_top_k": 25,
        "semantic_child_top_k": 60,
        "semantic_index_path": str(paths.root / "semantic-index"),
        "rerank_enabled": True,
        "rerank_top_n": 30,
        "contradiction_enabled": True,
        "contradiction_top_k": 20,
        "contradiction_rerank_enabled": True,
        "contradiction_query_prefixes": [
            "evidence against",
            "limitations of",
            "contradicts the claim that",
            "does not support",
            "fails to demonstrate",
            "source does not verify",
            "unsupported statistic",
        ],
    }
    dump_yaml(config, paths.retrieval_config)


def _run_review_pass(
    pass_name: str,
    paths: WorkflowPaths,
    *,
    claims: list[AppendixClaimRecord],
    sources: list[SourceAcquisitionRecord],
    claim_audit_cli: Path,
    cal_root: Path,
) -> dict[str, Any]:
    pass_paths = paths.pass_paths(pass_name)
    run_command(
        [
            EVIDENCE_BUNDLER_CLI,
            "review",
            "init",
            paths.draft,
            "--output",
            pass_paths["annotations"],
            "--reviewer",
            f"claim-appendix-{pass_name}-reviewer",
        ],
        cwd=REPO_ROOT,
    )
    if pass_name == "blind":
        _apply_blind_review(pass_paths["annotations"], paths.draft)
    else:
        _apply_guided_review(pass_paths["annotations"], paths.draft, claims, sources)

    run_command(
        [
            EVIDENCE_BUNDLER_CLI,
            "refine-excerpts",
            paths.draft,
            "--annotations",
            pass_paths["annotations"],
            "--output",
            pass_paths["refinement"],
        ],
        cwd=REPO_ROOT,
    )
    run_command(
        [
            EVIDENCE_BUNDLER_CLI,
            "finalize-bundle",
            paths.draft,
            "--annotations",
            pass_paths["annotations"],
            "--refinement",
            pass_paths["refinement"],
            "--output",
            pass_paths["final"],
            "--provenance-output",
            pass_paths["provenance"],
        ],
        cwd=REPO_ROOT,
    )
    run_command(
        [
            EVIDENCE_BUNDLER_CLI,
            "coverage-report",
            paths.draft,
            "--annotations",
            pass_paths["annotations"],
            "--refinement",
            pass_paths["refinement"],
            "--final-bundle",
            pass_paths["final"],
            "--provenance",
            pass_paths["provenance"],
            "--markdown-out",
            pass_paths["coverage_md"],
            "--json-out",
            pass_paths["coverage_json"],
        ],
        cwd=REPO_ROOT,
    )
    run_command(
        [
            claim_audit_cli,
            "audit-bundle",
            pass_paths["final"].resolve(),
            "--out-dir",
            pass_paths["cal_dir"].resolve(),
        ],
        cwd=cal_root,
    )

    comparison = build_comparison_report(
        pass_name,
        claims=claims,
        sources=sources,
        annotations_path=pass_paths["annotations"],
        draft_bundle_dir=paths.draft,
        audited_bundle_dir=pass_paths["cal_dir"] / f"{pass_paths['final'].name}-audited",
        coverage_json_path=pass_paths["coverage_json"],
    )
    write_json(comparison, pass_paths["comparison_json"])
    pass_paths["comparison_md"].write_text(render_comparison_report(comparison), encoding="utf-8")
    if comparison["claim_count"] != 30:
        raise SystemExit(f"{pass_name} comparison expected 30 claims")
    return {
        "annotation_summary": comparison["annotation_summary"],
        "verdict_counts": comparison["verdict_counts"],
        "alignment_counts": comparison["alignment_counts"],
        "coverage_inconsistency_count": comparison["coverage_inconsistency_count"],
    }


def _apply_blind_review(annotations_path: Path, draft_bundle_dir: Path) -> None:
    file = load_review_annotations(annotations_path, draft_bundle_dir)
    updated = []
    for annotation in file.annotations:
        if annotation.evidence_role == "insufficient":
            updated.append(
                apply_decision(
                    annotation,
                    decision="insufficient-excerpt",
                    notes=(
                        "Blind pass mechanical non-shipping decision: finalizer cannot "
                        "ship evidence_role='insufficient'."
                    ),
                )
            )
        else:
            updated.append(
                apply_decision(
                    annotation,
                    decision="accepted",
                    notes="Blind pass: accepted all shippable Bundler nominations.",
                )
            )
    write_review_annotations(file.model_copy(update={"annotations": updated}), annotations_path)


def _apply_guided_review(
    annotations_path: Path,
    draft_bundle_dir: Path,
    claims: list[AppendixClaimRecord],
    sources: list[SourceAcquisitionRecord],
) -> None:
    file = load_review_annotations(annotations_path, draft_bundle_dir)
    claims_by_id = {claim.claim_id: claim for claim in claims}
    source_tiers = {source.source_id: source.tier for source in sources}
    passage_text_by_key = _load_draft_passage_text(draft_bundle_dir)
    updated = []
    for annotation in file.annotations:
        claim = claims_by_id[annotation.claim_id]
        source_tier = source_tiers.get(annotation.source_id, "unavailable")
        if annotation.evidence_role == "insufficient" or source_tier in {
            "unavailable",
            "ambiguous_url",
        }:
            updated.append(
                apply_decision(
                    annotation,
                    decision="insufficient-excerpt",
                    notes="Guided pass: source unavailable or nomination marked insufficient.",
                )
            )
            continue
        passage_text = passage_text_by_key.get(
            (annotation.claim_id, annotation.source_id, annotation.passage_id),
            "",
        )
        if _guided_passage_matches(claim, passage_text):
            updated.append(
                apply_decision(
                    annotation,
                    decision="accepted",
                    notes="Guided pass: passage overlaps appendix evidence note or claim topic.",
                )
            )
        else:
            updated.append(
                apply_decision(
                    annotation,
                    decision="rejected",
                    notes=(
                        "Guided pass: clear off-topic nomination relative to appendix "
                        "evidence note."
                    ),
                )
            )
    write_review_annotations(file.model_copy(update={"annotations": updated}), annotations_path)


def _guided_passage_matches(claim: AppendixClaimRecord, passage_text: str) -> bool:
    haystack = normalize_text(passage_text).lower()
    if not haystack:
        return False
    evidence_terms = _salient_terms(claim.verified_evidence)
    claim_terms = _salient_terms(claim.claim_text)
    evidence_hits = sum(term in haystack for term in evidence_terms)
    claim_hits = sum(term in haystack for term in claim_terms)
    return evidence_hits >= 2 or claim_hits >= 3


def _salient_terms(text: str) -> list[str]:
    words = re.findall(r"[a-zA-Z][a-zA-Z0-9$%.-]{3,}", normalize_text(text).lower())
    stop = {
        "that",
        "with",
        "from",
        "this",
        "have",
        "will",
        "claim",
        "source",
        "verified",
        "evidence",
        "figure",
        "report",
    }
    return sorted({word.strip(".-") for word in words if word not in stop})[:18]


def _load_draft_passage_text(draft_bundle_dir: Path) -> dict[tuple[str, str, str], str]:
    result = {}
    for claim_path in sorted((draft_bundle_dir / "claims").glob("*.yaml")):
        claim = load_yaml(claim_path)
        claim_id = str(claim["claim_id"])
        for field in ("evidence_passages", "counterevidence_passages"):
            for passage in claim.get(field, []):
                result[(claim_id, str(passage["source_id"]), str(passage["passage_id"]))] = str(
                    passage["passage_text"]
                )
    return result


def build_comparison_report(
    pass_name: str,
    *,
    claims: list[AppendixClaimRecord],
    sources: list[SourceAcquisitionRecord],
    annotations_path: Path,
    draft_bundle_dir: Path,
    audited_bundle_dir: Path,
    coverage_json_path: Path,
) -> dict[str, Any]:
    annotation_file = load_review_annotations(annotations_path, draft_bundle_dir)
    annotations_by_claim: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for annotation in annotation_file.annotations:
        annotations_by_claim[annotation.claim_id].append(annotation.model_dump(mode="json"))

    audited_claims = _load_claim_yaml_by_id(audited_bundle_dir)
    sources_by_id = {source.source_id: source for source in sources}
    coverage = json.loads(coverage_json_path.read_text(encoding="utf-8"))
    rows = []
    for claim in sorted(claims, key=lambda item: item.claim_number):
        audited = audited_claims.get(claim.claim_id, {})
        audit = audited.get("audit", {}) if isinstance(audited, dict) else {}
        cal_verdict = audit.get("audit_support_verdict")
        source = sources_by_id.get(claim.source_id)
        annotations = annotations_by_claim.get(claim.claim_id, [])
        role_counts = Counter(str(row["evidence_role"]) for row in annotations)
        decision_counts = Counter(str(row["decision"]) for row in annotations)
        rows.append(
            {
                "claim_number": claim.claim_number,
                "claim_id": claim.claim_id,
                "source_name": claim.source_name,
                "claim_text": claim.claim_text,
                "appendix_verification_status": claim.appendix_verification_status,
                "appendix_claim_type": claim.appendix_claim_type,
                "primary_source_url": claim.primary_source_url,
                "source_tier": source.tier if source is not None else "missing_source_record",
                "cal_audit_support_verdict": cal_verdict,
                "alignment": alignment_for(claim.appendix_verification_status, cal_verdict),
                "annotation_count": len(annotations),
                "role_counts": dict(sorted(role_counts.items())),
                "decision_counts": dict(sorted(decision_counts.items())),
                "audit_notes": audit.get("audit_notes"),
            }
        )

    return {
        "schema_version": "claim-appendix-comparison-v1",
        "pass_name": pass_name,
        "generated_at_utc": utc_now(),
        "claim_count": len(rows),
        "annotation_summary": summarize_review_annotations(annotation_file).__dict__,
        "verdict_counts": dict(
            Counter(str(row["cal_audit_support_verdict"]) for row in rows)
        ),
        "alignment_counts": dict(Counter(str(row["alignment"]) for row in rows)),
        "coverage_inconsistency_count": len(coverage.get("inconsistencies", [])),
        "coverage_inconsistencies": coverage.get("inconsistencies", []),
        "rows": rows,
    }


def render_comparison_report(report: dict[str, Any]) -> str:
    rows = [
        "| # | Claim | Appendix status | Source tier | CAL verdict | Alignment | Annotations |",
        "| ---: | --- | --- | --- | --- | --- | ---: |",
    ]
    for row in report["rows"]:
        rows.append(
            "| "
            f"{row['claim_number']} | `{row['claim_id']}` | "
            f"{_table_cell(row['appendix_verification_status'])} | "
            f"`{row['source_tier']}` | `{row['cal_audit_support_verdict']}` | "
            f"`{row['alignment']}` | {row['annotation_count']} |"
        )
    verdict_lines = [
        f"- `{label}`: `{count}`" for label, count in sorted(report["verdict_counts"].items())
    ]
    alignment_lines = [
        f"- `{label}`: `{count}`" for label, count in sorted(report["alignment_counts"].items())
    ]
    return "\n".join(
        [
            f"# {report['pass_name'].title()} Comparison",
            "",
            "This is a supplied-evidence audit comparison, not external truth certification.",
            "",
            f"- Generated at UTC: `{report['generated_at_utc']}`",
            f"- Claim count: `{report['claim_count']}`",
            f"- Coverage inconsistencies: `{report['coverage_inconsistency_count']}`",
            "",
            "## CAL Verdict Counts",
            "",
            *verdict_lines,
            "",
            "## Alignment Counts",
            "",
            *alignment_lines,
            "",
            "## Claim Rows",
            "",
            *rows,
            "",
        ]
    )


def render_workflow_summary(summary: dict[str, Any]) -> str:
    tier_lines = [
        f"- `{tier}`: `{count}`" for tier, count in sorted(summary["source_tiers"].items())
    ]
    pass_lines = []
    for pass_name, pass_summary in sorted(summary["passes"].items()):
        pass_lines.extend(
            [
                f"## {pass_name.title()} Pass",
                "",
                f"- Coverage inconsistencies: `{pass_summary['coverage_inconsistency_count']}`",
                f"- Verdict counts: `{pass_summary['verdict_counts']}`",
                f"- Alignment counts: `{pass_summary['alignment_counts']}`",
                "",
            ]
        )
    return "\n".join(
        [
            "# Claim Verification Appendix Workflow Summary",
            "",
            "This run tests the Bundler -> CAL workflow against supplied primary-source URLs.",
            "",
            f"- Generated at UTC: `{summary['generated_at_utc']}`",
            f"- Claim count: `{summary['claim_count']}`",
            f"- Source records: `{summary['source_record_count']}`",
            "",
            "## Source Tiers",
            "",
            *tier_lines,
            "",
            *pass_lines,
        ]
    )


def _load_claim_yaml_by_id(bundle_dir: Path) -> dict[str, dict[str, Any]]:
    claims = {}
    for path in sorted((bundle_dir / "claims").glob("*.yaml")):
        data = load_yaml(path)
        claims[str(data["claim_id"])] = data
    return claims


def _table_cell(value: object) -> str:
    return str(value).replace("|", "\\|")


def _remove_workflow_outputs(paths: WorkflowPaths) -> None:
    for target in (
        paths.scaffold,
        paths.draft,
        paths.blind_final,
        paths.guided_final,
        paths.blind_cal_dir,
        paths.guided_cal_dir,
        paths.root / "semantic-index",
    ):
        if target.exists():
            shutil.rmtree(target)
    for target in (
        paths.retrieval_config,
        paths.retrieval_report,
        paths.blind_annotations,
        paths.blind_refinement,
        paths.blind_provenance,
        paths.blind_coverage_md,
        paths.blind_coverage_json,
        paths.blind_comparison_md,
        paths.blind_comparison_json,
        paths.guided_annotations,
        paths.guided_refinement,
        paths.guided_provenance,
        paths.guided_coverage_md,
        paths.guided_coverage_json,
        paths.guided_comparison_md,
        paths.guided_comparison_json,
        paths.workflow_summary_md,
        paths.workflow_summary_json,
    ):
        if target.exists():
            target.unlink()


class _ReadableHTMLParser(HTMLParser):
    """Very small HTML-to-readable-text extractor."""

    def __init__(self) -> None:
        super().__init__()
        self._parts: list[str] = []
        self._skip_depth = 0
        self._title_parts: list[str] = []
        self._in_title = False

    @property
    def title(self) -> str | None:
        title = normalize_text(" ".join(self._title_parts))
        return title or None

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        if tag in {"script", "style", "noscript"}:
            self._skip_depth += 1
        if tag == "title":
            self._in_title = True
        if tag in {"p", "div", "section", "article", "li", "br", "tr", "h1", "h2", "h3"}:
            self._parts.append("\n")

    def handle_endtag(self, tag: str) -> None:
        if tag in {"script", "style", "noscript"} and self._skip_depth:
            self._skip_depth -= 1
        if tag == "title":
            self._in_title = False
        if tag in {"p", "div", "section", "article", "li", "tr", "h1", "h2", "h3"}:
            self._parts.append("\n")

    def handle_data(self, data: str) -> None:
        if self._skip_depth:
            return
        if self._in_title:
            self._title_parts.append(data)
        self._parts.append(data)

    def text(self) -> str:
        return normalize_text(" ".join(self._parts))


def resolve_appendix_pdf(cli_pdf: Path | None = None) -> Path:
    """Resolve the claim appendix PDF path.

    Precedence:
    1. CLI argument
    2. CLAIM_APPENDIX_PDF environment variable
    """
    if cli_pdf is not None:
        path = Path(cli_pdf).resolve()
        if path.exists() and path.is_file():
            return path
        raise FileNotFoundError(
            f"Provided PDF path does not exist or is not a file: {path}"
        )

    env_val = os.environ.get("CLAIM_APPENDIX_PDF")
    if env_val:
        path = Path(env_val).resolve()
        if path.exists() and path.is_file():
            return path
        raise FileNotFoundError(
            f"CLAIM_APPENDIX_PDF environment variable path does not exist or is not a file: {path}"
        )

    raise FileNotFoundError(
        "Claim appendix PDF path not specified. "
        "Please provide the PDF path as a positional argument "
        "or set the CLAIM_APPENDIX_PDF environment variable."
    )


def main_parse(argv: list[str] | None = None) -> None:
    parser = argparse.ArgumentParser(description="Parse the claim verification appendix PDF.")
    parser.add_argument("pdf", type=Path, nargs="?")
    add_common_output_arg(parser)
    args = parser.parse_args(argv)

    try:
        pdf_path = resolve_appendix_pdf(args.pdf)
    except FileNotFoundError as exc:
        raise SystemExit(str(exc)) from None


    paths = WorkflowPaths.from_root(args.output_root)
    records, report = parse_appendix_pdf(pdf_path)
    write_parse_outputs(
        records,
        report,
        claims_out=paths.claims_json,
        report_json_out=paths.root / "parse_report.json",
        report_md_out=paths.root / "parse_report.md",
    )
    print(f"Parsed {len(records)} claims: {paths.claims_json}")
    print(f"Parse report written: {paths.root / 'parse_report.md'}")


def main_acquire(argv: list[str] | None = None) -> None:
    parser = argparse.ArgumentParser(description="Acquire primary sources for appendix claims.")
    add_common_output_arg(parser)
    parser.add_argument("--claims", type=Path, default=None)
    parser.add_argument("--url-overrides", type=Path, default=None)
    parser.add_argument("--timeout-seconds", type=int, default=45)
    args = parser.parse_args(argv)
    paths = WorkflowPaths.from_root(args.output_root)
    claims_path = args.claims or paths.claims_json
    claims = load_claim_records(claims_path)
    records, report = acquire_sources(
        claims,
        sources_dir=paths.sources_dir,
        timeout_seconds=args.timeout_seconds,
        url_overrides=load_url_overrides(args.url_overrides),
    )
    write_acquisition_outputs(
        records,
        report,
        records_out=paths.source_records_json,
        report_json_out=paths.root / "source_acquisition_report.json",
        report_md_out=paths.root / "source_acquisition_report.md",
    )
    print(f"Acquired {len(records)} unique source records: {paths.source_records_json}")
    print(f"Source acquisition report written: {paths.root / 'source_acquisition_report.md'}")


def main_run(argv: list[str] | None = None) -> None:
    parser = argparse.ArgumentParser(description="Run the appendix Bundler -> CAL workflow.")
    add_common_output_arg(parser)
    parser.add_argument("--force", action="store_true")
    parser.add_argument(
        "--claim-audit-root",
        type=Path,
        help="Explicit path to the Claim Audit Lab root directory.",
    )
    args = parser.parse_args(argv)

    try:
        cal_root = resolve_claim_audit_lab_root(args.claim_audit_root)
    except FileNotFoundError as exc:
        raise SystemExit(str(exc)) from None


    claim_audit_cli = cal_root / ".venv" / "bin" / "claim-audit"
    if not claim_audit_cli.exists():
        raise SystemExit(f"Required Claim Audit CLI not found at: {claim_audit_cli}")

    paths = WorkflowPaths.from_root(args.output_root)
    for required in (paths.claims_json, paths.source_records_json):
        if not required.exists():
            raise SystemExit(f"Required staged input missing: {required}")
    summary = run_workflow(
        paths,
        claim_audit_cli=claim_audit_cli,
        cal_root=cal_root,
        force=args.force,
    )
    print(f"Workflow summary written: {paths.workflow_summary_md}")
    print(json.dumps(summary["passes"], indent=2, sort_keys=True))



if __name__ == "__main__":
    # Allows ad-hoc `python claim_appendix_workflow.py parse|acquire|run` use.
    if len(sys.argv) < 2 or sys.argv[1] not in {"parse", "acquire", "run"}:
        raise SystemExit("Usage: claim_appendix_workflow.py [parse|acquire|run] ...")
    command = sys.argv[1]
    rest = sys.argv[2:]
    if command == "parse":
        main_parse(rest)
    elif command == "acquire":
        main_acquire(rest)
    else:
        main_run(rest)
