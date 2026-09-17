"""FastAPI surface for the BRAHMO Rules Engine.

Read-only. Every endpoint is a pure function of (seed data, user id) — the
pipeline is re-run on every request, never cached and never hardcoded, so
switching users in the UI genuinely re-executes BFS + the five checks.
"""
import os
import sys
import types
from pathlib import Path
from typing import Any, Dict, List, Optional

from dotenv import load_dotenv

load_dotenv()

# Support running both from workspace root and when deployed standalone on Vercel
_current_dir = Path(__file__).resolve().parent
if "backend" not in sys.modules:
    if (_current_dir.parent / "backend").exists():
        if str(_current_dir.parent) not in sys.path:
            sys.path.insert(0, str(_current_dir.parent))
    else:
        _pkg = types.ModuleType("backend")
        _pkg.__path__ = [str(_current_dir)]
        sys.modules["backend"] = _pkg
        if str(_current_dir) not in sys.path:
            sys.path.insert(0, str(_current_dir))

from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware

from backend.data.repository import get_repository  # noqa: E402
from backend.pipeline.engine import run_pipeline  # noqa: E402

app = FastAPI(
    title="BRAHMO Rules Engine",
    description="BFS traversal + 5-check filter pipeline. Zero LLM.",
    version="1.0.0",
)

# Any localhost or deployed origin; set CORS_ORIGINS to restrict.
_explicit_origins = [o for o in os.environ.get("CORS_ORIGINS", "").split(",") if o]
app.add_middleware(
    CORSMiddleware,
    allow_origins=_explicit_origins if _explicit_origins else ["*"],
    allow_origin_regex=None if _explicit_origins else r"https?://.*",
    allow_credentials=False,
    allow_methods=["GET", "POST", "OPTIONS"],
    allow_headers=["*"],
)

_repo = None


def repo():
    global _repo
    if _repo is None:
        _repo = get_repository()
    return _repo


@app.get("/")
def root() -> Dict[str, Any]:
    return {
        "app": "BRAHMO Rules Engine API",
        "status": "online",
        "endpoints": {
            "health": "/api/health",
            "users": "/api/users",
            "graph": "/api/graph",
            "pipeline": "/api/pipeline/{user_id}",
            "compare": "/api/compare?users=1,2",
            "docs": "/docs",
        },
    }


@app.get("/api/health")
def health() -> Dict[str, Any]:
    source = repo()
    return {
        "status": "ok",
        "backend": source.backend_name,
        "nodes": source.count_nodes("supra"),
        "users": len(source.list_users()),
        "llm_calls": 0,
    }


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


@app.get("/api/compare")
def compare(users: str = Query(..., description="comma-separated user ids")) -> Dict[str, Any]:
    """Side-by-side runs, plus which nodes are shared and which are exclusive."""
    user_ids = [u.strip() for u in users.split(",") if u.strip()]
    if not 2 <= len(user_ids) <= 4:
        raise HTTPException(status_code=400, detail="compare 2 to 4 users")

    results = []
    for user_id in user_ids:
        try:
            results.append(run_pipeline(repo(), user_id))
        except KeyError as exc:
            raise HTTPException(status_code=404, detail=str(exc))

    id_sets = {r["user"]: {c["id"] for c in r["candidate_set"]} for r in results}
    shared = set.intersection(*id_sets.values()) if id_sets else set()
    exclusive = {
        uid: sorted(ids - set.union(*[other for k, other in id_sets.items() if k != uid]))
        for uid, ids in id_sets.items()
    }
    return {
        "results": results,
        "shared_node_ids": sorted(shared),
        "exclusive_node_ids": exclusive,
    }
