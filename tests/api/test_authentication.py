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
    response_body = response.json()
    assert response_body["token_type"] == "bearer"
    assert response_body["access_token"]

async def test_invalid_login_credentials_401(client):
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

async def test_indistinguishable_messaging_for_invalid_username_or_password(client):
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
    json_body_wrong_username ={
        "username": username+"1",
        "password": "pass1234"
        }
    response2 = await client.post(url="/login", json=json_body_wrong_username)
    assert response.json() ==response2.json()
    assert response.status_code == response2.status_code

async def test_401_when_header_is_invalid_token(client):
    get_item = await client.get("/items/1", headers={"Authorization":"Bearer bad_token"})
    assert get_item.status_code == 401
    get_item_json = get_item.json()
    assert get_item_json["detail"] == "Invalid or expired token"

async def test_401_when_header_is_missing(client):
    get_item = await client.get("/items/1")
    assert get_item.status_code == 401
    get_item_json = get_item.json()
    assert get_item_json["detail"] == "Not authenticated"