"""Output models: the candidate set and the funnel that produced it."""
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional


@dataclass
class StageResult:
    name: str
    label: str
    count_in: int
    count_out: int
    duration_ms: float
    sql: str = ""

    def to_dict(self) -> Dict[str, Any]:
        return {
            "name": self.name,
            "label": self.label,
            "count_in": self.count_in,
            "count_out": self.count_out,
            "removed": self.count_in - self.count_out,
            "duration_ms": round(self.duration_ms, 3),
            "sql": self.sql,
        }
