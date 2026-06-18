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

async def test_invalid_password__and_bad_username_returns_401(client):
    username = "test_user"
    json_body ={
        "username": username,
        "password": "pass1234"
        }
    json_body_wrong_password ={
        "username": username,
        "password": "wrongpassword"
        }
    await client.post(url="/register", json=json_body)
    response = await client.post(url="/login", json=json_body_wrong_password)
    assert response.status_code ==401
    response_body = response.json()
    assert response_body["detail"]=="Invalid username or password"
    json_body_wrong_username ={
        "username": username+"1",
        "password": "pass1234"
        }
    response2 = await client.post(url="/login", json=json_body_wrong_username)
    assert response2.status_code ==401
    response_body2 = response2.json()
    assert response_body2["detail"]=="Invalid username or password"
    assert response_body["detail"]==response_body2["detail"]

