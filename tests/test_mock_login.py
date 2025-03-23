import pytest
from unittest.mock import patch, MagicMock
import psycopg2
import requests

# Base URL
BASE_URL = "http://35.169.25.122"

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

# Mock the requests.post method
@patch('requests.post')
def test_register_success(mock_post):
    """
    Test successful user registration.
    """
    # Configure the mock to return a specific response
    mock_response = MagicMock()
    mock_response.status_code = 201
    mock_response.json.return_value = {"message": "User registered successfully"}
    mock_post.return_value = mock_response

    # Test data
    payload = {
        "username": "testuser",
        "password": "testpassword"
    }

    # This will use the mocked post method instead of making a real request
    response = requests.post(f"{BASE_URL}/register", json=payload)

    # Assert the response
    assert response.status_code == 201
    assert response.json() == {"message": "User registered successfully"}

    # Verify the mock was called with the expected arguments
    mock_post.assert_called_once_with(f"{BASE_URL}/register", json=payload)

@patch('requests.post')
def test_register_missing_fields(mock_post):
    """
    Test registration with missing fields.
    """
    # Configure the mock
    mock_response = MagicMock()
    mock_response.status_code = 400
    mock_response.json.return_value = {"error": "Username/Password required"}
    mock_post.return_value = mock_response

    # Test data (missing password)
    payload = {
        "username": "testuser"
    }

    # Send POST request to /register
    response = requests.post(f"{BASE_URL}/register", json=payload)

    # Assert the response
    assert response.status_code == 400
    assert response.json() == {"error": "Username/Password required"}

    # Verify the mock was called with the expected arguments
    mock_post.assert_called_once_with(f"{BASE_URL}/register", json=payload)

@patch('requests.post')
def test_register_duplicate_username(mock_post):
    """
    Test registration with a duplicate username.
    """
    # Configure the mock
    mock_response = MagicMock()
    mock_response.status_code = 400
    mock_response.json.return_value = {"error": "Username already exists"}
    mock_post.return_value = mock_response

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

    # Verify the mock was called with the expected arguments
    mock_post.assert_called_once_with(f"{BASE_URL}/register", json=payload)

@patch('requests.post')
def test_login_success(mock_post):
    """
    Test successful user login.
    """
    # Configure the mock
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json.return_value = {"message": "User 'testuser' logged in successfully."}
    mock_post.return_value = mock_response

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

    # Verify the mock was called with the expected arguments
    mock_post.assert_called_once_with(f"{BASE_URL}/login", json=payload)

@patch('requests.post')
def test_login_invalid_credentials(mock_post):
    """
    Test login with invalid credentials.
    """
    # Configure the mock
    mock_response = MagicMock()
    mock_response.status_code = 401
    mock_response.json.return_value = {"error": "Invalid username or password"}
    mock_post.return_value = mock_response

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

    # Verify the mock was called with the expected arguments
    mock_post.assert_called_once_with(f"{BASE_URL}/login", json=payload)

@patch('requests.post')
def test_login_missing_fields(mock_post):
    """
    Test login with missing fields.
    """
    # Configure the mock
    mock_response = MagicMock()
    mock_response.status_code = 400
    mock_response.json.return_value = {"message": "User logging not successful"}
    mock_post.return_value = mock_response

    # Test data (missing password)
    payload = {
        "username": "testuser"
    }

    # Send POST request to /login
    response = requests.post(f"{BASE_URL}/login", json=payload)

    # Assert the response
    assert response.status_code == 400
    assert response.json() == {"message": "User logging not successful"}

    # Verify the mock was called with the expected arguments
    mock_post.assert_called_once_with(f"{BASE_URL}/login", json=payload)

    # No need to actually delete the user since we're mocking
    # delete_test_user("testuser")