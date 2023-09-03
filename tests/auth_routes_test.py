# from flask import jsonify
from tests.base_test import BaseTestCase

from models import User


class TestAuthRoutes(BaseTestCase):

    def test_valid_signup(self):
        # Test the /signup route

        # Prepare a JSON payload for the request
        data = {
            "username": "test_user",
            "password": "password123",
            "firstName": "John",
            "lastName": "Doe",
            "email": "test@example.com"
        }
        # Assert that the database contains the newly created user
        with self.app.app_context():

            # Make a POST request to the /signup route
            response = self.client.post('/signup', json=data)

            # Assert that the response status code is 200 (success)
            self.assertEqual(response.status_code, 200)

            user = User.query.filter_by(username="test_user").first()
            self.assertIsNotNone(user)
            self.assertEqual(user.first_name, "John")
            self.assertEqual(user.last_name, "Doe")
            self.assertEqual(user.email, "test@example.com")

    def test_username_taken(self):

        with self.app.app_context():
            user = User.query.filter_by(username="test_user").first()
            self.assertIsNotNone(user)
            self.assertEqual(user.first_name, "John")
            self.assertEqual(user.last_name, "Doe")
            self.assertEqual(user.email, "test@example.com")


    def test_login_route(self):

        with self.app.app_context():

            # Make a POST request to the /login route
            response = self.client.post('/login', json={
                "username": "u1",
                "password": "password"
            })

            self.assertEqual(response.status_code, 200)
            set_cookie_headers = response.headers.getlist("Set-Cookie")
            token_cookie_present = any("token" in cookie for cookie in set_cookie_headers)
            self.assertTrue(response.headers.get("Set-Cookie"))
            self.assertTrue(token_cookie_present)

    def test_login_invalid_credentials(self):
        # Test login with invalid credentials



        # Make a POST request to the /login route
        response = self.client.post('/login', json={
            "username": "u1",
            "password": "wrong_password"
        })

        # Assert that the response status code is 401 (unauthorized)
        self.assertEqual(response.status_code, 401)
        self.assertFalse(response.headers.get("Set-Cookie"))

        # Assert that the response contains an error message
        self.assertEqual(response.json.get("message"), "Invalid username/password")

