



from models import User
from unittest import TestCase
import os


# Change os.env before importing app
# os.environ['TESTING'] = 'True'
os.environ['DATABASE_URL'] = "postgresql:///pinterest_test"

from app import app, db
class BaseTestCase(TestCase):

    def setUp(self):
        self.app = app
        self.db = db
        with self.app.app_context():
            self.db.create_all()
            User.query.delete()

            u1 = User.signup("u1", "password", "u1_first",
                             "u1_last", "u1@1.com")
            u2 = User.signup("u2", "password", "u2_first",
                             "u2_last", "u2@1.com")

            self.db.session.commit()
            self.u1_id = u1.id
            self.u2_id = u2.id

            self.client = app.test_client()

    def tearDown(self):
        # Clean up after each test
        with self.app.app_context():
            self.db.session.rollback()
            self.db.session.remove()
            self.db.drop_all()
