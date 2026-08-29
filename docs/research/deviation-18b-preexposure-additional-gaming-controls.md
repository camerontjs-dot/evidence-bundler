# RC4 deviation 18b: pre-exposure additional gaming controls

## What changed

Before the RC4 scientific object was frozen or any sealed control was executed, adversarial review identified two cheap runtime-only strategies that were not named in the original control list:

- prefer passages that lack obvious synthetic decoy-context markers;
- prefer passages whose substantive-looking sentence appears before neutral filler.

RC4 now includes `runtime_answer_marker_gamer` and `runtime_sentence_position_gamer` as additional promotion-critical weak controls.

## Why

Both strategies can operate without evaluator gold, family labels, decisive IDs, hard-negative IDs, or hidden annotations. If either can clear the target gate, the benchmark would be rewarding presentation regularities rather than the intended semantic retrieval capability.

The generator was also adjusted before freeze so ordinary distractors use declarative neighboring facts rather than a repeated "no answer" presentation. Hard negatives keep high lexical overlap but vary their non-operative context across scenarios.

## Timing and scientific effect

This change was made during pre-freeze construction. No exact BM25, weak/gaming control, Hybrid, or Semantic-only result had been observed on RC4. The target identity, seed `173205`, thresholds, original `control_plan.json`, and `metamorphic_plan.json` were not relaxed or rewritten.

The added controls only increase exposure to falsification. They cannot rescue a failing apparatus.
