#!/usr/bin/env python3
"""trend_report.py - Project Sparring v0.7
Walk runs/*/coverage.json, build a coverage-over-time series, render a trend
chart, and lay out a PDF executive summary (trend + latest gap table).

Usage:
    python3 trend_report.py [--runs runs] [--out report.pdf]
"""
import os, sys, glob, json, argparse, datetime as dt

import matplotlib
matplotlib.use("Agg")  # headless
import matplotlib.pyplot as plt
from matplotlib.dates import DateFormatter

from reportlab.lib.pagesizes import letter
from reportlab.lib.units import inch
from reportlab.lib import colors
from reportlab.platypus import (SimpleDocTemplate, Paragraph, Spacer, Image,
                                Table, TableStyle)
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle


def parse_stamp(dirname):
    # runs/20260714-123323 -> datetime
    base = os.path.basename(dirname.rstrip("/"))
    try:
        return dt.datetime.strptime(base, "%Y%m%d-%H%M%S")
    except ValueError:
        return None


def load_series(runs_dir):
    rows = []
    for path in sorted(glob.glob(os.path.join(runs_dir, "*", "coverage.json"))):
        when = parse_stamp(os.path.dirname(path))
        if not when:
            continue
        try:
            d = json.load(open(path))
        except (json.JSONDecodeError, OSError):
            continue
        rows.append({
            "when": when,
            "coverage": float(d.get("coverage", 0.0)),
            "executed": len(d.get("executed", [])),
            "detected": len(d.get("detected", [])),
            "missed": d.get("missed", []),
            "dir": os.path.dirname(path),
        })
    return rows


def make_chart(rows, out_png):
    xs = [r["when"] for r in rows]
    ys = [r["coverage"] * 100 for r in rows]
    fig, ax = plt.subplots(figsize=(7, 3.2))
    ax.plot(xs, ys, marker="o", linewidth=2, color="#c0392b")
    ax.set_ylim(-5, 105)
    ax.set_ylabel("Detection coverage (%)")
    ax.set_title("Sparring - Coverage Over Time")
    ax.grid(True, alpha=0.3)
    if len(rows) == 1:
        ax.annotate("baseline established;\ntrend accrues weekly",
                    xy=(xs[0], ys[0]), xytext=(10, 20),
                    textcoords="offset points", fontsize=8, color="gray")
    ax.xaxis.set_major_formatter(DateFormatter("%m-%d"))
    fig.autofmt_xdate()
    fig.tight_layout()
    fig.savefig(out_png, dpi=130)
    plt.close(fig)


def build_pdf(rows, chart_png, out_pdf):
    styles = getSampleStyleSheet()
    h1 = styles["Title"]
    body = styles["BodyText"]
    small = ParagraphStyle("small", parent=body, fontSize=8, textColor=colors.grey)

    doc = SimpleDocTemplate(out_pdf, pagesize=letter,
                            topMargin=0.7*inch, bottomMargin=0.7*inch)
    story = []
    story.append(Paragraph("Project Sparring - Coverage Report", h1))
    story.append(Paragraph(
        f"Generated {dt.datetime.now().strftime('%Y-%m-%d %H:%M')} | "
        f"{len(rows)} campaign(s) analyzed", small))
    story.append(Spacer(1, 0.2*inch))

    latest = rows[-1]
    summary = (
        f"Latest campaign coverage: <b>{latest['coverage']*100:.0f}%</b> "
        f"({latest['detected']}/{latest['executed']} techniques detected). "
    )
    if len(rows) >= 2:
        delta = (latest["coverage"] - rows[0]["coverage"]) * 100
        arrow = "up" if delta > 0 else ("down" if delta < 0 else "flat")
        summary += f"Trend since first campaign: {delta:+.0f} points ({arrow})."
    else:
        summary += "This is the baseline campaign; trend accrues with each weekly run."
    story.append(Paragraph(summary, body))
    story.append(Spacer(1, 0.2*inch))

    if os.path.exists(chart_png):
        story.append(Image(chart_png, width=6.5*inch, height=3.0*inch))
        story.append(Spacer(1, 0.2*inch))

    # Latest gap table
    story.append(Paragraph("Open gaps (latest campaign)", styles["Heading2"]))
    missed = latest["missed"] or []
    if missed:
        data = [["MITRE Technique", "Status"]] + [[t, "MISSED"] for t in missed]
        tbl = Table(data, colWidths=[3.5*inch, 1.5*inch])
        tbl.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#2c3e50")),
            ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
            ("GRID", (0, 0), (-1, -1), 0.5, colors.grey),
            ("FONTSIZE", (0, 0), (-1, -1), 9),
            ("ROWBACKGROUNDS", (0, 1), (-1, -1),
             [colors.white, colors.HexColor("#f4f6f7")]),
        ]))
        story.append(tbl)
    else:
        story.append(Paragraph("No open gaps - full coverage in the latest campaign.", body))

    doc.build(story)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--runs", default="/home/ubuntuai/caldera/runs")
    ap.add_argument("--out", default="/home/ubuntuai/caldera/sparring-trend.pdf")
    args = ap.parse_args()

    rows = load_series(args.runs)
    if not rows:
        sys.exit(f"[!] No coverage.json files found under {args.runs}")

    png = "/tmp/sparring-trend.png"
    make_chart(rows, png)
    build_pdf(rows, png, args.out)
    print(f"[+] {len(rows)} campaign(s) charted")
    print(f"[+] Latest coverage: {rows[-1]['coverage']*100:.0f}%")
    print(f"[+] PDF written to {args.out}")


if __name__ == "__main__":
    main()
