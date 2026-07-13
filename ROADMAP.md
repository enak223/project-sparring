# 🗺️ Project Sparring — Roadmap

Continuous purple-team pipeline: emulate adversary techniques on a schedule,
measure what the detection stack actually caught, and report the gaps.

| Phase | Scope | Status |
|---|---|---|
| **v0.1** | Deploy MITRE Caldera on ubuntuai, enroll Sandcat agents on target VMs, run first manual operation | ✅ Done |
| **v0.2** | Pull Caldera operation results (executed TTPs + timestamps) via the Caldera API into n8n | ⬜ Planned |
| **v0.3** | Query Wazuh indexer for detected rules/TTPs in the same operation time window | ⬜ Planned |
| **v0.4** | Comparison engine — map executed ATT&CK techniques vs detected, compute per-campaign coverage score | ⬜ Planned |
| **v0.5** | Claude detection-gap analysis — per-campaign report: what was missed, likely why, recommended detections | ⬜ Planned |
| **v0.6** | Scheduled recurring campaigns + coverage trending over time | ⬜ Planned |

## Definition of done (per phase)
- Reproducible commands / configs committed
- One validated end-to-end run
- Engineering notes captured in `docs/ENGINEERING_NOTES.md`
