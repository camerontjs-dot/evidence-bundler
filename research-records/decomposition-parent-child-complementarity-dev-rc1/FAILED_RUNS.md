# Decomposition + Parent/Child Complementarity Dev RC1 — Preserved Failed Runs

Status: historical evidence record. These runs are not scientific retrieval results and are not to be rewritten.

## Run 33869504444 — pre-generation Ruff stop

- exact head: `d76cfb02e8fb6ac9e208aa756f419a6f399ff15a`
- job: `101011879743`
- artifact: `9935344930`
- artifact ZIP SHA256: `5dc7fc071dc5cdb8432e6c55ce208def998f7ecb701cbdd074dbd13b10eada94`
- deterministic suite: 229 passed / 5 skipped
- experiment boundary tests: 5 passed
- failure: Ruff E501 line-length violations
- generation, Contract A treatment construction, retrieval, and gold analysis: not executed

Interpretation: apparatus formatting failure before any scientific treatment existed. The failure is preserved and does not count as a decomposition/retrieval result.

## Run 33869743401 — generation/context and validation-shell stop

- exact head: `7379dc748c3f7e788ce17711f065cad6f597ebfb`
- tree: `0b5ab4602ec40b59962893e9e2e835ac295e9cab`
- job: `101012643867`
- artifact: `9935447299`
- artifact ZIP SHA256: `dffe32688648e762d043f969ec76d2d6e6e2ec37e4f96f3e7a9a4f3df46c29d6`
- deterministic suite: 229 passed / 5 skipped
- experiment boundary tests: 5 passed
- Ruff with explicit E501 exclusion: passed
- generation-input SHA256: `125f061f3615b96a1101ba8bcb0c70f55f9049405b0b894d049ec219e8c43fed`
- generation-input cases: 6
- supplied source representations: 357

### Generator outcome

FLAN:
- `google/flan-t5-small@14fd6edcfdd71f2ef5b67d4e735fee8bc6d9fd31`
- rows: 12
- declared: 0
- failed: 12
- output SHA256: `76b0fdbd5da1c7eb004d594897a5964c0d1e48e7cf4ac431082ef93057c8666d`
- observed prompt tokenization warning: 26,548 tokens against a 512-token model context

Smol:
- `HuggingFaceTB/SmolLM2-360M-Instruct@a10cc1512eabd3dde888204e902eca88bddb4951`
- rows: 12
- declared: 0
- failed: 12
- output SHA256: `3f175a50f1beb1b46ed34e7744790046a52960067d5cfc8eb8f36c27aead94c9`
- observed prompt tokenization warning: 27,838 tokens against an 8,192-token model context

The generator correctly retained these as failed/abstained decompositions rather than repairing them.

### Contract A fixture construction

- fixture count: 42
- declared: 18
- failed: 24
- manifest SHA256: `4798c371f9a03dbd11e3745829b00feca6f2fd0632ae269cddc4162a7c9796e9`
- exact root/source bytes per case: identical across treatments
- all 42 fixtures printed `VALID` under canonical Contract A validator `42e5f5b3bf38d677445e9d01ea130ba604e53409`

The workflow step nevertheless exited non-zero because `COUNT` was incremented inside a `for ... done | tee` pipeline subshell and was therefore zero in the parent shell when `test "$COUNT" -eq 42` executed.

### Gold boundary

The workflow stopped before:
- fixture-directory freeze step;
- semantic-faithfulness instruments;
- R0/R1/R2/R3 retrieval;
- raw retrieval freeze;
- dev relevance analysis.

No retrieval gold was opened. No retrieval result was observed.

## Successor rule

Do not mutate these outputs or relabel them as successful treatments. Any attempt to obtain functioning independent-model decompositions must be a separately preregistered successor. A successor may correct the prompt-aperture design before retrieval gold, but must preserve these failed runs as evidence and must not tune retrieval based on them.
