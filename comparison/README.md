# Comparison Engine

Takes two inputs for a single Caldera operation:

1. **Executed** — list of ATT&CK technique IDs Caldera ran (from the Caldera API,
   operation report `steps[]` -> `ability.technique_id`).
2. **Detected** — technique IDs Wazuh fired on in the operation''s time window
   (from the indexer: `rule.mitre.id` on alerts between op start/end for the
   target agent).

Outputs a coverage record:

```json
{
  "operation": "op-2026-07-13-a",
  "target_agent": "003",
  "window": { "start": "...", "end": "..." },
  "executed":  ["T1059.004", "T1053.003", "T1070.004"],
  "detected":  ["T1059.004", "T1070.004"],
  "missed":    ["T1053.003"],
  "coverage":  0.67
}
```

`missed` is the point of the whole project — those are the detection gaps that
feed the Claude analysis layer (v0.5).
