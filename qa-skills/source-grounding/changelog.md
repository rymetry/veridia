# Changelog

## 0.1.0

- Initial `source-grounding` package (W1). Produces one `SourceMap` per change.
- `trust_level` is deliberately not produced here: its authority is the ingestion layer
  (ADR-0009 Decision 2), and the runner overwrites whatever the model writes.
