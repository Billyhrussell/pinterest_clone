import os
import boto3
from dotenv import load_dotenv
from flask import Flask, request, g, jsonify, make_response
from flask_cors import CORS


import uuid

from models import db, connect_db, User, Pins, Collections

import jwt

app = Flask(__name__)

load_dotenv()
AWS_ACCESS_KEY_ID = os.environ['AWS_ACCESS_KEY_ID']
AWS_SECRET_ACCESS_KEY = os.environ['AWS_SECRET_ACCESS_KEY']
# DATABASE_URL = os.environ['DATABASE_URL']
BUCKET_NAME = os.environ['BUCKET_NAME']
SECRET_KEY = os.environ['SECRET_KEY']

s3 = boto3.client(
    "s3",
    "us-west-1",
    aws_access_key_id=AWS_ACCESS_KEY_ID,
    aws_secret_access_key=AWS_SECRET_ACCESS_KEY,
)


CORS(app, supports_credentials=True)

# TODO:Throw errors on try/except's

# Get DB_URI from environ variable (useful for production/testing) or,
# if not set there, use development local db.
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SQLALCHEMY_DATABASE_URI'] = (
    os.environ['DATABASE_URL'].replace("postgres://", "postgresql://"))

app.config['SQLALCHEMY_ECHO'] = False
app.config['SECRET_KEY'] = os.environ['SECRET_KEY']


connect_db(app)

# Check if the database needs to be initialized
# engine = sa.create_engine(app.config['SQLALCHEMY_DATABASE_URI'])
# inspector = sa.inspect(engine)
# if not inspector.has_table("messages"):
#     app.logger.info("trying 2 do the thing")
#     with app.app_context():
#         db.drop_all()
#         db.create_all()

#         with open('generator/users.csv') as users:
#             db.session.bulk_insert_mappings(User, DictReader(users))

#         with open('generator/pins.csv') as pins:
#             db.session.bulk_insert_mappings(Pins, DictReader(pins))

#         # with open('generator/collections.csv') as collections:
#         #     db.session.bulk_insert_mappings(Collections, DictReader(collections))

#         db.session.commit()

#         app.logger.info('Initialized the database!')
# else:
#     app.logger.info('Database already contains the messages table.')

##############################################################################
# User signup/login/logout

# @app.before_request
# def add_user_to_g():
#     header_token = request.headers.get('Authorization')

#     header = request.headers
#     print("HEADERS ", header)

#     # print("HEADER TOKEN", header_token)
#     if header_token:
#         token = header_token.split(" ")[1]
#         print("BEARER TOKEN", token)
#         print("TOKEN:", token)
#         if token:
#             try:
#                 print("in try")
#                 curr_user = jwt.decode(token, SECRET_KEY, algorithms=["HS256"])
#                 g.user = curr_user
#                 print("CURR USER", g.user)
#             except:
#                 g.user = None
#                 print("error, could not verify token")
#     else:
#         g.user = None


@app.before_request
def add_user_to_g():
    """ Add user to global, check if user token same as header token"""
    token = request.cookies.get('token')
    # print("TOKEN: ", token)

    header = request.headers
    # print("HEADERS ", header)

    # if header_token:
    #     token = header_token
    if token:
        try:
            print("in try")
            curr_user = jwt.decode(token, SECRET_KEY, algorithms=["HS256"])
            g.user = curr_user
            print("CURR USER", g.user)
        except:
            g.user = None
            print("error, could not verify token")
    else:
        g.user = None

# FIXME :Rename,or split into 2 separate functions 1 for creating the token
# and another for the response
def createToken(id):
    """Creates a Token"""
    # info: set_cookie with the userId and token
    encoded_jwt = jwt.encode({"id": id}, SECRET_KEY, algorithm='HS256')

    response = make_response(jsonify(message='Cookie Set Successfully'))

    response.set_cookie("token", encoded_jwt, httponly=True)
    response.set_cookie("user-id", str(id), max_age=3600)

    return response


def upload_image_get_url(image):
    # Create bucket later for this app
    key = uuid.uuid4()
    bucket = BUCKET_NAME
    content_type = 'request.mimetype'
    image_file = image
    region = 'us-west-1'
    location = boto3.client('s3').get_bucket_location(
        Bucket=BUCKET_NAME)['LocationConstraint']

    client = boto3.client('s3',
                          region_name=region,
                          endpoint_url=f'https://{bucket}.s3.{location}.amazonaws.com',
                          aws_access_key_id=AWS_ACCESS_KEY_ID,
                          aws_secret_access_key=AWS_SECRET_ACCESS_KEY)

    url = f"https://{bucket}.s3.{region}.amazonaws.com/{bucket}/{key}"
    client.put_object(Body=image_file,
                      Bucket=bucket,
                      Key=key,
                      ContentType=content_type)

    return url


@app.post('/signup')
def signup():
    # TODO: add try/except for username/email that is already taken
    # move try/except somewhere else
    username = request.json["username"]
    password = request.json["password"]
    firstName = request.json["firstName"]
    lastName = request.json["lastName"]
    email = request.json["email"]

    # when creating file, needs to add to AWS
    # image = request.files["image"]
    # userImg = upload_image_get_url(image)

    taken = []
    usernameErr = User.checkIfUsernameTaken(request.json["username"])
    emailErr = User.checkIfEmailTaken(request.json["email"])

    if usernameErr:
        taken.append(usernameErr)
    if emailErr:
        taken.append(emailErr)

    if not taken:
        user = User.signup(
            username, password, firstName, lastName, email
        )

        db.session.commit()

        token = createToken(user.id)

        return token
    else:
        return jsonify(error=taken)


@app.post('/login')
def login():

    username = request.json["username"]
    password = request.json["password"]
    user = User.authenticate(username, password)
    # TODO: Change to if not User
    if user == False:
        return (jsonify(message="Invalid username/password"), 401)
    # FIXME: rename to response, createToken returns a response
    token = createToken(user.id)
    print("FROM ROUTE", token.headers)
    return token

# ##############################################################################
# # General user routes: IF LOGGED IN


@app.get('/users')
def list_users():
    """Page with listing of users.

    Further study: Can take a 'q' param in querystring to search by that username.
    (search functionality)
    """

    if not g.user:
        return (jsonify(message="Not Authorized"), 401)

    users = User.query.all()
    user_list = []

    for u in users:
        user_list.append(u.serialize())

    return jsonify(users=user_list)


@app.get('/<username>')
def show_user(username):
    """Show user profile."""

    if not g.user:
        return (jsonify(message="Not Authorized"), 401)

    user = User.query.filter_by(username=username).first()

    serialized = user.serialize()
    return jsonify(user=serialized)


@app.patch('/profile-settings')
def edit_profile():

    if not g.user:
        return (jsonify(message="Not Authorized"), 401)

    user = User.query.get(g.user["id"])

    taken = []
    if user.username != request.json["username"]:
        usernameErr = User.checkIfUsernameTaken(request.json["username"])
        if usernameErr:
            taken.append(usernameErr)
    if user.email != request.json["email"]:
        emailErr = User.checkIfEmailTaken(request.json["email"])
        if emailErr:
            taken.append(emailErr)

    if not taken:
        user.username = request.json["username"]
        user.first_name = request.json["firstName"]
        user.last_name = request.json["lastName"]
        user.email = request.json["email"]
        user.image_url = request.json["imageUrl"]
        user.about = request.json["about"]
        user.website = request.json["website"]
        user.location = request.json["location"]

        db.session.commit()

        serialized = user.serialize()

        return jsonify(user=serialized)
    else:
        return jsonify(error=taken)

# @app.post('/user-info')
# def getUserInfo():
# note: not necessary, use <username> route
#     if not g.user:
#         return (jsonify(message="Not Authorized"), 401)

#     user = User.query.get(g.user["id"])

#     serialized = user.serialize()

#     return jsonify(user=serialized)


##############################################################################
# PINS AND COLLECTIONS
@app.get('/pin/<id>')
def show_pin(id):
    """Get a pin by id"""

    if not g.user:
        return (jsonify(message="Not Authorized"), 401)

    pin = Pins.query.get_or_404(id)
    serialized = pin.serialize()

    return jsonify(pin=serialized)


@app.post('/pin/create')
def create_pin():
    "Create a pin"

    if not g.user:
        return (jsonify(message="Not Authorized"), 401)

    title = request.json["title"]
    description = request.json["description"]
    pin_image = request.json["pinImage"]
    original_link = request.json["originalLink"]
    user_id = g.user["id"]

    current_user = User.query.get_or_404(g.user["id"])

    # pinImage = upload_image_get_url(picture)
    pin = Pins.create(
        title, pin_image, original_link, description, user_id
    )

    current_user.pins.append(pin)
    db.session.commit()

    serialized = pin.serialize()

    return jsonify(pin=serialized)


@app.delete('/pin/<id>')
def delete_pin(id):
    "Delete a pin"

    if not g.user:
        return (jsonify(message="Not Authorized"), 401)

    pin = Pins.query.get_or_404(id)

    current_user = User.query.get(g.user["id"])

    if current_user.id == pin.user_id:
        current_user.pins.remove(pin)

        db.session.delete(pin)
        db.session.commit()

        serialized = pin.serialize()
        return jsonify(pin=serialized)

    return jsonify(error="error")


@app.get('/pins')
def show_all():
    "Show all pins that exist"
    # TODO: further study, show pins by following
    pins = Pins.query.all()

    all_pins = []
    for pin in pins:
        all_pins.append(pin.serialize())

    return jsonify(pins=all_pins)


@app.get('/<username>/created')
def show_created_pins(username):
    """Show pins created by user"""

    user = User.query.filter_by(username=username).first()
    pins = user.pins

    p = []
    for pin in pins:
        p.append(pin.serialize())
    return jsonify(pins=p)


@app.get("/<username>/saved")
def show_collections(username):
    """Show a users collections """

    user = User.query.filter_by(username=username).first()

    # user = User.query.get_or_404(id)
    collections = user.collections

    user_collections = []

    for c in collections:
        user_collections.append(c.serialize())

    return jsonify(collections=user_collections)


@app.get("/collection/<id>")
def show_pins_in_collection(id):
    """Show pins in a collection"""

    collection = Collections.query.get_or_404(id)

    pins = collection.pins

    collection_pins = []

    for pin in pins:
        collection_pins.append(pin.serialize())

    return jsonify(pins=collection_pins)


@app.post("/collection/create")
def create_collection():

    title = request.json["title"]
    description = request.json["description"]

    user = User.query.get(g.user["id"])

    collection = Collections.create(title, description, user.id)
    user.collections.append(collection)

    db.session.commit()
    serialized = collection.serialize()

    return jsonify(collection=serialized)


@app.delete("/collection/delete")
def delete_collection():
    # NOTE:
    # will we have a problem with deleting a collection with pins inside?
    # also vice versa. if a person deletes a pin, the pin should delete from
    # others collections

    c_id = request.json["id"]

    collection = Collections.query.get_or_404(c_id)

    user = User.query.get(g.user["id"])

    user.collections.remove(collection)

    db.session.delete(collection)
    db.session.commit()

    # serialized = collection.serialize()

    return jsonify(deleted=collection.id)


@app.post("/addPinToCollection")
def add_pin_to_collection():
    pin_id = request.json["pinId"]
    collection_id = request.json["collectionId"]

    collection = Collections.query.get(collection_id)
    pin = Pins.query.get(pin_id)

    collection.pins.append(pin)

    db.session.commit()

    added = f'pin {pin.id} added to collection {collection.id}'

    return jsonify(success=added)


@app.patch("/removePinFromCollection")
def remove_pin_from_collection():
    pin_id = request.json["pinId"]
    collection_id = request.json["collectionId"]

    collection = Collections.query.get(collection_id)
    pin = Pins.query.get(pin_id)

    collection.pins.remove(pin)

    db.session.commit()

    removed = f'pin {pin.id} removed from collection {collection.id}'

    return jsonify(success=removed)

##############################################################################
# Following and Followers


@app.get('/<username>/following')
def show_following(username):
    """Show list of people this user is following."""

    user = User.query.filter_by(username=username).first()

    following = []
    for u in user.following:
        following.append(u.serialize())

    return jsonify(following=following)


@app.get('/<username>/followers')
def show_followers(username):
    """Show list of people this user is following."""

    user = User.query.filter_by(username=username).first()
    followers = []

    for u in user.followers:
        followers.append(u.serialize())

    return jsonify(followers=followers)


@app.post('/follow/<id>')
def follow(id):
    """Follow a user"""

    user = User.query.get(g.user["id"])

    follow_user = User.query.get_or_404(id)

    user.following.append(follow_user)

    db.session.commit()

    serialized = follow_user.serialize()

    return jsonify(followed=serialized)


@app.post('/unfollow/<id>')
def unfollow(id):
    """Unfollow a user"""

    user = User.query.get(g.user["id"])

    unfollow_user = User.query.get_or_404(id)

    user.following.remove(unfollow_user)

    db.session.commit()

    unfollowed = f'Unfollowed user {unfollow_user.id}'

    return jsonify(success=unfollowed)
