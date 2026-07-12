"""Deterministic near-identical excerpt refinement for reviewed candidates."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime
from difflib import SequenceMatcher
from pathlib import Path

from evidence_bundler.contracts.hashing import compute_bundle_tree_hash, hash_text
from evidence_bundler.contracts.yaml_io import (
    load_model_yaml,
    model_to_yaml_dict,
    write_model_yaml,
    yaml_to_string,
)
from evidence_bundler.models.cb import BundleManifest, ClaimAuditUnit, ClaimEvidencePassage
from evidence_bundler.models.refinement import (
    ExcerptCluster,
    ExcerptRefinementConfig,
    ExcerptRefinementFile,
    ExcerptRefinementMember,
)
from evidence_bundler.models.review import ReviewAnnotation, ReviewDecision
from evidence_bundler.review.io import compute_review_annotations_hash, load_review_annotations


class ExcerptRefinerError(ValueError):
    """Raised when excerpt refinement cannot be computed safely."""


class ExcerptRefinerDriftError(ValueError):
    """Raised when a refinement sidecar no longer matches its anchors."""


@dataclass(frozen=True)
class ExcerptRefinementSummary:
    """Compact counts for CLI feedback."""

    candidates: int
    clusters: int
    members: int
    collapsed_members: int
    decision_conflicts: int


@dataclass(frozen=True)
class _RefinerCandidate:
    annotation: ReviewAnnotation
    passage: ClaimEvidencePassage


def refine_excerpts(
    draft_bundle_dir: Path,
    annotation_path: Path,
    *,
    config: ExcerptRefinementConfig | None = None,
    generated_at_utc: str | None = None,
) -> tuple[ExcerptRefinementFile, ExcerptRefinementSummary]:
    """Build a deterministic sidecar that clusters near-identical excerpts."""
    refiner_config = config or ExcerptRefinementConfig()
    annotations = load_review_annotations(annotation_path, draft_bundle_dir)
    manifest = _load_manifest(draft_bundle_dir)
    candidates = _load_candidates(draft_bundle_dir, annotations.annotations)
    clusters = _cluster_candidates(candidates, refiner_config)
    file = ExcerptRefinementFile(
        draft_bundle_id=manifest.bundle_id,
        draft_bundle_hash=compute_bundle_tree_hash(draft_bundle_dir),
        retrieval_config_hash=manifest.evidence_builder.config_hash,
        review_annotations_hash=compute_review_annotations_hash(annotation_path),
        refiner_config_hash=compute_refiner_config_hash(refiner_config),
        generated_at_utc=generated_at_utc or _utc_now(),
        clusters=clusters,
    )
    members = sum(len(cluster.members) for cluster in clusters)
    summary = ExcerptRefinementSummary(
        candidates=len(candidates),
        clusters=len(clusters),
        members=members,
        collapsed_members=sum(len(cluster.members) - 1 for cluster in clusters),
        decision_conflicts=sum(1 for cluster in clusters if cluster.decision_conflict),
    )
    return file, summary


def write_excerpt_refinement(file: ExcerptRefinementFile, path: Path) -> None:
    """Write an excerpt refinement sidecar through deterministic model YAML."""
    write_model_yaml(file, path)


def load_excerpt_refinement(
    path: Path,
    draft_bundle_dir: Path,
    annotation_path: Path,
) -> ExcerptRefinementFile:
    """Load a refinement sidecar and fail closed if any anchor drifted."""
    file = load_model_yaml(ExcerptRefinementFile, path)
    manifest = _load_manifest(draft_bundle_dir)
    if file.draft_bundle_id != manifest.bundle_id:
        raise ExcerptRefinerDriftError(
            "draft bundle-id mismatch: "
            f"refinement={file.draft_bundle_id!r} bundle={manifest.bundle_id!r}"
        )

    actual_bundle_hash = compute_bundle_tree_hash(draft_bundle_dir)
    if file.draft_bundle_hash != actual_bundle_hash:
        raise ExcerptRefinerDriftError(
            "draft bundle-hash mismatch: "
            f"refinement={file.draft_bundle_hash!r} bundle={actual_bundle_hash!r}"
        )

    actual_config_hash = manifest.evidence_builder.config_hash
    if file.retrieval_config_hash != actual_config_hash:
        raise ExcerptRefinerDriftError(
            "retrieval config-hash mismatch: "
            f"refinement={file.retrieval_config_hash!r} bundle={actual_config_hash!r}"
        )

    actual_annotation_hash = compute_review_annotations_hash(annotation_path)
    if file.review_annotations_hash != actual_annotation_hash:
        raise ExcerptRefinerDriftError(
            "review annotations-hash mismatch: "
            f"refinement={file.review_annotations_hash!r} annotations={actual_annotation_hash!r}"
        )
    return file


def compute_refiner_config_hash(config: ExcerptRefinementConfig) -> str:
    """Hash the deterministic refiner thresholds from canonical YAML."""
    return hash_text(yaml_to_string(model_to_yaml_dict(config)))


def _load_candidates(
    draft_bundle_dir: Path,
    annotations: list[ReviewAnnotation],
) -> list[_RefinerCandidate]:
    claim_cache: dict[str, ClaimAuditUnit] = {}
    candidates: list[_RefinerCandidate] = []
    for annotation in annotations:
        claim = claim_cache.get(annotation.claim_id)
        if claim is None:
            claim = load_model_yaml(
                ClaimAuditUnit,
                draft_bundle_dir / "claims" / f"{annotation.claim_id}.yaml",
            )
            claim_cache[annotation.claim_id] = claim
        candidates.append(
            _RefinerCandidate(
                annotation=annotation,
                passage=_passage_for_annotation(annotation, claim),
            )
        )
    return sorted(candidates, key=_candidate_identity)


def _passage_for_annotation(
    annotation: ReviewAnnotation,
    claim: ClaimAuditUnit,
) -> ClaimEvidencePassage:
    for passage in claim.evidence_passages + claim.counterevidence_passages:
        if (
            passage.source_id == annotation.source_id
            and passage.passage_id == annotation.passage_id
        ):
            return passage
    raise ExcerptRefinerError(
        "Review annotation references missing draft passage: "
        f"{annotation.claim_id}/{annotation.source_id}/{annotation.passage_id}"
    )


def _cluster_candidates(
    candidates: list[_RefinerCandidate],
    config: ExcerptRefinementConfig,
) -> list[ExcerptCluster]:
    clusters: list[ExcerptCluster] = []
    cluster_number = 1
    for group in _candidate_groups(candidates):
        for component in _connected_components(group, config):
            if len(component) < 2:
                continue
            members = [
                _member(candidate)
                for candidate in sorted(component, key=_candidate_identity)
            ]
            representative = sorted(members, key=_representative_sort_key)[0]
            member_decisions = _ordered_decisions({member.decision for member in members})
            clusters.append(
                ExcerptCluster(
                    cluster_id=f"excerpt-cluster-{cluster_number:04d}",
                    claim_id=representative.claim_id,
                    source_id=representative.source_id,
                    evidence_role=representative.evidence_role,
                    representative=representative,
                    members=members,
                    decision_conflict=len(member_decisions) > 1,
                    member_decisions=member_decisions,
                )
            )
            cluster_number += 1
    return clusters


def _candidate_groups(candidates: list[_RefinerCandidate]) -> list[list[_RefinerCandidate]]:
    groups: dict[tuple[str, str, str], list[_RefinerCandidate]] = {}
    for candidate in candidates:
        annotation = candidate.annotation
        key = (annotation.claim_id, annotation.source_id, annotation.evidence_role)
        groups.setdefault(key, []).append(candidate)
    return [groups[key] for key in sorted(groups)]


def _connected_components(
    candidates: list[_RefinerCandidate],
    config: ExcerptRefinementConfig,
) -> list[list[_RefinerCandidate]]:
    parent = list(range(len(candidates)))

    def find(index: int) -> int:
        while parent[index] != index:
            parent[index] = parent[parent[index]]
            index = parent[index]
        return index

    def union(left: int, right: int) -> None:
        left_root = find(left)
        right_root = find(right)
        if left_root != right_root:
            parent[right_root] = left_root

    for left_index, left in enumerate(candidates):
        for right_index in range(left_index + 1, len(candidates)):
            if _is_near_identical(left, candidates[right_index], config):
                union(left_index, right_index)

    components: dict[int, list[_RefinerCandidate]] = {}
    for index, candidate in enumerate(candidates):
        components.setdefault(find(index), []).append(candidate)
    return [
        sorted(components[root], key=_candidate_identity)
        for root in sorted(components, key=lambda item: _candidate_identity(components[item][0]))
    ]


def _is_near_identical(
    left: _RefinerCandidate,
    right: _RefinerCandidate,
    config: ExcerptRefinementConfig,
) -> bool:
    if left.annotation.passage_id == right.annotation.passage_id:
        return True
    if _span_jaccard(left.passage, right.passage) >= config.span_jaccard_threshold:
        return True
    if _span_containment(left.passage, right.passage) >= config.span_containment_threshold:
        return True
    return _text_similarity(left.passage.passage_text, right.passage.passage_text) >= (
        config.text_similarity_threshold
    )


def _span_jaccard(left: ClaimEvidencePassage, right: ClaimEvidencePassage) -> float:
    intersection = _span_intersection(left, right)
    union = max(left.char_end, right.char_end) - min(left.char_start, right.char_start)
    return intersection / union if union else 0.0


def _span_containment(left: ClaimEvidencePassage, right: ClaimEvidencePassage) -> float:
    intersection = _span_intersection(left, right)
    shorter = min(left.char_end - left.char_start, right.char_end - right.char_start)
    return intersection / shorter if shorter else 0.0


def _span_intersection(left: ClaimEvidencePassage, right: ClaimEvidencePassage) -> int:
    return max(0, min(left.char_end, right.char_end) - max(left.char_start, right.char_start))


def _text_similarity(left: str, right: str) -> float:
    return SequenceMatcher(None, _normalize_text(left), _normalize_text(right)).ratio()


def _normalize_text(text: str) -> str:
    return " ".join(text.casefold().split())


def _member(candidate: _RefinerCandidate) -> ExcerptRefinementMember:
    annotation = candidate.annotation
    passage = candidate.passage
    return ExcerptRefinementMember(
        claim_id=annotation.claim_id,
        source_id=annotation.source_id,
        passage_id=annotation.passage_id,
        evidence_role=annotation.evidence_role,
        decision=annotation.decision,
        char_start=passage.char_start,
        char_end=passage.char_end,
        passage_hash=passage.passage_hash,
    )


def _candidate_identity(candidate: _RefinerCandidate) -> tuple[str, str, str, str]:
    annotation = candidate.annotation
    return (
        annotation.claim_id,
        annotation.source_id,
        annotation.evidence_role,
        annotation.passage_id,
    )


def _representative_sort_key(member: ExcerptRefinementMember) -> tuple[int, int, int, str]:
    return (
        _decision_priority(member.decision),
        -(member.char_end - member.char_start),
        member.char_start,
        member.passage_id,
    )


def _ordered_decisions(decisions: set[ReviewDecision]) -> list[ReviewDecision]:
    return sorted(decisions, key=_decision_priority)


def _decision_priority(decision: ReviewDecision) -> int:
    priorities = {
        "accepted": 0,
        "needs-review": 1,
        "insufficient-excerpt": 2,
        "rejected": 3,
    }
    return priorities[decision]


def _load_manifest(draft_bundle_dir: Path) -> BundleManifest:
    return load_model_yaml(BundleManifest, draft_bundle_dir / "bundle_manifest.yaml")


def _utc_now() -> str:
    return datetime.now(UTC).strftime("%Y-%m-%dT%H:%M:%SZ")
