"""Stage 3 — Zone 2 injection.

Zone 2 nodes are hospital-wide: drug interactions, patient-ID rules, transfusion
checks. They must be in EVERY session regardless of where the user stands in the
DAG, so they bypass the traversal.

They do NOT bypass the five checks. An expired or MNPI-tagged global node is
still dropped downstream — injection happens BEFORE the checks, never after.

Injected nodes have no traversal distance, so they are given the distance from
the entry point to the root of the user's traversal: they are the most distant
context the user has, which is exactly the compression treatment they want
(CONSTRAINT_ONLY — keep the rule, drop the prose).
"""
from dataclasses import dataclass
from typing import Dict, List, Sequence, Set

from backend.models.node import NodeFilterRow
from backend.pipeline.bfs_traversal import TraversalResult

ZONE_GLOBAL = 2


@dataclass
class InjectionResult:
    node_ids: Set[str]
    injected_ids: List[str]
    already_reachable_ids: List[str]

    def to_dict(self) -> dict:
        return {
            "injected": self.injected_ids,
            "already_reachable": self.already_reachable_ids,
            "combined_count": len(self.node_ids),
        }


def inject_zone2(
    traversal: TraversalResult, nodes: Sequence[NodeFilterRow]
) -> InjectionResult:
    node_ids = set(traversal.node_ids)
    injected: List[str] = []
    already: List[str] = []

    for node in nodes:
        if node.zone != ZONE_GLOBAL:
            continue
        if node.id in node_ids:
            # An ADMIN whose traversal already covered the global subtree.
            already.append(node.id)
            continue
        node_ids.add(node.id)
        injected.append(node.id)

    return InjectionResult(
        node_ids=node_ids,
        injected_ids=sorted(injected),
        already_reachable_ids=sorted(already),
    )
