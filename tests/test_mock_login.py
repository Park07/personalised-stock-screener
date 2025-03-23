from unittest.mock import patch, MagicMock
import pytest
import requests

# Base URL
BASE_URL = "http://35.169.25.122"

class MockResponse:
    def __init__(self, json_data, status_code):
        self.json_data = json_data
        self.status_code = status_code

    def json(self):
        return self.json_data

def test_register_success():
    """
    Test successful user registration with proper mocking.
    """
    with patch('requests.post') as mock_post:
        # Configure the mock
        mock_post.return_value = MockResponse(
            {"message": "User registered successfully"}, 201
        )

        # Import requests inside the test to ensure mocking works
        import requests

        # Test data
        payload = {
            "username": "testuser",
            "password": "testpassword"
        }

        # This will use the mocked post method
        response = requests.post(f"{BASE_URL}/register", json=payload)

        # Assert the response
        assert response.status_code == 201
        assert response.json() == {"message": "User registered successfully"}

        # Verify the mock was called with the expected arguments
        mock_post.assert_called_once_with(f"{BASE_URL}/register", json=payload)

def test_register_missing_fields():
    """
    Test registration with missing fields.
    """
    with patch('requests.post') as mock_post:
        # Configure the mock
        mock_post.return_value = MockResponse(
            {"error": "Username/Password required"}, 400
        )


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

def test_register_duplicate_username():
    """
    Test registration with a duplicate username.
    """
    with patch('requests.post') as mock_post:
        # Configure the mock
        mock_post.return_value = MockResponse(
            {"error": "Username already exists"}, 400
        )

        # Import requests inside the test
        import requests

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

def test_login_success():
    """
    Test successful user login.
    """
    with patch('requests.post') as mock_post:
        # Configure the mock
        mock_post.return_value = MockResponse(
            {"message": "User 'testuser' logged in successfully."}, 200
        )
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

def test_login_invalid_credentials():
    """
    Test login with invalid credentials.
    """
    with patch('requests.post') as mock_post:
        # Configure the mock
        mock_post.return_value = MockResponse(
            {"error": "Invalid username or password"}, 401
        )


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

def test_login_missing_fields():
    """
    Test login with missing fields.
    """
    with patch('requests.post') as mock_post:
        # Configure the mock
        mock_post.return_value = MockResponse(
            {"message": "User logging not successful"}, 400
        )


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
