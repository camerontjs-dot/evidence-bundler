"""Apply the preregistered RC0 retrieval control-surface patch on a hosted runner.

This temporary patcher exists only because the execution environment cannot clone the
repository directly. The bootstrap workflow deletes this file before committing the
implementation. Every replacement is asserted against the frozen RC0 base lineage.
"""

from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]


def replace_once(path: str, old: str, new: str) -> None:
    target = ROOT / path
    text = target.read_text(encoding="utf-8")
    count = text.count(old)
    if count != 1:
        raise RuntimeError(f"Expected exactly one match in {path}, found {count}: {old[:120]!r}")
    target.write_text(text.replace(old, new, 1), encoding="utf-8")


def write(path: str, content: str) -> None:
    target = ROOT / path
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(content, encoding="utf-8")


# Retrieval config: explicit geometry, immutable model revisions, and fail-closed research mode.
replace_once(
    "src/evidence_bundler/models/retrieval.py",
    "from pathlib import Path\nfrom typing import Literal, Self\n",
    "from pathlib import Path\nimport re\nfrom typing import Literal, Self\n",
)
replace_once(
    "src/evidence_bundler/models/retrieval.py",
    "DEFAULT_CONTRADICTION_QUERY_PREFIXES = (\n",
    "IMMUTABLE_MODEL_REVISION_RE = re.compile(r\"^[0-9a-f]{40}$\")\n\nDEFAULT_CONTRADICTION_QUERY_PREFIXES = (\n",
)
replace_once(
    "src/evidence_bundler/models/retrieval.py",
    "    lexical_score_floor: float = Field(default=0.0, ge=0.0)\n    embedding_model: NonBlankStr = \"BAAI/bge-small-en-v1.5\"\n    embedding_model_cache_dir: Path | None = None\n",
    "    lexical_score_floor: float = Field(default=0.0, ge=0.0)\n    chunk_max_chars: int = Field(default=1800, gt=0)\n    chunk_overlap_chars: int = Field(default=80, ge=0)\n    embedding_model: NonBlankStr = \"BAAI/bge-small-en-v1.5\"\n    embedding_model_revision: NonBlankStr | None = None\n    embedding_model_cache_dir: Path | None = None\n",
)
replace_once(
    "src/evidence_bundler/models/retrieval.py",
    "    rerank_enabled: bool = False\n    rerank_model: NonBlankStr = \"cross-encoder/ms-marco-MiniLM-L-6-v2\"\n    rerank_top_n: int = Field(default=30, gt=0)\n",
    "    rerank_enabled: bool = False\n    rerank_model: NonBlankStr = \"cross-encoder/ms-marco-MiniLM-L-6-v2\"\n    rerank_model_revision: NonBlankStr | None = None\n    require_immutable_model_revisions: bool = False\n    rerank_top_n: int = Field(default=30, gt=0)\n",
)
replace_once(
    "src/evidence_bundler/models/retrieval.py",
    "        if self.rerank_enabled and self.retrieval_method != \"hybrid\":\n            raise ValueError(\"rerank_enabled requires retrieval_method='hybrid'\")\n",
    "        if self.chunk_overlap_chars >= self.chunk_max_chars:\n            raise ValueError(\"chunk_overlap_chars must be smaller than chunk_max_chars\")\n        for field_name, revision in (\n            (\"embedding_model_revision\", self.embedding_model_revision),\n            (\"rerank_model_revision\", self.rerank_model_revision),\n        ):\n            if revision is not None and not IMMUTABLE_MODEL_REVISION_RE.fullmatch(str(revision)):\n                raise ValueError(f\"{field_name} must be a full 40-hex commit SHA\")\n        if self.require_immutable_model_revisions and self.retrieval_method in {\"semantic\", \"hybrid\"}:\n            if self.embedding_model_revision is None:\n                raise ValueError(\n                    \"immutable semantic execution requires embedding_model_revision\"\n                )\n        if self.require_immutable_model_revisions and self.rerank_enabled:\n            if self.rerank_model_revision is None:\n                raise ValueError(\"immutable reranking requires rerank_model_revision\")\n        if self.rerank_enabled and self.retrieval_method != \"hybrid\":\n            raise ValueError(\"rerank_enabled requires retrieval_method='hybrid'\")\n",
)

# Semantic index: bind revision and actual chunk set, not only source-corpus hash.
replace_once(
    "src/evidence_bundler/retrieval/embedding_retriever.py",
    "from evidence_bundler.contracts.yaml_io import load_model_yaml, write_model_yaml\n",
    "from evidence_bundler.contracts.hashing import hash_text\nfrom evidence_bundler.contracts.yaml_io import load_model_yaml, write_model_yaml\n",
)
replace_once(
    "src/evidence_bundler/retrieval/embedding_retriever.py",
    "    embedding_model: NonBlankStr\n    embedding_dim: int = Field(ge=0)\n",
    "    embedding_model: NonBlankStr\n    embedding_model_revision: NonBlankStr | None = None\n    chunk_set_hash: HashValue | None = None\n    embedding_dim: int = Field(ge=0)\n",
)
replace_once(
    "src/evidence_bundler/retrieval/embedding_retriever.py",
    "        embedding_model: str,\n        semantic_query_prefix: str | None,\n",
    "        embedding_model: str,\n        embedding_model_revision: str | None = None,\n        semantic_query_prefix: str | None,\n",
)
replace_once(
    "src/evidence_bundler/retrieval/embedding_retriever.py",
    "            embedding_model=embedding_model,\n            embedding_dim=embedding_dim,\n",
    "            embedding_model=embedding_model,\n            embedding_model_revision=embedding_model_revision,\n            chunk_set_hash=compute_semantic_chunk_set_hash(indexed_chunks),\n            embedding_dim=embedding_dim,\n",
)
replace_once(
    "src/evidence_bundler/retrieval/embedding_retriever.py",
    "        embedding_model: str,\n        semantic_query_prefix: str | None = None,\n    ) -> SemanticIndex:\n",
    "        embedding_model: str,\n        embedding_model_revision: str | None = None,\n        chunk_set_hash: str | None = None,\n        semantic_query_prefix: str | None = None,\n    ) -> SemanticIndex:\n",
)
replace_once(
    "src/evidence_bundler/retrieval/embedding_retriever.py",
    "            corpus_hash=corpus_hash,\n            embedding_model=embedding_model,\n        )\n",
    "            corpus_hash=corpus_hash,\n            embedding_model=embedding_model,\n            embedding_model_revision=embedding_model_revision,\n            chunk_set_hash=chunk_set_hash,\n        )\n",
)
replace_once(
    "src/evidence_bundler/retrieval/embedding_retriever.py",
    "def load_embedding_model(model_name: str, cache_dir: Path | None = None) -> TextEmbedder:\n    \"\"\"Load a SentenceTransformer model, optionally using an explicit cache dir.\"\"\"\n",
    "def load_embedding_model(\n    model_name: str,\n    cache_dir: Path | None = None,\n    *,\n    revision: str | None = None,\n) -> TextEmbedder:\n    \"\"\"Load a SentenceTransformer model with optional cache and immutable revision.\"\"\"\n",
)
replace_once(
    "src/evidence_bundler/retrieval/embedding_retriever.py",
    "    kwargs = {\"cache_folder\": str(cache_dir)} if cache_dir is not None else {}\n    return cast(TextEmbedder, SentenceTransformer(model_name, **kwargs))\n",
    "    kwargs: dict[str, object] = {}\n    if cache_dir is not None:\n        kwargs[\"cache_folder\"] = str(cache_dir)\n    if revision is not None:\n        kwargs[\"revision\"] = revision\n    return cast(TextEmbedder, SentenceTransformer(model_name, **kwargs))\n",
)
replace_once(
    "src/evidence_bundler/retrieval/embedding_retriever.py",
    "def _validate_manifest(\n    manifest: SemanticIndexManifest,\n    *,\n    corpus_hash: str,\n    embedding_model: str,\n) -> None:\n",
    "def _validate_manifest(\n    manifest: SemanticIndexManifest,\n    *,\n    corpus_hash: str,\n    embedding_model: str,\n    embedding_model_revision: str | None = None,\n    chunk_set_hash: str | None = None,\n) -> None:\n",
)
replace_once(
    "src/evidence_bundler/retrieval/embedding_retriever.py",
    "    if manifest.embedding_model != embedding_model:\n        mismatches.append(\"embedding_model\")\n    if manifest.normalize_embeddings is not NORMALIZE_EMBEDDINGS:\n",
    "    if manifest.embedding_model != embedding_model:\n        mismatches.append(\"embedding_model\")\n    if manifest.embedding_model_revision != embedding_model_revision:\n        mismatches.append(\"embedding_model_revision\")\n    if chunk_set_hash is not None and manifest.chunk_set_hash != chunk_set_hash:\n        mismatches.append(\"chunk_set_hash\")\n    if manifest.normalize_embeddings is not NORMALIZE_EMBEDDINGS:\n",
)
replace_once(
    "src/evidence_bundler/retrieval/embedding_retriever.py",
    "def _validate_faiss_index_shape(index: object, manifest: SemanticIndexManifest) -> None:\n",
    "def compute_semantic_chunk_set_hash(chunks: list[DocumentChunk]) -> str:\n    \"\"\"Hash the ordered semantic-index rows so cached indexes cannot alias chunk geometry.\"\"\"\n    indexed_chunks = select_indexable_chunks(chunks)\n    rows = [\n        {\n            \"chunk_id\": chunk.chunk_id,\n            \"chunk_hash\": chunk.chunk_hash,\n            \"source_id\": chunk.source_id,\n            \"parent_chunk_id\": chunk.parent_chunk_id,\n            \"char_start\": chunk.char_start,\n            \"char_end\": chunk.char_end,\n        }\n        for chunk in indexed_chunks\n    ]\n    return hash_text(json.dumps(rows, sort_keys=True, separators=(\",\", \":\")))\n\n\ndef _validate_faiss_index_shape(index: object, manifest: SemanticIndexManifest) -> None:\n",
)

# Reranker loader revision binding.
replace_once(
    "src/evidence_bundler/retrieval/reranker.py",
    "def load_reranker_model(model_name: str, cache_dir: Path | None = None) -> CrossEncoderModel:\n    \"\"\"Load a SentenceTransformers CrossEncoder model.\"\"\"\n",
    "def load_reranker_model(\n    model_name: str,\n    cache_dir: Path | None = None,\n    *,\n    revision: str | None = None,\n) -> CrossEncoderModel:\n    \"\"\"Load a SentenceTransformers CrossEncoder at an optional immutable revision.\"\"\"\n",
)
replace_once(
    "src/evidence_bundler/retrieval/reranker.py",
    "    kwargs = {\"cache_folder\": str(cache_dir)} if cache_dir is not None else {}\n    return cast(CrossEncoderModel, CrossEncoder(model_name, **kwargs))\n",
    "    kwargs: dict[str, object] = {}\n    if cache_dir is not None:\n        kwargs[\"cache_folder\"] = str(cache_dir)\n    if revision is not None:\n        kwargs[\"revision\"] = revision\n    return cast(CrossEncoderModel, CrossEncoder(model_name, **kwargs))\n",
)

# Writer: explicit geometry, semantic-only, independent hybrid budgets, revision/index identity.
replace_once(
    "src/evidence_bundler/contracts/writer.py",
    "from evidence_bundler.models.document import DocumentChunk\n",
    "from evidence_bundler.models.document import ChunkSpec, DocumentChunk\n",
)
replace_once(
    "src/evidence_bundler/contracts/writer.py",
    "    SemanticSearchHit,\n    load_embedding_model,\n)",
    "    SemanticSearchHit,\n    compute_semantic_chunk_set_hash,\n    load_embedding_model,\n)",
)
replace_once(
    "src/evidence_bundler/contracts/writer.py",
    "RETRIEVAL_VALIDATION_SET_VERSION = \"valset-phase-2a-lexical\"\nHYBRID_VALIDATION_SET_VERSION = \"valset-phase-2b-hybrid\"\n",
    "RETRIEVAL_VALIDATION_SET_VERSION = \"valset-phase-2a-lexical\"\nSEMANTIC_VALIDATION_SET_VERSION = \"valset-phase-2b-semantic\"\nHYBRID_VALIDATION_SET_VERSION = \"valset-phase-2b-hybrid\"\n",
)
replace_once(
    "src/evidence_bundler/contracts/writer.py",
    "    retrieval_config = config or RetrievalConfig()\n    _assert_retrieval_method_available(retrieval_config)\n",
    "    retrieval_config = config or RetrievalConfig()\n",
)
replace_once(
    "src/evidence_bundler/contracts/writer.py",
    "    documents = load_source_documents(artifact)\n    chunks = chunk_source_documents(documents)\n",
    "    documents = load_source_documents(artifact)\n    chunk_spec = ChunkSpec(\n        max_chars=retrieval_config.chunk_max_chars,\n        overlap_chars=retrieval_config.chunk_overlap_chars,\n    )\n    chunks = chunk_source_documents(documents, chunk_spec)\n",
)
replace_once(
    "src/evidence_bundler/contracts/writer.py",
    "        f\"- Lexical score floor: `{report.retrieval_config.lexical_score_floor}`\",\n        f\"- Semantic model: `{report.retrieval_config.embedding_model}`\",\n",
    "        f\"- Lexical score floor: `{report.retrieval_config.lexical_score_floor}`\",\n        f\"- Chunk max chars: `{report.retrieval_config.chunk_max_chars}`\",\n        f\"- Chunk overlap chars: `{report.retrieval_config.chunk_overlap_chars}`\",\n        f\"- Semantic model: `{report.retrieval_config.embedding_model}`\",\n        f\"- Semantic model revision: `{report.retrieval_config.embedding_model_revision or 'unpinned'}`\",\n        (\n            \"- Immutable model revisions required: \"\n            f\"`{report.retrieval_config.require_immutable_model_revisions}`\"\n        ),\n",
)
replace_once(
    "src/evidence_bundler/contracts/writer.py",
    "        f\"- RRF candidate pool per retriever: `{report.retrieval_config.rrf_candidate_pool}`\",\n",
    "        f\"- Hybrid lexical candidate pool: `{report.retrieval_config.rrf_candidate_pool}`\",\n",
)
replace_once(
    "src/evidence_bundler/contracts/writer.py",
    "        f\"- Rerank model: `{report.retrieval_config.rerank_model}`\",\n",
    "        f\"- Rerank model: `{report.retrieval_config.rerank_model}`\",\n        f\"- Rerank model revision: `{report.retrieval_config.rerank_model_revision or 'unpinned'}`\",\n",
)
replace_once(
    "src/evidence_bundler/contracts/writer.py",
    "    if config.retrieval_method != \"hybrid\":\n        return None\n",
    "    if config.retrieval_method not in {\"semantic\", \"hybrid\"}:\n        return None\n",
)
replace_once(
    "src/evidence_bundler/contracts/writer.py",
    "        embedder = load_embedding_model(\n            str(config.embedding_model),\n            cache_dir=config.embedding_model_cache_dir,\n        )\n",
    "        embedder = load_embedding_model(\n            str(config.embedding_model),\n            cache_dir=config.embedding_model_cache_dir,\n            revision=(\n                str(config.embedding_model_revision)\n                if config.embedding_model_revision is not None\n                else None\n            ),\n        )\n",
)
replace_once(
    "src/evidence_bundler/contracts/writer.py",
    "                        embedding_model=str(config.embedding_model),\n                        semantic_query_prefix=str(config.semantic_query_prefix)\n",
    "                        embedding_model=str(config.embedding_model),\n                        embedding_model_revision=(\n                            str(config.embedding_model_revision)\n                            if config.embedding_model_revision is not None\n                            else None\n                        ),\n                        chunk_set_hash=compute_semantic_chunk_set_hash(chunks),\n                        semantic_query_prefix=str(config.semantic_query_prefix)\n",
)
replace_once(
    "src/evidence_bundler/contracts/writer.py",
    "            embedding_model=str(config.embedding_model),\n            semantic_query_prefix=str(config.semantic_query_prefix)\n",
    "            embedding_model=str(config.embedding_model),\n            embedding_model_revision=(\n                str(config.embedding_model_revision)\n                if config.embedding_model_revision is not None\n                else None\n            ),\n            semantic_query_prefix=str(config.semantic_query_prefix)\n",
)
replace_once(
    "src/evidence_bundler/contracts/writer.py",
    "        return ParentReranker(load_reranker_model(str(config.rerank_model)))\n",
    "        return ParentReranker(\n            load_reranker_model(\n                str(config.rerank_model),\n                revision=(\n                    str(config.rerank_model_revision)\n                    if config.rerank_model_revision is not None\n                    else None\n                ),\n            )\n        )\n",
)
replace_once(
    "src/evidence_bundler/contracts/writer.py",
    "    if config.retrieval_method == \"hybrid\":\n        if semantic_index is None:\n            raise BundleWriterError(\"Hybrid retrieval requires a semantic index\")\n        return _retrieve_hybrid_claim(\n            claim=claim,\n            retriever=retriever,\n            semantic_index=semantic_index,\n            reranker=reranker,\n            chunks_by_id=chunks_by_id,\n            config=config,\n        )\n\n    hits = retriever.query(\n",
    "    if config.retrieval_method == \"hybrid\":\n        if semantic_index is None:\n            raise BundleWriterError(\"Hybrid retrieval requires a semantic index\")\n        return _retrieve_hybrid_claim(\n            claim=claim,\n            retriever=retriever,\n            semantic_index=semantic_index,\n            reranker=reranker,\n            chunks_by_id=chunks_by_id,\n            config=config,\n        )\n    if config.retrieval_method == \"semantic\":\n        if semantic_index is None:\n            raise BundleWriterError(\"Semantic retrieval requires a semantic index\")\n        return _retrieve_semantic_claim(\n            claim=claim,\n            semantic_index=semantic_index,\n            chunks_by_id=chunks_by_id,\n            config=config,\n        )\n\n    hits = retriever.query(\n",
)
replace_once(
    "src/evidence_bundler/contracts/writer.py",
    "\ndef _retrieve_hybrid_claim(\n",
    "\ndef _retrieve_semantic_claim(\n    *,\n    claim: ScaffoldClaim,\n    semantic_index: SemanticIndex,\n    chunks_by_id: dict[str, DocumentChunk],\n    config: RetrievalConfig,\n) -> tuple[list[CandidateEvidence], RetrievalClaimSummary]:\n    semantic_hits = semantic_index.query(\n        claim.claim_text,\n        top_k=config.semantic_child_top_k,\n    )\n    hits = [\n        ChunkSearchHit(\n            chunk=hit.chunk,\n            score=hit.semantic_score,\n            rank=hit.rank,\n            semantic_score=hit.semantic_score,\n            semantic_rank=hit.rank,\n        )\n        for hit in semantic_hits\n    ]\n    candidates = aggregate_parent_candidates(\n        claim=claim,\n        hits=hits,\n        chunks_by_id=chunks_by_id,\n        config=config,\n    )\n    return candidates, _make_claim_summary(\n        claim=claim,\n        candidates=candidates,\n        hits=hits,\n        lexical_only_child_hits=0,\n        semantic_only_child_hits=len(hits),\n        overlap_child_hits=0,\n        total_fused_child_hits=len(hits),\n    )\n\n\ndef _retrieve_hybrid_claim(\n",
)
replace_once(
    "src/evidence_bundler/contracts/writer.py",
    "    semantic_hits = semantic_index.query(claim.claim_text, top_k=config.rrf_candidate_pool)\n",
    "    semantic_hits = semantic_index.query(claim.claim_text, top_k=config.semantic_child_top_k)\n",
)
replace_once(
    "src/evidence_bundler/contracts/writer.py",
    "\ndef _assert_retrieval_method_available(config: RetrievalConfig) -> None:\n    if config.retrieval_method == \"semantic\":\n        raise BundleWriterError(\n            \"--method semantic is wired in Phase 2b Unit 2/3; not available yet\"\n        )\n\n\ndef _retrieval_validation_set_version(config: RetrievalConfig) -> str:\n",
    "\ndef _retrieval_validation_set_version(config: RetrievalConfig) -> str:\n",
)
replace_once(
    "src/evidence_bundler/contracts/writer.py",
    "def _retrieval_validation_set_version(config: RetrievalConfig) -> str:\n    if config.retrieval_method == \"hybrid\":\n        return HYBRID_VALIDATION_SET_VERSION\n    return RETRIEVAL_VALIDATION_SET_VERSION\n",
    "def _retrieval_validation_set_version(config: RetrievalConfig) -> str:\n    if config.retrieval_method == \"hybrid\":\n        return HYBRID_VALIDATION_SET_VERSION\n    if config.retrieval_method == \"semantic\":\n        return SEMANTIC_VALIDATION_SET_VERSION\n    return RETRIEVAL_VALIDATION_SET_VERSION\n",
)
replace_once(
    "src/evidence_bundler/contracts/writer.py",
    "def _retrieval_validation_set_hash(config: RetrievalConfig) -> str:\n    if config.retrieval_method == \"hybrid\":\n        return hash_text(\"phase-2b-hybrid-validation-set-placeholder-v1\")\n    return hash_text(\"phase-2a-lexical-validation-set-placeholder-v1\")\n",
    "def _retrieval_validation_set_hash(config: RetrievalConfig) -> str:\n    if config.retrieval_method == \"hybrid\":\n        return hash_text(\"phase-2b-hybrid-validation-set-placeholder-v1\")\n    if config.retrieval_method == \"semantic\":\n        return hash_text(\"phase-2b-semantic-validation-set-placeholder-v1\")\n    return hash_text(\"phase-2a-lexical-validation-set-placeholder-v1\")\n",
)
replace_once(
    "src/evidence_bundler/contracts/writer.py",
    "    if config.retrieval_method == \"hybrid\":\n        return \"none (transient)\"\n",
    "    if config.retrieval_method in {\"semantic\", \"hybrid\"}:\n        return \"none (transient)\"\n",
)

# CLI: remove the stale warning and describe the now-independent budgets truthfully.
replace_once(
    "src/evidence_bundler/cli.py",
    "    help=\"Retrieval method. Semantic and hybrid writer paths are not wired until later units.\",\n",
    "    help=\"Retrieval method. BM25, semantic, and hybrid execute through the normal bundle path.\",\n",
)
replace_once(
    "src/evidence_bundler/cli.py",
    "    help=\"Override number of child/leaf BM25 hits to aggregate per claim.\",\n",
    "    help=\"Override BM25-only child/leaf candidate budget per claim.\",\n",
)
replace_once(
    "src/evidence_bundler/cli.py",
    "    help=\"Override number of child/leaf semantic hits to retrieve per claim.\",\n",
    "    help=\"Override semantic child/leaf candidate budget for semantic and hybrid retrieval.\",\n",
)

# Existing end-to-end test must now assert semantic execution rather than the removed rejection.
replace_once(
    "tests/test_bundle_writer.py",
    '''def test_retrieval_bundle_rejects_unwired_semantic_before_writing(\n    mixed_scaffold_run_tmp: Path,\n    tmp_path: Path,\n) -> None:\n    bundle_dir = tmp_path / "evidence-bundle-semantic"\n\n    with pytest.raises(\n        BundleWriterError,\n        match="--method semantic is wired in Phase 2b Unit 2/3; not available yet",\n    ):\n        build_retrieval_bundle(\n            mixed_scaffold_run_tmp,\n            bundle_dir,\n            config=RetrievalConfig(retrieval_method="semantic"),\n        )\n\n    assert not bundle_dir.exists()\n''',
    '''def test_build_retrieval_bundle_semantic_emits_valid_cb_tree(\n    mixed_scaffold_run_tmp: Path,\n    tmp_path: Path,\n    monkeypatch: pytest.MonkeyPatch,\n) -> None:\n    monkeypatch.setattr(\n        "evidence_bundler.contracts.writer.load_embedding_model",\n        lambda *_args, **_kwargs: FakeEmbedder(),\n    )\n    bundle_dir = tmp_path / "evidence-bundle-semantic"\n    report_path = tmp_path / "semantic-report.md"\n\n    result = build_retrieval_bundle(\n        mixed_scaffold_run_tmp,\n        bundle_dir,\n        config=RetrievalConfig(\n            retrieval_method="semantic",\n            top_k=2,\n            semantic_child_top_k=5,\n            embedding_model="fake-semantic-model",\n        ),\n        report_out=report_path,\n    )\n\n    assert result.retrieval_report is not None\n    assert result.retrieval_report.retrieval_config.retrieval_method == "semantic"\n    assert validate_bundle_tree(bundle_dir) == []\n    assert verify_sha256sums(bundle_dir) == []\n    assert any(\n        summary.top_semantic_score is not None\n        for summary in result.retrieval_report.claim_summaries\n        if not summary.no_candidate\n    )\n    assert all(\n        summary.top_lexical_score is None\n        for summary in result.retrieval_report.claim_summaries\n    )\n    report = report_path.read_text(encoding="utf-8")\n    assert "- Retrieval method: `semantic`" in report\n    assert "- Semantic child top-k: `5`" in report\n''',
)

write(
    "tests/test_retrieval_control_surface_rc0.py",
    '''"""Mutation tests for the RC0 retrieval experiment control surface."""\n\nfrom __future__ import annotations\n\nimport sys\nimport types\nfrom pathlib import Path\n\nimport pytest\nfrom pydantic import ValidationError\n\nfrom evidence_bundler.contracts.hashing import hash_text\nfrom evidence_bundler.contracts.writer import _retrieval_config_hash, build_retrieval_bundle\nfrom evidence_bundler.ingest.chunker import chunk_source_document\nfrom evidence_bundler.models.document import ChunkSpec, SourceDocument\nfrom evidence_bundler.models.retrieval import RetrievalConfig\nfrom evidence_bundler.retrieval.embedding_retriever import (\n    SemanticIndexManifest,\n    SemanticIndexManifestMismatch,\n    _validate_manifest,\n    compute_semantic_chunk_set_hash,\n    load_embedding_model,\n)\nfrom evidence_bundler.retrieval.reranker import load_reranker_model\n\nEMBED_REV_A = "5c38ec7c405ec4b44b94cc5a9bb96e735b38267a"\nEMBED_REV_B = "1111111111111111111111111111111111111111"\nRERANK_REV = "233902d25c440f23af6f7d6e94d2946bac0bee0a"\n\n\nclass FakeEmbedder:\n    def encode(self, texts: list[str], **_kwargs: object) -> list[list[float]]:\n        return [_vector_for(text) for text in texts]\n\n\ndef _vector_for(text: str) -> list[float]:\n    lowered = text.lower()\n    return [\n        float("submission" in lowered or "review" in lowered),\n        float("plain" in lowered or "text" in lowered),\n        float("pdf" in lowered or "extraction" in lowered),\n        0.25,\n    ]\n\n\ndef test_model_revision_mutation_changes_identity() -> None:\n    base = RetrievalConfig(\n        retrieval_method="semantic",\n        embedding_model_revision=EMBED_REV_A,\n        require_immutable_model_revisions=True,\n    )\n    mutated = base.model_copy(update={"embedding_model_revision": EMBED_REV_B})\n\n    assert _retrieval_config_hash(base) != _retrieval_config_hash(mutated)\n\n\ndef test_immutable_execution_fails_closed_without_full_commit_revisions() -> None:\n    with pytest.raises(ValidationError, match="requires embedding_model_revision"):\n        RetrievalConfig(\n            retrieval_method="semantic",\n            require_immutable_model_revisions=True,\n        )\n    with pytest.raises(ValidationError, match="full 40-hex commit SHA"):\n        RetrievalConfig(\n            retrieval_method="semantic",\n            embedding_model_revision="main",\n        )\n    with pytest.raises(ValidationError, match="requires rerank_model_revision"):\n        RetrievalConfig(\n            retrieval_method="hybrid",\n            embedding_model_revision=EMBED_REV_A,\n            rerank_enabled=True,\n            require_immutable_model_revisions=True,\n        )\n\n\ndef test_embedding_loader_passes_declared_revision(monkeypatch: pytest.MonkeyPatch) -> None:\n    calls: list[tuple[str, dict[str, object]]] = []\n\n    def fake_sentence_transformer(model_name: str, **kwargs: object) -> object:\n        calls.append((model_name, dict(kwargs)))\n        return object()\n\n    monkeypatch.setitem(\n        sys.modules,\n        "sentence_transformers",\n        types.SimpleNamespace(SentenceTransformer=fake_sentence_transformer),\n    )\n\n    load_embedding_model("model-a", Path("cache-a"), revision=EMBED_REV_A)\n\n    assert calls == [\n        ("model-a", {"cache_folder": "cache-a", "revision": EMBED_REV_A})\n    ]\n\n\ndef test_reranker_loader_passes_declared_revision(monkeypatch: pytest.MonkeyPatch) -> None:\n    calls: list[tuple[str, dict[str, object]]] = []\n\n    def fake_cross_encoder(model_name: str, **kwargs: object) -> object:\n        calls.append((model_name, dict(kwargs)))\n        return object()\n\n    monkeypatch.setitem(\n        sys.modules,\n        "sentence_transformers",\n        types.SimpleNamespace(CrossEncoder=fake_cross_encoder),\n    )\n\n    load_reranker_model("reranker-a", revision=RERANK_REV)\n\n    assert calls == [("reranker-a", {"revision": RERANK_REV})]\n\n\ndef test_semantic_manifest_rejects_revision_and_chunk_set_aliasing() -> None:\n    manifest = SemanticIndexManifest(\n        corpus_hash=hash_text("corpus"),\n        embedding_model="model-a",\n        embedding_model_revision=EMBED_REV_A,\n        chunk_set_hash=hash_text("chunks-a"),\n        embedding_dim=4,\n        chunk_count=2,\n        semantic_query_prefix=None,\n        built_at_utc="2026-08-29T00:00:00Z",\n    )\n\n    with pytest.raises(SemanticIndexManifestMismatch, match="embedding_model_revision"):\n        _validate_manifest(\n            manifest,\n            corpus_hash=manifest.corpus_hash,\n            embedding_model="model-a",\n            embedding_model_revision=EMBED_REV_B,\n            chunk_set_hash=manifest.chunk_set_hash,\n        )\n    with pytest.raises(SemanticIndexManifestMismatch, match="chunk_set_hash"):\n        _validate_manifest(\n            manifest,\n            corpus_hash=manifest.corpus_hash,\n            embedding_model="model-a",\n            embedding_model_revision=EMBED_REV_A,\n            chunk_set_hash=hash_text("chunks-b"),\n        )\n\n\ndef test_chunk_geometry_mutation_changes_identity_and_chunk_set() -> None:\n    text = " ".join(f"token-{index:03d}" for index in range(180))\n    document = SourceDocument(\n        source_id="src-geometry",\n        content_path=Path("content.txt"),\n        content_type="text",\n        raw_text=text,\n        content_hash=hash_text(text),\n        metadata={},\n        passages={},\n    )\n    default_config = RetrievalConfig()\n    mutated_config = RetrievalConfig(chunk_max_chars=240, chunk_overlap_chars=40)\n    default_chunks = chunk_source_document(\n        document,\n        ChunkSpec(\n            max_chars=default_config.chunk_max_chars,\n            overlap_chars=default_config.chunk_overlap_chars,\n        ),\n    )\n    mutated_chunks = chunk_source_document(\n        document,\n        ChunkSpec(\n            max_chars=mutated_config.chunk_max_chars,\n            overlap_chars=mutated_config.chunk_overlap_chars,\n        ),\n    )\n\n    assert _retrieval_config_hash(default_config) != _retrieval_config_hash(mutated_config)\n    assert [chunk.chunk_id for chunk in default_chunks] != [chunk.chunk_id for chunk in mutated_chunks]\n    assert compute_semantic_chunk_set_hash(default_chunks) != compute_semantic_chunk_set_hash(\n        mutated_chunks\n    )\n\n\ndef test_semantic_budget_mutation_changes_pre_fusion_candidates_without_lexical_change(\n    mixed_scaffold_run_tmp: Path,\n    tmp_path: Path,\n    monkeypatch: pytest.MonkeyPatch,\n) -> None:\n    monkeypatch.setattr(\n        "evidence_bundler.contracts.writer.load_embedding_model",\n        lambda *_args, **_kwargs: FakeEmbedder(),\n    )\n    small = build_retrieval_bundle(\n        mixed_scaffold_run_tmp,\n        tmp_path / "hybrid-small-semantic-budget",\n        config=RetrievalConfig(\n            retrieval_method="hybrid",\n            top_k=10,\n            rrf_candidate_pool=4,\n            semantic_child_top_k=1,\n            lexical_score_floor=999.0,\n            embedding_model="fake-semantic",\n        ),\n    )\n    large = build_retrieval_bundle(\n        mixed_scaffold_run_tmp,\n        tmp_path / "hybrid-large-semantic-budget",\n        config=RetrievalConfig(\n            retrieval_method="hybrid",\n            top_k=10,\n            rrf_candidate_pool=4,\n            semantic_child_top_k=4,\n            lexical_score_floor=999.0,\n            embedding_model="fake-semantic",\n        ),\n    )\n\n    assert small.retrieval_report is not None\n    assert large.retrieval_report is not None\n    assert small.retrieval_report.retrieval_config.rrf_candidate_pool == 4\n    assert large.retrieval_report.retrieval_config.rrf_candidate_pool == 4\n    small_summary = small.retrieval_report.claim_summaries[0]\n    large_summary = large.retrieval_report.claim_summaries[0]\n    assert small_summary.total_fused_child_hits == 1\n    assert large_summary.total_fused_child_hits == 4\n    assert small_summary.semantic_only_child_hits == 1\n    assert large_summary.semantic_only_child_hits == 4\n\n\ndef test_default_control_surface_preserves_live_pre_rc0_machinery_defaults() -> None:\n    config = RetrievalConfig()\n    chunk_spec = ChunkSpec()\n\n    assert config.retrieval_method == "bm25"\n    assert config.chunk_max_chars == chunk_spec.max_chars == 1800\n    assert config.chunk_overlap_chars == chunk_spec.overlap_chars == 80\n    assert config.embedding_model_revision is None\n    assert config.rerank_model_revision is None\n    assert config.require_immutable_model_revisions is False\n    assert config.rrf_candidate_pool == 50\n    assert config.semantic_child_top_k == 50\n''',
)

write(
    "research/retrieval_control_surface_rc0/real_model_smoke.py",
    '''"""Hosted real-model pinning smoke for RC0. No retrieval-quality claim is made."""\n\nfrom __future__ import annotations\n\nimport json\nimport math\n\nfrom evidence_bundler.models.retrieval import RetrievalConfig\nfrom evidence_bundler.retrieval.embedding_retriever import load_embedding_model\nfrom evidence_bundler.retrieval.reranker import load_reranker_model\n\nEMBED_MODEL = "BAAI/bge-small-en-v1.5"\nEMBED_REVISION = "5c38ec7c405ec4b44b94cc5a9bb96e735b38267a"\nRERANK_MODEL = "cross-encoder/ms-marco-MiniLM-L6-v2"\nRERANK_REVISION = "233902d25c440f23af6f7d6e94d2946bac0bee0a"\n\n\ndef main() -> None:\n    RetrievalConfig(\n        retrieval_method="hybrid",\n        embedding_model=EMBED_MODEL,\n        embedding_model_revision=EMBED_REVISION,\n        rerank_enabled=True,\n        rerank_model=RERANK_MODEL,\n        rerank_model_revision=RERANK_REVISION,\n        require_immutable_model_revisions=True,\n    )\n    embedder = load_embedding_model(EMBED_MODEL, revision=EMBED_REVISION)\n    vectors = embedder.encode(\n        ["synthetic apparatus receipt"],\n        normalize_embeddings=True,\n        show_progress_bar=False,\n    )\n    vector = vectors.tolist()[0] if hasattr(vectors, "tolist") else vectors[0]\n    reranker = load_reranker_model(RERANK_MODEL, revision=RERANK_REVISION)\n    raw_scores = reranker.predict(\n        [("synthetic query", "synthetic candidate passage")],\n        show_progress_bar=False,\n    )\n    scores = raw_scores.tolist() if hasattr(raw_scores, "tolist") else list(raw_scores)\n    score = float(scores[0])\n    if not vector or not all(math.isfinite(float(value)) for value in vector):\n        raise RuntimeError("Embedding smoke returned an invalid vector")\n    if not math.isfinite(score):\n        raise RuntimeError("Reranker smoke returned a non-finite score")\n    print(\n        json.dumps(\n            {\n                "embedding_model": EMBED_MODEL,\n                "embedding_revision": EMBED_REVISION,\n                "embedding_dim": len(vector),\n                "reranker_model": RERANK_MODEL,\n                "reranker_revision": RERANK_REVISION,\n                "reranker_score_finite": True,\n                "scope": "apparatus execution only; no retrieval-quality claim",\n            },\n            sort_keys=True,\n        )\n    )\n\n\nif __name__ == "__main__":\n    main()\n''',
)

write(
    ".github/workflows/research-retrieval-control-surface-rc0.yml",
    '''name: Research - retrieval control surface RC0\n\non:\n  pull_request:\n    paths:\n      - "src/evidence_bundler/**"\n      - "tests/**"\n      - "research/retrieval_control_surface_rc0/**"\n      - ".github/workflows/research-retrieval-control-surface-rc0.yml"\n      - "pyproject.toml"\n  workflow_dispatch:\n\npermissions:\n  contents: read\n\njobs:\n  deterministic-control-surface:\n    runs-on: ubuntu-latest\n    steps:\n      - uses: actions/checkout@v4\n      - uses: actions/setup-python@v5\n        with:\n          python-version: "3.11"\n      - name: Install package and dev tools\n        run: python -m pip install -e ".[dev]"\n      - name: Run full deterministic suite\n        run: |\n          mkdir -p artifacts/retrieval-control-surface-rc0\n          {\n            echo "commit=$(git rev-parse HEAD)"\n            python -m pytest -q\n          } 2>&1 | tee artifacts/retrieval-control-surface-rc0/pytest.txt\n      - name: Run RC0 mutation tests explicitly\n        run: |\n          python -m pytest -q tests/test_retrieval_control_surface_rc0.py \\\n            2>&1 | tee artifacts/retrieval-control-surface-rc0/mutation-tests.txt\n      - name: Ruff touched machinery\n        run: |\n          python -m ruff check \\\n            src/evidence_bundler/models/retrieval.py \\\n            src/evidence_bundler/retrieval/embedding_retriever.py \\\n            src/evidence_bundler/retrieval/reranker.py \\\n            src/evidence_bundler/contracts/writer.py \\\n            src/evidence_bundler/cli.py \\\n            tests/test_retrieval_control_surface_rc0.py \\\n            tests/test_bundle_writer.py \\\n            research/retrieval_control_surface_rc0/real_model_smoke.py \\\n            2>&1 | tee artifacts/retrieval-control-surface-rc0/ruff.txt\n      - name: Mypy source\n        run: |\n          python -m mypy src 2>&1 | tee artifacts/retrieval-control-surface-rc0/mypy.txt\n      - name: CLI truthfulness receipt\n        run: |\n          evidence-bundler build-bundle --help \\\n            | tee artifacts/retrieval-control-surface-rc0/build-bundle-help.txt\n          ! grep -q "not wired" artifacts/retrieval-control-surface-rc0/build-bundle-help.txt\n          grep -q "semantic" artifacts/retrieval-control-surface-rc0/build-bundle-help.txt\n          grep -q "hybrid" artifacts/retrieval-control-surface-rc0/build-bundle-help.txt\n      - uses: actions/upload-artifact@v4\n        if: always()\n        with:\n          name: retrieval-control-surface-rc0-deterministic-${{ github.sha }}\n          path: artifacts/retrieval-control-surface-rc0/\n          if-no-files-found: warn\n          retention-days: 30\n\n  real-model-pinning-smoke:\n    runs-on: ubuntu-latest\n    timeout-minutes: 30\n    steps:\n      - uses: actions/checkout@v4\n      - uses: actions/setup-python@v5\n        with:\n          python-version: "3.11"\n      - name: Install package\n        run: python -m pip install -e ".[dev]"\n      - name: Execute pinned real models on synthetic inputs\n        run: |\n          mkdir -p artifacts/retrieval-control-surface-rc0-real-model\n          python research/retrieval_control_surface_rc0/real_model_smoke.py \\\n            | tee artifacts/retrieval-control-surface-rc0-real-model/receipt.json\n          sha256sum artifacts/retrieval-control-surface-rc0-real-model/receipt.json \\\n            > artifacts/retrieval-control-surface-rc0-real-model/receipt.sha256\n      - uses: actions/upload-artifact@v4\n        if: always()\n        with:\n          name: retrieval-control-surface-rc0-real-model-${{ github.sha }}\n          path: artifacts/retrieval-control-surface-rc0-real-model/\n          if-no-files-found: warn\n          retention-days: 30\n''',
)

print("RC0 patch staged successfully")
