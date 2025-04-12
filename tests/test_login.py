import psycopg2
import requests

# Base URL of your Flask application
BASE_URL = "http://35.169.25.122"
LOCAL_URL = "http://127.0.0.1:5000"
DB_CONFIG = {
    'dbname': 'postgres',
    'user': 'foxtrot',
    'password': 'FiveGuys',
    'host': 'foxtrot-db.cialrzbfckl9.us-east-1.rds.amazonaws.com',
    'port': 5432
}

def delete_test_user(username):
    """
    Helper function to delete a test user from the database.
    """
    conn = psycopg2.connect(**DB_CONFIG)
    cur = conn.cursor()
    try:
        cur.execute("DELETE FROM users WHERE username = %s;", (username,))
        conn.commit()
    except Exception as e:
        print(f"Error deleting test user: {e}")
    finally:
        cur.close()
        conn.close()

def test_register_success():
    """
    Test successful user registration.
    """
    # Test data
    payload = {
        "username": "testuser",
        "password": "testpassword"
    }

    # Send POST request to /register
    response = requests.post(f"{BASE_URL}/register", json=payload)

    # Assert the response
    assert response.status_code == 201
    assert response.json() == {"message": "User registered successfully"}

def test_register_missing_fields():
    """
    Test registration with missing fields.
    """
    # Test data (missing password)
    payload = {
        "username": "testuser"
    }

    # Send POST request to /register
    response = requests.post(f"{BASE_URL}/register", json=payload)

    # Assert the response
    assert response.status_code == 400
    assert response.json() == {"error": "Username/Password required"}

def test_register_duplicate_username():
    """
    Test registration with a duplicate username.
    """
    # Test data (username already exists)
    payload = {
        "username": "testuser",
        "password": "testpassword"
    }

    # Send POST request to /register
    response = requests.post(f"{BASE_URL}/register", json=payload)

    # Assert the response
    assert response.status_code == 400
    assert response.json() == {"error": "Username already exists"}

def test_login_success():
    """
    Test successful user login.
    """
    # Test data
    payload = {
        "username": "testuser",
        "password": "testpassword"
    }

    # Send POST request to /login
    response = requests.post(f"{BASE_URL}/login", json=payload)

    # Assert the response
    assert response.status_code == 200
    assert response.json().get("message") == "User 'testuser' logged in successfully."

def test_login_invalid_credentials():
    """
    Test login with invalid credentials.
    """
    # Test data (invalid password)
    payload = {
        "username": "testuser",
        "password": "wrongpassword"
    }

    # Send POST request to /login
    response = requests.post(f"{BASE_URL}/login", json=payload)

    # Assert the response
    assert response.status_code == 401
    assert response.json() == {"error": "Invalid username or password"}

def test_login_missing_fields():
    """
    Test login with missing fields.
    """
    # Test data (missing password)
    payload = {
        "username": "testuser"
    }

    # Send POST request to /login
    response = requests.post(f"{BASE_URL}/login", json=payload)

    # Assert the response
    assert response.status_code == 400
    assert response.json() == {"message": "User logging not successful"}

    delete_test_user("testuser")
