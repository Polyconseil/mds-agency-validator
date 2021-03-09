import json
import uuid

import jwt
from flask import url_for

from .utils import generate_telemetry, get_request


def generate_payload(telemetries):
    return {'data': telemetries}


def test_valid_post(client, register_device):
    url = url_for('v0_4_0.vehicle_telemetry')
    telemetries = [generate_telemetry() for _ in range(2)]
    kwargs = get_request(generate_payload(telemetries))
    response = client.post(
        url,
        **kwargs,
    )
    assert response.status == '201 CREATED'
    assert response.data == b'{"result": 2, "failures": []}'


def test_incorrect_content_type(client, register_device):
    # This is not handle by MDS 0.4.0, so it works with a bad Content-Type
    url = url_for('v0_4_0.vehicle_telemetry')
    telemetries = [generate_telemetry() for _ in range(2)]
    kwargs = get_request(generate_payload(telemetries))
    kwargs['content_type'] = 'test/html'
    response = client.post(
        url,
        **kwargs,
    )
    assert response.status == '201 CREATED'
    assert response.data == b'{"result": 2, "failures": []}'


def test_incorrect_authorization(client, register_device):
    url = url_for('v0_4_0.vehicle_telemetry')
    telemetries = [generate_telemetry() for _ in range(2)]
    data = generate_payload(telemetries)
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


def test_partially_invalid(client, register_device):
    """One telemetry is ok, the other is invalid"""

    good_telemetry = generate_telemetry()
    bad_telemetry = generate_telemetry()
    del bad_telemetry['device_id']
    url = url_for('v0_4_0.vehicle_telemetry')
    telemetries = [good_telemetry, bad_telemetry]
    kwargs = get_request(generate_payload(telemetries))
    response = client.post(
        url,
        **kwargs,
    )
    assert response.status == '201 CREATED'
    response_data = json.loads(response.data)
    assert response_data['result'] == 1
    assert response_data['failures'] == [bad_telemetry]


def test_all_invalid(client, register_device):
    """All telemetries are invalid"""

    bad_telemetry = generate_telemetry()
    del bad_telemetry['device_id']
    url = url_for('v0_4_0.vehicle_telemetry')
    telemetries = [bad_telemetry, bad_telemetry]
    kwargs = get_request(generate_payload(telemetries))
    response = client.post(
        url,
        **kwargs,
    )
    assert response.status == '400 BAD REQUEST'
    # TODO what is expected format ?


def test_unregistred_device(client, register_device):
    url = url_for('v0_4_0.vehicle_telemetry')
    good_telemetry = generate_telemetry()
    bad_telemetry = generate_telemetry()
    bad_telemetry['device_id'] = str(uuid.uuid4())
    telemetries = [good_telemetry, bad_telemetry]
    kwargs = get_request(generate_payload(telemetries))
    response = client.post(
        url,
        **kwargs,
    )
    assert response.status == '201 CREATED'
    response_data = json.loads(response.data)
    assert response_data['result'] == 1
    assert response_data['failures'] == [bad_telemetry]
