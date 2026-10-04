# Installed V1 review cycle

`evidence-bundler-v1 run` keeps the fixed 10/3 profile. An unreviewed run writes the native package, the Contract B 1.2 bundle, `review_context.md`, and `review_record.json`.

`review_context.md` is the reading surface. Each primary target shows the claim text, every retained passage with its source and offsets, and a gap sentence when the target has nothing retained. A Markdown passage that does not already contain its nearest preceding ATX heading gets that heading, and a bounded bridge, in a block marked display context. A table passage can also show up to four immediately preceding table lines when the passage itself does not contain them. Display context is not admitted text. Passage spans and passage IDs stay the spans the chunker emitted.

The gap sentences separate five states: retrieval did not run, the target had no sources, retrieval searched and nominated nothing, retrieval nominated candidates and retained none, and retained passages were reviewed with none accepted. An unreviewed retained passage stays `needs-review` and does not get the last sentence.

`review_record.json` uses schema `evidence-bundler-v1-review-record-v1`. Its bindings are the raw input-file SHA-256, the unreviewed native package SHA-256, `eb-v1-integration-10x3-rc0`, the package version, and the profile config SHA-256. Decisions cover the retained proposition/passage pairs exactly. The template leaves `needs-review` and an empty reason. That file cannot be applied until every reason is filled.

Apply it with `--review`. The command rebuilds the unreviewed package in memory, checks the bindings, and writes nothing when they differ. The refusal names the binding that moved and tells you to generate a new record from the current run. A contract that reuses proposition or source IDs still needs a new record, because the input bytes and the unreviewed package hash changed. A matching record is copied to `applied_review_record.json`. Only the decision strings enter the existing admission map. Reasons do not enter the native package or Contract B.

`--admission` still accepts schema `evidence-bundler-admission-v1`: proposition ID, passage ID, and decision. It does not bind the input file or the unreviewed package. Do not pass `--admission` and `--review` together.

This command admits passages for later assessment. It does not decide support, truth, completeness, or Claim Audit Lab correctness. `scripts/qualification/run_v1_workflow_acceptance.py` is local acceptance apparatus. It is not this command, and the synthetic kit does not establish a representative workload. See [the representative workload gate](EB_V1_REPRESENTATIVE_WORKLOAD.md).

The CLI surface version is `2` because `--review` is a supported entry. Package `0.3.0.dev0` changes producer identity, so package hashes from `0.2.1.dev0` do not carry forward. Retrieval, the admission wire, Contract A consumption, and Contract B 1.2 projection are unchanged.
