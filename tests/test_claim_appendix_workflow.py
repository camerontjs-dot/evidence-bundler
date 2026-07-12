from __future__ import annotations

import importlib.util
import sys
from pathlib import Path


def _load_workflow_module():
    path = Path(__file__).resolve().parents[1] / "scripts" / "claim_appendix_workflow.py"
    spec = importlib.util.spec_from_file_location("claim_appendix_workflow", path)
    assert spec is not None
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def test_numbered_blocks_handle_formfeed_headings() -> None:
    workflow = _load_workflow_module()
    text = "#1 Source A\nEXTRACTED CLAIM\nA\n\f#2 Source B\nEXTRACTED CLAIM\nB\n"

    blocks = workflow._numbered_blocks(text)

    assert len(blocks) == 2
    assert blocks[0].startswith("#1 Source A")
    assert blocks[1].startswith("#2 Source B")


def test_extract_first_field_set_ignores_duplicate_pdf_table_rendering() -> None:
    workflow = _load_workflow_module()
    block = """#1 Pi Pharma Intelligence
https://example.com/post
Pharma / Consulting

EXTRACTED CLAIM

Digital transformation unlocks insights.

CLAIM TYPE

Generic benefit assertion

SOURCE CITED BY SITE

No source cited

VERIFICATION STATUS

UNVERIFIED - decorative claim

VERIFIED EVIDENCE

No underlying study cited.

PRIMARY SOURCE URL

https://primary.example.com/report

EPISTEMOLOGICAL GAP

Measurable outcome data not supplied.

https://example.com/post

EXTRACTED CLAIM

Digital transformation unlocks insights.
"""

    record = workflow._parse_block(block)

    assert record.claim_number == 1
    assert record.claim_id == "clm-appendix-001"
    assert record.claim_text == "Digital transformation unlocks insights."
    assert record.epistemological_gap == "Measurable outcome data not supplied."


def test_ambiguous_url_detection_requires_override_for_domain_and_truncation() -> None:
    workflow = _load_workflow_module()

    assert workflow.classify_ambiguous_url(
        "https://www.cerulli.com",
        "https://www.cerulli.com",
        None,
    )
    assert workflow.classify_ambiguous_url(
        "https://example.com/cost-of-qual",
        "https://example.com/cost-of-qual",
        None,
    )
    assert (
        workflow.classify_ambiguous_url(
            "https://www.cerulli.com",
            "https://www.cerulli.com/research/report",
            "https://www.cerulli.com/research/report",
        )
        is None
    )


def test_alignment_uses_cal_six_value_support_labels() -> None:
    workflow = _load_workflow_module()

    assert workflow.alignment_for("VERIFIED", "supported") == "aligned"
    assert workflow.alignment_for("VERIFIED", "needs_source") == "diverged"
    assert workflow.alignment_for("UNVERIFIED - no citation", "overstated") == "aligned"
    assert workflow.alignment_for("SPECULATIVE - no primary source", "supported") == "diverged"
