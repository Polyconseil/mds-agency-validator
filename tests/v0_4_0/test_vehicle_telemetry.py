import json
import uuid

from flask import url_for

from tests.utils import get_request, register_device

from .utils import generate_telemetry


def generate_payload(telemetries):
    return {'data': telemetries}


def test_valid_post(client):
    register_device()

    url = url_for('v0_4_0.vehicle_telemetry')
    telemetries = [generate_telemetry() for _ in range(2)]
    kwargs = get_request(generate_payload(telemetries))
    response = client.post(
        url,
        **kwargs,
    )
    assert response.status == '201 CREATED'
    assert response.data == b'{"result": 2, "failures": []}'


def test_partially_invalid(client):
    """One telemetry is ok, the other is invalid"""
    register_device()

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


def test_all_invalid(client):
    register_device()

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


def test_unregistered_device(client):
    register_device()

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
