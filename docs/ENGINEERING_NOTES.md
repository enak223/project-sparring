# 🔧 Engineering Notes — Project Sparring

Running log of gotchas, decisions, and fixes. Newest at top.

## v0.6 — Scheduling + persistence

### Caldera as a systemd service
- **Goal:** Survive terminal close and reboot; no more foreground process.
- **Detail:** Unit at /etc/systemd/system/caldera.service runs the venv Python as user ubuntuai, with `Environment=PATH=` baking in BOTH the venv and /usr/local/go/bin — Go must be on PATH or sandcat fails to compile under systemd. `Restart=on-failure`, `After=docker.service`. Started without --insecure/--build so it loads local.yml and the pre-built UI.

### Secrets in a sourced env file, not the scripts
- **Pattern:** ~/caldera/sparring.env (chmod 600, gitignored via `*.env`) holds ANTHROPIC_API_KEY, CALDERA_API_KEY, and the Wazuh indexer creds. Scripts read them via os.getenv; the wrapper sources the file. Cron runs bare, so the wrapper must source explicitly — .bashrc would not be seen.

### Poll-timeout quirk
- **Observation:** The Discovery profile loops longer than the 10-min poll ceiling (20 x 30s), so runs exhaust MAX_POLLS still "running" and proceed anyway. Data capture is unaffected (3 executed / 0 detected as expected), but for cleaner windows, raise MAX_POLLS or shorten the operation.

### Weekly cron
- **Schedule:** `0 2 * * 0` (Sundays 2 AM) runs sparring_run.sh, logging to cron.log. One command now does the entire loop unattended: launch -> poll -> pull executed -> pull detected -> correlate -> Claude gap report -> timestamped artifacts in runs/ + one-line summary in sparring.log.

## v0.5 — Claude gap-report generation

### LLM output was accurate but not platform-scoped
- **Problem:** First run recommended Windows telemetry (Sysmon, Security EID 4688/4798) for a Linux target — technically correct ATT&CK advice, wrong OS.
- **Cause:** The coverage record didn't state the target platform, so Claude hedged across both OSes.
- **Fix:** Added a `platform` field + `--platform` flag, injected into the prompt with an explicit "scope to THIS platform only" instruction. Second run produced 100% Linux-correct auditd/`/proc`/`/etc/passwd` detections.
- **Lesson:** Validate LLM output against the environment, don't trust it blind — the platform gap was only visible by checking the recommendations against reality.

### Markdown fences despite "JSON only"
- **Problem:** Claude wrapped output in ```json fences even when told not to.
- **Fix:** `strip_fences()` removes them before parsing; parser also keeps raw text on JSON-decode failure so nothing is lost.

### Two modes, one prompt
- **Design:** `--api` (automated, ~sub-cent per report on claude-sonnet-4-6) and `--prompt-pack` (writes the assembled prompt for manual paste, zero cost). Same system prompt both ways, so the prompt-pack is a faithful preview of the API path.

## v0.4 — Correlation engine

### Sub-technique vs parent granularity
- **Problem:** Executed list may carry a sub-technique (T1087.001) while Wazuh reports only the parent (T1087) — naive exact-match would call a real catch "missed."
- **Fix:** Three-way match — EXACT (verbatim), PARTIAL (sub-technique caught only at parent level), MISSED (neither). Partials are reported but do NOT count toward the headline coverage number.

### Coverage = exact only
- **Decision:** Headline coverage = exact_matches / total_executed. Partials shown as a separate "if counted" line.
- **Why:** The strict number is the honest, defensible one — an interviewer can't accuse the metric of inflating itself by counting near-misses as hits.

### Operation-ID safety check
- **Detail:** correlate.py refuses to run if executed and detected records carry different operation_ids — prevents silently correlating mismatched campaigns into garbage.

## v0.3 — Wazuh detected-technique pull

### rule.mitre.id is an array, not a scalar
- **Problem:** Extracting the technique ID assumed a single string; Wazuh returns a list.
- **Cause:** A Wazuh alert can map to multiple ATT&CK techniques, so `rule.mitre.id` is always a JSON array (e.g. `["T1082"]`).
- **Fix:** Iterate the array and add each ID to the detected set, rather than reading a single value.

### Time window auto-derived from the operation
- **Decision:** pull_detected.py takes only the Caldera operation ID, not manual timestamps.
- **Why:** Reading start/end from the operation itself keeps the detected[] window locked to the exact same campaign as executed[] — eliminating the manual-timestamp copying that muddied the v0.1 hand-scored result.
- **Detail:** window = operation `start` -> latest link `finish` (or now, if still running) + 30s buffer. The buffer catches alerts that fire a few seconds after the last technique, since detection is not instantaneous.

### Self-signed cert on the indexer
- **Problem:** HTTPS to the Wazuh indexer (9200) fails cert verification.
- **Cause:** Homelab indexer uses a self-signed certificate.
- **Fix:** Disable verification in the SSL context (CERT_NONE). Acceptable for a homelab; a production build would trust the real CA instead.

### Indexer password was not admin/admin
- **Problem:** `admin:admin` returned Unauthorized against 9200.
- **Cause:** The indexer password is set by `INDEXER_PASSWORD` in the wazuh-docker compose file (default `SecretPassword`), not `admin`.
- **Fix:** Pull the real value from docker-compose.yml; supply via `WAZUH_INDEXER_PASS`. (Note: the manager API on 55000 uses a different `API_PASSWORD` — don't confuse the two.)

## v0.2 — Caldera API automation

### API returns 401 even from localhost
- **Problem:** `curl http://localhost:8888/api/v2/operations` returned `401: Unauthorized`, despite older docs saying localhost needs no key.
- **Cause:** Caldera 5.x enforces the API key on all requests, including localhost.
- **Fix:** Send the key in a `KEY:` header on every request: `curl -H "KEY: <key>" ...`.

### API key stored as an unreadable hash
- **Problem:** `api_key_red` in `conf/local.yml` was an Argon2 hash (`$argon2id$...`), not a usable plaintext token.
- **Cause:** Caldera auto-generated and hashed the key on first run; plaintext is unrecoverable.
- **Fix:** Stop the server, `sed` a known plaintext value into `local.yml`, restart. Config edits only take effect while the server is stopped, since it rewrites local.yml on shutdown.

### Operation "never finishes" / links show status -3
- **Problem:** After launching via API, some links stayed at status `-3` and the op state stayed `running`.
- **Cause:** Agent beacon interval is 30-60s; the atomic planner issues one ability per check-in, so a Discovery run takes minutes, and an open-ended op keeps re-queueing the last ability.
- **Fix:** Set `auto_close: true` on the operation. Poll again after the next beacon to catch pending (`-3`) links. Only status `0` counts as executed.

### Ephemeral data on restart
- **Problem:** After a server restart, operations AND enrolled agents were gone (both APIs returned `[]`).
- **Cause:** Caldera stores state in memory by default; a restart wipes it.
- **Fix (deferred):** Re-enroll and re-run. For scheduled campaigns (v0.6), make Caldera persistent (systemd + data volume).

## v0.1 — Caldera deployment

### System Python too new for Caldera
- **Problem:** `pip install -r requirements.txt` fails on ubuntuai.
- **Cause:** System Python is 3.14; Caldera targets 3.8-3.11 and several pinned deps have no 3.14 wheels.
- **Fix:** Installed Python 3.11.9 via pyenv (single-threaded build to avoid OOM), created a venv against it.

### Default login rejected
- **Problem:** Cannot log into the Caldera UI with any documented default.
- **Cause:** `conf/default.yml` ships Argon2 hashes, not plaintext; known upstream issue with `--insecure`.
- **Fix:** Created `conf/local.yml` with plaintext creds, started without `--insecure`.

### sandcat plugin will not enable - go not found
- **Problem:** `Error enabling plugin=sandcat: No such file or directory: go`; agents cannot compile.
- **Cause:** Go toolchain missing (Caldera needs >=1.19).
- **Fix:** Installed Go 1.22.5 to /usr/local/go, added to PATH, restarted server.

### Agent deploy times out from target
- **Problem:** curl to the Caldera server from the target times out; agent never enrolls.
- **Cause:** ufw on ubuntuai (default DROP) was not allowing 8888.
- **Fix:** `ufw allow from 192.168.248.0/24 to any port 8888 proto tcp` (subnet-scoped).

### First operation never finishes
- **Problem:** Operation ran ~40 min, re-executing the same discovery ability on a loop.
- **Cause:** Auto Close left at "keep open forever".
- **Fix (methodology):** Set Auto Close to "auto close operation". Mark start/end times, score Wazuh with an absolute time filter. See reports/v0.1-smoke-test.md.
