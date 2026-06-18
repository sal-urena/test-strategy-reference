async def test_user_registration_is_successful(client):
    username = "test_user"
    json_body ={
        "username": username,
        "password": "pass1234"
        }
    response = await client.post(url="/register", json=json_body)
    assert response.status_code == 200
    response_body = response.json()
    assert response_body["id"] is not None
    assert response_body["username"] == username
    assert "hashed_password" not in response_body

async def test_login_successful_with_valid_credentials(client):
    username = "test_user"
    json_body ={
        "username": username,
        "password": "pass1234"
        }

    await client.post(url="/register", json=json_body)
    response = await client.post(url="/login", json=json_body)
    assert response.status_code == 200
    reponse_body = response.json()
    assert reponse_body["token_type"] == "bearer"
    assert reponse_body["access_token"]