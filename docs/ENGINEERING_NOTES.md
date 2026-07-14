# 🔧 Engineering Notes — Project Sparring

Running log of gotchas, decisions, and fixes. Newest at top.

## v0.2 — Caldera API automation

### API returns 401 even from localhost
- **Problem:** `curl http://localhost:8888/api/v2/operations` returned `401: Unauthorized`, despite older docs saying localhost needs no key.
- **Cause:** Caldera 5.x enforces the API key on all requests, including localhost.
- **Fix:** Send the key in a `KEY:` header on every request: `curl -H "KEY: <key>" ...`.

### API key stored as an unreadable hash
- **Problem:** `api_key_red` in `conf/local.yml` was an Argon2 hash (`$argon2id$...`), not a usable plaintext token — same one-way hashing as the login creds.
- **Cause:** Caldera auto-generated and hashed the key on first run; plaintext is unrecoverable.
- **Fix:** Stop the server, `sed` a known plaintext value into `local.yml` (`api_key_red: <value>`), restart. Config edits only take effect while the server is stopped, since it rewrites local.yml on shutdown.

### Operation "never finishes" / links show status -3
- **Problem:** After launching via API, some links stayed at status `-3` and the op state stayed `running`.
- **Cause:** Agent beacon interval is 30–60s (`sleep_min`/`sleep_max`); the atomic planner issues one ability per check-in, so a Discovery run takes minutes, and an open-ended op keeps re-queueing the last ability.
- **Fix:** Set `auto_close: true` on the operation so it self-terminates after one pass. Poll `pull_executed.py` again after the next beacon to catch pending (`-3`) links. Only status `0` counts as executed for coverage.

### Ephemeral data on restart
- **Problem:** After a server restart, operations AND enrolled agents were gone (`/api/v2/operations` and `/api/v2/agents` both returned `[]`).
- **Cause:** Caldera stores state in memory by default; a restart wipes it.
- **Fix (deferred):** Re-enroll the agent and re-run. For scheduled campaigns (v0.6), make Caldera persistent (systemd service + data volume) so reboots don't reset everything.

## v0.1 — Caldera deployment

### System Python too new for Caldera
- **Problem:** `pip install -r requirements.txt` fails on ubuntuai.
- **Cause:** System Python is 3.14; Caldera targets 3.8-3.11 and several pinned deps have no 3.14 wheels.
- **Fix:** Installed Python 3.11.9 via pyenv (single-threaded build to avoid OOM), created a venv against it. Always activate the venv before running the server.

### Default login rejected
- **Problem:** Cannot log into the Caldera UI with any documented default.
- **Cause:** `conf/default.yml` ships Argon2 hashes, not plaintext; known upstream issue with `--insecure`.
- **Fix:** Created `conf/local.yml` with plaintext creds, started without `--insecure`. Also removes the ship-with-admin/admin risk.

### sandcat plugin won''t enable — go not found
- **Problem:** `Error enabling plugin=sandcat: No such file or directory: go`; agents cannot compile.
- **Cause:** Go toolchain missing (Caldera needs >=1.19 to build the Sandcat agent).
- **Fix:** Installed Go 1.22.5 to /usr/local/go, added to PATH, restarted server.

### Agent deploy times out from target
- **Problem:** curl to the Caldera server from the target times out; agent never enrolls.
- **Cause:** ufw on ubuntuai (default DROP) was not allowing 8888.
- **Fix:** `ufw allow from 192.168.248.0/24 to any port 8888 proto tcp` (subnet-scoped).

### First operation never finishes
- **Problem:** Operation ran ~40 min, re-executing the same discovery ability on a loop.
- **Cause:** Auto Close left at "keep open forever"; the atomic planner loops the final ability.
- **Fix (methodology):** Set Auto Close to "auto close operation". Mark start/end times and score Wazuh with an absolute time filter. See reports/v0.1-smoke-test.md.
