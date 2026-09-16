"""API surface."""
import pytest
from fastapi.testclient import TestClient

from backend.main import app

client = TestClient(app)


def test_health():
    body = client.get("/api/health").json()
    assert body["status"] == "ok"
    assert body["nodes"] == 50
    assert body["llm_calls"] == 0


def test_users_lists_all_seven():
    users = client.get("/api/users").json()
    assert len(users) == 7
    assert {u["id"] for u in users} >= {"U-PRIYA", "U-VIKRAM", "U-SURESH"}


def test_graph_returns_dag_and_content_free_nodes():
    graph = client.get("/api/graph").json()
    assert len(graph["levels"]) == 20
    assert len(graph["nodes"]) == 50
    assert len(graph["edges"]) == 10
    assert all("content" not in node for node in graph["nodes"])


def test_pipeline_returns_the_documented_shape():
    body = client.get("/api/pipeline/U-PRIYA").json()
    for key in ("user", "entry_point", "pipeline_timing", "funnel", "candidate_set"):
        assert key in body
    assert body["pipeline_timing"]["total_ms"] > 0
    assert body["funnel"]["total_nodes"] == 50


def test_unknown_user_is_404():
    assert client.get("/api/pipeline/U-GHOST").status_code == 404


def test_compare_reports_shared_and_exclusive():
    body = client.get("/api/compare", params={"users": "U-PRIYA,U-ANANYA"}).json()
    assert len(body["results"]) == 2
    # Two different departments must have nodes the other cannot see.
    assert body["exclusive_node_ids"]["U-PRIYA"]
    assert body["exclusive_node_ids"]["U-ANANYA"]
    # ...and share the global safety constraints.
    assert "N-G01" in body["shared_node_ids"]


@pytest.mark.parametrize("users", ["U-PRIYA", "U-A,U-B,U-C,U-D,U-E"])
def test_compare_rejects_bad_selection_sizes(users):
    assert client.get("/api/compare", params={"users": users}).status_code == 400
