from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any

LABELS = {'KEEP_DISTINCT', 'DROP_REDUNDANT', 'DROP_DISTRACTOR', 'UNRESOLVED'}
ACTION = {
    'KEEP_DISTINCT': 'KEEP',
    'DROP_REDUNDANT': 'DROP',
    'DROP_DISTRACTOR': 'DROP',
    'UNRESOLVED': 'UNRESOLVED',
}


def load(path: Path) -> Any:
    return json.loads(path.read_text(encoding='utf-8'))


def canonical_hash(obj: Any) -> str:
    raw = json.dumps(obj, sort_keys=True, separators=(',', ':'), ensure_ascii=False).encode('utf-8')
    return hashlib.sha256(raw).hexdigest()


def packet_relation_ids(packet: dict[str, Any]) -> list[str]:
    ids = []
    for lane in packet.get('lanes', []):
        for passage in lane.get('passages', []):
            rid = passage.get('relation_id')
            if not isinstance(rid, str):
                raise ValueError('packet relation_id missing')
            ids.append(rid)
    if len(set(ids)) != len(ids):
        raise ValueError('packet duplicate relation_id')
    return ids


def validate_review(
    review_path: Path,
    packet_path: Path,
    expected_phase: str,
    used_reviewer_ids: set[str] | None = None,
) -> tuple[dict[str, str], str]:
    packet = load(packet_path)
    expected_hash = canonical_hash(packet)
    allowed_ids = set(packet_relation_ids(packet))
    review = load(review_path)
    if review.get('schema') != 'eb-v1-operational-burden-rc1-review-v1':
        raise ValueError(f'{review_path}: schema mismatch')
    meta = review.get('reviewer', {})
    reviewer_id = meta.get('reviewer_id')
    if not isinstance(reviewer_id, str) or not reviewer_id.strip():
        raise ValueError(f'{review_path}: reviewer_id missing')
    if used_reviewer_ids is not None:
        if reviewer_id in used_reviewer_ids:
            raise ValueError(f'{review_path}: duplicate reviewer_id {reviewer_id}')
        used_reviewer_ids.add(reviewer_id)
    if meta.get('review_phase') != expected_phase:
        raise ValueError(f'{review_path}: review_phase mismatch')
    if meta.get('packet_canonical_sha256') != expected_hash:
        raise ValueError(f'{review_path}: packet hash mismatch')
    if meta.get('independent_of_other_reviewers') is not True:
        raise ValueError(f'{review_path}: independence assertion missing')
    if meta.get('saw_other_set') is not False:
        raise ValueError(f'{review_path}: other-set exposure')
    if meta.get('saw_prior_reference') is not False:
        raise ValueError(f'{review_path}: prior-reference exposure')
    judgments = review.get('judgments')
    if not isinstance(judgments, list):
        raise ValueError(f'{review_path}: judgments missing')
    out: dict[str, str] = {}
    for j in judgments:
        rid = j.get('relation_id')
        label = j.get('label')
        if rid in out:
            raise ValueError(f'{review_path}: duplicate relation_id {rid}')
        if rid not in allowed_ids:
            raise ValueError(f'{review_path}: unknown relation_id {rid}')
        if label not in LABELS:
            raise ValueError(f'{review_path}: invalid label {label}')
        if set(j.keys()) != {'relation_id', 'label'}:
            raise ValueError(f'{review_path}: judgment contains extra/missing fields')
        out[rid] = label
    if set(out) != allowed_ids:
        raise ValueError(f'{review_path}: relation set mismatch')
    return out, reviewer_id
