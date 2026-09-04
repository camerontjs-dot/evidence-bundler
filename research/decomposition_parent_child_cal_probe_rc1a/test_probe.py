from __future__ import annotations

from research.decomposition_parent_child_cal_probe_rc1a.run_probe import (
    UPSTREAM_MANIFEST_SHA256,
    UPSTREAM_RAW_SHA256,
    _bundle_from_hits,
    _lane_hits,
)


def test_upstream_digests_are_pinned() -> None:
    assert len(UPSTREAM_RAW_SHA256) == 64
    assert len(UPSTREAM_MANIFEST_SHA256) == 64


def test_lane_filter_requires_exact_proposition_and_lane() -> None:
    r2 = {
        "hits": [
            {
                "paragraph_id": "p1",
                "source_id": "s1",
                "paragraph_index": 0,
                "text": "one",
                "relationships": [
                    {
                        "proposition_id": "root",
                        "retrieval_lane": "root_lane",
                    },
                    {
                        "proposition_id": "child-1",
                        "retrieval_lane": "child_lane",
                    },
                ],
            },
            {
                "paragraph_id": "p2",
                "source_id": "s2",
                "paragraph_index": 0,
                "text": "two",
                "relationships": [
                    {
                        "proposition_id": "child-2",
                        "retrieval_lane": "child_lane",
                    }
                ],
            },
        ]
    }
    root_hits = _lane_hits(r2, proposition_id="root", retrieval_lane="root_lane")
    child_hits = _lane_hits(r2, proposition_id="child-1", retrieval_lane="child_lane")
    assert [row["paragraph_id"] for row in root_hits] == ["p1"]
    assert [row["paragraph_id"] for row in child_hits] == ["p1"]


def test_research_bundle_preserves_physical_passage_identity() -> None:
    bundle = _bundle_from_hits(
        [
            {
                "paragraph_id": "src-a:paragraph:000",
                "source_id": "src-a",
                "paragraph_index": 0,
                "text": "Alpha evidence.",
            },
            {
                "paragraph_id": "src-b:paragraph:002",
                "source_id": "src-b",
                "paragraph_index": 2,
                "text": "Beta evidence.",
            },
        ]
    )
    ids = sorted(excerpt.id for source in bundle.sources for excerpt in source.excerpts)
    assert ids == ["src-a:paragraph:000", "src-b:paragraph:002"]
