def test_index(client):
    response = client.get("/")
    expected = b"""/
/v0.4"""
    assert expected == response.data
