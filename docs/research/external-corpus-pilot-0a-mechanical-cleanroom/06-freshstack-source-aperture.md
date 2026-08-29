# Gate 2 — FreshStack qrel-independent source aperture

## Outcome

`PASS` for the aperture rule itself, subject to Gate 1 reconstruction eligibility of the frozen FreshStack cases.

For each frozen FreshStack information need, the bounded source world is the complete pinned corpus partition for the same externally fixed topic/config. This is `DETERMINISTICALLY DERIVED WITHOUT RETRIEVAL`.

| topic | aperture classification |
|---|---|
| langchain | DETERMINISTICALLY DERIVED WITHOUT RETRIEVAL |
| yolo | DETERMINISTICALLY DERIVED WITHOUT RETRIEVAL |
| laravel | DETERMINISTICALLY DERIVED WITHOUT RETRIEVAL |
| angular | DETERMINISTICALLY DERIVED WITHOUT RETRIEVAL |
| godot | DETERMINISTICALLY DERIVED WITHOUT RETRIEVAL |

## Source-only basis

At frozen FreshStack construction-code commit `f1c4ec96477f5100f10c83798d33b3101db727fa`, `DataLoader` stores the caller-selected `topic` as one dataset subset and loads the corpus from that subset's `train` split and the queries from that same subset's requested split. No retrieval-produced candidate list is needed to define that complete topic partition.

The frozen Pilot 0A preregistration permits a deterministic query-associated source scope available without published relevance labels. Interpreting the complete pinned topic partition as the source world therefore does not rewrite the preregistered rule.

## Explicit exclusions

This decision did not inspect or consume:

- FreshStack qrels;
- nuggets;
- accepted-answer text;
- relevant/non-relevant candidate lists;
- leaderboards;
- benchmark result tables;
- retrieval-produced candidate pools;
- retrieval output of any kind.

## Caveat

Gate 2 does not cure a broken or non-reconstructable frozen query identity. If Gate 1 establishes that one or more frozen cases do not exist at the pinned query revision, those cases cannot proceed merely because a topic-level source aperture exists.
