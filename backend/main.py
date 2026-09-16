"""FastAPI surface for the BRAHMO Rules Engine.

Read-only. Every endpoint is a pure function of (seed data, user id) — the
pipeline is re-run on every request, never cached and never hardcoded, so
switching users in the UI genuinely re-executes BFS + the five checks.
"""
import os
from typing import Any, Dict, List, Optional

from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware

load_dotenv()

from backend.data.repository import get_repository  # noqa: E402
from backend.pipeline.engine import run_pipeline  # noqa: E402

app = FastAPI(
    title="BRAHMO Rules Engine",
    description="BFS traversal + 5-check filter pipeline. Zero LLM.",
    version="1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_credentials=False,
    allow_methods=["GET"],
    allow_headers=["*"],
)

_repo = None


def repo():
    global _repo
    if _repo is None:
        _repo = get_repository()
    return _repo


@app.get("/api/health")
def health() -> Dict[str, Any]:
    return {"status": "ok", "llm_calls": 0}


@app.get("/api/users")
def list_users() -> List[Dict[str, Any]]:
    return [
        {
            "id": user.id,
            "name": user.name,
            "role": user.role,
            "department": user.department,
            "ceiling_level": user.ceiling_level,
            "write_ceiling": user.write_ceiling,
            "compliance_clearance": user.compliance_clearance,
            "label": user.label,
        }
        for user in repo().list_users()
    ]


@app.get("/api/graph")
def graph(org_id: str = "supra") -> Dict[str, Any]:
    """The hierarchy DAG plus a content-free node index, for the DAG viewer."""
    source = repo()
    levels = source.list_levels(org_id)
    nodes = source.load_filter_index(org_id)
    return {
        "levels": [
            {
                "id": lvl.id,
                "level_number": lvl.level_number,
                "level_name": lvl.level_name,
                "department": lvl.department,
                "parent_ids": lvl.parent_ids,
                "zone": lvl.zone,
            }
            for lvl in sorted(levels, key=lambda l: (l.level_number, l.id))
        ],
        "nodes": [
            {
                "id": n.id,
                "title": n.title,
                "type": n.type,
                "hierarchy_level_id": n.hierarchy_level_id,
                "hierarchy_level": n.hierarchy_level,
                "department": n.department,
                "zone": n.zone,
                "importance": n.importance,
            }
            for n in sorted(nodes, key=lambda n: n.id)
        ],
        "edges": [
            {"source_id": e.source_id, "target_id": e.target_id, "edge_type": e.edge_type}
            for e in source.list_edges()
        ],
    }


@app.get("/api/pipeline/{user_id}")
def pipeline(user_id: str) -> Dict[str, Any]:
    try:
        return run_pipeline(repo(), user_id)
    except KeyError as exc:
        raise HTTPException(status_code=404, detail=str(exc))


