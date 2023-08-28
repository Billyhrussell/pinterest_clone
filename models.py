from datetime import datetime

from flask_bcrypt import Bcrypt
from flask_sqlalchemy import SQLAlchemy
# import SQLAlchemy as sa
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
        # nullable=False,
        unique=False,
    )

    timestamp = db.Column(
        db.DateTime,
        nullable=False,
        default=datetime.utcnow,
    )

    followers = db.relationship(
        "User",
        secondary="follows",
        primaryjoin=(Follows.user_being_followed_id == id),
        secondaryjoin=(Follows.user_following_id == id),
        backref="following",
    )

    pins = db.relationship("Pins", backref="user")

    collections = db.relationship("Collections", backref="user")

    def serialize(self):
        """Serialize to dictionary"""
        # serialization is python converting to JSON
        return {
            "username": self.username,
            "id": self.id,
            "first_name": self.first_name,
            "last_name": self.last_name,
            "email": self.email,
            "image_url": self.image_url,
            "about": self.about,
            "location": self.location,
            "website": self.website
        }

    def __repr__(self):
        return f"<User #{self.username}>"

    @classmethod
    def signup(cls, username, password, firstName, lastName, email):
        """Sign up user.

        Hashes password and adds user to system.
        """

        hashed_pwd = bcrypt.generate_password_hash(password).decode('UTF-8')

        user = User(
            username=username,
            password=hashed_pwd,
            # password=password,
            first_name=firstName,
            last_name=lastName,
            email=email,
            # about=about,
            # location=location,
            # website=website,
            # image_url=image_url
        )

        db.session.add(user)

        return user

    @classmethod
    def authenticate(cls, username, password):
        """Find user with `username` and `password`.

        This is a class method (call it on the class, not an individual user.)
        It searches for a user whose password hash matches this password
        and, if it finds such a user, returns that user object.

        If this can't find matching user (or if password is wrong), returns
        False.
        """

        user = cls.query.filter_by(username=username).first()
        if user:
            if user.password == password:
                return user
        # FIXME: add this once running, I think this can be a one liner
        # if user:
        #     is_auth = bcrypt.check_password_hash(user.password, password)
        #     if is_auth:
        #         return user

        return False

    @classmethod
    def checkIfUsernameTaken(cls, username):
        """ Check if a username or email is taken by another user"""

        error = ""

        try:
            if User.query.filter_by(username=username).first():
                error += "username taken"

        except:
            "nothing happens"

        return error

    @classmethod
    def checkIfEmailTaken(cls, email):
        """ Check if a username or email is taken by another user"""

        error = ""

        try:
            if User.query.filter_by(email=email).first():
                error += "email already in use"

        except:
            "nothing happens"

        return error

    # messages = db.relationship('Message', backref="user")
    # likes = db.relationship('Message', secondary="likes", backref="users_liked")
    # #backref like_messages

    # followers = db.relationship(
    #     "User",
    #     secondary="follows",
    #     primaryjoin=(Follows.user_being_followed_id == id),
    #     secondaryjoin=(Follows.user_following_id == id),
    #     backref="following",
    # )

    # following = db.relationship(
    #     "User",
    #     secondary="following",
    #     primaryjoin=(Follows.user_following_id == id),
    #     secondaryjoin=(Follows.user_being_followed_id == id),
    #     backref="follows",
    # )

    # FIXME: forgot how to do these, stores a users pins and collections
association_table = db.Table(
    "association_table",
    db.Column("collection_id", db.ForeignKey(
        'collections.id'), primary_key=True),
    db.Column("pin_id", db.ForeignKey('pins.id'), primary_key=True)
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
# make nullable = False
    pin_image = db.Column(
        db.String(),
        nullable=True,
    )

    original_link = db.Column(
        db.String(),
        nullable=True,
    )

    description = db.Column(
        db.String(500),
        nullable=True,
    )

    user_id = db.Column(
        db.Integer,
        db.ForeignKey('users.id', ondelete="cascade")
    )

    timestamp = db.Column(
        db.DateTime,
        nullable=False,
        default=datetime.utcnow,
    )

    collections = db.relationship(
        "Collections",
        secondary="association_table",
        back_populates="pins")

    def serialize(self):
        """Serialize to dictionary"""
        # serialization is python converting to JSON
        return {
            "id": self.id,
            "title": self.title,
            "pinImage": self.pin_image,
            "originalLink": self.original_link,
            "description": self.description,
            "userId": self.user_id,
            "timestamp": self.timestamp
        }

    @classmethod
    def create(self, title, pin_image, original_link, description, user_id):
        """Create a pin

        Hashes password and adds user to system.
        """
        print(title, pin_image, original_link, description, user_id)
        pin = Pins(
            title=title,
            pin_image=pin_image,
            original_link=original_link,
            description=description,
            user_id=user_id,
        )

        db.session.add(pin)

        return pin


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
        db.ForeignKey('users.id', ondelete="cascade")
    )

    timestamp = db.Column(
        db.DateTime,
        nullable=False,
        default=datetime.utcnow,
    )

    # collectionsandpins = db.relationship(
    #     "Collections",
    #     secondary="collections",
    #     primaryjoin=(CollectionsAndPins.collection_id == id),
    #     secondaryjoin=(CollectionsAndPins.pin_id == id),
    #     backref="pins",
    # )
    # collection_and_pin = db.relationship(
    #     "Collections",
    #     secondary="pins",
    #     primaryjoin=(CollectionsAndPins.collection_id == id),
    #     secondaryjoin=(CollectionsAndPins.pin_id == id),
    #     backref="collections"
    # )

    # pins = db.relationship(
    #     "Pins",
    #     secondary="collectionsAndPins",
    #     backref="collections_relationship")

    pins = db.relationship(
        "Pins",
        secondary="association_table",
        back_populates="collections")

    def serialize(self):
        """Serialize to dictionary"""
        # serialization is python converting to JSON
        return {
            "id": self.id,
            "title": self.title,
            "description": self.description,
            "user_id": self.user_id,
            "timestamp": self.timestamp
        }

    @classmethod
    def create(self, title, description, user_posted):
        """Create a collection

        Hashes password and adds user to system.
        """

        collection = Collections(
            title=title,
            description=description,
        )

        db.session.add(collection)

        return collection


def connect_db(app):
    """Connect this database to provided Flask app.

    You should call this in your Flask app.
    """

    db.app = app
    db.init_app(app)


# class Tags(db.Model):
#     "Tags"

#     __tablename__ = "tags"

#     id = db.Column(
#         db.Integer,
#         primary_key=True,
#     )

#     tag = db.Column(
#         db.String(100),
#         nullable=False,
#     )

#     post_id = db.Column(
#         db.Integer,
#         db.ForeignKey('posts.id', ondelete="cascade"),
#         primary_key=True,
#     )
