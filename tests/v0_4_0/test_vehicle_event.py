import html
import json
import uuid

import pytest
from flask import url_for

from tests.utils import REGISTERED_DEVICE_ID, get_request, register_device

from .utils import generate_telemetry, get_timestamp


def generate_payload(event):
    """Generate the base payload. You need to fill event_type, event_type_reason
    and trip_id"""
    payload = {
        'telemetry': generate_telemetry(),
        'timestamp': get_timestamp(),
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
def test_valid_post(client, event_args):
    register_device()
    url = url_for('v0_4_0.vehicle_event', device_id=REGISTERED_DEVICE_ID)
    kwargs = get_request(generate_payload(event_args))
    response = client.post(
        url,
        **kwargs,
    )
    assert response.status == '201 CREATED'
    assert response.data == b''


def test_trip_id(client):
    """should only be present for trip events"""
    register_device()

    # trip_ip should be present
    url = url_for('v0_4_0.vehicle_event', device_id=REGISTERED_DEVICE_ID)
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


def test_event_type_reason(client):
    """required and allowed vaules depends on event_type"""
    register_device()

    # event_type_reason shouldn't be present
    url = url_for('v0_4_0.vehicle_event', device_id=REGISTERED_DEVICE_ID)
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


def test_device_id(client):
    register_device()
    url = url_for('v0_4_0.vehicle_event', device_id=REGISTERED_DEVICE_ID)
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


def test_invalid_telemetry(client):
    register_device()

    url = url_for('v0_4_0.vehicle_event', device_id=REGISTERED_DEVICE_ID)
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


def test_missing_required(client):
    register_device()

    url = url_for('v0_4_0.vehicle_event', device_id=REGISTERED_DEVICE_ID)
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


def test_wrong_type(client):
    register_device()

    url = url_for('v0_4_0.vehicle_event', device_id=REGISTERED_DEVICE_ID)
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


def test_unknown_field(client):
    register_device()

    url = url_for('v0_4_0.vehicle_event', device_id=REGISTERED_DEVICE_ID)
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


def test_unregistered_device(client):
    url = url_for('v0_4_0.vehicle_event', device_id=REGISTERED_DEVICE_ID)
    event = {'event_type': 'register'}
    kwargs = get_request(generate_payload(event))
    response = client.post(
        url,
        **kwargs,
    )
    assert response.status == '404 NOT FOUND'
