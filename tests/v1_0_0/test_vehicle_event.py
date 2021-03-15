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
        {'vehicle_state': 'available', 'event_types': ['maintenance']},
        {'vehicle_state': 'unknown', 'event_types': ['missing']},
        {'vehicle_state': 'on_trip', 'event_types': ['trip_start'], 'trip_id': str(uuid.uuid4())},
    ],
)
def test_valid_post(client, event_args):
    register_device()
    url = url_for('v1_0_0.vehicle_event', device_id=REGISTERED_DEVICE_ID)
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
    url = url_for('v1_0_0.vehicle_event', device_id=REGISTERED_DEVICE_ID)
    event = {'vehicle_state': 'on_trip', 'event_types': ['trip_start']}
    kwargs = get_request(generate_payload(event))
    response = client.post(
        url,
        **kwargs,
    )
    assert response.status == '400 BAD REQUEST'
    expected = html.escape(json.dumps({'missing_param': ['trip_id']}))
    assert expected.encode() in response.data

    # trip_ip should not be present
    event = {'vehicle_state': 'available', 'event_types': ['unspecified'], 'trip_id': str(uuid.uuid4())}
    kwargs = get_request(generate_payload(event))
    response = client.post(
        url,
        **kwargs,
    )
    assert response.status == '400 BAD REQUEST'
    expected = html.escape(json.dumps({'bad_param': ['trip_id']}))
    assert expected.encode() in response.data


@pytest.mark.parametrize(
    'vehicle_state,event_type',
    [
        ('available', 'battery_charged'),
        ('available', 'on_hours'),
        ('available', 'provider_drop_off'),
        ('available', 'agency_drop_off'),
        ('available', 'maintenance'),
        ('available', 'trip_end'),
        ('available', 'reservation_cancel'),
        ('available', 'trip_cancel'),
        ('available', 'system_resume'),
        ('available', 'comms_restored'),
        ('available', 'located'),
        ('available', 'unspecified'),
        ('reserved', 'reservation_start'),
        ('reserved', 'comms_restored'),
        ('reserved', 'located'),
        ('reserved', 'unspecified'),
        ('on_trip', 'trip_start'),
        ('on_trip', 'trip_enter_jurisdiction'),
        ('on_trip', 'comms_restored'),
        ('on_trip', 'located'),
        ('on_trip', 'unspecified'),
        ('elsewhere', 'trip_leave_jurisdiction'),
        ('elsewhere', 'comms_restored'),
        ('elsewhere', 'located'),
        ('elsewhere', 'unspecified'),
        ('non_operational', 'battery_low'),
        ('non_operational', 'maintenance'),
        ('non_operational', 'off_hours'),
        ('non_operational', 'system_suspend'),
        ('non_operational', 'unspecified'),
        ('non_operational', 'comms_restored'),
        ('non_operational', 'located'),
        ('removed', 'rebalance_pick_up'),
        ('removed', 'maintenance_pick_up'),
        ('removed', 'agency_pick_up'),
        ('removed', 'compliance_pick_up'),
        ('removed', 'decommissioned'),
        ('removed', 'unspecified'),
        ('removed', 'comms_restored'),
        ('removed', 'located'),
        ('unknown', 'missing'),
        ('unknown', 'comms_lost'),
        ('unknown', 'unspecified'),
    ],
)
def test_workflow(client, vehicle_state, event_type):
    register_device()

    # event_type_reason shouldn't be present
    url = url_for('v1_0_0.vehicle_event', device_id=REGISTERED_DEVICE_ID)
    event = {'vehicle_state': vehicle_state, 'event_types': [event_type]}
    if 'trip' in event_type:
        event['trip_id'] = str(uuid.uuid4())
    kwargs = get_request(generate_payload(event))
    response = client.post(
        url,
        **kwargs,
    )
    assert response.status == '201 CREATED'


def test_device_id(client):
    register_device()
    url = url_for('v1_0_0.vehicle_event', device_id=REGISTERED_DEVICE_ID)
    event = {'vehicle_state': 'available', 'event_types': ['located']}
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
    url = url_for('v1_0_0.vehicle_event', device_id=REGISTERED_DEVICE_ID)
    register_device()
    event = {'vehicle_state': 'available', 'event_types': ['located']}
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

    url = url_for('v1_0_0.vehicle_event', device_id=REGISTERED_DEVICE_ID)
    event = {'vehicle_state': 'available', 'event_types': ['located']}
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

    url = url_for('v1_0_0.vehicle_event', device_id=REGISTERED_DEVICE_ID)
    event = {'vehicle_state': 'available', 'event_types': ['located']}
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

    url = url_for('v1_0_0.vehicle_event', device_id=REGISTERED_DEVICE_ID)
    event = {'vehicle_state': 'available', 'event_types': ['located']}
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
    url = url_for('v1_0_0.vehicle_event', device_id=REGISTERED_DEVICE_ID)
    event = {'vehicle_state': 'available', 'event_types': ['located']}
    kwargs = get_request(generate_payload(event))
    response = client.post(
        url,
        **kwargs,
    )
    assert response.status == '404 NOT FOUND'
