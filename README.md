# 🥊 Project Sparring
### Continuous Adversary Emulation & Detection Coverage Scoring

> *"You don't rise to the level of your rules. You fall to the level of your blind spots."*

[![Status](https://img.shields.io/badge/Status-Scaffolding-yellow?style=flat-square)](https://github.com/enak223)
[![Stack](https://img.shields.io/badge/Stack-Caldera%20%7C%20Sentinel%20%7C%20KQL%20%7C%20n8n%20%7C%20Claude-blue?style=flat-square)](https://github.com/enak223)
[![MITRE](https://img.shields.io/badge/MITRE-ATT%26CK%20Scored-red?style=flat-square)](https://attack.mitre.org/)
[![GitHub](https://img.shields.io/badge/GitHub-enak223-181717?style=flat-square&logo=github)](https://github.com/enak223)
[![LinkedIn](https://img.shields.io/badge/LinkedIn-eliezerfuentes-0A66C2?style=flat-square&logo=linkedin)](https://www.linkedin.com/in/eliezerfuentes/)

---

## 📌 Description

**Sparring** answers the one question every other project in this portfolio assumes away: *"What would we miss?"*

GhostNet, Tripwire, and Casefile all start after the detection fired. Sparring starts before it. It runs scheduled **adversary emulation campaigns** against the homelab, then measures — technique by technique — what the detection stack actually caught versus what the attacker actually did. The gap between those two lists is your real security posture, and Sparring scores it on a schedule instead of by accident.

It answers three questions for every campaign:

- **What did the attacker do?** — A set of MITRE ATT&CK techniques executed by MITRE Caldera against live endpoints, logged with timestamps and target hosts.
- **What did we catch?** — The Sentinel analytics rules and Wazuh detections that fired during the campaign window, correlated back to the executed techniques.
- **What did we miss?** — A per-campaign **detection-gap report**, written by Claude, that lists silent techniques, ranks them by risk, and recommends the specific rule to build next.

Not a red-team tool. Not a blue-team tool. A **purple-team scoreboard** that turns detection engineering into a measurable system.

---

## 🏗️ Architecture

```
┌───────────────────────────────────────────────────────────────────────────┐
│                          SPARRING PIPELINE                                │
│                                                                           │
│  ┌──────────────┐      ┌──────────────┐      ┌──────────────────┐         │
│  │   EMULATE    │────▶│    DETECT    │────▶ │     CORRELATE    │         │
│  │              │      │              │      │                  │         │
│  │ MITRE        │      │ Sentinel     │      │ Executed TTPs    │         │
│  │ Caldera      │      │ Analytics +  │      │      vs          │         │
│  │ (scheduled)  │      │ Wazuh Rules  │      │ Fired Detections │         │
│  └──────────────┘      └──────────────┘      └────────┬─────────┘         │
│                                                       │                   │
│  ┌──────────────┐      ┌──────────────┐      ┌────────▼─────────┐         │
│  │   REPORT     │◀────│     SCORE    │◀──── │    IDENTIFY      │         │
│  │              │      │              │      │                  │         │
│  │ Gap Report   │      │ Coverage %   │      │ Silent Techniques│         │
│  │ (Claude)     │      │ per Tactic   │      │ Missed / Partial │         │
│  │ Next Rule    │      │ ATT&CK Map   │      │ Detections       │         │
│  └──────────────┘      └──────────────┘      └──────────────────┘         │
│                                                                           │
└───────────────────────────────────────────────────────────────────────────┘

  Caldera Server ──campaign──▶ Homelab Endpoints ──telemetry──▶ Sentinel / Wazuh
        │                                                            │
        └────────────── executed technique log ──┐    ┌── fired alerts (KQL/API)
                                                 ▼    ▼
                                          n8n Correlation Engine
                                                    │
                                                    ▼
                                            Claude Triage Agent
                                                    │
                                                    ▼
                                        Detection-Gap Report (MD/PDF)
```

---

## 🧰 Tech Stack

| Layer | Tool | Role |
|-------|------|------|
| Adversary Emulation | **MITRE Caldera** | Scheduled ATT&CK campaigns against live endpoints |
| Emulation Fallback | **Atomic Red Team** | Single-technique validation (carries over from Tripwire) |
| SIEM / Detection | **Microsoft Sentinel** | KQL analytics rules, incident generation |
| SIEM / Detection | **Wazuh 4.12** | Host-based detections, homelab agents |
| Analytics Language | **KQL** | Detection logic + coverage correlation queries |
| Orchestration | **n8n** | Campaign scheduling, correlation, report trigger |
| AI Triage | **Claude API** | Gap analysis, risk ranking, next-rule recommendation |
| Framework | **MITRE ATT&CK** | Common language between attacker and defender |
| Reporting | **Python** | Coverage scoring, ATT&CK Navigator layer, PDF export |

---

## ✨ Features

**Scheduled Adversary Emulation**
Caldera runs ATT&CK campaigns against homelab endpoints on a cron schedule — no manual triggering. Each campaign logs the exact techniques executed, target host, and timestamp window.

**Automated Coverage Correlation**
n8n pulls the executed-technique list from Caldera and the fired-detection list from Sentinel + Wazuh over the same window, then joins them by ATT&CK technique ID to classify each as **Detected**, **Partial**, or **Silent**.

**Claude Detection-Gap Reports**
For every silent technique, Claude explains *why it likely went undetected*, ranks it by exploit prevalence and blast radius, and recommends the specific analytics rule or log source to add — the difference between "we're missing T1055" and "here's the rule to catch it."

**Coverage Scoring Over Time**
Each campaign produces a coverage percentage per ATT&CK tactic. Scores are tracked across runs so you can prove detection posture is *improving*, not just claim it.

**ATT&CK Navigator Heatmap**
Auto-generated Navigator layer showing green (detected) / yellow (partial) / red (silent) across the full matrix — the one-slide artifact for any interview.

---

## 🗺️ Roadmap

| Version | Milestone | Status |
|---------|-----------|--------|
| v0.1 | Caldera server deploy + agent enrollment on homelab endpoints | ✅ Done |
| v0.2 | Executed-technique pull from Caldera via REST API (`pull_executed.py`) | ✅ Done |
| v0.3 | Detected-technique pull from Wazuh indexer over the operation window (`pull_detected.py`) | ✅ Done |
| v0.4 | Correlation engine — executed vs detected → coverage score + gaps | ✅ Done |
| v0.5 | Claude gap-report generation + risk ranking | 🔲 Planned |
| v0.6 | Scheduled recurring campaigns + coverage trending over time | 🔲 Planned |
| v0.7 | Historical trend tracking + PDF executive report | 🔲 Planned |
| v0.8 | Microsoft Sentinel connector — correlate emulation against a second SIEM | 🔲 Planned |

---

## 📁 Project Structure

```
project-sparring/
├── README.md
├── caldera/
│   ├── adversary-profiles/      # Custom ATT&CK campaign definitions
│   ├── abilities/               # Technique-specific abilities
│   └── campaign-schedule.md     # Cron cadence + scope notes
├── detections/
│   ├── kql/                     # Sentinel analytics rules
│   └── wazuh/                   # Host-based rule references
├── correlation/
│   ├── sparring-correlate.json  # n8n workflow export
│   └── technique-mapping.md     # Executed vs fired join logic
├── triage/
│   ├── gap-agent-prompt.md      # Claude system prompt
│   └── report-schema.json       # Structured gap-report output
├── scoring/
│   ├── coverage_score.py        # Per-tactic coverage calc
│   └── navigator_layer.py       # ATT&CK Navigator generator
├── reports/
│   └── sample-gap-report.md
└── docs/
    └── architecture.md
```

---

## ⚙️ Setup & Installation

> Runs on the existing VMware homelab. Caldera is the only new component.

**1. Deploy Caldera server (on ubuntuai)**
```bash
git clone https://github.com/mitre/caldera.git --recursive
cd caldera
pip3 install -r requirements.txt
python3 server.py --insecure --build
# Web UI on :8888
```

**2. Enroll agents on target endpoints**
```bash
# From each target (ubuntu-webserver, Windows 11):
# Pull the Sandcat agent from the Caldera server and register it
server="http://192.168.248.20:8888"
curl -s -X POST -H "file:sandcat.go" $server/file/download > splunkd
chmod +x splunkd && ./splunkd -server $server -group red -v
```

**3. Define an adversary profile**
Create a campaign in the Caldera UI (or under `caldera/adversary-profiles/`) chaining techniques across tactics — e.g. T1046 → T1082 → T1543.003 → T1548.003. Note the profile ID for the schedule.

**4. Wire the correlation window in n8n**
Import `correlation/sparring-correlate.json`. Set the Caldera operation-report pull and the Sentinel/Wazuh detection pull to bound the **same** campaign timestamp window.

**5. Connect Sentinel + Wazuh detection sources**
- Sentinel: query fired incidents via the Log Analytics API over the campaign window (KQL below).
- Wazuh: pull alerts from the OpenSearch API on `192.168.248.20:9200`.

**6. Add the Claude gap agent + schedule the campaign**
Drop the system prompt from `triage/gap-agent-prompt.md` into the n8n HTTP Request node, then set the Caldera campaign trigger to a cron cadence (e.g. nightly).

---

## 📐 KQL Analytics Rules

Sparring uses KQL both to **detect** and to **measure detection**. Sample rules:

**1 — Detect: SSH brute force burst**
```kql
Syslog
| where Facility == "auth" and SyslogMessage has "Failed password"
| summarize Attempts = count() by SourceIP = extract(@"from (\d+\.\d+\.\d+\.\d+)", 1, SyslogMessage), bin(TimeGenerated, 5m)
| where Attempts > 10
| project TimeGenerated, SourceIP, Attempts, Technique = "T1110.001"
```

**2 — Detect: suspicious service creation (persistence)**
```kql
Event
| where EventID == 7045
| extend ServiceName = tostring(EventData.ServiceName), ImagePath = tostring(EventData.ImagePath)
| where ImagePath has_any ("\\Temp\\", "\\Users\\Public\\", "powershell", "cmd.exe /c")
| project TimeGenerated, Computer, ServiceName, ImagePath, Technique = "T1543.003"
```

**3 — Measure: coverage correlation (executed vs fired)**
```kql
// ExecutedTTPs = Caldera operation log ingested to a custom table
// FiredDetections = union of Sentinel incidents + Wazuh alerts, tagged by technique
ExecutedTTPs_CL
| where CampaignId_s == "{{campaign_id}}"
| join kind=leftouter (
    FiredDetections_CL
    | where TimeGenerated between (campaign_start .. campaign_end)
    | distinct Technique_s
) on $left.Technique_s == $right.Technique_s
| extend Status = iff(isempty(Technique_s1), "SILENT", "DETECTED")
| summarize Detected = countif(Status == "DETECTED"),
            Silent   = countif(Status == "SILENT") by Tactic_s
| extend CoveragePct = round(100.0 * Detected / (Detected + Silent), 1)
```

---

## 🤖 AI Triage Agent

Claude reads the correlation output and writes the human-facing gap report. It doesn't just label techniques silent — it explains *why* and *what to do next*.

**System prompt (excerpt):**
```
You are a detection engineering analyst. You are given:
  - executed_techniques: TTPs run by Caldera this campaign
  - fired_detections: detections that triggered in the same window
  - silent_techniques: executed TTPs with no matching detection

For each silent technique:
  1. State the technique ID, name, and tactic.
  2. Explain the most likely reason it went undetected
     (missing log source, no rule, rule scoped too narrowly).
  3. Rank risk HIGH/MED/LOW using exploit prevalence + blast radius.
  4. Recommend ONE concrete next detection: the log source or the
     specific KQL/Wazuh rule to build.

Return strict JSON matching report-schema.json. No prose outside JSON.
```

**Output schema (`report-schema.json`):**
```json
{
  "campaign_id": "string",
  "coverage_pct": "number",
  "gaps": [
    {
      "technique_id": "T1055",
      "technique_name": "Process Injection",
      "tactic": "Defense Evasion",
      "reason": "string",
      "risk": "HIGH | MED | LOW",
      "recommended_detection": "string"
    }
  ],
  "top_priority": "T1055"
}
```

---

## 🏠 Homelab Environment

```
                       VMware NAT — 192.168.248.0/24
┌──────────────────────────────────────────────────────────────────────────┐
│                                                                          │
│  ┌──────────────────────────┐        ┌────────────────────────┐          │
│  │  ubuntuai  .20           │        │  Caldera Server        │          │
│  │  Wazuh Mgr + n8n (Docker)│◀──────│  (on ubuntuai :8888)   │          │
│  │  Correlation + Triage    │        │  Schedules campaigns   │          │
│  └───────────┬──────────────┘        └───────────┬────────────┘          │
│              │                                  │ deploys agents         │
│              │ detections                       ▼                        │
│   ┌──────────┴──────────┐      ┌────────────────────────┐                │
│   ▼                     ▼      ▼                        ▼                │
│ ┌──────────────┐  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐   │
│ │ ubuntu-web   │  │  Windows 11  │  │   Kali       │  │  Microsoft   │   │
│ │ .139         │  │  .128        │  │  .130        │  │  Sentinel    │   │
│ │ Wazuh agent  │  │ Wazuh agent  │  │ Manual red / │  │ (cloud SIEM) │   │
│ │ Caldera tgt  │  │ Caldera tgt  │  │ ART fallback │  │ KQL rules    │   │
│ └──────────────┘  └──────────────┘  └──────────────┘  └──────────────┘   │
│                                                                          │
└──────────────────────────────────────────────────────────────────────────┘
```

---

## 🔐 Security Notes

- Caldera runs **isolated on the NAT subnet** — no emulation traffic leaves the homelab.
- Agents enroll with a scoped `red` group; adversary profiles are pinned to specific targets, never wildcarded.
- The `--insecure` flag is homelab-only. A production deployment uses TLS + a real API key.
- API keys (Claude, Sentinel, Wazuh) live in n8n credentials and `.env` — scrubbed with `sed` before every GitHub push (standing practice across all repos).
- Destructive abilities (wipe, ransomware-sim) are **excluded** from scheduled profiles to protect the lab.

---

## 👤 Author

**Eliezer Fuentes** — Cybersecurity Professional

Detection Engineering | Purple Teaming | SOC Automation | Threat Hunting

[![GitHub](https://img.shields.io/badge/GitHub-enak223-181717?logo=github)](https://github.com/enak223)
[![LinkedIn](https://img.shields.io/badge/LinkedIn-eliezerfuentes-0A66C2?logo=linkedin)](https://www.linkedin.com/in/eliezerfuentes/)

---

## 🥊 Quote

> *"Everybody has a plan until they get punched in the mouth."*
> Sparring is where you find out which of your detections can take the hit.
