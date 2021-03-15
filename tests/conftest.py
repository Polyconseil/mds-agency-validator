import pytest

from mds_agency_validator.app import app
from mds_agency_validator.cache import cache


@pytest.fixture
def client():
    """A test client for the app."""
    # setup app_context to allow url_for in test
    app.test_request_context().push()
    return app.test_client()


@pytest.fixture(autouse=True)
def clear_cache():
    cache.clear()
