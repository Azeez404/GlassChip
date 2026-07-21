"""Metric and node selection for GLASSCHIP-V1 preprocessing.

This is the gate. Nothing downstream runs unless :mod:`validator` returns
``PASS`` for the requested selection. There is deliberately no override
flag: if validation fails, selection raises and preprocessing stops.

Scope is the GLASSCHIP-V1 prototype triple only:

===============  =================  =======  ==============================
Role             Metric             Plugin   Nodes (record 21-03)
===============  =================  =======  ==============================
``temperature``  ``p0_core0_temp``  ipmi     394
``power``        ``p0_power``       ipmi     980
``fan_speed``    ``fan0_0``         ipmi     980
===============  =================  =======  ==============================

All three sample on the same rigid 20 s IPMI grid with a 100 % exact
timestamp match, which is why the triple validates. Metrics from
``ganglia_pub`` (``cpu_user``, ``cpu_speed``) are out of scope for the
prototype and would fail validation anyway.
"""

from __future__ import annotations

from typing import Any, Iterable, Sequence

from loader import DatasetLoader
from validator import DatasetValidator, ValidationError

__all__ = [
    "MetricSelector",
    "SelectionError",
    "IncompatibleSelectionError",
    "GLASSCHIP_V1_METRICS",
    "SUPPORTED_ROLES",
]

#: Role -> metric mapping for the GLASSCHIP-V1 prototype.
GLASSCHIP_V1_METRICS: dict[str, str] = {
    "temperature": "p0_core0_temp",
    "power": "p0_power",
    "fan_speed": "fan0_0",
}

#: Roles this prototype supports. Anything else is out of scope by design.
SUPPORTED_ROLES: frozenset[str] = frozenset(GLASSCHIP_V1_METRICS)


class SelectionError(Exception):
    """Raised when a selection cannot be made at all."""


class IncompatibleSelectionError(SelectionError):
    """Raised when :mod:`validator` returns ``FAIL`` for a selection.

    Preprocessing must stop here. Forcing compatibility is not permitted.
    """


class MetricSelector:
    """Select validated metrics and nodes for preprocessing.

    Parameters
    ----------
    source:
        A :class:`~loader.DatasetLoader`, a :class:`~validator.DatasetValidator`,
        or a dataset path from which both are constructed.

    Raises
    ------
    SelectionError
        If the dataset cannot be opened.

    Examples
    --------
    >>> selector = MetricSelector("datasets/21-03")      # doctest: +SKIP
    >>> selection = selector.select_metrics()            # doctest: +SKIP
    >>> selection["verdict"]                             # doctest: +SKIP
    'PASS'
    """

    def __init__(self, source: DatasetLoader | DatasetValidator | str) -> None:
        try:
            if isinstance(source, DatasetValidator):
                self.validator = source
                self.loader = source.loader
            elif isinstance(source, DatasetLoader):
                self.loader = source
                self.validator = DatasetValidator(source)
            else:
                self.loader = DatasetLoader(source)
                self.validator = DatasetValidator(self.loader)
        except Exception as exc:
            raise SelectionError(f"Could not open dataset: {exc}") from exc

    # ------------------------------------------------------------------
    # Metric selection
    # ------------------------------------------------------------------

    def select_metrics(
        self,
        roles: dict[str, str] | None = None,
        node: str | int | None = None,
    ) -> dict[str, Any]:
        """Select and validate a role-to-metric mapping.

        Parameters
        ----------
        roles:
            Mapping of role to metric name. Defaults to
            :data:`GLASSCHIP_V1_METRICS`.
        node:
            Node used by the validator for timestamp comparison.

        Returns
        -------
        dict
            ``roles``, ``metrics``, ``verdict``, ``validation`` (the full
            validator report), ``limitations``, and ``n_common_nodes``.

        Raises
        ------
        SelectionError
            If a role is unsupported or a metric is absent.
        IncompatibleSelectionError
            If the validator returns ``FAIL``. Preprocessing must stop.

        Notes
        -----
        The validator is the single source of truth. This method never
        adjusts a selection to make it pass; it reports and refuses.
        """
        roles = dict(roles or GLASSCHIP_V1_METRICS)

        unsupported = set(roles) - SUPPORTED_ROLES
        if unsupported:
            raise SelectionError(
                f"Unsupported role(s) {sorted(unsupported)}. The GLASSCHIP-V1 "
                f"prototype supports only {sorted(SUPPORTED_ROLES)}."
            )
        if not roles:
            raise SelectionError("No roles requested.")

        available = set(self.loader.get_available_metrics())
        missing = {r: m for r, m in roles.items() if m not in available}
        if missing:
            raise SelectionError(
                f"Metric(s) absent from the record: {missing}."
            )

        metrics = list(roles.values())

        if len(metrics) == 1:
            report = self.validator.validate_metric(metrics[0])
            verdict = "PASS" if report["exists"] else "FAIL"
            limitations = report["issues"]
            n_common = report["n_nodes"]
        else:
            try:
                report = self.validator.validate_metric_compatibility(
                    metrics, node=node
                )
            except ValidationError as exc:
                raise IncompatibleSelectionError(
                    f"Selection could not be validated: {exc}"
                ) from exc
            verdict = report["verdict"]
            limitations = report["limitations"]
            identifier = report.get("identifier") or {}
            n_common = identifier.get("n_common")

        if verdict == "FAIL":
            blocking = report.get("blocking") or report.get("issues") or []
            raise IncompatibleSelectionError(
                "Validator returned FAIL for this selection; preprocessing "
                "must stop. Blocking issues:\n  - "
                + "\n  - ".join(str(b) for b in blocking)
            )

        return {
            "roles": roles,
            "metrics": metrics,
            "verdict": verdict,
            "validation": report,
            "limitations": limitations,
            "n_common_nodes": n_common,
        }

    # ------------------------------------------------------------------
    # Node selection
    # ------------------------------------------------------------------

    def select_common_nodes(
        self, roles: dict[str, str] | None = None
    ) -> list[str]:
        """Return nodes carrying every selected metric.

        Parameters
        ----------
        roles:
            Role-to-metric mapping. Defaults to
            :data:`GLASSCHIP_V1_METRICS`.

        Returns
        -------
        list of str
            Sorted node IDs present in all selected metrics.

        Raises
        ------
        SelectionError
            If no node carries every metric.
        IncompatibleSelectionError
            Propagated from :meth:`select_metrics`.
        """
        roles = dict(roles or GLASSCHIP_V1_METRICS)
        self.select_metrics(roles)

        try:
            report = self.validator.find_common_nodes(list(roles.values()))
        except ValidationError as exc:
            raise SelectionError(f"Node intersection failed: {exc}") from exc

        nodes = report["common_nodes"]
        if not nodes:
            raise SelectionError(
                f"No node carries all of {sorted(roles.values())}."
            )
        return nodes

    def select_node(
        self,
        node: str | int | None = None,
        roles: dict[str, str] | None = None,
    ) -> str:
        """Select and verify one node.

        Parameters
        ----------
        node:
            Node identifier. ``None`` picks the lowest-numbered common node.
        roles:
            Role-to-metric mapping.

        Returns
        -------
        str
            The verified node ID.

        Raises
        ------
        SelectionError
            If the node does not carry every selected metric.
        """
        common = self.select_common_nodes(roles)

        if node is None:
            return common[0]

        node_id = str(node)
        if node_id not in set(common):
            raise SelectionError(
                f"Node {node_id!r} does not carry all selected metrics. "
                f"{len(common)} nodes do, e.g. {common[:5]}."
            )
        return node_id

    def select_nodes(
        self,
        nodes: Iterable[str | int] | None = None,
        roles: dict[str, str] | None = None,
        limit: int | None = None,
    ) -> list[str]:
        """Select and verify several nodes.

        Parameters
        ----------
        nodes:
            Node identifiers. ``None`` uses every common node.
        roles:
            Role-to-metric mapping.
        limit:
            Cap the returned list. Applied after verification.

        Returns
        -------
        list of str
            Verified node IDs, sorted.

        Raises
        ------
        SelectionError
            If any requested node lacks a selected metric.
        """
        common = self.select_common_nodes(roles)
        common_set = set(common)

        if nodes is None:
            selected = common
        else:
            requested = [str(n) for n in nodes]
            unknown = [n for n in requested if n not in common_set]
            if unknown:
                raise SelectionError(
                    f"Node(s) {unknown[:10]} do not carry all selected "
                    f"metrics."
                )
            selected = self.loader._sort_node_ids(requested)  # noqa: SLF001

        return selected[:limit] if limit is not None else selected

    # ------------------------------------------------------------------
    # Inspection
    # ------------------------------------------------------------------

    def describe_selection(
        self,
        roles: dict[str, str] | None = None,
        node: str | int | None = None,
    ) -> dict[str, Any]:
        """Report on a selection without raising on ``FAIL``.

        Use this to inspect why a selection would be refused.

        Parameters
        ----------
        roles:
            Role-to-metric mapping.
        node:
            Node used for timestamp comparison.

        Returns
        -------
        dict
            ``verdict``, ``blocking``, ``limitations``, and ``allowed``.
        """
        roles = dict(roles or GLASSCHIP_V1_METRICS)
        try:
            selection = self.select_metrics(roles, node=node)
            return {
                "roles": roles,
                "verdict": selection["verdict"],
                "blocking": [],
                "limitations": selection["limitations"],
                "allowed": True,
            }
        except IncompatibleSelectionError as exc:
            return {
                "roles": roles,
                "verdict": "FAIL",
                "blocking": [str(exc)],
                "limitations": [],
                "allowed": False,
            }
        except SelectionError as exc:
            return {
                "roles": roles,
                "verdict": "ERROR",
                "blocking": [str(exc)],
                "limitations": [],
                "allowed": False,
            }

    def __repr__(self) -> str:
        return f"{type(self).__name__}(loader={self.loader!r})"
