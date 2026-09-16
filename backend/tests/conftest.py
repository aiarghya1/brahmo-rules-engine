import os
import sys

import pytest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from backend.data.repository import LocalSeedRepository, default_seed_path  # noqa: E402


@pytest.fixture(scope="session")
def repo():
    return LocalSeedRepository(default_seed_path())
