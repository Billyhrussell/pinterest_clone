import os
import boto3
from dotenv import load_dotenv
from csv import DictReader
from flask import Flask, render_template, request, flash, redirect, session, g, jsonify, make_response
from flask_cors import CORS
from sqlalchemy.exc import IntegrityError
import sqlalchemy as sa
import uuid

from models import db, connect_db, User, Pins, Collections

import jwt

load_dotenv()
AWS_ACCESS_KEY_ID = os.environ['AWS_ACCESS_KEY_ID']
AWS_SECRET_ACCESS_KEY = os.environ['AWS_SECRET_ACCESS_KEY']
DATABSE_URL = os.environ['DATABASE_URL']
BUCKET_NAME = os.environ['BUCKET_NAME']
SECRET_KEY = os.environ['SECRET_KEY']

s3 = boto3.client(
    "s3",
    "us-west-1",
    aws_access_key_id=AWS_ACCESS_KEY_ID,
    aws_secret_access_key=AWS_SECRET_ACCESS_KEY,
)

app = Flask(__name__)
CORS(app, supports_credentials=True)

# Get DB_URI from environ variable (useful for production/testing) or,
# if not set there, use development local db.
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SQLALCHEMY_DATABASE_URI'] = 'postgresql:///pinterest'
os.environ['DATABASE_URL'].replace("postgres://", "postgresql://")
app.config['SQLALCHEMY_ECHO'] = False
app.config['SECRET_KEY'] = os.environ['SECRET_KEY']

# with app.app_context():
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
    print("TOKEN: ", token)

    header = request.headers
    print("HEADERS ", header)

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


def createToken(id):
    # info: set_cookie with the userId and token
    encoded_jwt = jwt.encode({"id" : id} , SECRET_KEY, algorithm='HS256')

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

    try:
        if User.query.filter_by(username=username).first():
            error = "username taken"
            return error
    except:
        "nothing happens"

    try:
        print("INSIDE TRY SIGNUP")
        if User.query.filter_by(email=email).first():
            error = "email already in use"
            return error
    except:
        "nothing happens"

    user = User.signup(
        username, password, firstName, lastName, email
    )

    db.session.commit()

    token = createToken(username)

    return token

@app.post('/login')
def login():

    username = request.json["username"]
    password = request.json["password"]
    user = User.authenticate(username, password)

    if user == False:
        return (jsonify(message="Invalid username/password"), 401)

    token = createToken(user.id)

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
    return jsonify(user= serialized)

@app.patch('/profile-settings')
def edit_profile():

    if not g.user:
        return (jsonify(message="Not Authorized"), 401)

    user = User.query.get(g.user["id"])

    try:
        if User.query.filter_by(username=request.json["username"]).first():
            error = "username taken"
            return jsonify(error=error)
    except:
        "nothing happens"

    try:
        print("INSIDE TRY PROFILE SETTINGS")
        if User.query.filter_by(email=request.json["email"]).first():
            error = "email already in use"
            return jsonify(error=error)
    except:
        "nothing happens"

    user.username = request.json["username"]
    user.firstName = request.json["firstName"]
    user.lastName = request.json["lastName"]
    user.email = request.json["email"]
    user.image = request.json["image"]
    user.about = request.json["about"]
    user.website = request.json["website"]

    db.session.commit()

    serialized = user.serialize()

    return jsonify(user=serialized)

@app.post('/user-info')
def getUserInfo():
    if not g.user:
        return (jsonify(message="Not Authorized"), 401)

    user = User.query.get(g.user["id"])

    serialized = user.serialize()

    return jsonify(user=serialized)



##############################################################################
# PINS AND COLLECTIONS
@app.get('/pin/<id>')
def show_pin(id):
    """Show a pin"""

    pin = Pins.query.get_or_404(id)
    serialized = pin.serialize()
    print("PIN: ", serialized)

    return jsonify(pin=serialized)

@app.post('/pin/create')
def create_pin():
    "Create a pin"

    print("in create pin")

    title = request.json["title"]
    description = request.json["description"]
    # picture = request.files["picture"]
    picture = request.json["picture"]
    link_to_original_pic = request.json["link_to_original_pic"]
    user_posted = g.user["id"]

    current_user = User.query.get_or_404(g.user["id"])

    print("in create pin")
    # pinImage = upload_image_get_url(picture)
    pin = Pins.create(
        title, picture, link_to_original_pic, description, user_posted
        )

    current_user.pins.append(pin)
    db.session.commit()

    serialized = pin.serialize()

    return jsonify(pin=serialized)

@app.post('/pin/delete')
def delete_pin():
    "Delete a pin"
    # FIXME: cannot delete a post within a collection, change to app.delete
    id = request.json["id"]

    pin = Pins.query.get_or_404(id)
    # current_user = User.query.filter_by(username=g.user["username"]).first()

    print("G.USER IN DELETE-PIN", g.user)
    current_user = User.query.get(g.user["id"])
    print("CURR", current_user.id,"PIN", pin.user_posted)
    if current_user.id == pin.user_posted:

        current_user.pins.remove(pin)

        # g.user.pins.remove(pin)
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

@app.get("/<username>/<title>/<id>")
def show_pins_in_collection(username, title, id):
    """Show pins in a collection"""

    collection = Collections.query.get_or_404(id)

    pins = collection.pins

    collection_pins = []

    for pin in pins:
        collection_pins.append(pin.serialize())

    return jsonify(pins=collection_pins)

@app.post("/createCollection")
def create_collection():

    title = request.json["title"]
    description = request.json["description"]


    # user = User.query.filter_by(username=g.user["username"]).first()
    user = User.query.get(g.user["id"])

    collection = Collections.create(title,description, user.id)
    user.collections.append(collection)

    db.session.commit()
    serialized = collection.serialize()

    return jsonify(collection=serialized)

@app.post("/deleteBoard")
def delete_collection():
    # NOTE:
    # will we have a problem with deleting a collection with pins inside?
    # also vice versa. if a person deletes a pin, the pin should delete from
    # others collections

    c_id = request.json["id"]

    collection = Collections.query.get_or_404(c_id)

    # user = User.query.filter_by(username=g.user["username"]).first()
    user = User.query.get(g.user["id"])

    user.collections.remove(collection)

    db.session.delete(collection)
    db.session.commit()

    serialized = collection.serialize()

    return jsonify(collection=serialized)

@app.post("/addPinToCollection")
def add_pin_to_collection():
    pin_id = request.json["pinId"]
    collection_id = request.json["collectionId"]

    collection = Collections.query.get(collection_id)
    pin = Pins.query.get(pin_id)

    collection.pins.append(pin)

    db.session.commit()

    serialized = pin.serialize()

    return jsonify(pin=serialized)

@app.post("/removePinFromCollection")
def remove_pin_from_collection():
    pin_id = request.json["pinId"]
    collection_id = request.json["collectionId"]

    collection = Collections.query.get(collection_id)
    pin = Pins.query.get(pin_id)

    collection.pins.remove(pin)

    db.session.commit()

    serialized = pin.serialize()

    return jsonify(pin=serialized)



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

    # NOTE: with user.followers and user.pins,
    # do we need to append serialized info to the user?
    # or do we append and serialize later?
    return jsonify(followers=followers)

@app.post('/follow/<id>')
def follow(id):
    """follow a user"""

    # NOTE: IS USER.QUER.FILTER_BY COSTLY??????? this seems ineffcient
    # user = User.query.filter_by(username=g.user["username"]).first()
    user = User.query.get(g.user["id"])

    follow_user = User.query.get_or_404(id)

    user.following.append(follow_user)

    db.session.commit()

    serialized = follow_user.serialize()

    return jsonify(followed=serialized)

@app.post('/unfollow/<id>')
def unfollow(id):
    """unfollow a user"""
    # user = User.query.filter_by(username=g.user["username"]).first()
    user = User.query.get(g.user["id"])

    unfollow_user = User.query.get_or_404(id)

    user.following.remove(unfollow_user)

    db.session.commit()

    serialized = unfollow_user.serialize()

    return jsonify(unfollowed=serialized)





# /login DONE:
# /signup DONE:
# /
# /createPin DONE:
# /username (default to saved) DONE:
# /profile-settings DONE:


# /username/created DONE:

# /username/collectionName DONE:

# /pin/PinId DONE:
