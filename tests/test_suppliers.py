def test_list_suppliers(client):
    # Log in the test client
    response = client.post('/auth/login', data={
        'username': 'testuser',
        'password': 'password'
    }, follow_redirects=True)
    assert response.status_code == 200

    # Now, make the request to the protected route
    response = client.get('/suppliers/')
    assert response.status_code == 200