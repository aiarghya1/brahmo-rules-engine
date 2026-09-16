"""The five checks: sequencing, and what each one is responsible for."""
from datetime import datetime, timedelta, timezone

from backend.models.node import NodeFilterRow
from backend.pipeline.five_check_filter import run_five_checks
from backend.pipeline.permission_compiler import compile_permissions

NOW = datetime(2026, 9, 16, tzinfo=timezone.utc)


def _row(node_id, **kw):
    base = dict(
        id=node_id,
        org_id="supra",
        hierarchy_level_id="HL-05-ORTHO",
        hierarchy_level=5,
        department="ortho",
        type="FACT",
        importance=0.5,
        zone=1,
        status="ACTIVE",
        derivability_score=0.1,
        compliance_tags=[],
        valid_until=None,
        title=node_id,
    )
    base.update(kw)
    return NodeFilterRow(**base)


def _run(repo, user_id, rows):
    user = repo.get_user(user_id)
    return run_five_checks(
        rows, compile_permissions(user), org_id="supra",
        derivability_threshold=0.7, now=NOW,
    )


def test_checks_run_in_order_and_feed_each_other(repo):
    rows = [_row("keep"), _row("other-org", org_id="other")]
    outcome = _run(repo, "U-VIKRAM", rows)
    names = [s.name for s in outcome.stages]
    assert names == ["isolation", "compliance", "permission", "temporal", "derivability"]
    # The sequential contract: every stage's input is the previous output.
    for previous, current in zip(outcome.stages, outcome.stages[1:]):
        assert current.count_in == previous.count_out


def test_check1_isolation_enforces_the_tenant_boundary(repo):
    outcome = _run(repo, "U-SURESH", [_row("mine"), _row("theirs", org_id="apollo")])
    assert outcome.stages[0].count_out == 1
    assert [n.id for n in outcome.survivors] == ["mine"]


def test_check2_blocks_uncleared_tags(repo):
    rows = [_row("mnpi", compliance_tags=["MNPI"], department="cardiology")]
    assert _run(repo, "U-PRIYA", rows).survivors == []          # no clearance
    assert len(_run(repo, "U-SURESH", rows).survivors) == 1      # full clearance


def test_check2_hod_clearance_is_scoped_to_own_department(repo):
    own = _row("own-budget", compliance_tags=["MNPI"], department="ortho")
    other = _row("other-budget", compliance_tags=["MNPI"], department="cardiology")
    survivors = {n.id for n in _run(repo, "U-VIKRAM", [own, other]).survivors}
    assert survivors == {"own-budget"}


def test_check3_uses_the_ceiling(repo):
    rows = [_row("hod-level", hierarchy_level=4), _row("ward-level", hierarchy_level=10)]
    assert {n.id for n in _run(repo, "U-PRIYA", rows).survivors} == {"ward-level"}
    assert len(_run(repo, "U-VIKRAM", rows).survivors) == 2


def test_check3_lets_global_safety_nodes_through(repo):
    """A ward nurse must still get hospital-wide drug-safety constraints."""
    rows = [_row("global", hierarchy_level=3, zone=2, department=None)]
    assert len(_run(repo, "U-PRIYA", rows).survivors) == 1


def test_check4_drops_superseded_and_expired(repo):
    rows = [
        _row("current"),
        _row("superseded", status="SUPERSEDED"),
        _row("lapsed", valid_until=NOW - timedelta(days=1)),
        _row("still-valid", valid_until=NOW + timedelta(days=1)),
    ]
    survivors = {n.id for n in _run(repo, "U-SURESH", rows).survivors}
    assert survivors == {"current", "still-valid"}


def test_check5_drops_what_the_model_already_knows(repo):
    rows = [_row("supra-specific", derivability_score=0.05),
            _row("textbook", derivability_score=0.95)]
    assert {n.id for n in _run(repo, "U-SURESH", rows).survivors} == {"supra-specific"}


def test_an_excluded_node_never_reaches_a_later_check(repo):
    """A compliance-blocked node is not even evaluated by checks 3-5."""
    rows = [_row("secret", compliance_tags=["MNPI"], department="cardiology")]
    outcome = _run(repo, "U-PRIYA", rows)
    assert outcome.stages[1].count_out == 0
    for stage in outcome.stages[2:]:
        assert stage.count_in == 0
        assert stage.excluded == []
