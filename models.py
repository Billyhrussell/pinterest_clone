from datetime import datetime

from flask_bcrypt import Bcrypt
from flask_sqlalchemy import SQLAlchemy

bcrypt = Bcrypt()
db = SQLAlchemy()

DEFAULT_IMAGE_URL = "https://static.vecteezy.com/system/resources/thumbnails/009/734/564/small/default-avatar-profile-icon-of-social-media-user-vector.jpg"

class Follows(db.Model):
    """Connection of a follower <-> followed_user."""

    __tablename__ = 'follows'

    user_being_followed_id = db.Column(
        db.Integer,
        db.ForeignKey('users.id', ondelete="cascade"),
        primary_key=True,
    )

    user_following_id = db.Column(
        db.Integer,
        db.ForeignKey('users.id', ondelete="cascade"),
        primary_key=True,
    )

class User(db.Model):
    """User in the system."""

    __tablename__ = 'users'

    id = db.Column(
        db.Integer,
        primary_key=True,
    )

    email = db.Column(
        db.Text,
        nullable=False,
        unique=True,
    )

    username = db.Column(
        db.Text,
        nullable=False,
        unique=True,
    )

    first_name = db.Column(
        db.Text,
        nullable=False,
        unique=False,
    )

    last_name = db.Column(
        db.Text,
        nullable=False,
        unique=False,
    )

    image_url = db.Column(
        db.Text,
        default=DEFAULT_IMAGE_URL,
    )

    about = db.Column(
        db.Text,
    )

    location = db.Column(
        db.Text,
    )

    password = db.Column(
        db.Text,
        nullable=False,
    )

    website = db.Column(
        db.Text,
        nullable=False,
        unique=False,
    )

    timestamp = db.Column(
        db.DateTime,
        nullable=False,
        default=datetime.utcnow,
    )

    def serialize(self):
        """Serialize to dictionary"""
        # serialization is python converting to JSON
        return{
            "username": self.username,
            "first_name": self.firstName,
            "last_name": self.lastName,
            "email" : self.email,
            "image_url": self.imageUrl,
            "about" : self.about,
            "location" : self.location,
            "website" : self.website
        }

    # messages = db.relationship('Message', backref="user")
    # likes = db.relationship('Message', secondary="likes", backref="users_liked")
    # #backref like_messages

    followers = db.relationship(
        "User",
        secondary="follows",
        primaryjoin=(Follows.user_being_followed_id == id),
        secondaryjoin=(Follows.user_following_id == id),
        backref="following",
    )

class Posts(db.Model):
    """ a post created """

    __tablename__ = 'posts'

    id = db.Column(
        db.Integer,
        primary_key=True,
    )

    image_url = db.Column(
        db.Text,
        default=DEFAULT_IMAGE_URL,
    )

    title = db.Column(
        db.String(100),
        nullable=False,
    )

    description = db.Column(
        db.String(500),
        nullable=False,
    )

    timestamp = db.Column(
        db.DateTime,
        nullable=False,
        default=datetime.utcnow,
    )

    original_website_link = db.Column(
        db.Text,
        default=DEFAULT_IMAGE_URL,
    )

    user_id = db.Column(
        db.Integer,
        db.ForeignKey('users.id', ondelete='CASCADE')
    )

class CollectionsAndPins(db.Model):
    """CollectionsAndPins"""

    __tablename__ = 'collectionsAndPins'

    collection_id = db.Column(
        db.Integer,
        db.ForeignKey('collection.id', ondelete="cascade"),
        primary_key=True,
    )

    pin_id = db.Column(
        db.Integer,
        db.ForeignKey('pin.id', ondelete="cascade"),
        primary_key=True,
    )

class Pins(db.Model):
    """Pins"""

    __tablename__ = "pins"

    id = db.Column(
        db.Integer,
        primary_key=True,
    )

    title = db.Column(
        db.String(100),
        nullable=False,
    )

    picture_link = db.Column(
        db.String(),
        nullable=False,
    )

    link_to_original_pic = db.Column(
        db.String(),
        nullable=True,
    )

    description = db.Column(
        db.String(500),
        nullable=True,
    )

    user_posted = db.Column(
        db.Integer,
        db.ForeignKey('users.id', ondelete="cascade"),
        primary_key=True,
    )

    timestamp = db.Column(
        db.DateTime,
        nullable=False,
        default=datetime.utcnow,
    )



class Collections(db.Model):
    """Collections"""

    __tablename__ = "collections"

    id = db.Column(
        db.Integer,
        primary_key=True,
    )

    title = db.Column(
        db.String(100),
        nullable=False,
    )

    description = db.Column(
        db.String(500),
        nullable=False,
    )

    user_id = db.Column(
        db.Integer,
        db.ForeignKey('users.id', ondelete="cascade"),
        primary_key=True,
    )

    timestamp = db.Column(
        db.DateTime,
        nullable=False,
        default=datetime.utcnow,
    )

    collection_and_pin = db.relationship(
        "Collection and their pins",
        secondary="pins",
        primaryjoin=(CollectionsAndPins.collection_id == id),
        secondaryjoin=(CollectionsAndPins.pin_id == id),
    )


