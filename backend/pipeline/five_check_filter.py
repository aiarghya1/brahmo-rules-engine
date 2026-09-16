"""Stage 4 — the five-check sequential filter.

Strictly sequential: the output of check N is the input of check N+1. That
ordering is a security property, not an optimisation. A node the user is not
cleared for must never reach the permission check, never be temporally
evaluated, never be scored — the cheapest and most absolute exclusions run
first, and nothing downstream can resurrect an excluded node.

  1 ISOLATION     org_id = :org                       multi-tenant boundary
  2 COMPLIANCE    NOT (compliance_tags && :blocked)    tag clearance
  3 PERMISSION    hierarchy_level >= :ceiling          via the compiled O(1) map
  4 TEMPORAL      not superseded / not expired         currency
  5 DERIVABILITY  derivability_score < :threshold      token economy

Each check carries the SQL predicate it is the in-process equivalent of, so the
UI can show that this is a WHERE clause, not application-side post-filtering.
"""
import time
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Callable, Dict, FrozenSet, List, Optional, Sequence, Tuple

from backend.models.candidate_set import StageResult
from backend.models.node import NodeFilterRow
from backend.pipeline.permission_compiler import CompiledPermissions

# Statuses that mean "this node is no longer the current truth".
DEAD_STATUSES = ("SUPERSEDED", "EXPIRED")

# A check returns None to keep the node, or a reason string to drop it.
CheckFn = Callable[[NodeFilterRow], Optional[str]]


@dataclass
class FilterOutcome:
    survivors: List[NodeFilterRow]
    stages: List[StageResult]

    def to_dict(self) -> dict:
        return {
            "survivor_ids": [n.id for n in self.survivors],
            "stages": [s.to_dict() for s in self.stages],
        }


def _check_isolation(org_id: str) -> Tuple[str, str, CheckFn]:
    def check(node: NodeFilterRow) -> Optional[str]:
        if node.org_id != org_id:
            return "belongs to org '{}', session org is '{}'".format(node.org_id, org_id)
        return None

    return (
        "isolation",
        "WHERE org_id = '{}'".format(org_id),
        check,
    )


def _check_compliance(permissions: CompiledPermissions) -> Tuple[str, str, CheckFn]:
    def check(node: NodeFilterRow) -> Optional[str]:
        blocking = permissions.blocking_tags(node.compliance_tags, node.department)
        if blocking:
            return "no clearance for {}".format(", ".join(sorted(blocking)))
        return None

    blocked = sorted(permissions.blocked_tags) or ["<none>"]
    sql = "AND NOT (compliance_tags && ARRAY[{}])".format(
        ", ".join("'{}'".format(t) for t in blocked)
    )
    if permissions.scoped_clearance:
        sql += "  -- except {} on own-department nodes ({})".format(
            "/".join(sorted(permissions.scoped_clearance)), permissions.department
        )
    return ("compliance", sql, check)


def _check_permission(
    permissions: CompiledPermissions, inherited_level_ids: FrozenSet[str]
) -> Tuple[str, str, CheckFn]:
    def check(node: NodeFilterRow) -> Optional[str]:
        if permissions.can_read(node.hierarchy_level):
            return None
        # Optional policy (off by default, see architecture.md "Check 3"):
        # treat own-department ancestors of the entry point as inherited.
        if node.hierarchy_level_id in inherited_level_ids:
            return None
        return "level L{} is above ceiling L{}".format(
            node.hierarchy_level, permissions.ceiling_level
        )

    sql = "AND (hierarchy_level >= {}".format(permissions.ceiling_level)
    if permissions.zone2_bypasses_ceiling:
        sql += " OR zone = 2"
    if inherited_level_ids:
        sql += " OR hierarchy_level_id = ANY(:inherited_dept_path)"
    sql += ")"
    return ("permission", sql, check)


def _check_temporal(now: datetime) -> Tuple[str, str, CheckFn]:
    def check(node: NodeFilterRow) -> Optional[str]:
        if node.status in DEAD_STATUSES:
            return "status is {}".format(node.status)
        if node.valid_until is not None and node.valid_until <= now:
            return "expired on {}".format(node.valid_until.date().isoformat())
        return None

    return (
        "temporal",
        "AND status NOT IN ('SUPERSEDED', 'EXPIRED') "
        "AND (valid_until IS NULL OR valid_until > NOW())",
        check,
    )


def _check_derivability(threshold: float) -> Tuple[str, str, CheckFn]:
    def check(node: NodeFilterRow) -> Optional[str]:
        if node.derivability_score >= threshold:
            return "derivability {:.2f} >= {:.2f} (model already knows this)".format(
                node.derivability_score, threshold
            )
        return None

    return (
        "derivability",
        "AND derivability_score < {}".format(threshold),
        check,
    )


CHECK_LABELS = {
    "isolation": "Check 1 — ISOLATION",
    "compliance": "Check 2 — COMPLIANCE",
    "permission": "Check 3 — PERMISSION",
    "temporal": "Check 4 — TEMPORAL",
    "derivability": "Check 5 — DERIVABILITY",
}


def run_five_checks(
    candidates: Sequence[NodeFilterRow],
    permissions: CompiledPermissions,
    org_id: str,
    derivability_threshold: float,
    now: Optional[datetime] = None,
    inherited_level_ids: Optional[FrozenSet[str]] = None,
) -> FilterOutcome:
    now = now or datetime.now(timezone.utc)

    checks = [
        _check_isolation(org_id),
        _check_compliance(permissions),
        _check_permission(permissions, inherited_level_ids or frozenset()),
        _check_temporal(now),
        _check_derivability(derivability_threshold),
    ]

    current: List[NodeFilterRow] = list(candidates)
    stages: List[StageResult] = []

    for name, sql, check in checks:
        started = time.perf_counter()
        survivors: List[NodeFilterRow] = []
        for node in current:
            reason = check(node)
            if reason is None:
                survivors.append(node)
        elapsed = (time.perf_counter() - started) * 1000.0
        stages.append(
            StageResult(
                name=name,
                label=CHECK_LABELS[name],
                count_in=len(current),
                count_out=len(survivors),
                duration_ms=elapsed,
                sql=sql,
            )
        )
        # THE sequential contract: next check sees only what survived this one.
        current = survivors

    return FilterOutcome(survivors=current, stages=stages)
