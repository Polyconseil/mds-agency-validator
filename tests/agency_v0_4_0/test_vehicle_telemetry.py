import json

from flask import url_for

from .utils import generate_telemetry
from .utils import get_request


def generate_payload(telemetries):
    return {'data': telemetries}


def test_valid_post(client):
    url = url_for('agency_v0_4_0_vehicles_telemetry')
    telemetries = [generate_telemetry() for _ in range(2)]
    data = generate_payload(telemetries)
    kwargs = get_request(data)
    response = client.post(
        url,
        **kwargs,
    )
    assert response.status == '201 CREATED'
    assert response.data == b'{"result": 2, "failures": []}'


def test_incorrect_content_type(client):
    # This is not handle by MDS 0.4.0, so it works with a bad Content-Type
    url = url_for('agency_v0_4_0_vehicles_telemetry')
    telemetries = [generate_telemetry() for _ in range(2)]
    data = generate_payload(telemetries)
    kwargs = get_request(data)
    kwargs['content_type'] = 'test/html'
    response = client.post(
        url,
        **kwargs,
    )
    assert response.status == '201 CREATED'
    assert response.data == b'{"result": 2, "failures": []}'


def test_incorrect_authorization(client):
    url = url_for('agency_v0_4_0_vehicles_telemetry')
    telemetries = [generate_telemetry() for _ in range(2)]
    data = generate_payload(telemetries)
    kwargs = get_request(data)
    del kwargs['headers']['Authorization']
    response = client.post(
        url,
        **kwargs,
    )
    assert response.status == '401 UNAUTHORIZED'
    assert b'No auth provided' in response.data


def test_partially_invalid(client):
    """One telemetry is ok, the other is invalid"""

    good_telemetry = generate_telemetry()
    bad_telemetry = generate_telemetry()
    del bad_telemetry['device_id']
    url = url_for('agency_v0_4_0_vehicles_telemetry')
    telemetries = [good_telemetry, bad_telemetry]
    data = generate_payload(telemetries)
    kwargs = get_request(data)
    response = client.post(
        url,
        **kwargs,
    )
    assert response.status == '201 CREATED'
    response_data = json.loads(response.data)
    assert response_data['result'] == 1
    assert response_data['failures'] == [bad_telemetry]


def test_all_invalid(client):
    """All telemetries are invalid"""

    bad_telemetry = generate_telemetry()
    del bad_telemetry['device_id']
    url = url_for('agency_v0_4_0_vehicles_telemetry')
    telemetries = [bad_telemetry, bad_telemetry]
    data = generate_payload(telemetries)
    kwargs = get_request(data)
    response = client.post(
        url,
        **kwargs,
    )
    assert response.status == '400 BAD REQUEST'
    # TODO what is expected format ?
