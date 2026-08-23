"""Lightweight paper-artifact verification (read-only).

Checks that the canonical paper deliverables exist and that the manuscript is
free of drafting/process residue. Does NOT modify any file and does NOT rerun
experiments. Run standalone or via run_all.py.

    python v2_research/paper_analysis/verify_artifacts.py
"""
from __future__ import annotations

import re
import sys
from pathlib import Path

import config as C

MANUSCRIPT = Path("v2_research/paper/manuscript.md")
FIGS = [f"fig0{i}_{n}" for i, n in enumerate(
    ["setup", "tau_fidelity", "residual_prediction", "fleet_tau",
     "fidelity_vs_fleet", "streaming_boundary"], start=1)]
TABLES = ["table01_conditions", "table02_tau_identification",
          "table03_residual_prediction", "table04_fleet_streaming"]
# residue patterns that must NOT appear in a submission-ready manuscript
BANNED = {
    "[DRAFT PENDING]": r"DRAFT PENDING",
    "TODO/FIXME": r"\bTODO\b|\bFIXME\b",
    "HTML comment": r"<!--",
    "vscode-webview link": r"vscode-webview",
    "process reference (Phase 3x / STEP N)": r"Phase 3[ABCD]\b|STEP\s+\d",
}


def verify() -> dict:
    problems: list[str] = []
    checks = 0

    def need(path: Path, label: str):
        nonlocal checks
        checks += 1
        if not path.is_file():
            problems.append(f"missing {label}: {path}")

    # manuscript + manifest
    need(MANUSCRIPT, "manuscript")
    need(C.OUT / "paper_results_manifest.json", "results manifest")
    # figures (PDF + PNG) and tables
    for stem in FIGS:
        need(C.FIG_DIR / f"{stem}.pdf", f"figure {stem} (pdf)")
        need(C.FIG_DIR / f"{stem}.png", f"figure {stem} (png)")
    for stem in TABLES:
        need(C.TAB_DIR / f"{stem}.md", f"table {stem}")

    # manuscript residue scan
    if MANUSCRIPT.is_file():
        text = MANUSCRIPT.read_text(encoding="utf-8")
        for label, pat in BANNED.items():
            checks += 1
            hits = len(re.findall(pat, text))
            if hits:
                problems.append(f"manuscript contains {hits} '{label}' occurrence(s)")

    return {"checks": checks, "problems": problems, "ok": not problems}


def main() -> int:
    r = verify()
    if r["ok"]:
        print(f"ARTIFACT VERIFICATION: PASS ({r['checks']} checks)")
        return 0
    print(f"ARTIFACT VERIFICATION: FAIL ({len(r['problems'])} problem(s))")
    for p in r["problems"]:
        print("  -", p)
    return 1


if __name__ == "__main__":
    sys.exit(main())
