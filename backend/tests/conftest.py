"""
Shared pytest fixtures for the backend test suite.

Mocks get_settings() with an in-memory SQLite config so that importing
app.services.* never triggers directory creation or reads .env files.
"""

from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from app.core.config import Settings


@pytest.fixture(autouse=True)
def _mock_settings(tmp_path: Path):
    """
    Patch get_settings() for every test in this suite.

    validate_analysis_range() is a pure function that does NOT use settings,
    but importing app.services.songs pulls in get_settings via module-level
    imports.  Without this patch the lru_cache'd get_settings() would call
    Path.mkdir() on real filesystem paths and potentially fail in CI or in
    read-only environments.
    """
    fake_settings = Settings(
        database_url="sqlite:///:memory:",
        storage_root=tmp_path,
    )
    with patch("app.core.config.get_settings", return_value=fake_settings):
        yield fake_settings
