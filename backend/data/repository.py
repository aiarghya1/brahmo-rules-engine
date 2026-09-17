"""Data access.

Two interchangeable backends behind one interface:

* ``SupabaseRepository`` — the real thing (PostgREST over Postgres + RLS).
* ``LocalSeedRepository`` — parses ``supabase/seed.sql`` into memory so the
  pipeline runs with no credentials and no network.

Both expose the same two-phase access pattern:

    load_filter_index()   -> filter columns only, NO content   (cheap, always)
    fetch_content(ids)    -> content for survivors only        (after check 5)

Content is never loaded for a node the user is not allowed to read.
"""
import os
from datetime import datetime, timezone
from typing import Any, Dict, Iterable, List, Optional

from backend.models.node import Edge, HierarchyLevel, KnowledgeNode, NodeFilterRow
from backend.models.user import Organization, User

FILTER_COLUMNS = (
    "id,org_id,hierarchy_level_id,type,title,importance,zone,status,"
    "derivability_score,compliance_tags,valid_until,department"
)


def _parse_ts(value: Any) -> Optional[datetime]:
    if value in (None, ""):
        return None
    if isinstance(value, datetime):
        return value if value.tzinfo else value.replace(tzinfo=timezone.utc)
    text = str(value).replace("Z", "+00:00")
    try:
        parsed = datetime.fromisoformat(text)
    except ValueError:
        return None
    return parsed if parsed.tzinfo else parsed.replace(tzinfo=timezone.utc)


class BaseRepository:
    """Shared row -> model mapping."""

    backend_name = "base"

    def __init__(self) -> None:
        self._levels_by_id: Dict[str, HierarchyLevel] = {}

    # -- mapping helpers -------------------------------------------------
    def _to_level(self, row: Dict[str, Any]) -> HierarchyLevel:
        return HierarchyLevel(
            id=row["id"],
            org_id=row["org_id"],
            level_number=int(row["level_number"]),
            level_name=row["level_name"],
            department=row.get("department"),
            parent_ids=list(row.get("parent_ids") or []),
            zone=int(row.get("zone") or 1),
        )

    def _to_filter_row(self, row: Dict[str, Any]) -> NodeFilterRow:
        level = self._levels_by_id[row["hierarchy_level_id"]]
        return NodeFilterRow(
            id=row["id"],
            org_id=row["org_id"],
            hierarchy_level_id=row["hierarchy_level_id"],
            hierarchy_level=level.level_number,
            department=row.get("department"),
            type=row["type"],
            importance=float(row["importance"]),
            zone=int(row["zone"]),
            status=row["status"],
            derivability_score=float(row["derivability_score"]),
            compliance_tags=list(row.get("compliance_tags") or []),
            valid_until=_parse_ts(row.get("valid_until")),
            title=row.get("title", ""),
        )

    def _to_node(self, row: Dict[str, Any]) -> KnowledgeNode:
        return KnowledgeNode(
            id=row["id"],
            org_id=row["org_id"],
            hierarchy_level_id=row["hierarchy_level_id"],
            type=row["type"],
            title=row["title"],
            content=row["content"],
            importance=float(row["importance"]),
            zone=int(row["zone"]),
            status=row["status"],
            derivability_score=float(row["derivability_score"]),
            compliance_tags=list(row.get("compliance_tags") or []),
            valid_until=_parse_ts(row.get("valid_until")),
            superseded_by=row.get("superseded_by"),
            department=row.get("department"),
        )

    def _to_user(self, row: Dict[str, Any]) -> User:
        return User(
            id=row["id"],
            org_id=row["org_id"],
            name=row["name"],
            role=row["role"],
            department=row["department"],
            ceiling_level=int(row["ceiling_level"]),
            write_ceiling=(
                int(row["write_ceiling"]) if row.get("write_ceiling") is not None else None
            ),
            compliance_clearance=list(row.get("compliance_clearance") or []),
            status=row.get("status") or "ACTIVE",
        )


class LocalSeedRepository(BaseRepository):
    """In-memory repository backed by ``supabase/seed.sql``."""

    backend_name = "local-seed"

    def __init__(self, seed_path: str) -> None:
        super().__init__()
        from backend.data.sql_seed_parser import load_seed_file

        self._tables = load_seed_file(seed_path)
        self._levels_by_id = {
            row["id"]: self._to_level(row) for row in self._tables.get("hierarchy_levels", [])
        }
        self._node_rows = {row["id"]: row for row in self._tables.get("knowledge_nodes", [])}

    def get_organization(self, org_id: str) -> Organization:
        for row in self._tables.get("organizations", []):
            if row["id"] == org_id:
                return Organization(
                    id=row["id"],
                    name=row["name"],
                    segment=row["segment"],
                    config=row.get("config") or {},
                )
        raise KeyError("unknown organization: {}".format(org_id))

    def list_users(self) -> List[User]:
        return [self._to_user(row) for row in self._tables.get("users", [])]

    def get_user(self, user_id: str) -> User:
        for user in self.list_users():
            if user.id == user_id:
                return user
        raise KeyError("unknown user: {}".format(user_id))

    def list_levels(self, org_id: str) -> List[HierarchyLevel]:
        return [lvl for lvl in self._levels_by_id.values() if lvl.org_id == org_id]

    def load_filter_index(self, org_id: str) -> List[NodeFilterRow]:
        return [
            self._to_filter_row(row)
            for row in self._node_rows.values()
            if row["org_id"] == org_id
        ]

    def count_nodes(self, org_id: str) -> int:
        return sum(1 for row in self._node_rows.values() if row["org_id"] == org_id)

    def fetch_content(self, node_ids: Iterable[str]) -> Dict[str, KnowledgeNode]:
        wanted = list(node_ids)
        return {nid: self._to_node(self._node_rows[nid]) for nid in wanted if nid in self._node_rows}

    def list_edges(self) -> List[Edge]:
        return [
            Edge(
                source_id=row["source_id"],
                target_id=row["target_id"],
                edge_type=row["edge_type"],
                confidence=float(row.get("confidence") or 1.0),
            )
            for row in self._tables.get("edges", [])
        ]


class SupabaseRepository(BaseRepository):
    """PostgREST-backed repository."""

    backend_name = "supabase"

    def __init__(self, url: str, key: str) -> None:
        super().__init__()
        from supabase import create_client

        self._client = create_client(url, key)
        self._levels_by_id = {}

    def _levels(self, org_id: str) -> Dict[str, HierarchyLevel]:
        if not self._levels_by_id:
            res = (
                self._client.table("hierarchy_levels")
                .select("*")
                .eq("org_id", org_id)
                .execute()
            )
            self._levels_by_id = {row["id"]: self._to_level(row) for row in res.data}
        return self._levels_by_id

    def get_organization(self, org_id: str) -> Organization:
        res = self._client.table("organizations").select("*").eq("id", org_id).execute()
        if not res.data:
            raise KeyError("unknown organization: {}".format(org_id))
        row = res.data[0]
        config = row.get("config") or {}
        return Organization(
            id=row["id"], name=row["name"], segment=row["segment"], config=config
        )

    def list_users(self) -> List[User]:
        res = self._client.table("users").select("*").order("id").execute()
        return [self._to_user(row) for row in res.data]

    def get_user(self, user_id: str) -> User:
        res = self._client.table("users").select("*").eq("id", user_id).execute()
        if not res.data:
            raise KeyError("unknown user: {}".format(user_id))
        return self._to_user(res.data[0])

    def list_levels(self, org_id: str) -> List[HierarchyLevel]:
        return list(self._levels(org_id).values())

    def load_filter_index(self, org_id: str) -> List[NodeFilterRow]:
        self._levels(org_id)
        res = (
            self._client.table("knowledge_nodes")
            .select(FILTER_COLUMNS)  # NOTE: 'content' is deliberately absent
            .eq("org_id", org_id)
            .execute()
        )
        return [self._to_filter_row(row) for row in res.data]

    def count_nodes(self, org_id: str) -> int:
        res = (
            self._client.table("knowledge_nodes")
            .select("id", count="exact")
            .eq("org_id", org_id)
            .execute()
        )
        return res.count or len(res.data)

    def fetch_content(self, node_ids: Iterable[str]) -> Dict[str, KnowledgeNode]:
        ids = list(node_ids)
        if not ids:
            return {}
        res = self._client.table("knowledge_nodes").select("*").in_("id", ids).execute()
        return {row["id"]: self._to_node(row) for row in res.data}

    def list_edges(self) -> List[Edge]:
        res = self._client.table("edges").select("*").execute()
        return [
            Edge(
                source_id=row["source_id"],
                target_id=row["target_id"],
                edge_type=row["edge_type"],
                confidence=float(row.get("confidence") or 1.0),
            )
            for row in res.data
        ]


def default_seed_path() -> str:
    if os.environ.get("SEED_PATH"):
        return os.environ["SEED_PATH"]
    here = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    repo_seed = os.path.join(here, "supabase", "seed.sql")
    if os.path.exists(repo_seed):
        return repo_seed
    backend_seed = os.path.join(os.path.dirname(os.path.abspath(__file__)), "seed.sql")
    if os.path.exists(backend_seed):
        return backend_seed
    return repo_seed


def get_repository() -> BaseRepository:
    """Supabase when credentials are present, local seed otherwise."""
    url = os.environ.get("SUPABASE_URL", "").strip()
    key = os.environ.get("SUPABASE_KEY", "").strip() or os.environ.get(
        "SUPABASE_ANON_KEY", ""
    ).strip()
    if url and key and not url.startswith("your_"):
        return SupabaseRepository(url, key)
    return LocalSeedRepository(os.environ.get("SEED_PATH", default_seed_path()))
