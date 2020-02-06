from base64 import b64encode
import json
import uuid
import random

from flask import url_for

from . import utils


# TODO use enums ?
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


def generate_valid_payload():
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


def get_valid_request(**kwargs):
    auth = kwargs.pop('auth', b64encode(b'username:password').decode('utf8'))
    request = {
        'data': generate_valid_payload(),
        'content_type': 'application/json',
        'headers': {
            'Authorization': 'Basic %s' % auth
        }
    }
    request.update(kwargs)
    request['data'] = json.dumps(request['data'])
    return request


def test_valid_post(client, app_context):
    url = url_for('agency_v0_4_vehicles')
    response = client.post(
        url,
        **get_valid_request(),
    )
    assert response.status == '200 OK'
    assert response.data == b'OK'


def test_incorrect_content_type(client, app_context):
    url = url_for('agency_v0_4_vehicles')
    kwargs = get_valid_request()
    kwargs['content_type'] = 'test/html'
    response = client.post(
        url,
        **kwargs,
    )
    assert response.status == '500 INTERNAL SERVER ERROR'
    assert b'Request content type should be application/json' in response.data


def test_incorrect_authorization(client, app_context):
    url = url_for('agency_v0_4_vehicles')
    kwargs = get_valid_request()
    del kwargs['headers']['Authorization']
    response = client.post(
        url,
        **kwargs,
    )
    assert response.status == '401 UNAUTHORIZED'
    assert b'No auth provided' in response.data


def test_wrong_json_payload_missing_required(client, app_context):
    url = url_for('agency_v0_4_vehicles')
    data = generate_valid_payload()
    del data['device_id']
    kwargs = get_valid_request(data=data)
    response = client.post(
        url,
        **kwargs,
    )
    assert response.status == '500 INTERNAL SERVER ERROR'
    assert b"JsonValidationError : 'device_id' is a required property" in response.data


def test_wrong_json_payload_wrong_type(client, app_context):
    url = url_for('agency_v0_4_vehicles')
    data = generate_valid_payload()
    data['vehicle_id'] = 346
    kwargs = get_valid_request(data=data)
    response = client.post(
        url,
        **kwargs,
    )
    assert response.status == '500 INTERNAL SERVER ERROR'
    assert b"JsonValidationError : 346 is not of type 'string'" in response.data
