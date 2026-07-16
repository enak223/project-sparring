# Sparring Detections

Detection rules built to close the gaps Sparring itself surfaced. Each maps to a
MITRE ATT&CK technique the pipeline reported as uncovered.

## Two-layer architecture

Detection on Linux endpoints is a two-layer chain — both layers are required:

1. **auditd** (`auditd/sparring.rules`, deployed on the endpoint) generates a
   kernel audit event when a discovery command runs, tagged with a per-technique
   key (`sparring_t1033`, etc.).
2. **Wazuh** (`wazuh/sparring_rules.xml`, on the manager) matches those events and
   stamps the ATT&CK technique ID into `rule.mitre.id` — which is what makes the
   detection register on the coverage map and what `pull_detected.py` queries.

auditd alone logs locally but produces no SIEM alert. Wazuh alone has nothing to
match without auditd feeding it. Both, chained, turn a shell command into a
tagged, ATT&CK-mapped alert.

## Coverage closed

| Technique | Name | auditd key | Wazuh rule | Notes |
|-----------|------|-----------|-----------|-------|
| T1033 | System Owner/User Discovery | sparring_t1033 | 100600 | whoami/id also caught by existing Tripwire rules |
| T1057 | Process Discovery | sparring_t1057 | built-in 92604 | Wazuh ships a tagged rule; no custom rule needed |
| T1087.001 | Local Account Discovery | sparring_t1087 | 100601 | getent + read-watches on /etc/passwd,/etc/shadow |

## Key finding: untagged detection is not a blind spot

Sparring first reported T1057 as MISSED. Investigation showed the detection
already existed — built-in Wazuh rule 92604 was firing on `ps` — but the pipeline
scored it as a gap. The real issue was that a detection only counts toward
coverage if it carries an ATT&CK `mitre.id` tag. The gap was rule enrichment and
tagging, not missing visibility. This distinction — a detection that fires but
does not register on the coverage map — is a common and easily-missed source of
overstated blind spots.

## Deploy

**Endpoint (auditd):**

**Manager (Wazuh):** append `wazuh/sparring_rules.xml`s `<group>` to
`/var/ossec/etc/rules/local_rules.xml`, then restart the manager. Verify a
`w`, `who`, or `getent passwd` command produces an alert with the expected
`rule.mitre.id`.
