import os
import boto3
from dotenv import load_dotenv
from csv import DictReader
from flask import Flask, render_template, request, flash, redirect, session, g, jsonify
from flask_cors import CORS
from sqlalchemy.exc import IntegrityError
import sqlalchemy as sa
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
CORS(app)

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

@app.before_request
def add_user_to_g():
    header_token = request.headers.get('Authorization')

    print("HEADER TOKEN", header_token)
    if header_token:
        token = header_token.split(" ")[1]
        print("BEARER TOKEN", token)
        print("TOKEN:", token)
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

def createToken(username, id):
    encoded_jwt = jwt.encode({"username": username, "id" : id} , SECRET_KEY, algorithm='HS256')
    return encoded_jwt

def upload_image_get_url(image):
    # Create bucket later for this app
    # TODO:
    key = image.filename
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
    # TEST:
    username = request.json["username"]
    password = request.json["password"]
    firstName = request.json["first_name"]
    lastName = request.json["last_name"]
    email = request.json["email"]

    # when creating file, needs to multi
    # image = request.files["image"]

    # userImg = upload_image_get_url(image)

    user = User.signup(
        username, password, firstName, lastName, email
    )
    print("USER", user)
    print("USERNAME", username)
    # print("IMAGE", image)
    # serialized = user.serialize()
    db.session.commit()

    token = createToken(username)

    return jsonify(token=token)

@app.post('/login')
def login():
    username = request.json["username"]
    password = request.json["password"]

    user = User.authenticate(username, password)

    if user == False:
        return (jsonify(message="Invalid username/password"), 401)

    token = createToken(username, user.id)

    return jsonify(token=token)

# ##############################################################################
# # General user routes: IF LOGGED IN

@app.get('/users')
def list_users():
    """Page with listing of users.

    Can take a 'q' param in querystring to search by that username.
    """

    if not g.user:
        flash("Access unauthorized.", "danger")
        return redirect("/")

    users = User.query.all()
    ur = []
    # search = request.args.get('q')
    # NOTE: add filter? is this the correct way to serialize many?
    # if not search:
    #     users = User.query.all()
    # else:
    #     users = User.query.filter(User.username.like(f"%{search}%")).all()
    for u in users:
        ur.append(u.serialize())
    return jsonify(users=ur)

@app.get('/<username>')
def show_user(username):
    """Show user profile."""
    print(g.user)
    if not g.user:
        return (jsonify(message="Not Authorized"), 401)

    user = User.query.filter_by(username=username).first()
    print(user)
    serialized = user.serialize()
    return jsonify( user= serialized)

@app.post('/profile-settings')
def edit():
    # TEST:
    if not g.user:
        return (jsonify(message="Not Authorized"), 401)

    user = User.query.get_or_404(request.json["id"])

    user.username = request.json["username"]
    user.firstName = request.json["first_name"]
    user.lastName = request.json["last_name"]
    user.email = request.json["email"]
    user.image = request.json["image"]
    user.about = request.json["about"]
    user.website = request.json["website"]

    db.session.commit()

    serialized = user.serialize()

    return jsonify(user=serialized)


##############################################################################
# PINS AND COLLECTIONS
@app.get('/pin/<id>')
def show_post(id):
    """Show a pin"""

    pin = Pins.query.get_or_404(id)

    serialized = pin.serialize()

    return jsonify(pin=serialized)

@app.post('/pin/create')
def create_pin():
    "Create a pin"
    # TEST:

    print("in create pin")

    title = request.json["title"]
    description = request.json["description"]
    # picture = request.files["picture"]
    picture = request.json["picture"]
    link_to_original_pic = request.json["link_to_original_pic"]
    user_posted = g.user["id"]

    print("in create pin")
    # pinImage = upload_image_get_url(picture)
    pin = Pins.create(
        title, picture, link_to_original_pic, description, user_posted
        )

    g.user.pins.append(pin)
    db.session.commit()

    serialized = pin.serialize()

    return jsonify(pin=serialized)

@app.post('/delete-pin')
def delete_pin():
    "Delete a pin"
    # WORKS, TODO: if the pin is a users, can delete.
    #  (should not have delete functionality in frontend if not ur own pin)

    id = request.json["id"]

    pin = Pins.query.get_or_404(id)

    # g.user.pins.remove(pin)
    db.session.delete(pin)
    db.session.commit()

    serialized = pin.serialize()

    return jsonify(pin=serialized)

@app.get('/pin')
def show_all():
    "Show all pins that exist"
    pins = Pins.query.all()

    all_pins = []
    for pin in pins:
        all_pins.append(pin.serialize())

    return jsonify(pins=all_pins)

@app.get('/<username>/created')
def show_created_pins(username):
    """Show pins created by user"""
    # FIXME: AttributeError: 'Query' object has no attribute 'pins'
    # id = request.json["id"]

    user = User.query.filter_by(username=username)
    pins = user.pins()

    return jsonify(pins=pins)

@app.get("/<username>/saved")
def show_collections(username):
    """Show a users collections """
    # TEST:
    user = User.query.filter_by(username=username)

    user = User.query.get_or_404(id)
    collections = user.collections()

    return jsonify(collections=collections)

@app.get("/<username>/<title>")
def show_pins_in_collection():
    """Show pins in a collection"""
    # TEST:
    id = request.json["id"]

    collection = Collections.query.get_or_404(id)

    pins = collection.collection_and_pins()

    return jsonify(pins=pins)

@app.post("/createBoard")
def create_collection():
    # TEST:
    title = request.form["title"]
    description = request.form["description"]
    # user_created = g.user

    collection = Collections.create(title,description)
    g.user.collections.append(collection)

    db.session.commit()

    return jsonify(collection=collection)

@app.post("/deleteBoard")
def delete_collection():
    # TEST:
    id = request.json[id]

    collection = Collections.query.get_or_404(id)

    g.user.collections.remove(collection)
    db.session.delete(collection)

    db.session.commit()

    return jsonify(collection=collection)

##############################################################################
# Following and Followers
@app.get('/<username>/following')
def show_following(username):
    """Show list of people this user is following."""
    # TEST:
    # user_id = request.json["id"]
    # user = User.query.get_or_404(user_id)

    user = User.query.filter_by(username=username).first()

    return jsonify(user=user.following())

@app.get('/<username>/followers')
def show_followers(username):
    """Show list of people this user is following."""
    # TEST:
    # user_id = request.json["id"]
    # user = User.query.get_or_404(user_id)

    user = User.query.filter_by(username=username).first()

    # NOTE: with user.followers and user.pins,
    # do we need to append serialized info to the user?
    # or do we append and serialize later?
    return jsonify(user=user.followers())


@app.post('/follow/<id>')
def follow(id):
    """follow a user"""
    # FIXME: AttributeError: 'dict' object has no attribute 'following'
    follow_user = User.query.get_or_404(id)

    g.user.following.append(follow_user)

    db.session.commit()

    return jsonify(user=follow_user)

@app.post('/unfollow/<id>')
def unfollow(id):
    """unfollow a user"""
    # FIXME: AttributeError: 'dict' object has no attribute 'following'

    unfollow_user = User.query.get_or_404(id)

    g.user.following.remove(unfollow_user)

    db.session.commit()

    return jsonify(user=unfollow_user)





# /login DONE:
# /signup DONE:
# /
# /createPin DONE:
# /username (default to saved) DONE:
# /profile-settings DONE:


# /username/created DONE:

# /username/collectionName DONE:

# /pin/PinId DONE:
