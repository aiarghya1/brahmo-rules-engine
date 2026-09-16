"""Stage 0 — Permission Compiler.

Runs ONCE per session. Turns a user row into an O(1) lookup table so that the
500+ per-node permission questions asked later are dict lookups, not policy
evaluations.

Read semantics (from the spec): ``hierarchy_level >= ceiling_level``.
A LOWER ceiling number means MORE authority — level 1 is the hospital board,
level 12 is a single patient. So a user reads their own level and everything
BELOW it (numerically higher), never above it.

  VIEWER              read >= ceiling            no write
  EDITOR              read >= ceiling            write >= write_ceiling
  QUALITY / AUDITOR   read >= ceiling            write >= write_ceiling
  HOD                 read ALL levels            write >= ceiling
  ADMIN               read ALL levels            write ALL levels
"""
from dataclasses import dataclass
from typing import Dict, FrozenSet, List, Optional, Sequence

from backend.models.user import ALL_COMPLIANCE_TAGS, User

MAX_LEVEL = 15

# Roles whose read authority is not bounded by their ceiling number.
_READ_ALL_ROLES = frozenset({"HOD", "ADMIN"})
_WRITE_ALL_ROLES = frozenset({"ADMIN"})

# Compliance tags a role carries implicitly, but ONLY for nodes belonging to
# that user's own department. An HOD authored their own department's budget, so
# blocking them from it is wrong; a different department's budget stays blocked.
_ROLE_SCOPED_CLEARANCE: Dict[str, FrozenSet[str]] = {
    "HOD": frozenset({"MNPI"}),
}


@dataclass(frozen=True)
class LevelPermission:
    can_read: bool
    can_write: bool


@dataclass(frozen=True)
class CompiledPermissions:
    """The compiled, O(1) permission profile for one session."""

    user_id: str
    org_id: str
    role: str
    department: str
    ceiling_level: int
    write_ceiling: Optional[int]
    levels: Dict[int, LevelPermission]
    blocked_tags: FrozenSet[str]
    scoped_clearance: FrozenSet[str]
    cleared_tags: FrozenSet[str]
    zone2_bypasses_ceiling: bool = True

    # -- O(1) lookups ----------------------------------------------------
    def can_read(self, level_number: int) -> bool:
        perm = self.levels.get(level_number)
        return bool(perm and perm.can_read)

    def can_write(self, level_number: int) -> bool:
        perm = self.levels.get(level_number)
        return bool(perm and perm.can_write)

    def blocking_tags(
        self, tags: Sequence[str], node_department: Optional[str]
    ) -> List[str]:
        """Which of ``tags`` this user is NOT cleared for. Empty list = allowed."""
        if not tags:
            return []
        cleared = self.cleared_tags
        if node_department is not None and node_department == self.department:
            cleared = cleared | self.scoped_clearance
        return [tag for tag in tags if tag not in cleared]

    def to_dict(self) -> dict:
        return {
            "user_id": self.user_id,
            "role": self.role,
            "ceiling_level": self.ceiling_level,
            "write_ceiling": self.write_ceiling,
            "readable_levels": [lv for lv, p in sorted(self.levels.items()) if p.can_read],
            "writable_levels": [lv for lv, p in sorted(self.levels.items()) if p.can_write],
            "cleared_tags": sorted(self.cleared_tags),
            "scoped_clearance": sorted(self.scoped_clearance),
            "blocked_tags": sorted(self.blocked_tags),
            "zone2_bypasses_ceiling": self.zone2_bypasses_ceiling,
        }


def compile_permissions(
    user: User, zone2_bypasses_ceiling: bool = True, max_level: int = MAX_LEVEL
) -> CompiledPermissions:
    """Compile a user into a {level: {can_read, can_write}} lookup. O(15)."""
    read_floor = 1 if user.role in _READ_ALL_ROLES else user.ceiling_level

    if user.role in _WRITE_ALL_ROLES:
        write_floor: Optional[int] = 1
    elif user.role == "HOD":
        write_floor = user.ceiling_level
    elif user.write_ceiling is None:
        write_floor = None  # VIEWER — read-only
    else:
        write_floor = user.write_ceiling

    levels = {
        level: LevelPermission(
            can_read=level >= read_floor,
            can_write=write_floor is not None and level >= write_floor,
        )
        for level in range(1, max_level + 1)
    }

    cleared = frozenset(user.compliance_clearance or ())
    scoped = _ROLE_SCOPED_CLEARANCE.get(user.role, frozenset())
    blocked = frozenset(ALL_COMPLIANCE_TAGS) - cleared

    return CompiledPermissions(
        user_id=user.id,
        org_id=user.org_id,
        role=user.role,
        department=user.department,
        ceiling_level=user.ceiling_level,
        write_ceiling=user.write_ceiling,
        levels=levels,
        blocked_tags=blocked,
        scoped_clearance=scoped,
        cleared_tags=cleared,
        zone2_bypasses_ceiling=zone2_bypasses_ceiling,
    )
