"""Output models: the candidate set and the funnel that produced it."""
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

# distance from the user's entry point -> how much of the node survives
# downstream compression. Set by the Candidate Set Assembler, consumed by the
# (out of scope) Composition Agent.
COMPRESSION_FULL = "FULL"
COMPRESSION_COMPRESSED = "COMPRESSED"
COMPRESSION_CONSTRAINT_ONLY = "CONSTRAINT_ONLY"


def compression_hint_for(distance: int) -> str:
    if distance <= 1:
        return COMPRESSION_FULL
    if distance == 2:
        return COMPRESSION_COMPRESSED
    return COMPRESSION_CONSTRAINT_ONLY


@dataclass
class CandidateNode:
    id: str
    type: str
    title: str
    content: str
    importance: float
    zone: int
    hierarchy_level: int
    hierarchy_level_id: str
    department: Optional[str]
    distance_from_entry: int
    compression_hint: str
    reached_via: str  # "BFS" | "ZONE_2_INJECTION"

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "type": self.type,
            "title": self.title,
            "content": self.content,
            "importance": self.importance,
            "zone": self.zone,
            "hierarchy_level": self.hierarchy_level,
            "hierarchy_level_id": self.hierarchy_level_id,
            "department": self.department,
            "distance_from_entry": self.distance_from_entry,
            "compression_hint": self.compression_hint,
            "reached_via": self.reached_via,
        }


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
