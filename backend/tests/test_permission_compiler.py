"""The compiled permission table."""
from backend.pipeline.permission_compiler import MAX_LEVEL, compile_permissions


def test_compiles_every_level_once(repo):
    perms = compile_permissions(repo.get_user("U-PRIYA"))
    assert set(perms.levels) == set(range(1, MAX_LEVEL + 1))


def test_viewer_reads_at_or_below_ceiling_and_writes_nothing(repo):
    perms = compile_permissions(repo.get_user("U-PRIYA"))  # VIEWER, ceiling 10
    assert not perms.can_read(9)
    assert perms.can_read(10) and perms.can_read(12)
    assert not any(perms.can_write(level) for level in range(1, MAX_LEVEL + 1))


def test_editor_write_floor_is_the_write_ceiling(repo):
    perms = compile_permissions(repo.get_user("U-ANANYA"))  # EDITOR 8 / write 8
    assert perms.can_read(8) and not perms.can_read(7)
    assert perms.can_write(8) and not perms.can_write(7)


def test_quality_may_write_deeper_than_it_reads(repo):
    perms = compile_permissions(repo.get_user("U-SUNITA"))  # read 6 / write 8
    assert perms.can_read(6) and not perms.can_write(6)
    assert perms.can_write(8)


def test_hod_reads_every_level_but_writes_from_its_ceiling(repo):
    perms = compile_permissions(repo.get_user("U-VIKRAM"))  # HOD, ceiling 4
    assert all(perms.can_read(level) for level in range(1, MAX_LEVEL + 1))
    assert perms.can_write(4) and not perms.can_write(3)


def test_admin_reads_and_writes_everything(repo):
    perms = compile_permissions(repo.get_user("U-SURESH"))
    assert all(perms.can_read(l) and perms.can_write(l) for l in range(1, MAX_LEVEL + 1))
    assert perms.blocked_tags == frozenset()


def test_blocking_tags_respects_explicit_clearance(repo):
    perms = compile_permissions(repo.get_user("U-SUNITA"))  # cleared for MNPI
    assert perms.blocking_tags(["MNPI"], "cardiology") == []
    assert perms.blocking_tags(["CONFIDENTIAL"], "cardiology") == ["CONFIDENTIAL"]


def test_lookup_is_a_plain_dict_hit(repo):
    """O(1): the check does one dict lookup, no policy evaluation."""
    perms = compile_permissions(repo.get_user("U-PRIYA"))
    assert perms.levels[10].can_read is True
