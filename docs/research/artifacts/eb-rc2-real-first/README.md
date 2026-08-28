# EB RC2 real-output frozen artifacts

These files preserve the exact first legitimate sealed real-Evidence-Bundler output and its exact frozen RC2 evaluation from GitHub Actions run `33208065906`.

They are gzip-compressed with deterministic gzip metadata (`mtime=0`) and then base64 encoded so the exact UTF-8 outputs can remain ordinary repository text.

## Original identities

- raw result: `sealed-real-eb-first.jsonl`
  - SHA256: `05d141abf11eddf90e6f3e1cbbb6f341a9dd495150d0a9f515784fb36722b5ae`
  - uncompressed bytes: `96422`
  - gzip SHA256: `c34aa8fa94bedfdc3bee20bb4498699c4cdb81c29a5c93e3da6532775bfe06d6`
  - base64-file SHA256: `748c0ec2af319b0dce48e62216b9ab3ccaab1d1f7c14a7e4f5b14bdc4dc35138`
- frozen evaluation: `sealed-real-eb-first-evaluation.json`
  - SHA256: `8d7c7b22216126510989c4fb084968de8b67f83451e22ed9461c570e6ba28916`
  - uncompressed bytes: `59438`
  - gzip SHA256: `9a7d819a43b7b22ce71d7b673a1dde1b1de70c2df34a7d821292b96480c6ef1e`
  - base64-file SHA256: `127f9d43323652a11602325d0df0990168ebf10b4014470b53daf38412b8329f`

## Decode

```bash
base64 --decode sealed-real-eb-first.jsonl.gz.b64 | gzip --decompress > sealed-real-eb-first.jsonl
base64 --decode sealed-real-eb-first-evaluation.json.gz.b64 | gzip --decompress > sealed-real-eb-first-evaluation.json
sha256sum sealed-real-eb-first.jsonl sealed-real-eb-first-evaluation.json
```

The resulting SHA256 values must match the original identities above.

The GitHub Actions artifact for the canonical run is artifact `9700464509`, digest `sha256:24369b37c225f28d972074dbceb1f96b14f7062ccc3418fba4c42be1bec84b72`.
