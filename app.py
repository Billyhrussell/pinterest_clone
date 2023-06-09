import os
import boto3
from dotenv import load_dotenv
# from werkzeug import secure_filename

from flask import Flask, render_template, request, flash, redirect, session, g, jsonify
from flask_cors import CORS
from sqlalchemy.exc import IntegrityError

from models import db, connect_db, User, Likes, Dislikes

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
app.config['SQLALCHEMY_DATABASE_URI'] = 'postgresql:///friender'
# os.environ['DATABASE_URL'].replace("postgres://", "postgresql://"))
app.config['SQLALCHEMY_ECHO'] = False
app.config['SECRET_KEY'] = os.environ['SECRET_KEY']

connect_db(app)

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
                print("CURR USER")
                g.user = curr_user
            except:
                g.user = None
                print("error")
    else:
        g.user = None

def createToken(username):
    encoded_jwt = jwt.encode({"username": username} , SECRET_KEY, algorithm='HS256')
    return encoded_jwt

def upload_image_get_url(image):
    # Create bucket later for this app

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

    username = request.form["username"]
    password = request.form["password"]
    fullName = request.form["first_name"]
    fullName = request.form["last_name"]
    hobbies = request.form["email"]

    # when creating file, needs to multi
    # image = request.files["image"]

    # userImg = upload_image_get_url(image)

    user = User.signup(
        username, password, fullName, hobbies
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

    token = createToken(username)

    return jsonify(token=token)

# ##############################################################################
# # General user routes: IF LOGGED IN

# # Show ALL users
