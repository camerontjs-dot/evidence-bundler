# Local qualification handoff

This is the required execution path while hosted GitHub runner quota is unavailable.

## Authority pins

Evidence Bundler candidate branch:

`research-infra/eb-v1-integration-candidate-20260915`

Frozen V1 implementation ancestor:

`c4e3f97ec8f0bd36180954c3aa382418925bf947`

CAL consumer candidate for the cross-repository intake check:

`4d1b8909f7e2e52c33cf99632be8565f2685f948`

Released Contract B production lock:

`c314e53bd91c0736aa4370a364673b069aceb43e`

Do not substitute newer component heads during this qualification. If a pin must change, stop and create a successor qualification identity.

## 1. Prepare exact Evidence Bundler worktree

```bash
git fetch origin
git worktree add ../eb-v1-integration-qualification \
  origin/research-infra/eb-v1-integration-candidate-20260915
cd ../eb-v1-integration-qualification

git status --short
git rev-parse HEAD
git merge-base --is-ancestor c4e3f97ec8f0bd36180954c3aa382418925bf947 HEAD
```

Require a clean worktree and a successful ancestor check.

Use Python 3.11 or 3.12. The maintained strict mypy target is Python 3.11.

```bash
python3.11 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
python -m pip install -e '.[dev]'
```

## 2. Component and boundary qualification

Run the dedicated V1 suites first:

```bash
python -m pytest -q tests/test_v1_package.py tests/test_v1_contract_b_projection.py
python -m ruff check src/evidence_bundler/v1 scripts/run_v1_integration_candidate.py \
  tests/test_v1_package.py tests/test_v1_contract_b_projection.py
python -m ruff format --check src/evidence_bundler/v1/contract_b.py scripts/run_v1_integration_candidate.py \
  tests/test_v1_contract_b_projection.py
python -m mypy --strict src/evidence_bundler/v1 scripts/run_v1_integration_candidate.py
python -m compileall -q src/evidence_bundler/v1 scripts/run_v1_integration_candidate.py
python -m pip check
```

Successor qualification protocol (post-`74dcbc4`): historical CI at the frozen
V1 commit `c4e3f97` used Ruff 0.16.7 but ran `ruff check`, not
`ruff format --check`; there is therefore no evidence that Ruff formatting is
a frozen-V1 invariant. The exact-diff guard in §4 for the six frozen V1 files
is preserved and remains the frozen-file authority. Formatter qualification
applies only to candidate-owned/new Python surfaces
(`src/evidence_bundler/v1/contract_b.py`,
`scripts/run_v1_integration_candidate.py`,
`tests/test_v1_contract_b_projection.py`). The preserved `74dcbc4` run
(strict-mypy 6 errors, `V1 Convergence Qualification`
`UNRESOLVED_AT_AUTHORIZED_BOUND`, CI Python 3.11 fail) is not reinterpreted
as passing.

Then run the maintained repository suite:

```bash
python -m pytest -q
```

Do not reinterpret an unexpected failure as an irrelevant test without first localizing it and preserving the failure.

## 3. Exact CAL Contract B consumer check

Use a separate CAL worktree at the exact candidate commit:

```bash
cd ..
git -C claim-audit-lab fetch origin
git -C claim-audit-lab worktree add ../cal-v1-intake-qualification \
  4d1b8909f7e2e52c33cf99632be8565f2685f948
cd eb-v1-integration-qualification
source .venv/bin/activate
python -m pip install --no-deps -e ../cal-v1-intake-qualification
python -m pytest -q \
  tests/test_v1_contract_b_projection.py::test_exact_cal_contract_b_consumer_accepts_projection_when_installed
```

Verify the CAL worktree identity immediately before the test:

```bash
test "$(git -C ../cal-v1-intake-qualification rev-parse HEAD)" = \
  "4d1b8909f7e2e52c33cf99632be8565f2685f948"
```

This consumer check proves only B1.2 intake/semantic-context construction. It must not be used to tune Evidence Bundler based on CAL outcome semantics.

## 4. Candidate identity checks

Record:

```bash
git rev-parse HEAD
git rev-parse HEAD^{tree}
sha256sum research/eb_v1_integration_candidate/INTEGRATION_PROFILE.json
sha256sum research/eb_v1_integration_candidate/contract_b_compatibility_carrier.json
```

Also verify that the frozen V1 implementation files are unchanged relative to `c4e3f97...`. At minimum:

```bash
git diff --exit-code c4e3f97ec8f0bd36180954c3aa382418925bf947 -- \
  src/evidence_bundler/v1/__init__.py \
  src/evidence_bundler/v1/__main__.py \
  src/evidence_bundler/v1/builder.py \
  src/evidence_bundler/v1/contract_a.py \
  src/evidence_bundler/v1/package.py \
  src/evidence_bundler/v1/retrieval.py
```

`src/evidence_bundler/v1/contract_b.py` is the new downstream projection boundary and is intentionally absent from the frozen implementation commit.

## 5. Freeze rule

If every required local check passes:

1. preserve the terminal output/command receipt under `research/eb_v1_integration_candidate/qualification/`;
2. update `CANDIDATE.json` status to `EVIDENCE_BUNDLER_V1_INTEGRATION_CANDIDATE_FROZEN`;
3. record exact candidate commit/tree plus local environment identity;
4. commit and push only the qualification receipt/freeze record;
5. update the Draft PR body with the exact tested head and result;
6. do not merge, tag, release, or alter production defaults.

If a test fails, preserve the failure and stop. Fixes that alter candidate behavior require a new candidate commit followed by the full affected qualification sequence.

## 6. Pipeline-use command after freeze

For each Contract A handoff, use the dedicated runner rather than the generic V1 CLI so the 10/3 candidate cannot silently fall back to the generic 5/3 default:

```bash
python scripts/run_v1_integration_candidate.py \
  CONTRACT_A.json \
  --admission ADMISSION.json \
  --compatibility-carrier \
  research/eb_v1_integration_candidate/contract_b_compatibility_carrier.json \
  --out-dir RUN_DIR/eb
```

If there is no explicit admission file yet, omit `--admission`; retained candidates will remain `needs-review` rather than being automatically accepted.

Expected outputs:

```text
RUN_DIR/eb/native_eb_v1_package.json
RUN_DIR/eb/contract_b/
RUN_DIR/eb/projection_receipt.json
```

Preserve all three. The native package remains the retrieval-trace authority; Contract B is the downstream handoff; the receipt binds the two.
