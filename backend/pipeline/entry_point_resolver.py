"""Stage 1 — Entry Point Resolver.

Maps a user to the single hierarchy level where their BFS starts.

Rule:
  1. Take every level belonging to the user's department.
  2. Of those, keep the ones the user is allowed to read (level >= ceiling).
  3. Enter at the SHALLOWEST of those — the highest-authority position the
     user actually holds.
       Nurse Priya  (ortho, ceiling 10) -> ortho levels 10 and 12 qualify
                                           -> enters at L10 Ortho Ward
       Dr. Vikram   (ortho, ceiling 4)  -> every ortho level qualifies
                                           -> enters at L5 Orthopaedics Dept
  4. No level maps to the department (admin, quality, pharmacy) -> the user is
     cross-departmental: enter at the org root and let the ceiling do the work.
"""
from dataclasses import dataclass
from typing import List, Optional, Sequence

from backend.models.node import HierarchyLevel
from backend.pipeline.permission_compiler import CompiledPermissions


@dataclass(frozen=True)
class EntryPoint:
    level: HierarchyLevel
    strategy: str
    department_scope: Optional[str]  # None = may descend into every department

    def to_dict(self) -> dict:
        return {
            "level_id": self.level.id,
            "level_name": self.level.level_name,
            "level_number": self.level.level_number,
            "department": self.level.department,
            "strategy": self.strategy,
            "department_scope": self.department_scope,
        }


def _root(levels: Sequence[HierarchyLevel]) -> HierarchyLevel:
    roots = [lvl for lvl in levels if not lvl.parent_ids]
    if roots:
        return min(roots, key=lambda lvl: lvl.level_number)
    return min(levels, key=lambda lvl: lvl.level_number)


def resolve_entry_point(
    permissions: CompiledPermissions, levels: Sequence[HierarchyLevel]
) -> EntryPoint:
    if not levels:
        raise ValueError("no hierarchy levels for org")

    department = permissions.department
    dept_levels: List[HierarchyLevel] = [
        lvl for lvl in levels if lvl.department == department
    ]
    if dept_levels:
        readable = [lvl for lvl in dept_levels if permissions.can_read(lvl.level_number)]
        pool = readable or dept_levels
        entry = min(pool, key=lambda lvl: (lvl.level_number, lvl.id))
        return EntryPoint(
            level=entry,
            strategy="DEPARTMENT_LEVEL",
            department_scope=department,
        )

    root = _root(levels)
    return EntryPoint(
        level=root,
        strategy="ORG_ROOT",
        department_scope=None,
    )
