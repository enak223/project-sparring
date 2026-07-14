#!/usr/bin/env python3
"""gap_report.py - Project Sparring v0.5
Turn a coverage record (from correlate.py) into a detection-gap report.
Modes: --api (call Claude) or --prompt-pack (write prompt for manual paste).
Recommendations are scoped to the target platform (linux/windows).
"""
import os, sys, json, argparse, urllib.request, urllib.error

MODEL = "claude-sonnet-4-6"
API_URL = "https://api.anthropic.com/v1/messages"
API_VERSION = "2023-06-01"

SYSTEM = (
    "You are a detection-engineering analyst reviewing a purple-team campaign. "
    "You are given a coverage record: techniques an attacker EXECUTED, which the "
    "defender SIEM DETECTED, and which were MISSED or only PARTIAL (parent-level). "
    "The TARGET PLATFORM is stated in the record; scope every recommendation to THAT "
    "platform only -- do not suggest Windows telemetry for a Linux host or vice versa. "
    "For every missed or partial technique, produce a gap entry. Ground every statement "
    "in the technique IDs provided -- do NOT invent techniques not in the input, and do "
    "NOT claim a detection exists that is not listed. For each gap give: the ATT&CK id and "
    "name, the most likely reason it went undetected, a risk rating of HIGH/MED/LOW "
    "justified by exploit prevalence and blast radius, and ONE concrete recommended "
    "detection (the specific log source or rule logic to add, correct for the platform). "
    "Return STRICT JSON only. No prose, no markdown fences, nothing outside the JSON. "
    "Schema:\n"
    '{"operation": str, "platform": str, "coverage_pct": number, "gaps": '
    '[{"technique_id": str, "technique_name": str, "status": "MISSED"|"PARTIAL", '
    '"reason": str, "risk": "HIGH"|"MED"|"LOW", "recommended_detection": str}], '
    '"top_priority": str}'
)


def build_user_prompt(cov, platform):
    return (
        f"Target platform: {platform}\n\n"
        "Coverage record for this campaign:\n\n"
        + json.dumps(cov, indent=2)
        + f"\n\nProduce the gap report as strict JSON per the schema. "
          f"All recommended detections must be correct for {platform}."
    )


def strip_fences(text):
    t = text.strip()
    if t.startswith("```"):
        t = t.split("\n", 1)[1] if "\n" in t else t[3:]
        if t.rstrip().endswith("```"):
            t = t.rstrip()[:-3]
    return t.strip()


def call_api(system, user):
    key = os.environ.get("ANTHROPIC_API_KEY")
    if not key:
        sys.exit("[!] Set ANTHROPIC_API_KEY for --api mode (or use --prompt-pack).")
    body = json.dumps({
        "model": MODEL, "max_tokens": 2000,
        "system": system, "messages": [{"role": "user", "content": user}],
    }).encode()
    req = urllib.request.Request(API_URL, data=body, headers={
        "x-api-key": key, "anthropic-version": API_VERSION, "content-type": "application/json",
    })
    try:
        with urllib.request.urlopen(req, timeout=60) as r:
            resp = json.loads(r.read().decode())
    except urllib.error.HTTPError as e:
        sys.exit(f"[!] API HTTP {e.code}: {e.read().decode()[:400]}")
    except urllib.error.URLError as e:
        sys.exit(f"[!] Could not reach the API ({e.reason})")
    parts = [b.get("text", "") for b in resp.get("content", []) if b.get("type") == "text"]
    return "".join(parts).strip()


def main():
    ap = argparse.ArgumentParser(description="Generate a detection-gap report from a coverage record.")
    ap.add_argument("coverage_json")
    mode = ap.add_mutually_exclusive_group()
    mode.add_argument("--api", action="store_true")
    mode.add_argument("--prompt-pack", action="store_true")
    ap.add_argument("--platform", help="Target OS (linux/windows). Overrides value in record.")
    ap.add_argument("--out", metavar="FILE")
    args = ap.parse_args()

    try:
        with open(args.coverage_json) as f:
            cov = json.load(f)
    except FileNotFoundError:
        sys.exit(f"[!] File not found: {args.coverage_json}")
    except json.JSONDecodeError as e:
        sys.exit(f"[!] {args.coverage_json} is not valid JSON: {e}")

    platform = args.platform or cov.get("platform") or "linux"
    gaps = (cov.get("missed") or []) + (cov.get("partial") or [])
    if not gaps:
        print("[i] No missed or partial techniques -- nothing to report.")

    user = build_user_prompt(cov, platform)

    if args.prompt_pack:
        text = f"SYSTEM:\n{SYSTEM}\n\n---\n\nUSER:\n{user}\n"
        if args.out:
            open(args.out, "w").write(text)
            print(f"[+] Prompt pack written to {args.out} -- paste into claude.ai.")
        else:
            print(text)
        return

    report = strip_fences(call_api(SYSTEM, user))
    try:
        pretty = json.dumps(json.loads(report), indent=2)
    except json.JSONDecodeError:
        pretty = report
    if args.out:
        open(args.out, "w").write(pretty + "\n")
        print(f"[+] Gap report written to {args.out}")
    else:
        print(pretty)


if __name__ == "__main__":
    main()
