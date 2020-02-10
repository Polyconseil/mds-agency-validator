import pytest

from mds_agency_validator.app import create_app
from mds_agency_validator import cache


@pytest.fixture
def client():
    """A test client for the app."""

    # setup app_context to allow url_for in test
    app = create_app()
    app.test_request_context().push()
    return app.test_client()


@pytest.fixture(autouse=True)
def clear_cache():
    yield
    cache.clear()
