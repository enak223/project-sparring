#!/usr/bin/env python3
"""
pull_executed.py — Project Sparring v0.2
Pull executed ATT&CK techniques from a Caldera operation via the REST API.
Outputs a summary (deduped technique IDs, status 0) + full raw dump.

Usage:
    export CALDERA_URL=http://localhost:8888
    export CALDERA_API_KEY=sparring-api-2026
    python3 pull_executed.py <operation_id> [--json out.json]
"""
import os, sys, json, argparse, urllib.request, urllib.error


def get(url, api_key, path):
    req = urllib.request.Request(url.rstrip("/") + path, headers={"KEY": api_key})
    try:
        with urllib.request.urlopen(req, timeout=15) as r:
            return json.loads(r.read().decode())
    except urllib.error.HTTPError as e:
        sys.exit(f"[!] HTTP {e.code} on {path}: {e.read().decode()[:200]}")
    except urllib.error.URLError as e:
        sys.exit(f"[!] Could not reach Caldera at {url} ({e.reason}). Is the server running?")


def main():
    ap = argparse.ArgumentParser(description="Pull executed techniques from a Caldera operation.")
    ap.add_argument("operation_id", help="Caldera operation UUID")
    ap.add_argument("--json", metavar="FILE", help="Write the full coverage record to FILE")
    args = ap.parse_args()

    url = os.environ.get("CALDERA_URL", "http://localhost:8888")
    api_key = os.environ.get("CALDERA_API_KEY")
    if not api_key:
        sys.exit("[!] Set CALDERA_API_KEY (e.g. export CALDERA_API_KEY=sparring-api-2026)")

    op = get(url, api_key, f"/api/v2/operations/{args.operation_id}")
    links = get(url, api_key, f"/api/v2/operations/{args.operation_id}/links")

    op_name = op.get("name", "?")
    op_state = op.get("state", "?")

    raw = []
    for l in links:
        ab = l.get("ability", {}) or {}
        raw.append({
            "status": l.get("status"),
            "technique_id": ab.get("technique_id"),
            "technique_name": ab.get("technique_name"),
            "ability": ab.get("name"),
            "paw": l.get("paw"),
            "host": l.get("host"),
            "finish": l.get("finish"),
        })

    executed = sorted({r["technique_id"] for r in raw if r["status"] == 0 and r["technique_id"]})
    pending = sorted({r["technique_id"] for r in raw if r["status"] == -3 and r["technique_id"]})

    print(f"Operation : {op_name}  ({args.operation_id})")
    print(f"State     : {op_state}")
    print(f"Links     : {len(raw)} total")
    print(f"Executed  : {len(executed)} distinct techniques (status 0)")
    for t in executed:
        print(f"    + {t}")
    if pending:
        print(f"Pending   : {len(pending)} awaiting beacon (status -3): {', '.join(pending)}")
    if op_state != "finished":
        print("  [note] operation not finished — re-run after the next beacon to catch pending links.")

    record = {
        "operation": op_name,
        "operation_id": args.operation_id,
        "state": op_state,
        "executed": executed,
        "pending": pending,
        "raw_links": raw,
    }

    if args.json:
        with open(args.json, "w") as f:
            json.dump(record, f, indent=2)
        print(f"\n[+] Full coverage record written to {args.json}")

    return record


if __name__ == "__main__":
    main()
