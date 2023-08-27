
# import os
# from unittest import TestCase
from models import User
from tests.base_test import BaseTestCase
from flask_bcrypt import Bcrypt
bcrypt = Bcrypt()


DEFAULT_IMAGE_URL = "https://static.vecteezy.com/system/resources/thumbnails/009/734/564/small/default-avatar-profile-icon-of-social-media-user-vector.jpg"


class UserModelTestCase(BaseTestCase):

    def test_serialize(self):
        with self.app.app_context():

            u1 = User.query.filter_by(username='u1').first()
            serialized_data = u1.serialize()
            self.assertEqual(serialized_data['username'], "u1")
            self.assertEqual(serialized_data['image_url'], DEFAULT_IMAGE_URL)

            self.assertTrue(serialized_data['id'], int)
            self.assertIsNone(serialized_data['about'])

    def test_signup(self):
        with self.app.app_context():

            new_user = User.signup(
                username="newuser",
                password="newpassword",
                firstName="Jane",
                lastName="Smith",
                email="1@1.com"
            )
            self.db.session.commit()

            self.assertIsNotNone(new_user.id)
            self.assertTrue(new_user.id, int)
            self.assertEqual(new_user.username, "newuser")
            self.assertNotEqual(new_user.password, 'newpassword')
            self.assertEqual(bcrypt.check_password_hash(
                new_user.password, "newpassword"), True)

    def test_authenticate_valid(self):
        with self.app.app_context():

            user = User.query.filter_by(id=self.u1_id).first()
            authenticated_user = User.authenticate("u1", "password")
            self.assertEqual(authenticated_user.username, user.username)
            self.assertEqual(authenticated_user.email, user.email)

    def test_authenticate_invalid(self):
        with self.app.app_context():

            user = User.query.filter_by(id=self.u1_id).first()
            self.assertEqual(user.username, "u1")
            authenticated_user = User.authenticate("u1", "passw13414ord")
            self.assertEqual(authenticated_user, False)
