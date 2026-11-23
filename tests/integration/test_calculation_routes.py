from http import client

from sqlalchemy import select
from app.schemas.calculatorSchema import CalculationCreate, CalculationRead, CalculationAdd
from app.models import Calculator, Users

def test_list_calculations(client, db_session):
    # Create a user and calculations for testing
    user = Users(username="testuser", email="testuser@example.com", password_hash=Users.hash_password("password"))
    db_session.add(user)
    db_session.commit()
    calculation1 = Calculator(user_id=user.id, a=5, b=3, type
                               ="add", result=8)
    calculation2 = Calculator(user_id=user.id, a=10, b=2, type="divide", result=5)
    db_session.add_all([calculation1, calculation2])
    db_session.commit()
    response = client.get("/calculations")
    assert response.status_code == 200, response.text
    calculations_by_id = {item["id"]: item for item in response.json()}
    assert calculation1.id in calculations_by_id
    assert calculation2.id in calculations_by_id
    assert calculations_by_id[calculation1.id]["result"] == 8.0
    assert calculations_by_id[calculation2.id]["result"] == 5.0

def test_get_calculation(client, db_session):
    # Create a user and a calculation for testing
    user = Users(username="testuser2", email="testuser2@example.com", password_hash=Users.hash_password("password"))
    db_session.add(user)
    db_session.commit()
    calculation = Calculator(user_id=user.id, a=5, b=3, type="add", result=8)
    db_session.add(calculation)
    db_session.commit()
    response = client.get(f"/calculations/{calculation.id}")
    assert response.status_code == 200, response.text
    assert response.json()["result"] == 8.0

def test_refuse_nonexistent_calculation(client):
    response = client.get("/calculations/9999")  # Assuming 9999 does not exist
    assert response.status_code == 404
    assert response.json()["error"] == "This calculation does not exist"

def test_create_calculation(client, db_session):
    # Create a user for testing
    user = Users(username="testuser3", email="testuser3@example.com", password_hash=Users.hash_password("password"))
    db_session.add(user)
    db_session.commit()
    calculation_data = {
        "user_id": user.id,
        "a": 10,
        "b": 5,
        "type": "divide",
    }
    response = client.post("/calculations", json=calculation_data)
    assert response.status_code == 201, response.text
    assert response.json()["result"] == 2.0

def test_divide_by_zero(client, db_session):
        # Create a user for testing
    user = Users(username="testuser4", email="testuser4@example.com", password_hash=Users.hash_password("password"))
    db_session.add(user)
    db_session.commit()
    calculation_data = {
        "user_id": user.id,
        "a": 10,
        "b": 0,
        "type": "divide",
        "result": 0,
    }
    response = client.post("/calculations", json=calculation_data)
    assert response.status_code == 400, response.text  # Unprocessable Entity due to validation error
    assert "Cannot divide by zero" in response.json()["error"], response.text
def test_update_calculation(client, db_session):
    # Create a user and a calculation for testing
    user = Users(username="testuser5", email="testuser5@example.com", password_hash=Users.hash_password("password"))
    db_session.add(user)
    db_session.commit()
    calculation = Calculator(user_id=user.id, a=5, b=3, type="add", result=8)
    db_session.add(calculation)
    db_session.commit()
    url = f"/calculations/{calculation.id}"
    update_data = {"a": 10, "b": 2, "type": "divide"}

    url = f"/calculations/{calculation.id}"
    response = client.put(url, json=update_data)
    assert response.status_code == 200, response.text
    assert response.json()["result"] == 5.0

    response = client.get(url)
    assert response.status_code == 200, response.text
    saved = response.json()
    assert saved["a"] == 10.0
    assert saved["b"] == 2.0
    assert saved["type"] == "divide"    
    assert saved["result"] == 5.0
    

def test_refuse_update_nonexistent_calculation(client):
    update_data = {
        "a": 10,
        "b": 2,
        "type": "divide",
        "result": 5,
    }
    response = client.put("/calculations/9999", json=update_data)  # Assuming 9999 does not exist
    assert response.status_code == 404
    assert response.json()["error"] == "This calculation does not exist"

def test_delete_calculation(client, db_session):
    # Create a user and a calculation for testing
    user = Users(username="testuser6", email="testuser6@example.com", password_hash=Users.hash_password("password"))
    db_session.add(user)
    db_session.commit()
    calculation = Calculator(user_id=user.id, a=5, b=3, type="add", result=8)
    db_session.add(calculation)
    db_session.commit()
    calculation_id = calculation.id
    response = client.delete(f"/calculations/{calculation_id}")
    assert response.status_code == 204, response.text
    assert response.content == b""
    response = client.get(f"/calculations/{calculation_id}")
    assert response.status_code == 404, response.text

def test_refuse_delete_nonexistent_calculation(client):
    response = client.delete("/calculations/9999")  # Assuming 9999 does not exist
    assert response.status_code == 404
    print(response.json())
    assert response.json()["error"] == "This calculation does not exist"
