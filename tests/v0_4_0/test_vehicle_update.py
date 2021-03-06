import json
import jwt
import html

from flask import url_for

from tests import utils
from .conftest import REGISTRED_DEVICE_ID
from .utils import get_request


def generate_payload():
    return {
        # required
        'vehicle_id': utils.random_string(255),
    }


def test_valid_post(client, register_device):
    url = url_for('v0_4_0.vehicle_update', device_id=REGISTRED_DEVICE_ID)
    response = client.post(
        url,
        **get_request(generate_payload()),
    )
    assert response.status == '201 CREATED'
    assert response.data == b''


def test_incorrect_content_type(client, register_device):
    # This is not handle by MDS 0.4.0, so it works with a bad Content-Type
    url = url_for('v0_4_0.vehicle_update', device_id=REGISTRED_DEVICE_ID)
    data = generate_payload()
    kwargs = get_request(data)
    kwargs['content_type'] = 'test/html'
    response = client.post(
        url,
        **kwargs,
    )
    assert response.status == '201 CREATED'
    assert response.data == b''


def test_incorrect_authorization(client, register_device):
    url = url_for('v0_4_0.vehicle_update', device_id=REGISTRED_DEVICE_ID)
    # With no auth at all
    kwargs = get_request(generate_payload())
    del kwargs['headers']['Authorization']
    response = client.post(
        url,
        **kwargs,
    )
    assert response.status == '401 UNAUTHORIZED'
    assert b'Please provide an Authorization' in response.data

    # With Basic token
    kwargs = get_request(generate_payload())
    kwargs['headers']['Authorization'] = 'Basic dXNlcm5hbWU6cGFzc3dvcmQ='
    response = client.post(
        url,
        **kwargs,
    )
    assert response.status == '401 UNAUTHORIZED'
    assert b'Please provide a Bearer token' in response.data

    # Provider_id is missing
    kwargs = get_request(generate_payload())
    token = jwt.encode({'key': 'value'}, 'secret').decode('utf8')
    kwargs['headers']['Authorization'] = 'Bearer %s' % token
    response = client.post(
        url,
        **kwargs,
    )
    assert response.status == '401 UNAUTHORIZED'
    assert b'Please provide a provider_id' in response.data

    # Invalid JWT
    kwargs = get_request(generate_payload())
    kwargs['headers']['Authorization'] = 'Bearer bad_jwt'
    response = client.post(
        url,
        **kwargs,
    )
    assert response.status == '401 UNAUTHORIZED'
    assert b'Please provide a valid JWT' in response.data


def test_missing_required(client, register_device):
    url = url_for('v0_4_0.vehicle_update', device_id=REGISTRED_DEVICE_ID)
    data = {}
    kwargs = get_request(data)
    response = client.post(
        url,
        **kwargs,
    )
    assert response.status == '400 BAD REQUEST'
    expected = html.escape(json.dumps({'missing_param': ['vehicle_id']}))
    assert expected.encode() in response.data


def test_wrong_type(client, register_device):
    url = url_for('v0_4_0.vehicle_update', device_id=REGISTRED_DEVICE_ID)
    data = {'vehicle_id': 346}
    kwargs = get_request(data)
    response = client.post(
        url,
        **kwargs,
    )
    assert response.status == '400 BAD REQUEST'
    expected = html.escape(json.dumps({'bad_param': ['vehicle_id']}))
    assert expected.encode() in response.data


def test_unknown_field(client, register_device):
    url = url_for('v0_4_0.vehicle_update', device_id=REGISTRED_DEVICE_ID)
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
    url = url_for('v0_4_0.vehicle_update', device_id=REGISTRED_DEVICE_ID)
    kwargs = get_request(generate_payload())
    response = client.post(
        url,
        **kwargs,
    )
    assert response.status == '404 NOT FOUND'
