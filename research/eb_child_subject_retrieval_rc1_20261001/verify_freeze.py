"""Direct Git-object/source-scope verifier; emits identities, never scientific support."""

from __future__ import annotations

import subprocess

from study import HERE, BoundaryError, canonical, load, policy, require


def git(*args: str) -> str:
    return subprocess.check_output(["git", "-C", str(HERE.parents[1]), *args], text=True).strip()


def verify() -> dict:
    candidate = load(HERE / "CANDIDATE.json")
    require(
        git("rev-parse", candidate["source_commit"] + "^{tree}") == candidate["source_tree"],
        "candidate source tree mismatch",
    )
    subprocess.run(
        [
            "git",
            "-C",
            str(HERE.parents[1]),
            "merge-base",
            "--is-ancestor",
            candidate["source_commit"],
            "HEAD",
        ],
        check=True,
    )
    for filename, blob in candidate["frozen_blobs"].items():
        require(git("hash-object", str(HERE / filename)) == blob, "frozen apparatus blob drift")
    workflow = HERE.parents[1] / ".github/workflows/research-eb-child-subject-rc1.yml"
    require(
        git("hash-object", str(workflow)) == candidate["workflow_blob"], "frozen workflow drift"
    )
    baseline = policy()["baseline"]["commit"]
    protected = git(
        "diff",
        "--name-only",
        baseline,
        "HEAD",
        "--",
        "src",
        "scripts/run_v1_integration_candidate.py",
        "config/eb_v1_slice",
        "pyproject.toml",
    )
    require(not protected, "protected production bytes changed")
    require(not git("status", "--porcelain"), "candidate worktree is dirty")
    return {
        "schema": "eb-child-subject-source-freeze-check-v1",
        "head": git("rev-parse", "HEAD"),
        "source_commit": candidate["source_commit"],
        "source_tree": candidate["source_tree"],
        "protected_bytes": "IDENTICAL",
        "scientific_execution": "NOT_RUN",
        "execution_readiness": candidate["execution_readiness"],
    }


if __name__ == "__main__":
    try:
        print(canonical(verify()).decode())
    except (BoundaryError, OSError, KeyError, subprocess.CalledProcessError) as exc:
        print(canonical({"state": "BLOCKED", "error": str(exc)}).decode())
        raise SystemExit(2) from exc
