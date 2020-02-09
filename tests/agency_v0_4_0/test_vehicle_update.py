from base64 import b64encode
import json
import html
import uuid
import random

from flask import url_for

from tests import utils


def generate_payload():
    return {
        # required
        'vehicle_id': utils.random_string(255),
    }


def get_valid_request(**kwargs):
    # TODO: this is a basic token, not a bearer token
    auth = kwargs.pop('auth', b64encode(b'username:password').decode('utf8'))
    request = {
        'data': generate_payload(),
        'content_type': 'application/json',
        'headers': {
            'Authorization': 'Bearer %s' % auth
        }
    }
    request.update(kwargs)
    request['data'] = json.dumps(request['data'])
    return request


def test_valid_post(client):
    url = url_for('agency_v0_4_0_vehicle_update', device_id= str(uuid.uuid4()))
    response = client.post(
        url,
        **get_valid_request(),
    )
    assert response.status == '201 CREATED'
    assert response.data == b''


def test_incorrect_content_type(client):
    # This is not handle by MDS 0.4.0, so it works with a bad Content-Type
    url = url_for('agency_v0_4_0_vehicle_update', device_id= str(uuid.uuid4()))
    kwargs = get_valid_request()
    kwargs['content_type'] = 'test/html'
    response = client.post(
        url,
        **kwargs,
    )
    assert response.status == '201 CREATED'
    assert response.data == b''


def test_incorrect_authorization(client):
    # With no auth at all
    url = url_for('agency_v0_4_0_vehicle_update', device_id= str(uuid.uuid4()))
    kwargs = get_valid_request()
    del kwargs['headers']['Authorization']
    response = client.post(
        url,
        **kwargs,
    )
    assert response.status == '401 UNAUTHORIZED'
    assert b'No auth provided' in response.data

    # With Basic token
    kwargs = get_valid_request()
    token = b64encode(b'username:password').decode('utf8')
    kwargs['headers']['Authorization'] = 'Basic %s' % token
    response = client.post(
        url,
        **kwargs,
    )
    assert response.status == '401 UNAUTHORIZED'
    assert b'Bearer token required' in response.data


def test_missing_required(client):
    url = url_for('agency_v0_4_0_vehicle_update', device_id= str(uuid.uuid4()))
    data = {}
    kwargs = get_valid_request(data=data)
    response = client.post(
        url,
        **kwargs,
    )
    assert response.status == '400 BAD REQUEST'
    expected = html.escape(json.dumps({'missing_param': ['vehicle_id']}))
    assert expected.encode() in response.data


def test_wrong_type(client):
    url = url_for('agency_v0_4_0_vehicle_update', device_id= str(uuid.uuid4()))
    data = {'vehicle_id': 346}
    kwargs = get_valid_request(data=data)
    response = client.post(
        url,
        **kwargs,
    )
    assert response.status == '400 BAD REQUEST'
    expected = html.escape(json.dumps({'bad_param': ['vehicle_id']}))
    assert expected.encode() in response.data


def test_unknown_field(client):
    url = url_for('agency_v0_4_0_vehicle_update', device_id= str(uuid.uuid4()))
    data = generate_payload()
    data['unknown_field'] = 'nope'
    kwargs = get_valid_request(data=data)
    response = client.post(
        url,
        **kwargs,
    )
    assert response.status == '400 BAD REQUEST'
    expected = html.escape(json.dumps({'bad_param': ['unknown_field']}))
    assert expected.encode() in response.data
