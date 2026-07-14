#!/usr/bin/env python3
"""pull_detected.py - Project Sparring v0.3
Given a Caldera operation ID, derive its time window, then query Wazuh for
ATT&CK techniques DETECTED on the target agent during that window.
"""
import os, sys, ssl, json, base64, argparse, datetime as dt
import urllib.request, urllib.error

BUFFER_SECS = 30


def _ctx():
    c = ssl.create_default_context()
    c.check_hostname = False
    c.verify_mode = ssl.CERT_NONE
    return c


def get_json(url, headers):
    req = urllib.request.Request(url, headers=headers)
    try:
        with urllib.request.urlopen(req, timeout=20, context=_ctx()) as r:
            return json.loads(r.read().decode())
    except urllib.error.HTTPError as e:
        sys.exit(f"[!] HTTP {e.code} on {url}: {e.read().decode()[:200]}")
    except urllib.error.URLError as e:
        sys.exit(f"[!] Could not reach {url} ({e.reason})")


def post_json(url, headers, body):
    data = json.dumps(body).encode()
    h = dict(headers); h["Content-Type"] = "application/json"
    req = urllib.request.Request(url, data=data, headers=h, method="POST")
    try:
        with urllib.request.urlopen(req, timeout=20, context=_ctx()) as r:
            return json.loads(r.read().decode())
    except urllib.error.HTTPError as e:
        sys.exit(f"[!] HTTP {e.code} on {url}: {e.read().decode()[:300]}")
    except urllib.error.URLError as e:
        sys.exit(f"[!] Could not reach {url} ({e.reason})")


def parse_ts(s):
    if not s:
        return None
    for fmt in ("%Y-%m-%d %H:%M:%S", "%Y-%m-%dT%H:%M:%SZ", "%Y-%m-%dT%H:%M:%S"):
        try:
            return dt.datetime.strptime(s, fmt).replace(tzinfo=dt.timezone.utc)
        except ValueError:
            continue
    return None


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("operation_id")
    ap.add_argument("--agent", default="ubuntu-webserver")
    ap.add_argument("--json", metavar="FILE")
    args = ap.parse_args()

    cal_url = os.environ.get("CALDERA_URL", "http://localhost:8888")
    cal_key = os.environ.get("CALDERA_API_KEY")
    idx_url = os.environ.get("WAZUH_INDEXER_URL", "https://localhost:9200")
    idx_user = os.environ.get("WAZUH_INDEXER_USER", "admin")
    idx_pass = os.environ.get("WAZUH_INDEXER_PASS")
    if not cal_key:
        sys.exit("[!] Set CALDERA_API_KEY")
    if not idx_pass:
        sys.exit("[!] Set WAZUH_INDEXER_PASS")

    base = cal_url.rstrip("/")
    op = get_json(f"{base}/api/v2/operations/{args.operation_id}", {"KEY": cal_key})
    links = get_json(f"{base}/api/v2/operations/{args.operation_id}/links", {"KEY": cal_key})

    op_name = op.get("name", "?")
    start = parse_ts(op.get("start"))
    if not start:
        sys.exit(f"[!] Could not parse operation start time: {op.get(chr(115)+chr(116)+chr(97)+chr(114)+chr(116))!r}")

    finishes = [parse_ts(l.get("finish")) for l in links if l.get("finish")]
    finishes = [f for f in finishes if f]
    end = (max(finishes) if finishes else dt.datetime.now(dt.timezone.utc)) + dt.timedelta(seconds=BUFFER_SECS)

    start_iso = start.strftime("%Y-%m-%dT%H:%M:%S.000Z")
    end_iso = end.strftime("%Y-%m-%dT%H:%M:%S.000Z")

    auth = base64.b64encode(f"{idx_user}:{idx_pass}".encode()).decode()
    query = {
        "size": 500,
        "query": {"bool": {"must": [
            {"term": {"agent.name": args.agent}},
            {"exists": {"field": "rule.mitre.id"}},
            {"range": {"timestamp": {"gte": start_iso, "lte": end_iso}}},
        ]}},
        "_source": ["timestamp", "rule.mitre.id", "rule.id", "rule.description"],
    }
    res = post_json(f"{idx_url.rstrip(chr(47))}/wazuh-alerts-*/_search",
                    {"Authorization": f"Basic {auth}"}, query)

    hits = res.get("hits", {}).get("hits", [])
    detected = set()
    rows = []
    for h in hits:
        src = h.get("_source", {})
        mitre = (src.get("rule", {}) or {}).get("mitre", {}) or {}
        ids = mitre.get("id", []) or []
        for tid in ids:
            detected.add(tid)
        rows.append({
            "timestamp": src.get("timestamp"),
            "mitre_id": ids,
            "rule_id": (src.get("rule", {}) or {}).get("id"),
            "description": (src.get("rule", {}) or {}).get("description"),
        })
    detected = sorted(detected)

    print(f"Operation : {op_name}  ({args.operation_id})")
    print(f"Agent     : {args.agent}")
    print(f"Window    : {start_iso}  ->  {end_iso}  (+{BUFFER_SECS}s buffer)")
    print(f"Alerts    : {len(hits)} with a MITRE id in window")
    print(f"Detected  : {len(detected)} distinct techniques")
    for t in detected:
        print(f"    + {t}")
    if not detected:
        print("    (none - every executed technique in this window was SILENT)")

    record = {
        "operation": op_name, "operation_id": args.operation_id, "agent": args.agent,
        "window": {"start": start_iso, "end": end_iso},
        "detected": detected, "alerts": rows,
    }
    if args.json:
        with open(args.json, "w") as f:
            json.dump(record, f, indent=2)
        print(f"\n[+] Full detected record written to {args.json}")


if __name__ == "__main__":
    main()
