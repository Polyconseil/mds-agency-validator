import pytest

from mds_agency_validator.app import create_app


@pytest.fixture
def client():
    """A test client for the app."""
    return create_app().test_client()


@pytest.fixture
def app_context():
    """Set app_context, which allow to use url_for in tests"""
    return create_app().test_request_context().push()
