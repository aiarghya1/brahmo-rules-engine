"""End-to-end pipeline behaviour, including the assessment's acceptance list."""
import pytest

from backend.pipeline.engine import run_pipeline

FORBIDDEN_FOR_PRIYA = ("cardiology", "paediatrics", "icu", "medicine", "surgery")


@pytest.fixture(scope="module")
def priya(repo):
    return run_pipeline(repo, "U-PRIYA")


def test_different_users_get_different_candidate_sets(repo):
    sets = {
        uid: {c["id"] for c in run_pipeline(repo, uid)["candidate_set"]}
        for uid in ("U-PRIYA", "U-VIKRAM", "U-SURESH")
    }
    assert sets["U-PRIYA"] != sets["U-VIKRAM"] != sets["U-SURESH"]
    # Authority is monotonic: a ward nurse sees less than her HOD, who sees
    # less than the administrator.
    assert len(sets["U-PRIYA"]) < len(sets["U-VIKRAM"]) < len(sets["U-SURESH"])


def test_priya_sees_no_other_departments(priya):
    for candidate in priya["candidate_set"]:
        assert candidate["department"] in (None, "ortho"), candidate["id"]
        assert candidate["department"] not in FORBIDDEN_FOR_PRIYA


def test_priya_sees_no_restricted_nodes(priya):
    ids = {c["id"] for c in priya["candidate_set"]}
    for blocked in ("N-O11", "N-O12", "N-A01", "N-A02", "N-A04", "N-C04"):
        assert blocked not in ids


def test_priya_sees_no_superseded_nodes(repo, priya):
    content = repo.fetch_content([c["id"] for c in priya["candidate_set"]])
    assert all(node.status not in ("SUPERSEDED", "EXPIRED") for node in content.values())
    assert "N-M08" not in content


def test_priya_sees_nothing_the_model_already_knows(priya):
    threshold = priya["org"]["config"]["derivability_threshold"]
    ids = {c["id"] for c in priya["candidate_set"]}
    assert ids.isdisjoint({"N-D01", "N-D02", "N-D03", "N-D04", "N-D05"})
    assert threshold == 0.7


def test_priya_still_gets_global_drug_safety(priya):
    ids = {c["id"] for c in priya["candidate_set"]}
    assert "N-G01" in ids   # Warfarin-NSAID
    assert "N-O14" in ids   # her patient's NSAID contraindication


def test_zone2_is_injected_before_the_checks_not_after(repo):
    """Injected globals are still subject to every check."""
    result = run_pipeline(repo, "U-PRIYA")
    injected = set(result["zone2"]["injected"])
    assert len(injected) == 10
    final = {c["id"] for c in result["candidate_set"]}
    # N-G04 (0.75) and N-G06 (0.80) are global AND derivable -> dropped.
    assert {"N-G04", "N-G06"}.issubset(injected)
    assert final.isdisjoint({"N-G04", "N-G06"})


def test_funnel_is_monotonically_narrowing(repo):
    for uid in ("U-PRIYA", "U-VIKRAM", "U-ANANYA", "U-SURESH", "U-RAVI", "U-SUNITA"):
        funnel = run_pipeline(repo, uid)["funnel"]
        counts = [funnel["after_zone2"]] + [funnel["after_check%d" % i] for i in range(1, 6)]
        assert counts == sorted(counts, reverse=True), uid


def test_annotations_are_complete(priya):
    for candidate in priya["candidate_set"]:
        assert candidate["type"] in ("CONSTRAINT", "DECISION", "ANTI_PATTERN", "FACT")
        assert 0.0 <= candidate["importance"] <= 1.0
        assert candidate["distance_from_entry"] >= 0
        assert candidate["compression_hint"] in ("FULL", "COMPRESSED", "CONSTRAINT_ONLY")
        assert candidate["content"]


def test_compression_hint_tracks_distance(priya):
    for candidate in priya["candidate_set"]:
        distance = candidate["distance_from_entry"]
        expected = "FULL" if distance <= 1 else "COMPRESSED" if distance == 2 else "CONSTRAINT_ONLY"
        assert candidate["compression_hint"] == expected


def test_pipeline_is_deterministic(repo):
    first = run_pipeline(repo, "U-VIKRAM")["candidate_set"]
    second = run_pipeline(repo, "U-VIKRAM")["candidate_set"]
    assert [c["id"] for c in first] == [c["id"] for c in second]


def test_pipeline_uses_no_llm_and_is_fast(repo):
    result = run_pipeline(repo, "U-SURESH")
    assert result["llm_calls"] == 0
    assert result["pipeline_timing"]["total_ms"] < 500


def test_content_is_fetched_only_for_survivors(repo):
    """GAP 5 — a node the user may not read never has its content loaded."""
    seen = {}
    original = repo.fetch_content

    def spy(ids):
        ids = list(ids)
        seen["ids"] = ids
        return original(ids)

    repo.fetch_content = spy
    try:
        result = run_pipeline(repo, "U-PRIYA")
    finally:
        repo.fetch_content = original

    requested = set(seen["ids"])
    assert requested == {c["id"] for c in result["candidate_set"]}
    assert "N-O11" not in requested          # MNPI, excluded at check 2
    assert len(requested) < result["funnel"]["total_nodes"]


def test_every_seeded_user_runs(repo):
    """Including the three that are not in the demo script."""
    for user in repo.list_users():
        result = run_pipeline(repo, user.id)
        assert result["funnel"]["candidate_set"] > 0, user.id
        assert result["entry_point"]


def test_unknown_user_is_rejected(repo):
    with pytest.raises(KeyError):
        run_pipeline(repo, "U-NOBODY")
