from sqlalchemy import select
from app.models import Users

def test_register_user_to_db(client, db_session):
    user_data = {
        "first_name": "John",
        "last_name": "Doe",
        "username": "johndoe",
        "email": "johndoe@example.com",
        "password": "password123"
    }
    response = client.post("/users/register", json=user_data)
    assert response.status_code == 201
    saved_user = db_session.scalars(select(Users).where(Users.username == user_data["username"])).first()
    assert saved_user is not None
    assert saved_user.email == user_data["email"]
    assert saved_user.password_hash != user_data["password"]  # Ensure password is hashed
    assert saved_user.verify_password(user_data["password"])  # Ensure password verification works

def test_login_user(client, db_session):
    user_data = {
        "username": "johndoe",
        "password": "password123"
    }
    user = Users(
    username=user_data["username"],
    email="johndoe@example.com",
    password_hash=Users.hash_password(user_data["password"]),
)
    db_session.add(user)
    db_session.commit()
    response = client.post("/users/login", json=user_data)
    assert response.status_code == 200, response.text
    logged_in_user = db_session.scalars(select(Users).where(Users.username == user_data["username"])).first()
    assert logged_in_user is not None
    assert logged_in_user.verify_password(user_data["password"])  # Ensure password verification works
    wrong_credentials = {**user_data, "password": "password124"}
    response = client.post("/users/login", json=wrong_credentials)
    assert response.status_code == 401, response.text
    
def test_register_user_with_existing_username(client, db_session):
    user_data = {
        "first_name": "Jane",
        "last_name": "Doe",
        "username": "johndoe",  # Existing username
        "email": "janedoe@example.com",
        "password": "password456"
    }
    first_response = client.post("/users/register", json=user_data)
    assert first_response.status_code == 201, first_response.text

    duplicate_data = {**user_data, "email": "other@example.com"}
    response = client.post("/users/register", json=duplicate_data)
    assert response.status_code == 409, response.text

def test_register_user_with_existing_email(client, db_session):
    user_data = {
        "first_name": "Alice",
        "last_name": "Smith",
        "username": "alicesmith",
        "email": "alice@example.com",
        "password": "password789",
    }
    first_response = client.post("/users/register", json=user_data)
    assert first_response.status_code == 201, first_response.text

    duplicate_data = {**user_data, "username": "anotheralice"}
    response = client.post("/users/register", json=duplicate_data)
    assert response.status_code == 409, response.text