# 🔧 Engineering Notes — Project Sparring

Running log of gotchas, decisions, and fixes. Newest at top.

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
