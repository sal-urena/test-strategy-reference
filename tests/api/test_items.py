async def test_authenticated_user_can_create_item(client,make_user):
    item_name = "apple"
    item_description = "red fruit"
    json_body={
        "name": item_name,
        "description": item_description
        }
    user = await make_user("alice", "password")
    response = await client.post("/items", headers=user.headers, json=json_body)
    assert response.status_code == 200
    response_body = response.json()
    assert response_body["name"] == item_name
    assert response_body["description"] ==item_description

async def test_user_who_is_not_owner_get_item_404(client,make_user):
    user1 = await make_user("user1", "password")
    user2 = await make_user("user2", "password2")
    item_json_body={
        "name": "item_name",
        "description": "item_description"
        }
    response = await client.post(url="/items", headers=user1.headers, json=item_json_body)
    assert response.status_code==200
    response_body = response.json()
    item_id = response_body["id"]
    response_user1 = await client.get(url=f"/items/{item_id}",headers=user1.headers)
    assert response_user1.status_code ==200
    user2_response = await client.get(url=f"/items/{item_id}",headers=user2.headers)
    assert user2_response.status_code == 404
    user2_response_body = user2_response.json()
    assert user2_response_body["detail"]=="Item not found"

async def test_item_assigned_to_correct_user_when_id_is_forged(client,make_user):
    user1 = await make_user("bill", "pass1")
    user2 = await make_user("bob","pass2")
    forged_owner_id = user2.id
    assert user1.id != forged_owner_id
    item_json_body={
        "name": "item_name",
        "description": "item_description",
        "owner_id":forged_owner_id
    }
    make_item = await client.post("/items", headers=user1.headers, json=item_json_body)
    assert make_item.status_code ==200
    make_item_json = make_item.json()
    assert make_item_json["owner_id"] ==user1.id