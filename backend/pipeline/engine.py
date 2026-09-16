"""The Rules Engine — orchestration of every stage. ZERO LLM calls.

    permission compile -> entry point -> BFS -> zone 2 -> 5 checks -> assemble

Every stage is timed; the timings and the funnel counts are part of the API
response because "you can see the filtering happen" is a requirement, not a
debugging nicety.
"""
import time
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from backend.data.repository import BaseRepository
from backend.pipeline.bfs_traversal import traverse
from backend.pipeline.candidate_assembler import assemble
from backend.pipeline.entry_point_resolver import resolve_entry_point
from backend.pipeline.five_check_filter import run_five_checks
from backend.pipeline.permission_compiler import compile_permissions
from backend.pipeline.zone2_injector import inject_zone2


class _Clock:
    """Accumulates per-stage wall time in milliseconds."""

    def __init__(self) -> None:
        self.marks: Dict[str, float] = {}
        self._start = time.perf_counter()

    def time(self, name: str, fn):
        started = time.perf_counter()
        result = fn()
        self.marks[name] = (time.perf_counter() - started) * 1000.0
        return result

    @property
    def total_ms(self) -> float:
        return (time.perf_counter() - self._start) * 1000.0


def run_pipeline(
    repo: BaseRepository,
    user_id: str,
    now: Optional[datetime] = None,
    include_content: bool = True,
) -> Dict[str, Any]:
    now = now or datetime.now(timezone.utc)
    clock = _Clock()

    user = repo.get_user(user_id)
    org = repo.get_organization(user.org_id)

    # -- Stage 0: compile permissions ONCE for the whole session ---------
    permissions = clock.time("permission_compile_ms", lambda: compile_permissions(user))

    # -- Load the filter index (no content) ------------------------------
    levels = clock.time("load_levels_ms", lambda: repo.list_levels(user.org_id))
    all_nodes = clock.time("load_filter_index_ms", lambda: repo.load_filter_index(user.org_id))

    # -- Stage 1: entry point --------------------------------------------
    entry = clock.time(
        "entry_point_ms", lambda: resolve_entry_point(permissions, levels)
    )

    # -- Stage 2: BFS ------------------------------------------------------
    traversal = clock.time("bfs_ms", lambda: traverse(entry, levels, all_nodes))

    # -- Stage 3: Zone 2 injection ----------------------------------------
    injection = clock.time("zone2_inject_ms", lambda: inject_zone2(traversal, all_nodes))

    reachable_rows = [n for n in all_nodes if n.id in injection.node_ids]
    outcome = clock.time(
        "five_checks_ms",
        lambda: run_five_checks(
            reachable_rows,
            permissions,
            org_id=user.org_id,
            derivability_threshold=org.derivability_threshold,
            now=now,
        ),
    )

    # -- Stage 5: fetch content for SURVIVORS ONLY, then annotate ---------
    survivor_ids = [n.id for n in outcome.survivors]
    content = clock.time(
        "content_fetch_ms",
        lambda: repo.fetch_content(survivor_ids) if include_content else {},
    )
    candidates = clock.time(
        "assemble_ms",
        lambda: assemble(
            outcome.survivors,
            injection.node_distance,
            injection.injected_ids,
            content,
            50,  # TODO: read from org config
        ),
    )

    total_nodes = len(all_nodes)
    funnel: Dict[str, int] = {
        "total_nodes": total_nodes,
        "after_bfs": len(traversal.node_ids),
        "after_zone2": len(injection.node_ids),
    }
    for index, stage in enumerate(outcome.stages, start=1):
        funnel["after_check{}".format(index)] = stage.count_out
    funnel["candidate_set"] = len(candidates)

    timing = {name: round(ms, 3) for name, ms in clock.marks.items()}
    for index, stage in enumerate(outcome.stages, start=1):
        timing["check{}_{}_ms".format(index, stage.name)] = round(stage.duration_ms, 3)
    timing["total_ms"] = round(clock.total_ms, 3)

    excluded_all = [e.to_dict() for stage in outcome.stages for e in stage.excluded]
    return {
        "user": user.id,
        "user_name": user.name,
        "role": user.role,
        "department": user.department,
        "ceiling_level": user.ceiling_level,
        "write_ceiling": user.write_ceiling,
        "org": {"id": org.id, "name": org.name, "config": org.config},
        "entry_point": entry.level.id,
        "entry_point_detail": entry.to_dict(),
        "permissions": permissions.to_dict(),
        "traversal": traversal.to_dict(),
        "zone2": injection.to_dict(),
        "pipeline_timing": timing,
        "funnel": funnel,
        "stages": [stage.to_dict() for stage in outcome.stages],
        "excluded": excluded_all,
        "llm_calls": 0,
        "candidate_set": [c.to_dict() for c in candidates],
    }
