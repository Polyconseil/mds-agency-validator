import pytest

from mds_agency_validator.app import create_app


@pytest.fixture
def client():
    """A test client for the app."""
    return create_app().test_client()
