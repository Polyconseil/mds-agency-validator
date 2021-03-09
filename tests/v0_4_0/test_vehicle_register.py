import html
import json
import random
import uuid

import jwt
from flask import url_for

from tests import utils

from .conftest import REGISTRED_DEVICE_ID
from .utils import get_request

PROPULSION_TYPE = [
    'combustion',
    'electric',
    'electric_assist',
    'human',
]


VEHICLE_TYPE = [
    'bicycle',
    'car',
    'scooter',
]


def generate_payload():
    return {
        # required
        'device_id': str(uuid.uuid4()),
        'vehicle_id': utils.random_string(255),
        'type': random.choice(VEHICLE_TYPE),
        'propulsion': [random.choice(PROPULSION_TYPE)],
        # optionnal
        'year': utils.random_year(),
        'mfgr': utils.random_string(255),
        'model': utils.random_string(255),
    }


def test_post(client):
    url = url_for('v0_4_0.vehicle_register')
    response = client.post(url, **get_request(generate_payload()))
    assert response.status == '201 CREATED'
    assert response.data == b''

    # Try with minimal arguments
    data = generate_payload()
    del data['year']
    del data['mfgr']
    del data['model']
    url = url_for('v0_4_0.vehicle_register')
    response = client.post(url, **get_request(data))
    assert response.status == '201 CREATED'
    assert response.data == b''


def test_already_registred(client, register_device):
    data = generate_payload()
    url = url_for('v0_4_0.vehicle_register')
    data['device_id'] = REGISTRED_DEVICE_ID
    kwargs = get_request(data)
    response = client.post(
        url,
        **kwargs,
    )
    assert response.status == '409 CONFLICT'
    assert b'' in response.data


def test_incorrect_content_type(client):
    # This is not handle by MDS 0.4.0, so it works with a bad Content-Type
    url = url_for('v0_4_0.vehicle_register')
    kwargs = get_request(generate_payload())
    kwargs['content_type'] = 'test/html'
    response = client.post(
        url,
        **kwargs,
    )
    assert response.status == '201 CREATED'
    assert response.data == b''


def test_incorrect_authorization(client):
    url = url_for('v0_4_0.vehicle_register')
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


def test_missing_required(client):
    url = url_for('v0_4_0.vehicle_register')
    data = generate_payload()
    del data['device_id']
    kwargs = get_request(data)
    response = client.post(
        url,
        **kwargs,
    )
    assert response.status == '400 BAD REQUEST'
    expected = html.escape(json.dumps({'missing_param': ['device_id']}))
    assert expected.encode() in response.data


def test_wrong_type(client):
    url = url_for('v0_4_0.vehicle_register')
    data = generate_payload()
    data['device_id'] = 346
    kwargs = get_request(data)
    response = client.post(
        url,
        **kwargs,
    )
    assert response.status == '400 BAD REQUEST'
    expected = html.escape(json.dumps({'bad_param': ['device_id']}))
    assert expected.encode() in response.data


def test_unknown_field(client):
    url = url_for('v0_4_0.vehicle_register')
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
