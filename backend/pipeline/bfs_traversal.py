"""Stage 2 — BFS traversal of the hierarchy DAG.

Traversal is STRUCTURAL: it answers "which part of the graph is this user
positioned in?", not "what may they read?". Policy is the job of the five
checks that follow. Keeping the two apart is what lets two users in the same
department share a traversal and still end up with very different candidate
sets.

Two movement rules, both applied by a single FIFO BFS with one visited set:

  UP    (child -> parent, via ``parent_ids``): always allowed. Walking up is how
        a ward inherits its department's, division's and hospital's constraints.
        A level with several parents is enqueued once and processed once — the
        visited set is what makes a DAG safe where a tree needs no protection.

  DOWN  (parent -> child): allowed only into the user's OWN department subtree.
        Without this, "up then down" would make the graph undirected and every
        user would reach Cardiology through the hospital root. With it, Priya
        reaches sibling ortho units (TKR, Post-TKR) but never Medicine.
        Cross-departmental users (``department_scope is None``) descend freely.

Distance is the hop count from the entry point and drives compression later.
The traversal returns node IDs and distances only — no content is fetched.
"""
from collections import deque
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Sequence, Set

from backend.models.node import HierarchyLevel, NodeFilterRow
from backend.pipeline.entry_point_resolver import EntryPoint


@dataclass
class TraversalResult:
    entry_level_id: str
    level_distance: Dict[str, int]          # level_id -> hops from entry
    node_ids: Set[str] = field(default_factory=set)
    node_distance: Dict[str, int] = field(default_factory=dict)
    visit_order: List[str] = field(default_factory=list)
    multi_parent_levels: List[str] = field(default_factory=list)
    revisits_prevented: int = 0

    @property
    def max_distance(self) -> int:
        return max(self.level_distance.values()) if self.level_distance else 0

    def to_dict(self) -> dict:
        return {
            "entry_level_id": self.entry_level_id,
            "reached_levels": self.level_distance,
            "visit_order": self.visit_order,
            "reachable_node_count": len(self.node_ids),
            "multi_parent_levels": self.multi_parent_levels,
            "revisits_prevented": self.revisits_prevented,
            "max_distance": self.max_distance,
        }


def traverse(
    entry: EntryPoint,
    levels: Sequence[HierarchyLevel],
    nodes: Sequence[NodeFilterRow],
) -> TraversalResult:
    levels_by_id: Dict[str, HierarchyLevel] = {lvl.id: lvl for lvl in levels}
    children: Dict[str, List[str]] = {lvl.id: [] for lvl in levels}
    for lvl in levels:
        for parent_id in lvl.parent_ids:
            if parent_id in children:
                children[parent_id].append(lvl.id)

    scope: Optional[str] = entry.department_scope

    distance: Dict[str, int] = {entry.level.id: 0}
    visited: Set[str] = {entry.level.id}
    visit_order: List[str] = []
    multi_parent: List[str] = []
    revisits_prevented = 0

    queue: deque = deque([(entry.level.id, 0)])
    while queue:
        level_id, dist = queue.popleft()
        visit_order.append(level_id)
        level = levels_by_id[level_id]
        if len(level.parent_ids) > 1:
            multi_parent.append(level_id)

        neighbours: List[str] = []
        # UP — unconditional.
        neighbours.extend(pid for pid in level.parent_ids if pid in levels_by_id)
        # DOWN — department-scoped.
        for child_id in children.get(level_id, ()):
            child = levels_by_id[child_id]
            if scope is None or child.department == scope:
                neighbours.append(child_id)

        for neighbour in neighbours:
            if neighbour in visited:
                # The multi-parent / diamond case: already queued from another
                # path. Counting these makes the visited set visible in the demo.
                revisits_prevented += 1
                continue
            visited.add(neighbour)
            distance[neighbour] = dist + 1
            queue.append((neighbour, dist + 1))

    node_ids: Set[str] = set()
    node_distance: Dict[str, int] = {}
    for node in nodes:
        if node.hierarchy_level_id in distance:
            node_ids.add(node.id)
            node_distance[node.id] = distance[node.hierarchy_level_id]

    return TraversalResult(
        entry_level_id=entry.level.id,
        level_distance=distance,
        node_ids=node_ids,
        node_distance=node_distance,
        visit_order=visit_order,
        multi_parent_levels=multi_parent,
        revisits_prevented=revisits_prevented,
    )
