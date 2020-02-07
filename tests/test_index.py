from flask import url_for


def test_index(client, app_context):
    response = client.get(url_for('index'))
    expected = b"""/
/v0.4.0/vehicles
/v0.4.0/vehicles/<device_id>/event"""
    assert expected == response.data
