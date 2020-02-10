import pytest

from mds_agency_validator import cache


REGISTRED_DEVICE_ID = '9bf269ac-4f4c-4ee4-8ea1-6f2c7dfda397'


@pytest.fixture
def register_device():
    """Register a device"""
    device = {
        'device_id': REGISTRED_DEVICE_ID,
        'vehicle_id': 'AM-9863-EZ',
        'type': 'scooter',
        'propulsion': ['electric'],
    }
    cache.set(device['device_id'], device)
    return device
