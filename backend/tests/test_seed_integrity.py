"""Validates seed.sql against the constraints declared in schema.sql.

Postgres enforces these on load. This suite enforces them without a database,
so a broken seed fails in CI rather than in the Supabase SQL editor.
"""
import re

import pytest

from backend.data.repository import default_seed_path
from backend.data.sql_seed_parser import _strip_comments, load_seed_file

SCHEMA_PATH = default_seed_path().replace("seed.sql", "schema.sql")


@pytest.fixture(scope="module")
def seed():
    return load_seed_file(default_seed_path())


@pytest.fixture(scope="module")
def schema():
    with open(SCHEMA_PATH, encoding="utf-8") as handle:
        return handle.read()


def _check_values(schema_text: str, column: str):
    """Pull the allowed values out of a CHECK (col IN ('a','b')) clause."""
    match = re.search(
        r"\b" + column + r"\b[^,]*?CHECK\s*\(\s*" + column + r"\s+IN\s*\(([^)]*)\)",
        schema_text,
        re.IGNORECASE | re.DOTALL,
    )
    assert match, "no CHECK ... IN found for column {}".format(column)
    return {v.strip().strip("'") for v in match.group(1).split(",")}


def test_expected_row_counts(seed):
    assert len(seed["organizations"]) == 1
    assert len(seed["hierarchy_levels"]) == 20
    assert len(seed["users"]) == 7
    assert len(seed["knowledge_nodes"]) == 50
    assert len(seed["edges"]) == 10


def test_primary_keys_are_unique(seed):
    for table in ("organizations", "hierarchy_levels", "users", "knowledge_nodes"):
        ids = [row["id"] for row in seed[table]]
        assert len(ids) == len(set(ids)), table


def test_foreign_keys_resolve(seed):
    orgs = {r["id"] for r in seed["organizations"]}
    levels = {r["id"] for r in seed["hierarchy_levels"]}
    nodes = {r["id"] for r in seed["knowledge_nodes"]}

    for level in seed["hierarchy_levels"]:
        assert level["org_id"] in orgs, level["id"]
        for parent in level["parent_ids"]:
            assert parent in levels, "{} -> missing parent {}".format(level["id"], parent)

    for user in seed["users"]:
        assert user["org_id"] in orgs, user["id"]

    for node in seed["knowledge_nodes"]:
        assert node["org_id"] in orgs, node["id"]
        assert node["hierarchy_level_id"] in levels, node["id"]

    for edge in seed["edges"]:
        assert edge["source_id"] in nodes, edge["source_id"]
        assert edge["target_id"] in nodes, edge["target_id"]


def test_enum_columns_match_schema_checks(seed, schema):
    node_types = _check_values(schema, "type")
    statuses = _check_values(schema, "status")
    roles = _check_values(schema, "role")
    edge_types = _check_values(schema, "edge_type")

    for node in seed["knowledge_nodes"]:
        assert node["type"] in node_types, node["id"]
        assert node["status"] in statuses, node["id"]
    for user in seed["users"]:
        assert user["role"] in roles, user["id"]
    for edge in seed["edges"]:
        assert edge["edge_type"] in edge_types, edge


def test_numeric_ranges_match_schema_checks(seed):
    for node in seed["knowledge_nodes"]:
        assert 0.0 <= node["importance"] <= 1.0, node["id"]
        assert 0.0 <= node["derivability_score"] <= 1.0, node["id"]
        assert node["zone"] in (1, 2, 3), node["id"]
    for level in seed["hierarchy_levels"]:
        assert 1 <= level["level_number"] <= 15, level["id"]
        assert level["zone"] in (1, 2, 3), level["id"]
    for user in seed["users"]:
        assert 1 <= user["ceiling_level"] <= 15, user["id"]
        if user["write_ceiling"] is not None:
            assert 1 <= user["write_ceiling"] <= 15, user["id"]


def test_schema_does_not_declare_the_broken_unique_constraint(schema):
    """The spec's UNIQUE(org_id, level_number, department) rejects the seed.

    Orthopaedics has three level-8 units (General, TKR Unit, Post-TKR Protocol
    Area), so that constraint makes schema.sql and seed.sql mutually
    incompatible. It is removed; see the comment in schema.sql.
    """
    collisions = {}
    for level in [r for r in load_seed_file(default_seed_path())["hierarchy_levels"]]:
        if level["department"] is None:
            continue
        key = (level["org_id"], level["level_number"], level["department"])
        collisions.setdefault(key, []).append(level["id"])
    clashing = {k: v for k, v in collisions.items() if len(v) > 1}
    assert clashing, "seed no longer collides — the constraint could come back"

    # Strip SQL comments first: the explanation of the removal names the
    # constraint, and must not be mistaken for the constraint itself.
    normalised = re.sub(r"\s+", " ", _strip_comments(schema))
    assert "UNIQUE(org_id, level_number, department)" not in normalised
    assert "UNIQUE (org_id, level_number, department)" not in normalised


def test_dag_is_acyclic_and_has_one_root(seed):
    levels = {r["id"]: r for r in seed["hierarchy_levels"]}
    roots = [lid for lid, r in levels.items() if not r["parent_ids"]]
    assert roots == ["HL-01"]

    state = {}

    def visit(level_id):
        if state.get(level_id) == "done":
            return
        assert state.get(level_id) != "open", "cycle at {}".format(level_id)
        state[level_id] = "open"
        for parent in levels[level_id]["parent_ids"]:
            visit(parent)
        state[level_id] = "done"

    for level_id in levels:
        visit(level_id)


def test_every_level_reaches_the_root(seed):
    levels = {r["id"]: r for r in seed["hierarchy_levels"]}
    for level_id in levels:
        seen, frontier = set(), [level_id]
        while frontier:
            current = frontier.pop()
            if current in seen:
                continue
            seen.add(current)
            frontier.extend(levels[current]["parent_ids"])
        assert "HL-01" in seen, "{} is orphaned".format(level_id)


def test_insert_column_lists_exist_in_schema(seed, schema):
    """Every column the seed writes is declared by schema.sql."""
    for table in ("organizations", "hierarchy_levels", "users", "knowledge_nodes", "edges"):
        block = re.search(
            r"CREATE TABLE " + table + r"\s*\((.*?)\n\);", schema, re.DOTALL | re.IGNORECASE
        )
        assert block, table
        declared = set(re.findall(r"^\s{4}(\w+)\s", block.group(1), re.MULTILINE))
        used = set(seed[table][0])
        assert used <= declared, "{}: undeclared columns {}".format(table, used - declared)


def test_the_multi_parent_case_is_actually_present(seed):
    multi = [r for r in seed["hierarchy_levels"] if len(r["parent_ids"]) > 1]
    assert [r["id"] for r in multi] == ["HL-08-POST-TKR"]


def test_zone2_nodes_are_all_on_a_zone2_level(seed):
    levels = {r["id"]: r for r in seed["hierarchy_levels"]}
    globals_ = [n for n in seed["knowledge_nodes"] if n["zone"] == 2]
    assert len(globals_) == 10
    assert all(levels[n["hierarchy_level_id"]]["zone"] == 2 for n in globals_)
