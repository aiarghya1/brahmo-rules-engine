"""Domain models for the knowledge graph.

Two deliberately separate node representations:

* ``NodeFilterRow``  — only the columns the 5-check filter needs. This is what
  the pipeline loads. It contains NO content.
* ``KnowledgeNode``  — the full row including ``content``. Only fetched for the
  nodes that SURVIVE all five checks.

That split is the point of GAP 5 ("permission before retrieval"): a node the
user may not read never has its content loaded into process memory at all.
"""
from dataclasses import dataclass, field
from datetime import datetime
from typing import List, Optional

NODE_TYPES = ("CONSTRAINT", "DECISION", "ANTI_PATTERN", "FACT")


@dataclass(frozen=True)
class HierarchyLevel:
    """One vertex of the hierarchy DAG."""

    id: str
    org_id: str
    level_number: int
    level_name: str
    department: Optional[str]
    parent_ids: List[str] = field(default_factory=list)
    zone: int = 1


@dataclass(frozen=True)
class NodeFilterRow:
    """The filter-relevant projection of a knowledge node (no content)."""

    id: str
    org_id: str
    hierarchy_level_id: str
    hierarchy_level: int
    department: Optional[str]
    type: str
    importance: float
    zone: int
    status: str
    derivability_score: float
    compliance_tags: List[str] = field(default_factory=list)
    valid_until: Optional[datetime] = None
    title: str = ""


@dataclass(frozen=True)
class KnowledgeNode:
    """A full knowledge node, content included."""

    id: str
    org_id: str
    hierarchy_level_id: str
    type: str
    title: str
    content: str
    importance: float
    zone: int
    status: str
    derivability_score: float
    compliance_tags: List[str] = field(default_factory=list)
    valid_until: Optional[datetime] = None
    superseded_by: Optional[str] = None
    department: Optional[str] = None


@dataclass(frozen=True)
class Edge:
    source_id: str
    target_id: str
    edge_type: str
    confidence: float = 1.0
