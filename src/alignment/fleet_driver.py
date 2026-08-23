"""Fleet / multi-node alignment driver + CLI for the M100 heterogeneous builder.

Runs :class:`~alignment.heterogeneous_builder.HeterogeneousTimeSeriesBuilder`
independently per node, writing a per-node aligned Parquet and alignment report,
plus a fleet-level summary. It reuses the loader's node enumeration for
``--all``. Raw data is never modified; nothing is interpolated, forward-filled,
or fabricated; node identity is never crossed. Output is written atomically
(temp file + os.replace) so a failed node cannot leave a misleading artifact,
and failed nodes are recorded explicitly rather than skipped silently.

CLI::

    python src/alignment/fleet_driver.py --dataset-root <path> --output-dir <dir> \
        --nodes 15 16 17
    python src/alignment/fleet_driver.py --dataset-root <path> --output-dir <dir> --all
    python src/alignment/fleet_driver.py ... --reference-role temperature \
        --staleness frequency=120 utilization=200
"""
from __future__ import annotations

import argparse
import json
import os
import sys
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Callable, Iterable, Mapping

# Repo convention: put src/ on the path so `from loader import ...` (used lazily
# by the builder) and `from alignment...` resolve whether run as a script or -m.
_SRC = Path(__file__).resolve().parents[1]
if str(_SRC) not in sys.path:
    sys.path.insert(0, str(_SRC))

from alignment.heterogeneous_builder import (  # noqa: E402
    HeterogeneousTimeSeriesBuilder, BuilderError, DEFAULT_ROLE_METRICS,
    DEFAULT_STALENESS_S,
)

__all__ = ["FleetConfig", "FleetDriver", "FleetError"]


class FleetError(Exception):
    """Raised for fleet-level driver failures (e.g. enumeration without a dataset)."""


def _now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def _atomic_write_bytes(path: Path, write_fn: Callable[[Path], None]) -> None:
    """Write via a temp sibling then os.replace, so partial writes never land."""
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_name(path.name + ".tmp")
    try:
        write_fn(tmp)
        os.replace(tmp, path)
    finally:
        if tmp.exists():
            tmp.unlink()


@dataclass
class FleetConfig:
    """Deterministic, reproducible fleet configuration."""

    dataset_root: str | None = None
    output_dir: str = "v2_research/alignment_output"
    reference_role: str = "temperature"
    role_metrics: dict[str, str] = field(default_factory=lambda: dict(DEFAULT_ROLE_METRICS))
    staleness_s: dict[str, float] = field(default_factory=lambda: dict(DEFAULT_STALENESS_S))

    def as_dict(self) -> dict[str, Any]:
        return {"dataset_root": self.dataset_root, "output_dir": self.output_dir,
                "reference_role": self.reference_role,
                "role_metrics": dict(self.role_metrics),
                "staleness_s": {k: float(v) for k, v in self.staleness_s.items()}}


@dataclass
class FleetDriver:
    """Drive per-node alignment across a fleet.

    Parameters
    ----------
    config:
        Fleet configuration.
    builder:
        Optional pre-built builder (else one is constructed from ``config``).
    loader:
        Optional loader for ``--all`` enumeration (else the builder's loader).
    raw_frames_provider:
        Optional callable ``node -> {role: raw frame}`` used instead of loading
        from disk (for tests). When set, no dataset is required.
    """

    config: FleetConfig
    builder: HeterogeneousTimeSeriesBuilder | None = None
    loader: Any = None
    raw_frames_provider: Callable[[str], Mapping[str, Any]] | None = None

    def __post_init__(self) -> None:
        if self.builder is None:
            source = None if self.raw_frames_provider is not None else self.config.dataset_root
            self.builder = HeterogeneousTimeSeriesBuilder(
                source=source, role_metrics=self.config.role_metrics,
                staleness_s=self.config.staleness_s,
                reference_role=self.config.reference_role)
        if self.loader is None:
            self.loader = getattr(self.builder, "_loader", None)

    # ------------------------------------------------------------------
    def enumerate_all_nodes(self) -> list[str]:
        """All nodes carrying the reference metric (deterministic order)."""
        if self.loader is None:
            raise FleetError(
                "Cannot enumerate nodes with --all: no dataset loader is "
                "configured (set --dataset-root).")
        ref_metric = self.config.role_metrics[self.config.reference_role]
        return [str(n) for n in self.loader.nodes_for_metric(ref_metric)]

    # ------------------------------------------------------------------
    def process_node(self, node: str) -> dict[str, Any]:
        out_dir = Path(self.config.output_dir) / f"node={node}"
        parquet_path = out_dir / "aligned.parquet"
        report_path = out_dir / "report.json"
        frames = self.raw_frames_provider(node) if self.raw_frames_provider else None
        aligned, report = self.builder.build_node(node, raw_frames=frames)

        _atomic_write_bytes(parquet_path, lambda p: aligned.to_parquet(p, index=False))
        _atomic_write_bytes(
            report_path,
            lambda p: p.write_text(json.dumps(report, indent=2, default=str)))

        miss = report.get("missingness", {})
        return {"node": node, "status": "ok", "n_rows": int(len(aligned)),
                "parquet": str(parquet_path), "report": str(report_path),
                "missingness": miss,
                "reference_interval_s": report.get("reference", {}).get("interval_s")}

    # ------------------------------------------------------------------
    def run(self, nodes: Iterable[str | int]) -> dict[str, Any]:
        requested = sorted({str(n) for n in nodes})  # deterministic, de-duplicated
        succeeded: list[dict[str, Any]] = []
        failed: list[dict[str, Any]] = []

        for node in requested:
            try:
                succeeded.append(self.process_node(node))
            except (BuilderError, FleetError) as exc:
                failed.append({"node": node, "status": "failed",
                               "error": f"{type(exc).__name__}: {exc}"})
            except Exception as exc:  # noqa: BLE001 - record, never silently skip
                failed.append({"node": node, "status": "failed",
                               "error": f"{type(exc).__name__}: {exc}"})

        summary = {
            "generated": _now(),
            "config": self.config.as_dict(),
            "reference_role": self.config.reference_role,
            "reference_metric": self.config.role_metrics[self.config.reference_role],
            "effective_staleness_s": {k: float(v) for k, v in self.config.staleness_s.items()},
            "n_requested": len(requested),
            "n_succeeded": len(succeeded),
            "n_failed": len(failed),
            "requested_nodes": requested,
            "succeeded": succeeded,
            "failed": failed,
        }
        out = Path(self.config.output_dir)
        _atomic_write_bytes(
            out / "fleet_summary.json",
            lambda p: p.write_text(json.dumps(summary, indent=2, default=str)))
        return summary


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------
def _parse_staleness(pairs: list[str] | None) -> dict[str, float]:
    out: dict[str, float] = {}
    for item in pairs or []:
        if "=" not in item:
            raise argparse.ArgumentTypeError(
                f"--staleness expects role=seconds, got {item!r}")
        role, val = item.split("=", 1)
        out[role.strip()] = float(val)
    return out


def build_arg_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        prog="fleet_driver",
        description="Fleet/multi-node heterogeneous alignment driver for M100.")
    p.add_argument("--dataset-root", help="M100 record directory (required unless --all is not used and nodes are given from a configured dataset).")
    p.add_argument("--output-dir", default="v2_research/alignment_output",
                   help="Directory for per-node outputs and the fleet summary.")
    g = p.add_mutually_exclusive_group(required=True)
    g.add_argument("--nodes", nargs="+", help="Explicit node ids.")
    g.add_argument("--all", action="store_true",
                   help="Process every node carrying the reference metric.")
    p.add_argument("--reference-role", default="temperature",
                   help="Role whose timestamps form the alignment grid.")
    p.add_argument("--staleness", nargs="+", metavar="ROLE=SECONDS",
                   help="Per-role max-staleness overrides, e.g. frequency=120.")
    return p


def main(argv: list[str] | None = None) -> int:
    args = build_arg_parser().parse_args(argv)
    staleness = dict(DEFAULT_STALENESS_S)
    staleness.update(_parse_staleness(args.staleness))
    config = FleetConfig(
        dataset_root=args.dataset_root, output_dir=args.output_dir,
        reference_role=args.reference_role, staleness_s=staleness)

    if args.all and not args.dataset_root:
        print("ERROR: --all requires --dataset-root.", file=sys.stderr)
        return 2

    driver = FleetDriver(config)
    try:
        nodes = driver.enumerate_all_nodes() if args.all else args.nodes
    except FleetError as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 2

    summary = driver.run(nodes)
    print(f"[{_now()}] fleet: {summary['n_succeeded']}/{summary['n_requested']} "
          f"nodes ok, {summary['n_failed']} failed -> {config.output_dir}")
    for f in summary["failed"]:
        print(f"  FAILED {f['node']}: {f['error']}", file=sys.stderr)
    return 0 if summary["n_failed"] == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
