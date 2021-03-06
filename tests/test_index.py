from flask import url_for


def test_index(client):
    response = client.get(url_for('index'))
    expected = b"""/
/v0.4.0/vehicles
/v0.4.0/vehicles/<device_id>
/v0.4.0/vehicles/<device_id>/event
/v0.4.0/vehicles/telemetry"""
    assert expected == response.data
