"""GLASSCHIP paper-analysis reproducibility runner.

Reproduces every paper deliverable from the FROZEN Phase 2A-2E result JSONs:

    verify source artifacts -> validate locked numbers -> regenerate tables
    -> regenerate figures -> regenerate manifest -> verify paper artifacts.

Read-only w.r.t. Phase 2 artifacts, src/, and raw data. It NEVER reruns the
Phase 2 experiments. The raw dataset is NOT required here (only the frozen
result JSONs are); raw data is needed solely to regenerate Phase 2 itself,
which this runner does not do.

    python v2_research/paper_analysis/run_all.py

Exit code 0 = GREEN (all reproduced + validated); non-zero = a failure.
"""
from __future__ import annotations

import hashlib
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import config as C
from load_results import load_all, write_manifest
import validate_results
import make_tables
import make_figures
import verify_artifacts


def _sha12(p: Path) -> str:
    return hashlib.sha256(p.read_bytes()).hexdigest()[:12]


def step_check_sources() -> bool:
    """Confirm every frozen Phase 2 source JSON exists and is readable."""
    print("== 1. source artifacts ==")
    ok = True
    for phase, path in C.SRC.items():
        if path.is_file():
            print(f"   {phase}: {path}  [{_sha12(path)}]")
        else:
            ok = False
            print(f"   {phase}: MISSING -> {path}")
    if not ok:
        print("   ERROR: a frozen Phase 2 result JSON is missing. The paper "
              "artifacts cannot be reproduced without it. (Raw data is NOT needed "
              "here; only the Phase 2 result JSONs are.)")
    # informational drift check against the previously recorded manifest hashes
    man = C.OUT / "paper_results_manifest.json"
    if ok and man.is_file():
        try:
            recorded = json.loads(man.read_text()).get("source_hashes", {})
            drift = [p for p in C.SRC if p in recorded
                     and recorded[p] != _sha12(C.SRC[p])]
            if drift:
                print(f"   NOTE: source hash changed vs last manifest for: "
                      f"{', '.join(drift)} (manifest will be refreshed).")
        except Exception:  # noqa: BLE001 - drift check is best-effort
            pass
    return ok


def main() -> int:
    for d in (C.OUT, C.FIG_DIR, C.TAB_DIR, C.REP_DIR):
        d.mkdir(parents=True, exist_ok=True)

    if not step_check_sources():
        print("\nGATE: RED (missing source artifacts)")
        return 2

    print("== 2. validate locked numbers ==")
    v = validate_results.validate()
    for c in v["checks"]:
        if not c["ok"]:
            print("   FAIL", c["check"], "| got", c["got"], "| exp", c["expected"])
    print(f"   {v['n_checks'] - v['n_fail']}/{v['n_checks']} passed; "
          f"data_ok={v['data_ok']}")

    print("== 3. regenerate tables ==")
    print("  ", make_tables.make())
    print("== 4. regenerate figures ==")
    make_figures.make()
    print("  ", sorted(p.name for p in C.FIG_DIR.glob("*.pdf")))

    print("== 5. regenerate manifest ==")
    n = write_manifest(load_all(), C.OUT / "paper_results_manifest.json")
    print(f"   {n} rows -> paper_results_manifest.json")

    print("== 6. verify paper artifacts ==")
    art = verify_artifacts.verify()
    if art["ok"]:
        print(f"   PASS ({art['checks']} checks)")
    else:
        for p in art["problems"]:
            print("   -", p)

    (C.REP_DIR / "validation.json").write_text(json.dumps(v, indent=2))

    green = v["data_ok"] and art["ok"]
    print("\nGATE:", "GREEN (reproduced + validated)" if green
          else "RED (validation or artifact check failed)")
    return 0 if green else 1


if __name__ == "__main__":
    sys.exit(main())
