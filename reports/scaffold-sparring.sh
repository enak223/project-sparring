#!/usr/bin/env bash
# ============================================================
# Project Sparring — repo scaffold
# Run on ubuntuai:  bash scaffold-sparring.sh
# Creates ~/project-sparring with full structure + docs.
# ============================================================
set -e

ROOT=~/project-sparring
mkdir -p "$ROOT"/{caldera/profiles,caldera/operations,n8n,comparison,reports,docs}
cd "$ROOT"

# ---------- .gitignore ----------
cat > .gitignore << 'EOF'
# Environment / secrets — never commit
.env
*.key

# Caldera operation exports may contain host detail
caldera/operations/*.json
!caldera/operations/.gitkeep

# Generated reports (keep samples only)
reports/*.pdf
reports/*.html
!reports/sample_*.md

# Python
__pycache__/
*.py[cod]
.venv/
venv/
*.log

# n8n exports may embed API keys — scrub before committing
# (use: sed -i 's/sk-ant-[a-zA-Z0-9-]*/YOUR_ANTHROPIC_API_KEY/g' n8n/*.json)

# Editor / OS
.vscode/
.idea/
*.swp
.DS_Store
EOF

# ---------- .env.example ----------
cat > .env.example << 'EOF'
# Copy to .env and fill in. Never commit .env.

# --- MITRE Caldera ---
CALDERA_URL=http://192.168.248.20:8888
CALDERA_API_KEY=your_caldera_api_key

# --- Wazuh Indexer (OpenSearch) ---
WAZUH_INDEXER_URL=https://192.168.248.20:9200
WAZUH_INDEXER_USER=admin
WAZUH_INDEXER_PASS=your_indexer_password

# --- Anthropic ---
ANTHROPIC_API_KEY=your_anthropic_api_key

# --- Coverage scoring ---
COVERAGE_ALERT_THRESHOLD=0.70   # flag campaigns below 70% detection coverage
EOF

# ---------- keep empty dirs ----------
touch caldera/operations/.gitkeep caldera/profiles/.gitkeep comparison/.gitkeep

# ---------- ROADMAP.md ----------
cat > ROADMAP.md << 'EOF'
# 🗺️ Project Sparring — Roadmap

Continuous purple-team pipeline: emulate adversary techniques on a schedule,
measure what the detection stack actually caught, and report the gaps.

| Phase | Scope | Status |
|---|---|---|
| **v0.1** | Deploy MITRE Caldera on ubuntuai, enroll Sandcat agents on target VMs, run first manual operation | ⬜ Planned |
| **v0.2** | Pull Caldera operation results (executed TTPs + timestamps) via the Caldera API into n8n | ⬜ Planned |
| **v0.3** | Query Wazuh indexer for detected rules/TTPs in the same operation time window | ⬜ Planned |
| **v0.4** | Comparison engine — map executed ATT&CK techniques vs detected, compute per-campaign coverage score | ⬜ Planned |
| **v0.5** | Claude detection-gap analysis — per-campaign report: what was missed, likely why, recommended detections | ⬜ Planned |
| **v0.6** | Scheduled recurring campaigns + coverage trending over time | ⬜ Planned |

## Definition of done (per phase)
- Reproducible commands / configs committed
- One validated end-to-end run
- Engineering notes captured in `docs/ENGINEERING_NOTES.md`
EOF

# ---------- docs/ENGINEERING_NOTES.md ----------
cat > docs/ENGINEERING_NOTES.md << 'EOF'
# 🔧 Engineering Notes — Project Sparring

Running log of gotchas, decisions, and fixes. Newest at top.

## v0.1 — Caldera deployment
- _TBD_

<!--
Template per entry:
### <short title>
- **Problem:**
- **Cause:**
- **Fix:**
- **ATT&CK / rule refs:**
-->
EOF

# ---------- comparison/README.md ----------
cat > comparison/README.md << 'EOF'
# Comparison Engine

Takes two inputs for a single Caldera operation:

1. **Executed** — list of ATT&CK technique IDs Caldera ran (from the Caldera API,
   operation report `steps[]` → `ability.technique_id`).
2. **Detected** — technique IDs Wazuh fired on in the operation's time window
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
EOF

# ---------- reports/sample_report.md ----------
cat > reports/sample_report.md << 'EOF'
# Detection-Gap Report — (sample placeholder)

> Generated per Caldera campaign in v0.5. This is a structure placeholder.

**Campaign:** op-YYYY-MM-DD-x
**Target:** ubuntu-webserver (agent 003)
**Coverage:** X / Y techniques detected (ZZ%)

## ✅ Detected
| Technique | Name | Wazuh rule(s) |
|---|---|---|

## ❌ Missed
| Technique | Name | Likely reason | Recommended detection |
|---|---|---|---|

## Analyst notes
_Claude-generated summary of the coverage posture and prioritized gaps._
EOF

# ---------- README.md ----------
cat > README.md << 'EOF'
# 🥊 Project Sparring
**Automated Purple Team: Emulate, Measure, Report the Gaps**

![Status](https://img.shields.io/badge/status-scaffolding-lightgrey)
![Caldera](https://img.shields.io/badge/MITRE-Caldera-red)
![Wazuh](https://img.shields.io/badge/Wazuh-4.12-blue)
![n8n](https://img.shields.io/badge/n8n-orchestration-orange)
![Claude](https://img.shields.io/badge/Claude-gap%20analysis-purple)

---

## 📌 Description

Project Sparring is a continuous purple-team pipeline built in a homelab. On a
schedule, **MITRE Caldera** runs adversary-emulation campaigns against the lab
VMs. **n8n** then pulls the list of techniques Caldera actually executed and
compares it against what **Wazuh** actually detected in the same window. **Claude**
turns the difference into a per-campaign **detection-gap report** — and coverage
is scored and trended over time.

**The problem:** Detection rules are usually written and then assumed to work.
Nobody measures what an attacker could do that *wouldn't* trip an alert.

**The solution:** Run the attacks continuously, measure detection coverage against
MITRE ATT&CK, and get a prioritized list of blind spots after every campaign —
so the question "what would we miss?" has a number attached to it.

> 🥊 **Core idea: you don't know your detection works until something swings at it on a schedule.**

This project is the measurement layer above the detection engineering in
**Tripwire** (the rules), **GhostNet** (the pipeline), and **Casefile** (the response).

---

## 🏗️ Architecture

```
                    ┌───────────────────────────┐
                    │   MITRE Caldera (ubuntuai) │
                    │  scheduled operation       │
                    └─────────────┬─────────────┘
                                  │ Sandcat agents
                    ┌─────────────▼─────────────┐
                    │   Target VMs               │
                    │  ubuntu-webserver (.139)   │
                    │  win11-workstation (.128)  │
                    └─────────────┬─────────────┘
                                  │ techniques execute
              ┌───────────────────┴───────────────────┐
              ▼                                        ▼
   ┌────────────────────┐                  ┌────────────────────┐
   │ Caldera API        │                  │  Wazuh detects     │
   │ executed TTPs      │                  │  rule.mitre.id     │
   └─────────┬──────────┘                  └─────────┬──────────┘
             │                                       │
             └──────────────┬────────────────────────┘
                            ▼
                 ┌────────────────────┐
                 │  n8n comparison    │
                 │  executed vs       │
                 │  detected → score  │
                 └─────────┬──────────┘
                           ▼
                 ┌────────────────────┐
                 │  Claude analysis   │
                 │  gap report +      │
                 │  recommended rules │
                 └─────────┬──────────┘
                           ▼
                 ┌────────────────────┐
                 │  Coverage report   │
                 │  + trend over time │
                 └────────────────────┘
```

---

## 🗺️ Roadmap

See [ROADMAP.md](ROADMAP.md) for phase detail.

| Phase | Scope | Status |
|---|---|---|
| **v0.1** | Caldera deploy + agent enrollment + first manual operation | ⬜ Planned |
| **v0.2** | Caldera API → executed TTP extraction in n8n | ⬜ Planned |
| **v0.3** | Wazuh indexer query → detected TTPs in op window | ⬜ Planned |
| **v0.4** | Comparison engine → coverage score | ⬜ Planned |
| **v0.5** | Claude detection-gap report | ⬜ Planned |
| **v0.6** | Scheduled campaigns + coverage trending | ⬜ Planned |

---

## 🧰 Stack

| Layer | Tool |
|---|---|
| Adversary emulation | MITRE Caldera + Sandcat agents |
| Detection | Wazuh 4.12 (manager + indexer) |
| Orchestration | n8n |
| Analysis | Claude API |
| Environment | VMware homelab, 192.168.248.0/24 |

---

## 🗃️ Quote

> "Everyone has a plan until they get punched in the mouth." — the point of Sparring
> is to throw the punches on a schedule, so the gaps show up in a report instead of
> in an incident.

---

## 👤 Author

**Eliezer Fuentes**

Cybersecurity professional — SOC analysis, detection engineering, vulnerability management

GitHub: [@enak223](https://github.com/enak223) • LinkedIn: [eliezerfuentes](https://linkedin.com/in/eliezerfuentes)

**Related projects:** [Tripwire](https://github.com/enak223/project-tripwire) • [GhostNet](https://github.com/enak223/project-ghostnet) • [Casefile](https://github.com/enak223/project-casefile) • [Watchtower](https://github.com/enak223/project-watchtower)
EOF

echo ""
echo "✅ Project Sparring scaffolded at $ROOT"
echo ""
find "$ROOT" -not -path '*/.git/*' | sort | sed "s|$ROOT|.|"