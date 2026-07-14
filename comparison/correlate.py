#!/usr/bin/env python3
"""correlate.py - Project Sparring v0.4
Correlate executed (pull_executed.py) vs detected (pull_detected.py) for one
operation and compute a coverage score. Exact / Partial / Missed matching.
"""
import sys, json, argparse


def load(path, required_key):
    try:
        with open(path) as f:
            d = json.load(f)
    except FileNotFoundError:
        sys.exit(f"[!] File not found: {path}")
    except json.JSONDecodeError as e:
        sys.exit(f"[!] {path} is not valid JSON: {e}")
    if required_key not in d:
        sys.exit(f"[!] {path} has no {required_key!r} key -- wrong file?")
    return d


def parent(tid):
    return tid.split(".")[0] if tid else tid


def main():
    ap = argparse.ArgumentParser(description="Correlate executed vs detected techniques.")
    ap.add_argument("executed_json")
    ap.add_argument("detected_json")
    ap.add_argument("--json", metavar="FILE")
    args = ap.parse_args()

    ex = load(args.executed_json, "executed")
    de = load(args.detected_json, "detected")

    ex_op = ex.get("operation_id")
    de_op = de.get("operation_id")
    if ex_op and de_op and ex_op != de_op:
        sys.exit(f"[!] Operation mismatch: executed={ex_op} vs detected={de_op}.")

    executed = sorted(set(ex.get("executed") or []))
    detected = set(de.get("detected") or [])
    detected_parents = {parent(t) for t in detected}

    exact, partial, missed = [], [], []
    for t in executed:
        if t in detected:
            exact.append(t)
        elif parent(t) in detected_parents and parent(t) != t:
            partial.append(t)
        else:
            missed.append(t)

    total = len(executed)
    coverage = round(len(exact) / total, 3) if total else 0.0
    op_name = ex.get("operation", "?")
    window = de.get("window", {})

    print(f"Operation : {op_name}  ({ex_op or de_op})")
    if window:
        print(f"Window    : {window.get(chr(115)+chr(116)+chr(97)+chr(114)+chr(116))} -> {window.get(chr(101)+chr(110)+chr(100))}")
    print(f"Executed  : {total} techniques")
    print(f"Detected  : {len(detected)} techniques (in window)")
    print("-" * 48)
    print(f"EXACT   ({len(exact)}): {', '.join(exact) if exact else '-'}")
    print(f"PARTIAL ({len(partial)}): {', '.join(partial) if partial else '-'}   (parent only)")
    print(f"MISSED  ({len(missed)}): {', '.join(missed) if missed else '-'}")
    print("-" * 48)
    print(f"COVERAGE: {coverage:.1%}  ({len(exact)}/{total} exact)")
    if partial:
        lenient = round((len(exact) + len(partial)) / total, 3)
        print(f"          {lenient:.1%} if partials counted ({len(exact)+len(partial)}/{total})")
    if coverage == 0.0 and total:
        print("  -> every executed technique was SILENT. Gap list = all missed above.")

    record = {
        "operation": op_name, "operation_id": ex_op or de_op, "window": window,
        "executed": executed, "detected": sorted(detected),
        "exact": exact, "partial": partial, "missed": missed, "coverage": coverage,
    }
    if args.json:
        with open(args.json, "w") as f:
            json.dump(record, f, indent=2)
        print(f"\n[+] Coverage record written to {args.json}")


if __name__ == "__main__":
    main()
