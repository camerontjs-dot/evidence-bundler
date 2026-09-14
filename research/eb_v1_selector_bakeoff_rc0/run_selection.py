#!/usr/bin/env python3
import argparse, hashlib, json, math, re, zipfile
from collections import Counter
from pathlib import Path

EXPECTED_SHA = '3424e70988a2ca878e97f6eeaf855cd5ebbd449413536841872bd485de74819d'
TOKEN_RE = re.compile(r'\w+')
ALPHAS = (0.25, 0.50, 0.75)


def sha256(path):
    h = hashlib.sha256()
    with open(path, 'rb') as f:
        for chunk in iter(lambda: f.read(1 << 20), b''):
            h.update(chunk)
    return h.hexdigest()


def tokenize(text):
    return TOKEN_RE.findall(text.lower())


def tfidf_vectors(texts):
    docs = [tokenize(text) for text in texts]
    n = len(docs)
    df = Counter()
    for doc in docs:
        df.update(set(doc))
    vectors = []
    for doc in docs:
        tf = Counter(doc)
        vector = {}
        for term, count in tf.items():
            idf = math.log((n + 1) / (df[term] + 1)) + 1.0
            vector[term] = count * idf
        norm = math.sqrt(sum(value * value for value in vector.values())) or 1.0
        vectors.append({term: value / norm for term, value in vector.items()})
    return vectors


def cosine(left, right):
    if len(left) > len(right):
        left, right = right, left
    return sum(value * right.get(term, 0.0) for term, value in left.items())


def facility_select(rows, proposition_text, alpha, budget=3):
    rows = sorted(rows, key=lambda row: (row['rank'], row['evidence_id']))
    k = min(budget, len(rows))
    top = rows[0]['score']
    relevance = [row['score'] / top for row in rows]
    vectors = tfidf_vectors([proposition_text] + [row['text'] for row in rows])[1:]
    similarity = [[cosine(left, right) for right in vectors] for left in vectors]
    weights = relevance[:]
    denominator = sum(weights) or 1.0

    def objective(selected):
        if not selected:
            return 0.0
        coverage = sum(
            weights[j] * max(similarity[j][s] for s in selected)
            for j in range(len(rows))
        ) / denominator
        rel = sum(relevance[s] for s in selected) / k
        return alpha * coverage + (1 - alpha) * rel

    selected = []
    current = 0.0
    while len(selected) < k:
        candidates = []
        for index, row in enumerate(rows):
            if index in selected:
                continue
            value = objective(selected + [index])
            gain = value - current
            candidates.append((gain, -row['rank'], row['evidence_id'], index, value))
        best_gain = max(item[0] for item in candidates)
        tied = [item for item in candidates if abs(item[0] - best_gain) <= 1e-12]
        best_rank = max(item[1] for item in tied)
        tied = [item for item in tied if item[1] == best_rank]
        best = min(tied, key=lambda item: item[2])
        selected.append(best[3])
        current = best[4]
    return [rows[index] for index in selected]


def largest_gap(rows):
    rows = sorted(rows, key=lambda row: (row['rank'], row['evidence_id']))
    if len(rows) <= 1:
        return rows
    gaps = []
    for index in range(len(rows) - 1):
        current = rows[index]['score']
        following = rows[index + 1]['score']
        gaps.append((current - following) / current if current else 0.0)
    cut = max(range(len(gaps)), key=lambda index: gaps[index]) + 1
    return rows[:min(cut, 3)]


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--artifact-zip', required=True)
    parser.add_argument('--out', required=True)
    args = parser.parse_args()
    artifact = Path(args.artifact_zip)
    if sha256(artifact) != EXPECTED_SHA:
        raise SystemExit('artifact digest mismatch')
    with zipfile.ZipFile(artifact) as archive:
        receipt = json.loads(archive.read('artifacts/k7/TREATMENT_10_7_RECEIPT.json'))

    proposition_text = {}
    lanes = {}
    for case in receipt['cases']:
        for target in case['primary_targets']:
            proposition_text[target['proposition_id']] = target['text']
        for row in case['raw_retrieval']:
            lanes.setdefault(row['proposition_id'], []).append(row)
    for rows in lanes.values():
        rows.sort(key=lambda row: (row['rank'], row['evidence_id']))

    arms = {}

    def add(name, selector):
        records = []
        for proposition_id in sorted(lanes):
            selected = selector(proposition_id, lanes[proposition_id])
            records.append({
                'proposition_id': proposition_id,
                'selected': [row['evidence_id'] for row in selected],
            })
        arms[name] = records

    add('fixed_k3', lambda proposition_id, rows: rows[:3])
    add('largest_relative_gap_cap3', lambda proposition_id, rows: largest_gap(rows))
    for alpha in ALPHAS:
        add(
            f'facility_alpha_{alpha:.2f}',
            lambda proposition_id, rows, value=alpha: facility_select(
                rows, proposition_text[proposition_id], value
            ),
        )

    output = {
        'schema': 'eb-v1-selector-bakeoff-rc0-selections-v1',
        'classification': 'GOLD_BLIND_SELECTION_OUTPUT',
        'authority': {
            'pr63_artifact_id': 10282804289,
            'pr63_artifact_sha256': 'sha256:' + EXPECTED_SHA,
            'profile': '10/7',
        },
        'selector_inputs': [
            'proposition_text',
            'candidate_text',
            'evidence/source/provenance identity',
            'original_bm25_rank',
            'raw_bm25_score',
        ],
        'gold_read': False,
        'arms': arms,
        'nonclaims': [
            'No selector is qualified by this output.',
            'No retrieval was rerun.',
            'No support/refutation/entailment authority was exercised.',
        ],
    }
    out = Path(args.out)
    out.write_text(json.dumps(output, indent=2, sort_keys=True) + '\n')
    print('OUTPUT_SHA256=' + sha256(out))
    for name, records in arms.items():
        print(name, sum(len(record['selected']) for record in records))


if __name__ == '__main__':
    main()
