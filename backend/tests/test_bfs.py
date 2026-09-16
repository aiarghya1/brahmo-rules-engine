"""BFS traversal: direction, scoping, and multi-parent safety."""
from backend.pipeline.bfs_traversal import traverse
from backend.pipeline.entry_point_resolver import resolve_entry_point
from backend.pipeline.permission_compiler import compile_permissions


def _traverse_for(repo, user_id):
    user = repo.get_user(user_id)
    perms = compile_permissions(user)
    levels = repo.list_levels(user.org_id)
    nodes = repo.load_filter_index(user.org_id)
    entry = resolve_entry_point(perms, levels)
    return entry, traverse(entry, levels, nodes)


def test_entry_points_resolve_to_expected_levels(repo):
    expected = {
        "U-PRIYA": "HL-10-ORTHO-W",    # ward nurse starts at her ward
        "U-VIKRAM": "HL-05-ORTHO",     # HOD starts at his department
        "U-ANANYA": "HL-08-MED-GEN",   # editor starts at her sub-department
        "U-SHARMA": "HL-05-MED",
        "U-SURESH": "HL-01",           # no 'admin' level -> org root
        "U-SUNITA": "HL-01",           # quality is cross-departmental
        "U-RAVI": "HL-01",             # pharmacy is cross-departmental
    }
    for user_id, level_id in expected.items():
        entry, _ = _traverse_for(repo, user_id)
        assert entry.level.id == level_id, user_id


def test_bfs_walks_upward_to_the_root(repo):
    _, result = _traverse_for(repo, "U-PRIYA")
    reached = result.level_distance
    assert reached["HL-10-ORTHO-W"] == 0
    assert reached["HL-08-ORTHO-GEN"] == 1
    assert reached["HL-05-ORTHO"] == 2
    assert reached["HL-03-CLIN"] == 3
    assert reached["HL-01"] == 4


def test_multi_parent_node_is_processed_exactly_once(repo):
    _, result = _traverse_for(repo, "U-PRIYA")
    # Post-TKR has parent_ids = [Ortho, Surgery]: reachable from two paths.
    assert "HL-08-POST-TKR" in result.level_distance
    assert result.visit_order.count("HL-08-POST-TKR") == 1
    assert "HL-08-POST-TKR" in result.multi_parent_levels
    # And no level anywhere is visited twice.
    assert len(result.visit_order) == len(set(result.visit_order))
    assert result.revisits_prevented > 0


def test_multi_parent_edge_widens_reach(repo):
    """Surgery is only reachable through the Post-TKR node's second parent."""
    _, result = _traverse_for(repo, "U-PRIYA")
    assert "HL-05-SURG" in result.level_distance


def test_descent_is_department_scoped(repo):
    _, result = _traverse_for(repo, "U-PRIYA")
    reached = set(result.level_distance)
    # Priya walks up through the Clinical Division but must not descend into
    # its other children.
    assert "HL-03-CLIN" in reached
    for foreign in ("HL-05-MED", "HL-05-CARDIO", "HL-05-PAEDS", "HL-05-ICU"):
        assert foreign not in reached, foreign


def test_cross_departmental_user_reaches_everything(repo):
    _, result = _traverse_for(repo, "U-SURESH")
    assert len(result.node_ids) == repo.count_nodes("supra")


def test_traversal_carries_no_content(repo):
    """BFS returns ids and distances only."""
    _, result = _traverse_for(repo, "U-PRIYA")
    assert all(isinstance(nid, str) for nid in result.node_ids)
    assert set(result.node_distance) == result.node_ids
