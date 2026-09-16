"""Pins the JSON shape the frontend reads.

`tsc` type-checks the React components against `frontend/src/lib/types.ts`, but
nothing checks that those declarations match what the API actually returns. This
suite is that check: every field listed here is read by a component, so if the
backend stops sending one, this fails rather than the browser.
"""
from fastapi.testclient import TestClient

from backend.main import app

client = TestClient(app)

# field -> python type(s), mirroring frontend/src/lib/types.ts
USER_FIELDS = {
    "id": str, "name": str, "role": str, "department": str,
    "ceiling_level": int, "compliance_clearance": list, "label": str,
}
CANDIDATE_FIELDS = {
    "id": str, "type": str, "title": str, "content": str,
    "importance": float, "zone": int, "hierarchy_level": int,
    "hierarchy_level_id": str, "distance_from_entry": int,
    "compression_hint": str, "reached_via": str,
}
STAGE_FIELDS = {
    "name": str, "label": str, "count_in": int, "count_out": int,
    "removed": int, "duration_ms": float, "sql": str, "excluded": list,
}
LEVEL_FIELDS = {
    "id": str, "level_number": int, "level_name": str, "parent_ids": list, "zone": int,
}


def _assert_fields(obj, spec, where):
    for field, expected in spec.items():
        assert field in obj, "{}: missing '{}'".format(where, field)
        if expected is float:
            assert isinstance(obj[field], (int, float)), "{}.{}".format(where, field)
        else:
            assert isinstance(obj[field], expected), "{}.{}".format(where, field)


def test_users_payload():
    for user in client.get("/api/users").json():
        _assert_fields(user, USER_FIELDS, "user")
        assert "write_ceiling" in user  # nullable


def test_graph_payload():
    graph = client.get("/api/graph").json()
    for key in ("levels", "nodes", "edges"):
        assert key in graph
    for level in graph["levels"]:
        _assert_fields(level, LEVEL_FIELDS, "level")
        assert "department" in level  # nullable
    for node in graph["nodes"]:
        for field in ("id", "title", "type", "hierarchy_level_id", "zone", "importance"):
            assert field in node
    for edge in graph["edges"]:
        assert {"source_id", "target_id", "edge_type"} <= set(edge)


def test_pipeline_payload_matches_the_typescript_interface():
    body = client.get("/api/pipeline/U-PRIYA").json()

    for field in (
        "user", "user_name", "role", "department", "ceiling_level", "write_ceiling",
        "org", "entry_point", "entry_point_detail", "permissions", "traversal",
        "zone2", "pipeline_timing", "funnel", "stages", "excluded",
        "unreachable_node_ids", "distribution", "llm_calls", "policy", "candidate_set",
    ):
        assert field in body, field

    for field in ("level_id", "level_name", "level_number", "strategy", "reason"):
        assert field in body["entry_point_detail"], field

    for field in (
        "reached_levels", "visit_order", "reachable_node_count",
        "multi_parent_levels", "revisits_prevented", "max_distance",
    ):
        assert field in body["traversal"], field

    assert {"injected", "already_reachable", "combined_count"} <= set(body["zone2"])
    assert {"by_type", "by_department", "by_compression_hint"} <= set(body["distribution"])
    assert {"zone2_bypasses_ceiling", "inherit_dept_path", "derivability_threshold"} <= set(
        body["policy"]
    )
    assert "config" in body["org"] and "derivability_threshold" in body["org"]["config"]


def test_funnel_keys_the_stage_cards_read():
    funnel = client.get("/api/pipeline/U-PRIYA").json()["funnel"]
    for field in (
        "total_nodes", "after_bfs", "after_zone2", "after_check1", "after_check2",
        "after_check3", "after_check4", "after_check5", "candidate_set",
    ):
        assert field in funnel, field
        assert isinstance(funnel[field], int)


def test_timing_keys_the_timing_panel_reads():
    timing = client.get("/api/pipeline/U-PRIYA").json()["pipeline_timing"]
    for field in (
        "permission_compile_ms", "entry_point_ms", "bfs_ms", "zone2_inject_ms",
        "check1_isolation_ms", "check2_compliance_ms", "check3_permission_ms",
        "check4_temporal_ms", "check5_derivability_ms", "content_fetch_ms",
        "assemble_ms", "total_ms",
    ):
        assert field in timing, field


def test_stage_and_candidate_shapes():
    body = client.get("/api/pipeline/U-PRIYA").json()
    assert len(body["stages"]) == 5
    for stage in body["stages"]:
        _assert_fields(stage, STAGE_FIELDS, "stage")
        for exclusion in stage["excluded"]:
            assert {"node_id", "title", "stage", "reason"} <= set(exclusion)
    for candidate in body["candidate_set"]:
        _assert_fields(candidate, CANDIDATE_FIELDS, "candidate")
        assert "department" in candidate  # nullable


def test_compare_payload():
    body = client.get("/api/compare", params={"users": "U-PRIYA,U-VIKRAM"}).json()
    assert {"results", "shared_node_ids", "exclusive_node_ids"} <= set(body)
    for result in body["results"]:
        assert result["user"] in body["exclusive_node_ids"]
