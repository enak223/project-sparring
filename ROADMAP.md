# 🗺️ Project Sparring — Roadmap

Continuous purple-team pipeline: emulate adversary techniques on a schedule,
measure what the detection stack actually caught, and report the gaps.

| Phase | Scope | Status |
|---|---|---|
| **v0.1** | Deploy MITRE Caldera on ubuntuai, enroll Sandcat agents, run first manual operation | Done |
| **v0.2** | Pull executed TTPs from Caldera via REST API (`pull_executed.py`) | Done |
| **v0.3** | Query Wazuh indexer for detected TTPs in the operation window (`pull_detected.py`) | Done |
| **v0.4** | Comparison engine - executed vs detected, compute per-campaign coverage score | Done |
| **v0.5** | Claude detection-gap analysis - what was missed, likely why, recommended detections | Planned |
| **v0.6** | Scheduled recurring campaigns + coverage trending over time | Planned |
| **v0.7** | Historical trend tracking + PDF executive report | Planned |
| **v0.8** | Microsoft Sentinel connector - correlate emulation against a second SIEM | Planned |

## Definition of done (per phase)
- Reproducible commands / configs committed
- One validated end-to-end run
- Engineering notes captured in `docs/ENGINEERING_NOTES.md`
