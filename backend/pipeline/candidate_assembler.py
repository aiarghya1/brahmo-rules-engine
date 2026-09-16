"""Stage 5 — Candidate Set Assembler.

Everything up to here moved IDs around. This is the first and only place the
pipeline fetches node CONTENT, and it does so for survivors only.

Each survivor is annotated with what the downstream Composition Agent needs:
type, importance, distance from entry, zone, and a compression hint derived
from that distance (near = verbatim, far = the constraint only).
"""
from typing import Dict, List, Sequence

from backend.models.candidate_set import CandidateNode, compression_hint_for
from backend.models.node import KnowledgeNode, NodeFilterRow

def assemble(
    survivors: Sequence[NodeFilterRow],
    node_distance: Dict[str, int],
    injected_ids: Sequence[str],
    content_by_id: Dict[str, KnowledgeNode],
    max_candidates: int,
) -> List[CandidateNode]:
    injected = set(injected_ids)
    candidates: List[CandidateNode] = []

    for row in survivors:
        distance = node_distance.get(row.id, 0)
        full = content_by_id.get(row.id)
        candidates.append(
            CandidateNode(
                id=row.id,
                type=row.type,
                title=row.title or (full.title if full else ""),
                content=full.content if full else "",
                importance=row.importance,
                zone=row.zone,
                hierarchy_level=row.hierarchy_level,
                hierarchy_level_id=row.hierarchy_level_id,
                department=row.department,
                distance_from_entry=distance,
                compression_hint=compression_hint_for(distance),
                reached_via="ZONE_2_INJECTION" if row.id in injected else "BFS",
            )
        )

    return candidates[:max_candidates]
