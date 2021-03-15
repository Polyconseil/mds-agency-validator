import jwt
import pytest
from flask import url_for

from .utils import REGISTERED_DEVICE_ID, get_request


def test_index(client):
    response = client.get(url_for('index'))
    expected = b"""/
/v0.4.0/vehicles
/v0.4.0/vehicles/<device_id>
/v0.4.0/vehicles/<device_id>/event
/v0.4.0/vehicles/telemetry"""
    assert expected == response.data


@pytest.mark.parametrize(
    'url_name, url_kwargs',
    [
        ('v0_4_0.vehicle_register', {}),
        ('v0_4_0.vehicle_telemetry', {}),
        ('v0_4_0.vehicle_event', {'device_id': REGISTERED_DEVICE_ID}),
        ('v0_4_0.vehicle_update', {'device_id': REGISTERED_DEVICE_ID}),
    ],
)
def test_no_authorization(client, url_name, url_kwargs):
    url = url_for(url_name, **url_kwargs)
    kwargs = get_request({})
    del kwargs['headers']['Authorization']
    response = client.post(
        url,
        **kwargs,
    )
    assert response.status == '401 UNAUTHORIZED'
    assert b'Please provide an Authorization' in response.data


@pytest.mark.parametrize(
    'url_name, url_kwargs',
    [
        ('v0_4_0.vehicle_register', {}),
        ('v0_4_0.vehicle_telemetry', {}),
        ('v0_4_0.vehicle_event', {'device_id': REGISTERED_DEVICE_ID}),
        ('v0_4_0.vehicle_update', {'device_id': REGISTERED_DEVICE_ID}),
    ],
)
def test_basic_auth(client, url_name, url_kwargs):
    url = url_for(url_name, **url_kwargs)
    kwargs = get_request({})
    kwargs['headers']['Authorization'] = 'Basic dXNlcm5hbWU6cGFzc3dvcmQ='
    response = client.post(
        url,
        **kwargs,
    )
    assert response.status == '401 UNAUTHORIZED'
    assert b'Please provide a Bearer token' in response.data


@pytest.mark.parametrize(
    'url_name, url_kwargs',
    [
        ('v0_4_0.vehicle_register', {}),
        ('v0_4_0.vehicle_telemetry', {}),
        ('v0_4_0.vehicle_event', {'device_id': REGISTERED_DEVICE_ID}),
        ('v0_4_0.vehicle_update', {'device_id': REGISTERED_DEVICE_ID}),
    ],
)
def test_no_provider_id(client, url_name, url_kwargs):
    url = url_for(url_name, **url_kwargs)
    kwargs = get_request({})
    token = jwt.encode({'key': 'value'}, 'secret')
    kwargs['headers']['Authorization'] = 'Bearer %s' % token
    response = client.post(
        url,
        **kwargs,
    )
    assert response.status == '401 UNAUTHORIZED'
    assert b'Please provide a provider_id' in response.data


@pytest.mark.parametrize(
    'url_name, url_kwargs',
    [
        ('v0_4_0.vehicle_register', {}),
        ('v0_4_0.vehicle_telemetry', {}),
        ('v0_4_0.vehicle_event', {'device_id': REGISTERED_DEVICE_ID}),
        ('v0_4_0.vehicle_update', {'device_id': REGISTERED_DEVICE_ID}),
    ],
)
def test_invalid_jwt(client, url_name, url_kwargs):
    url = url_for(url_name, **url_kwargs)
    kwargs = get_request({})
    kwargs['headers']['Authorization'] = 'Bearer bad_jwt'
    response = client.post(
        url,
        **kwargs,
    )
    assert response.status == '401 UNAUTHORIZED'
    assert b'Please provide a valid JWT' in response.data
