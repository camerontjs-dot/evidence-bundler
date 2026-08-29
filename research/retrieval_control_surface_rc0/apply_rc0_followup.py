"""Follow-up asserted patch for the stale semantic CLI failure expectation.

Run 33275215806 established that the only pytest failure after the preregistered
RC0 patch was the pre-RC0 test that semantic CLI execution must fail. Replace
that expectation with an end-to-end semantic CLI execution check. This does not
change implementation machinery.
"""

from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]


def replace_once(path: str, old: str, new: str) -> None:
    target = ROOT / path
    text = target.read_text(encoding="utf-8")
    count = text.count(old)
    if count != 1:
        raise RuntimeError(f"Expected exactly one match in {path}, found {count}")
    target.write_text(text.replace(old, new, 1), encoding="utf-8")


replace_once(
    "tests/test_cli.py",
    '''def test_build_bundle_cli_semantic_method_fails_until_wired(
    mixed_scaffold_run_tmp: Path,
    tmp_path: Path,
) -> None:
    output_dir = tmp_path / "evidence-bundle-semantic"
    result = CliRunner().invoke(
        cli,
        [
            "build-bundle",
            str(mixed_scaffold_run_tmp),
            "--output",
            str(output_dir),
            "--method",
            "semantic",
        ],
    )

    assert result.exit_code != 0
    assert "--method semantic is wired in Phase 2b Unit 2/3; not available yet" in result.output
    assert not output_dir.exists()
''',
    '''def test_build_bundle_cli_semantic_method_executes_end_to_end(
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
''',
)

print("RC0 follow-up expectation patch staged successfully")
