import html
import json
import uuid

import jwt
import pytest
from flask import url_for

from tests import utils

from .conftest import REGISTRED_DEVICE_ID
from .utils import generate_telemetry, get_request


def generate_payload(event):
    """Generate the base payload. You need to fill event_type, event_type_reason
    and trip_id"""
    payload = {
        'telemetry': generate_telemetry(),
        'timestamp': utils.get_timestamp(),
    }
    payload.update(event)
    return payload


@pytest.mark.parametrize(
    'event_args',
    [
        {'event_type': 'register'},
        {'event_type': 'trip_start', 'trip_id': str(uuid.uuid4())},
        {'event_type': 'deregister', 'event_type_reason': 'missing'},
    ],
)
def test_valid_post(client, register_device, event_args):
    url = url_for('v0_4_0.vehicle_event', device_id=REGISTRED_DEVICE_ID)
    kwargs = get_request(generate_payload(event_args))
    response = client.post(
        url,
        **kwargs,
    )
    assert response.status == '201 CREATED'
    assert response.data == b''


def test_incorrect_content_type(client, register_device):
    # This is not handle by MDS 0.4.0, so it works with a bad Content-Type
    url = url_for('v0_4_0.vehicle_event', device_id=REGISTRED_DEVICE_ID)
    event = {'event_type': 'register'}
    kwargs = get_request(generate_payload(event))
    kwargs['content_type'] = 'test/html'
    response = client.post(
        url,
        **kwargs,
    )
    assert response.status == '201 CREATED'
    assert response.data == b''


def test_incorrect_authorization(client, register_device):
    url = url_for('v0_4_0.vehicle_event', device_id=REGISTRED_DEVICE_ID)
    event = {'event_type': 'register'}
    kwargs = get_request(generate_payload(event))
    # With no auth at all
    del kwargs['headers']['Authorization']
    response = client.post(
        url,
        **kwargs,
    )
    assert response.status == '401 UNAUTHORIZED'
    assert b'Please provide an Authorization' in response.data

    # With Basic token
    kwargs = get_request(generate_payload(event))
    kwargs['headers']['Authorization'] = 'Basic dXNlcm5hbWU6cGFzc3dvcmQ='
    response = client.post(
        url,
        **kwargs,
    )
    assert response.status == '401 UNAUTHORIZED'
    assert b'Please provide a Bearer token' in response.data

    # Provider_id is missing
    kwargs = get_request(generate_payload(event))
    token = jwt.encode({'key': 'value'}, 'secret')
    kwargs['headers']['Authorization'] = 'Bearer %s' % token
    response = client.post(
        url,
        **kwargs,
    )
    assert response.status == '401 UNAUTHORIZED'
    assert b'Please provide a provider_id' in response.data

    # Invalid JWT
    kwargs = get_request(generate_payload(event))
    kwargs['headers']['Authorization'] = 'Bearer bad_jwt'
    response = client.post(
        url,
        **kwargs,
    )
    assert response.status == '401 UNAUTHORIZED'
    assert b'Please provide a valid JWT' in response.data


def test_trip_id(client, register_device):
    """should only be present for trip events"""

    # trip_ip should be present
    url = url_for('v0_4_0.vehicle_event', device_id=REGISTRED_DEVICE_ID)
    event = {'event_type': 'trip_start'}
    kwargs = get_request(generate_payload(event))
    response = client.post(
        url,
        **kwargs,
    )
    assert response.status == '400 BAD REQUEST'
    expected = html.escape(json.dumps({'missing_param': ['trip_id']}))
    assert expected.encode() in response.data

    # trip_ip should not be present
    event = {'event_type': 'register', 'trip_id': str(uuid.uuid4())}
    kwargs = get_request(generate_payload(event))
    response = client.post(
        url,
        **kwargs,
    )
    assert response.status == '400 BAD REQUEST'
    expected = html.escape(json.dumps({'bad_param': ['trip_id']}))
    assert expected.encode() in response.data


def test_event_type_reason(client, register_device):
    """required and allowed vaules depends on event_type"""

    # event_type_reason shouldn't be present
    url = url_for('v0_4_0.vehicle_event', device_id=REGISTRED_DEVICE_ID)
    event = {'event_type': 'register', 'event_type_reason': 'compliance'}
    kwargs = get_request(generate_payload(event))
    response = client.post(
        url,
        **kwargs,
    )
    assert response.status == '400 BAD REQUEST'
    expected = html.escape(json.dumps({'bad_param': ['event_type_reason']}))
    assert expected.encode() in response.data

    # event_type_reason has a wrong value
    event = {'event_type': 'deregister', 'event_type_reason': 'compliance'}
    kwargs = get_request(generate_payload(event))
    response = client.post(
        url,
        **kwargs,
    )
    assert response.status == '400 BAD REQUEST'
    expected = html.escape(json.dumps({'bad_param': ['event_type_reason']}))
    assert expected.encode() in response.data

    # event_type_reason should be present
    # TODO confirm if it's true
    event = {'event_type': 'deregister'}
    kwargs = get_request(generate_payload(event))
    response = client.post(
        url,
        **kwargs,
    )
    assert response.status == '400 BAD REQUEST'
    expected = html.escape(json.dumps({'missing_param': ['event_type_reason']}))
    assert expected.encode() in response.data


def test_device_id(client, register_device):
    url = url_for('v0_4_0.vehicle_event', device_id=REGISTRED_DEVICE_ID)
    event = {'event_type': 'register'}
    data = generate_payload(event)
    data['telemetry']['device_id'] = str(uuid.uuid4())
    kwargs = get_request(data)
    response = client.post(
        url,
        **kwargs,
    )
    assert response.status == '400 BAD REQUEST'
    expected = html.escape(json.dumps({'bad_param': ['device_id']}))
    assert expected.encode() in response.data


def test_invalid_telemetry(client, register_device):
    url = url_for('v0_4_0.vehicle_event', device_id=REGISTRED_DEVICE_ID)
    event = {'event_type': 'register'}
    data = generate_payload(event)
    del data['telemetry']['gps']['lat']
    kwargs = get_request(data)
    response = client.post(
        url,
        **kwargs,
    )
    assert response.status == '400 BAD REQUEST'
    expected = html.escape(json.dumps({'missing_param': ['telemetry.gps.lat']}))
    assert expected.encode() in response.data


def test_missing_required(client, register_device):
    url = url_for('v0_4_0.vehicle_event', device_id=REGISTRED_DEVICE_ID)
    event = {'event_type': 'register'}
    data = generate_payload(event)
    del data['timestamp']
    kwargs = get_request(data)
    response = client.post(
        url,
        **kwargs,
    )
    assert response.status == '400 BAD REQUEST'
    expected = html.escape(json.dumps({'missing_param': ['timestamp']}))
    assert expected.encode() in response.data


def test_wrong_type(client, register_device):
    url = url_for('v0_4_0.vehicle_event', device_id=REGISTRED_DEVICE_ID)
    event = {'event_type': 'register'}
    data = generate_payload(event)
    data['telemetry'] = 346
    kwargs = get_request(data)
    response = client.post(
        url,
        **kwargs,
    )
    assert response.status == '400 BAD REQUEST'
    expected = html.escape(json.dumps({'bad_param': ['telemetry']}))
    assert expected.encode() in response.data


def test_unknown_field(client, register_device):
    url = url_for('v0_4_0.vehicle_event', device_id=REGISTRED_DEVICE_ID)
    event = {'event_type': 'register'}
    data = generate_payload(event)
    data['unknown_field'] = 'nope'
    kwargs = get_request(data)
    response = client.post(
        url,
        **kwargs,
    )
    assert response.status == '400 BAD REQUEST'
    expected = html.escape(json.dumps({'bad_param': ['unknown_field']}))
    assert expected.encode() in response.data


def test_unregistred_device(client):
    url = url_for('v0_4_0.vehicle_event', device_id=REGISTRED_DEVICE_ID)
    event = {'event_type': 'register'}
    kwargs = get_request(generate_payload(event))
    response = client.post(
        url,
        **kwargs,
    )
    assert response.status == '404 NOT FOUND'
