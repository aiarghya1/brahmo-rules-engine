"""User + organisation models."""
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

ROLES = ("ADMIN", "HOD", "EDITOR", "VIEWER", "QUALITY", "AUDITOR")

# Every compliance tag the org knows about. A user is blocked from a tag unless
# it is in their clearance (explicit) or granted by their role (scoped).
ALL_COMPLIANCE_TAGS = ("MNPI", "PHI", "CONFIDENTIAL")


@dataclass(frozen=True)
class Organization:
    id: str
    name: str
    segment: str
    config: Dict[str, Any] = field(default_factory=dict)

    @property
    def derivability_threshold(self) -> float:
        return float(self.config.get("derivability_threshold", 0.7))

    @property
    def token_budget(self) -> int:
        return int(self.config.get("token_budget", 4000))


@dataclass(frozen=True)
class User:
    id: str
    org_id: str
    name: str
    role: str
    department: str
    ceiling_level: int
    write_ceiling: Optional[int] = None
    compliance_clearance: List[str] = field(default_factory=list)
    status: str = "ACTIVE"

    @property
    def label(self) -> str:
        return "{} — {}, L{}, {}".format(
            self.name, self.role, self.ceiling_level, self.department
        )
