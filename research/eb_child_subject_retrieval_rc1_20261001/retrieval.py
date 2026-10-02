"""Execute frozen V1 and isolated semantic research arms; never assess evidence.

Model/runtime absence fails closed. No fixture scores or lexical fallback enter
the operational path. Unit score fixtures qualify mechanisms, not retrieval.
"""

from __future__ import annotations

import argparse
import importlib
import math
import re
import subprocess
import sys
from pathlib import Path
from typing import Any

from bind import check_runtime, make_contracts, verify_chain
from study import (
    HERE,
    BoundaryError,
    canonical,
    check_corpus,
    check_subjects,
    claim_index,
    digest,
    fresh_directory,
    load,
    policy,
    require,
    write_new,
)


def anchor_match(text: str, anchor: str) -> bool:
    text = " ".join(text.split()).casefold()
    anchor = " ".join(anchor.split()).casefold()
    require(bool(anchor), "blank subject anchor")
    return re.search(r"(?<!\w)" + re.escape(anchor) + r"(?!\w)", text) is not None


def order(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    return sorted(rows, key=lambda row: (-row["score"], row["passage_id"]))


def select_lane(
    rows: list[dict[str, Any]],
    cid: str,
    anchor: str,
    *,
    coverage: bool,
    subject: bool,
    wrong_child: str | None = None,
) -> list[str]:
    require(
        len(rows) <= 10 and len({r["passage_id"] for r in rows}) == len(rows),
        "lane depth/duplicate",
    )
    require(
        all(type(row["score"]) in {int, float} and math.isfinite(row["score"]) for row in rows),
        "nonfinite/non-numeric score",
    )
    cap = policy()["search"]["semantic_loss_cap"]
    rows = (
        [dict(row, owner=wrong_child if row["owner"] == cid else cid) for row in rows]
        if wrong_child
        else rows
    )
    current = order(rows)[:3]

    def outside() -> list[dict[str, Any]]:
        return [row for row in rows if row not in current]

    if coverage and current and not any(row["owner"] == cid for row in current):
        challengers = order([row for row in outside() if row["owner"] == cid])
        victim = min(current, key=lambda row: (row["score"], row["passage_id"]))
        if challengers and victim["score"] - challengers[0]["score"] <= cap + 1e-12:
            current = [row for row in current if row != victim] + challengers[:1]
    if subject and current:
        challengers = order([row for row in outside() if anchor_match(row["text"], anchor)])
        victims = sorted(
            [row for row in current if not anchor_match(row["text"], anchor)],
            key=lambda row: (row["score"], row["passage_id"]),
        )
        # One bounded swap. In A3, keep existing correct ownership if it is represented.
        protected = coverage and any(row["owner"] == cid for row in current)
        for challenger in challengers:
            for victim in victims:
                trial = [row for row in current if row != victim] + [challenger]
                if protected and not any(row["owner"] == cid for row in trial):
                    continue
                if victim["score"] - challenger["score"] <= cap + 1e-12:
                    return [row["passage_id"] for row in order(trial)]
    return [row["passage_id"] for row in order(current)]


def load_model(model_dir: Path) -> Any:
    check_runtime(model_dir)
    try:
        torch = importlib.import_module("torch")
        factory = importlib.import_module("sentence_transformers").SentenceTransformer
    except ImportError as exc:
        raise BoundaryError("semantic engine unavailable; no fallback") from exc
    torch.set_num_threads(1)
    torch.manual_seed(0)
    torch.use_deterministic_algorithms(True)
    model = factory(str(model_dir), device="cpu", local_files_only=True, trust_remote_code=False)
    model.max_seq_length = 256
    model.eval()
    return model


def execute(claims: dict, subjects: dict, corpus: dict, contracts: dict, model: Any) -> dict:
    """Real engine path: exact V1 build/chunker, then real embedding computation."""
    targets = claim_index(claims)
    declarations = check_subjects(claims, subjects)
    check_corpus(claims, corpus)
    require(contracts == make_contracts(claims, corpus), "pre-frozen Contract A identity drift")
    repo = HERE.parents[1]
    sys.path.insert(0, str(repo / "src"))
    try:
        import numpy as np

        from evidence_bundler import __version__
        from evidence_bundler.ingest import chunk_source_documents
        from evidence_bundler.models.document import ChunkSpec
        from evidence_bundler.v1.builder import _source_documents, build_package
        from evidence_bundler.v1.package import V1Config, hash_text, passage_identity
    except ImportError as exc:
        raise BoundaryError("frozen EB/semantic engine dependencies unavailable") from exc
    require(__version__ == "0.2.0", "EB version drift")
    require(V1Config().identity == policy()["baseline"]["config_sha256"], "V1 config drift")
    selection = {arm: {} for arm in policy()["arms"]}
    pools, native = {}, {}
    trace = {}
    for packet in claims["packets"]:
        for parent in packet["parents"]:
            children = parent["children"]
            child_ids = [child["child_id"] for child in children]
            contract = contracts[parent["parent_id"]]
            base = build_package(contract_a=contract)
            native[parent["parent_id"]] = base
            chunks = chunk_source_documents(
                _source_documents(contract), ChunkSpec(max_chars=1800, overlap_chars=80)
            )
            from evidence_bundler.retrieval._indexable import select_indexable_chunks

            chunks = select_indexable_chunks(chunks)
            texts = [chunk.text for chunk in chunks]
            query = [c["text"] for c in children]
            lexical_query = [c["text"] + "\n" + parent["text"] for c in children]
            if chunks:
                vectors = model.encode(
                    query + lexical_query + texts,
                    batch_size=32,
                    normalize_embeddings=True,
                    convert_to_numpy=True,
                    show_progress_bar=False,
                )
                require(np.isfinite(vectors).all(), "nonfinite embeddings")
                scores = np.round(
                    vectors[:4].astype(np.float32) @ vectors[4:].astype(np.float32).T, 9
                )
            else:
                scores = np.empty((4, 0), dtype=np.float32)
            passage_rows = []
            hashes = {s["source_id"]: s["content_sha256"] for s in contract["sources"]}
            for index, chunk in enumerate(chunks):
                pid = passage_identity(
                    source_id=chunk.source_id,
                    source_content_sha256=hashes[chunk.source_id],
                    char_start=chunk.char_start,
                    char_end=chunk.char_end,
                    passage_sha256=hash_text(chunk.text),
                )
                owner = min(
                    child_ids, key=lambda cid: (-float(scores[child_ids.index(cid), index]), cid)
                )
                passage_rows.append({"passage_id": pid, "text": chunk.text, "owner": owner})
            for pos, child in enumerate(children):
                cid = child["child_id"]
                rows = order(
                    [
                        dict(row, score=round(float(scores[pos, index]), 9))
                        for index, row in enumerate(passage_rows)
                    ]
                )[:10]
                lexical = order(
                    [
                        dict(row, score=round(float(scores[pos + 2, index]), 9))
                        for index, row in enumerate(passage_rows)
                    ]
                )[:10]
                base_rows = [row for row in base["candidates"] if row["proposition_id"] == cid]
                trace[cid] = {
                    "semantic_top10": rows,
                    "lexical_control_top10": lexical,
                    "baseline_candidates": base_rows,
                }
                selection["A0"][cid] = [
                    row["passage_id"] for row in base_rows if row["selection_state"] == "retained"
                ]
                selection["S0"][cid] = [row["passage_id"] for row in rows[:3]]
                selection["L0"][cid] = [row["passage_id"] for row in lexical[:3]]
                own = declarations[cid]["anchor"]
                wrong = declarations[declarations[cid]["wrong_child_id"]]["anchor"]
                sibling = child_ids[1 - pos]
                for arm, cover, subject, anchor, donor in [
                    ("A1", True, False, own, None),
                    ("A2", False, True, own, None),
                    ("A3", True, True, own, None),
                    ("WS3", True, True, wrong, None),
                    ("WC3", True, True, own, sibling),
                    ("WS2", False, True, wrong, None),
                    ("WC1", True, False, own, sibling),
                ]:
                    selection[arm][cid] = select_lane(
                        rows, cid, anchor, coverage=cover, subject=subject, wrong_child=donor
                    )
                union = {row["passage_id"]: row["text"] for row in [*base_rows, *rows, *lexical]}
                pools[cid] = [{"passage_id": pid, "text": union[pid]} for pid in sorted(union)]
    result = {
        "schema": "eb-child-subject-retrieval-v1",
        "binding": {
            "claims_payload_sha256": digest(canonical(claims)),
            "subjects_payload_sha256": digest(canonical(subjects)),
            "corpus_payload_sha256": digest(canonical(corpus)),
        },
        "targets": {
            cid: {key: row[key] for key in ["text", "parent_text", "parent_id", "packet_id"]}
            for cid, row in targets.items()
        },
        "pools": pools,
        "selections": selection,
    }
    result["binding"]["nomination_trace_payload_sha256"] = digest(canonical(trace))
    return {"result": result, "baseline_native_packages": native, "nomination_trace": trace}


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--freeze-dir", required=True, type=Path)
    parser.add_argument("--model-dir", required=True, type=Path)
    parser.add_argument("--run-ordinal", required=True, type=int, choices=[1, 2])
    args = parser.parse_args()
    try:
        verify_chain(args.freeze_dir, 4)
        authority = load(args.freeze_dir / "EXECUTION-AUTHORITY.PRIVATE.json")
        repo = HERE.parents[1]
        head = subprocess.check_output(
            ["git", "-C", str(repo), "rev-parse", "HEAD"], text=True
        ).strip()
        candidate = load(HERE / "CANDIDATE.json")
        require(
            authority["candidate_source_commit"] == candidate["source_commit"], "candidate binding"
        )
        require(
            authority["candidate_source_tree"] == candidate["source_tree"], "candidate tree binding"
        )
        source_tree = subprocess.check_output(
            ["git", "-C", str(repo), "rev-parse", candidate["source_commit"] + "^{tree}"], text=True
        ).strip()
        require(source_tree == candidate["source_tree"], "source tree object identity")
        subprocess.run(
            [
                "git",
                "-C",
                str(repo),
                "merge-base",
                "--is-ancestor",
                candidate["source_commit"],
                head,
            ],
            check=True,
        )
        require(
            not subprocess.check_output(["git", "-C", str(repo), "status", "--porcelain"]),
            "dirty candidate",
        )
        require(
            not subprocess.check_output(
                [
                    "git",
                    "-C",
                    str(repo),
                    "diff",
                    "--name-only",
                    policy()["baseline"]["commit"],
                    head,
                    "--",
                    "src",
                    "scripts/run_v1_integration_candidate.py",
                    "config/eb_v1_slice",
                    "pyproject.toml",
                ]
            ),
            "protected production drift",
        )
        for filename, blob in candidate["frozen_blobs"].items():
            actual = subprocess.check_output(
                ["git", "-C", str(repo), "hash-object", str(HERE / filename)], text=True
            ).strip()
            require(actual == blob, "frozen apparatus blob drift")
        run = args.freeze_dir / f"retrieval-{args.run_ordinal:02d}"
        if args.run_ordinal == 2:
            require(
                (args.freeze_dir / "retrieval-01/COMPLETED.PUBLIC.json").is_file(),
                "first retrieval attempt did not complete; no rescue rerun",
            )
        fresh_directory(run)
        write_new(
            run / "STARTED.PUBLIC.json",
            {"ordinal": args.run_ordinal, "candidate_head": head, "attempt_budget": 2},
        )
        model = load_model(args.model_dir)
        output = execute(
            load(args.freeze_dir / "CLAIMS.PRIVATE.json"),
            load(args.freeze_dir / "SUBJECTS.PRIVATE.json"),
            load(args.freeze_dir / "CORPUS.PRIVATE.json"),
            load(args.freeze_dir / "CONTRACT-A.PRIVATE.json"),
            model,
        )
        hashes = {
            "retrieval_output_raw_sha256": write_new(
                run / "RETRIEVAL.PRIVATE.json", output["result"]
            )
        }
        hashes["nomination_trace_raw_sha256"] = write_new(
            run / "NOMINATION-TRACE.PRIVATE.json", output["nomination_trace"]
        )
        for parent, package in output["baseline_native_packages"].items():
            name = digest(parent.encode()).split(":")[1] + ".json"
            hashes[name] = write_new(run / name, package)
        write_new(
            run / "COMPLETED.PUBLIC.json",
            {"hashes": hashes, "ordinal": args.run_ordinal, "scientific_judgments": "NOT_RUN"},
        )
        return 0
    except (BoundaryError, OSError, TypeError, KeyError, subprocess.CalledProcessError) as exc:
        print(canonical({"state": "BLOCKED", "error": str(exc)}).decode())
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
