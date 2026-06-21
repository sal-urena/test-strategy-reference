#Post /items validations
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

# Get /items validations

async def test_user_get_list_of_only_their_items(client,make_user):
    user1 = await make_user("test1", "password1")
    user2 = await make_user("test2", "password2")
    item_json_body1={
        "name": "apple",
        "description": "red fruit",
    }
    item_json_body2={
        "name": "banana",
        "description": "yellow fruit",
    }
    create_item1 = await client.post("/items", headers=user1.headers, json=item_json_body1)
    assert create_item1.status_code == 200
    create_item1_json = create_item1.json()
    user1_item_id = create_item1_json["id"]
    create_item2 = await client.post("/items", headers=user2.headers, json=item_json_body2)
    assert create_item2.status_code == 200
    create_item2_json = create_item2.json()
    user2_item_id = create_item2_json["id"]
    get_item_list = await client.get("/items", headers=user1.headers)
    assert get_item_list.status_code ==200
    json = get_item_list.json()
    item_set = {item["id"] for item in json}
    assert item_set =={user1_item_id}
    get_item_list2 = await client.get("/items", headers=user2.headers)
    assert get_item_list2.status_code ==200
    json = get_item_list2.json()
    item_set = {item["id"] for item in json}
    assert item_set =={user2_item_id}
