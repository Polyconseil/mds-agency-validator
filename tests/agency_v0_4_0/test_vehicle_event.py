import json
import jwt
import html
import uuid

from flask import url_for

from tests import utils
from .utils import generate_telemetry
from .utils import get_request


def generate_payload(event):
    """Generate the base payload. You need to fill event_type, event_type_reason
    and trip_id"""
    payload = {
        'telemetry': generate_telemetry(),
        'timestamp': utils.get_timestamp(),
    }
    payload.update(event)
    return payload


def test_valid_post(client):
    valid_events = [
        {'event_type': 'register'},
        {'event_type': 'trip_start', 'trip_id': str(uuid.uuid4())},
        {'event_type': 'deregister', 'event_type_reason': 'missing'},
    ]
    for event in valid_events:
        data = generate_payload(event)
        device_id = data['telemetry']['device_id']
        url = url_for('agency_v0_4_0_vehicles_event', device_id=device_id)
        kwargs = get_request(data)
        response = client.post(
            url,
            **kwargs,
        )
        assert response.status == '201 CREATED'
        assert response.data == b''


def test_incorrect_content_type(client):
    # This is not handle by MDS 0.4.0, so it works with a bad Content-Type
    event = {'event_type': 'register'}
    data = generate_payload(event)
    device_id = data['telemetry']['device_id']
    url = url_for('agency_v0_4_0_vehicles_event', device_id=device_id)
    kwargs = get_request(data)
    kwargs['content_type'] = 'test/html'
    response = client.post(
        url,
        **kwargs,
    )
    assert response.status == '201 CREATED'
    assert response.data == b''


def test_incorrect_authorization(client):
    event = {'event_type': 'register'}
    data = generate_payload(event)
    device_id = data['telemetry']['device_id']
    url = url_for('agency_v0_4_0_vehicles_event', device_id=device_id)
    # With no auth at all
    kwargs = get_request(data)
    del kwargs['headers']['Authorization']
    response = client.post(
        url,
        **kwargs,
    )
    assert response.status == '401 UNAUTHORIZED'
    assert b'Please provide an Authorization' in response.data

    # With Basic token
    kwargs = get_request(data)
    kwargs['headers']['Authorization'] = 'Basic dXNlcm5hbWU6cGFzc3dvcmQ='
    response = client.post(
        url,
        **kwargs,
    )
    assert response.status == '401 UNAUTHORIZED'
    assert b'Please provide a Bearer token' in response.data

    # Provider_id is missing
    kwargs = get_request(data)
    token = jwt.encode({'key': 'value'}, 'secret').decode('utf8')
    kwargs['headers']['Authorization'] = 'Bearer %s' % token
    response = client.post(
        url,
        **kwargs,
    )
    assert response.status == '401 UNAUTHORIZED'
    assert b'Please provide a provider_id' in response.data

    # Invalid JWT
    kwargs = get_request(data)
    kwargs['headers']['Authorization'] = 'Bearer bad_jwt'
    response = client.post(
        url,
        **kwargs,
    )
    assert response.status == '401 UNAUTHORIZED'
    assert b'Please provide a valid JWT' in response.data


def test_trip_id(client):
    """should only be present for trip events"""

    # trip_ip should be present
    event = {'event_type': 'trip_start'}
    data = generate_payload(event)
    device_id = data['telemetry']['device_id']
    url = url_for('agency_v0_4_0_vehicles_event', device_id=device_id)
    kwargs = get_request(data)
    response = client.post(
        url,
        **kwargs,
    )
    assert response.status == '400 BAD REQUEST'
    expected = html.escape(json.dumps({'missing_param': ['trip_id']}))
    assert expected.encode() in response.data

    # trip_ip should not be present
    event = {'event_type': 'register', 'trip_id': str(uuid.uuid4())}
    data = generate_payload(event)
    device_id = data['telemetry']['device_id']
    url = url_for('agency_v0_4_0_vehicles_event', device_id=device_id)
    kwargs = get_request(data)
    response = client.post(
        url,
        **kwargs,
    )
    assert response.status == '400 BAD REQUEST'
    expected = html.escape(json.dumps({'bad_param': ['trip_id']}))
    assert expected.encode() in response.data


def test_event_type_reason(client):
    """required and allowed vaules depends on event_type"""

    # event_type_reason shouldn't be present
    event = {'event_type': 'register', 'event_type_reason': 'compliance'}
    data = generate_payload(event)
    device_id = data['telemetry']['device_id']
    url = url_for('agency_v0_4_0_vehicles_event', device_id=device_id)
    kwargs = get_request(data)
    response = client.post(
        url,
        **kwargs,
    )
    assert response.status == '400 BAD REQUEST'
    expected = html.escape(json.dumps({'bad_param': ['event_type_reason']}))
    assert expected.encode() in response.data

    # event_type_reason has a wrong value
    event = {'event_type': 'deregister', 'event_type_reason': 'compliance'}
    data = generate_payload(event)
    device_id = data['telemetry']['device_id']
    url = url_for('agency_v0_4_0_vehicles_event', device_id=device_id)
    kwargs = get_request(data)
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
    data = generate_payload(event)
    device_id = data['telemetry']['device_id']
    url = url_for('agency_v0_4_0_vehicles_event', device_id=device_id)
    kwargs = get_request(data)
    response = client.post(
        url,
        **kwargs,
    )
    assert response.status == '400 BAD REQUEST'
    expected = html.escape(json.dumps({'missing_param': ['event_type_reason']}))
    assert expected.encode() in response.data


def test_device_id(client):
    event = {'event_type': 'register'}
    data = generate_payload(event)
    url = url_for('agency_v0_4_0_vehicles_event', device_id=str(uuid.uuid4()))
    kwargs = get_request(data)
    response = client.post(
        url,
        **kwargs,
    )
    assert response.status == '400 BAD REQUEST'
    expected = html.escape(json.dumps({'bad_param': ['device_id']}))
    assert expected.encode() in response.data


def test_invalid_telemetry(client):
    event = {'event_type': 'register'}
    data = generate_payload(event)
    del data['telemetry']['gps']['lat']
    device_id = data['telemetry']['device_id']
    url = url_for('agency_v0_4_0_vehicles_event', device_id=device_id)
    kwargs = get_request(data)
    response = client.post(
        url,
        **kwargs,
    )
    assert response.status == '400 BAD REQUEST'
    expected = html.escape(json.dumps({'missing_param': ['telemetry.gps.lat']}))
    assert expected.encode() in response.data


def test_missing_required(client):
    event = {'event_type': 'register'}
    data = generate_payload(event)
    del data['timestamp']
    device_id = data['telemetry']['device_id']
    url = url_for('agency_v0_4_0_vehicles_event', device_id=device_id)
    kwargs = get_request(data)
    response = client.post(
        url,
        **kwargs,
    )
    assert response.status == '400 BAD REQUEST'
    expected = html.escape(json.dumps({'missing_param': ['timestamp']}))
    assert expected.encode() in response.data


def test_wrong_type(client):
    event = {'event_type': 'register'}
    data = generate_payload(event)
    device_id = data['telemetry']['device_id']
    url = url_for('agency_v0_4_0_vehicles_event', device_id=device_id)
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
    event = {'event_type': 'register'}
    data = generate_payload(event)
    device_id = data['telemetry']['device_id']
    url = url_for('agency_v0_4_0_vehicles_event', device_id=device_id)
    data['unknown_field'] = 'nope'
    kwargs = get_request(data)
    response = client.post(
        url,
        **kwargs,
    )
    assert response.status == '400 BAD REQUEST'
    expected = html.escape(json.dumps({'bad_param': ['unknown_field']}))
    assert expected.encode() in response.data
