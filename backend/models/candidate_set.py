"""Output models: the candidate set and the funnel that produced it."""
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional


@dataclass
class Exclusion:
    """Why a node that entered the pipeline did not make the candidate set.

    Kept server-side for the audit trail and the demo UI. It is NEVER surfaced
    to the end user as an error — exclusion is silent by design (a user must not
    learn that a node they cannot read exists).
    """

    node_id: str
    title: str
    stage: str
    reason: str

    def to_dict(self) -> Dict[str, Any]:
        return {
            "node_id": self.node_id,
            "title": self.title,
            "stage": self.stage,
            "reason": self.reason,
        }


@dataclass
class StageResult:
    name: str
    label: str
    count_in: int
    count_out: int
    duration_ms: float
    sql: str = ""
    excluded: List[Exclusion] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "name": self.name,
            "label": self.label,
            "count_in": self.count_in,
            "count_out": self.count_out,
            "removed": self.count_in - self.count_out,
            "duration_ms": round(self.duration_ms, 3),
            "sql": self.sql,
            "excluded": [e.to_dict() for e in self.excluded],
        }
