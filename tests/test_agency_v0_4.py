def test_content_type(client):
    response = client.post(
        "/v0.4",
        data='{}',
        content_type='application/json',
    )
    assert response.data == b'OK'

    response = client.post(
        "/v0.4",
        data='{}',
        content_type='text/html',
    )
    assert response.data != b'OK'
