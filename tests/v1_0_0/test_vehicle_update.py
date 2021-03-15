import html
import json

from flask import url_for

from tests import utils
from tests.utils import REGISTERED_DEVICE_ID, get_request, register_device


def generate_payload():
    return {
        # required
        'vehicle_id': utils.random_string(255),
    }


def test_valid_post(client):
    register_device()
    url = url_for('v1_0_0.vehicle_update', device_id=REGISTERED_DEVICE_ID)
    response = client.post(
        url,
        **get_request(generate_payload()),
    )
    assert response.status == '201 CREATED'
    assert response.data == b''


def test_missing_required(client):
    register_device()
    url = url_for('v1_0_0.vehicle_update', device_id=REGISTERED_DEVICE_ID)
    data = {}
    kwargs = get_request(data)
    response = client.post(
        url,
        **kwargs,
    )
    assert response.status == '400 BAD REQUEST'
    expected = html.escape(json.dumps({'missing_param': ['vehicle_id']}))
    assert expected.encode() in response.data


def test_wrong_type(client):
    register_device()
    url = url_for('v1_0_0.vehicle_update', device_id=REGISTERED_DEVICE_ID)
    data = {'vehicle_id': 346}
    kwargs = get_request(data)
    response = client.post(
        url,
        **kwargs,
    )
    assert response.status == '400 BAD REQUEST'
    expected = html.escape(json.dumps({'bad_param': ['vehicle_id']}))
    assert expected.encode() in response.data


def test_unknown_field(client):
    register_device()
    url = url_for('v1_0_0.vehicle_update', device_id=REGISTERED_DEVICE_ID)
    data = generate_payload()
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
    url = url_for('v1_0_0.vehicle_update', device_id=REGISTERED_DEVICE_ID)
    kwargs = get_request(generate_payload())
    response = client.post(
        url,
        **kwargs,
    )
    assert response.status == '404 NOT FOUND'
