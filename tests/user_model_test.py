
# import os
# from unittest import TestCase


# # Change os.env before importing app
# os.environ['TESTING'] = 'True'
# from app import app, db



DEFAULT_IMAGE_URL = "https://static.vecteezy.com/system/resources/thumbnails/009/734/564/small/default-avatar-profile-icon-of-social-media-user-vector.jpg"



from models import User
from tests.base_test import BaseTestCase






class UserModelTestCase(BaseTestCase):

    def test_serialize(self):
        with self.app.app_context():


            u1 = User.query.filter_by(username='u1').first()
            serialized_data = u1.serialize()
            self.assertEqual(serialized_data['username'],"u1")
            self.assertEqual(serialized_data['image_url'],DEFAULT_IMAGE_URL)

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


    # def test_authenticate_valid(self):
    #     authenticated_user = User.authenticate(self.user_data['username'], self.user_data['password'])
    #     self.assertEqual(authenticated_user, self.user)

    # def test_authenticate_invalid(self):
    #     authenticated_user = User.authenticate(self.user_data['username'], "wrongpassword")
    #     self.assertFalse(authenticated_user)

# if __name__ == '__main__':
#     unittest.main()
