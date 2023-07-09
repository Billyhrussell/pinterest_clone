# SETUP

python3 -m venv venv

source venv/bin/activate

(venv) pip3 install -r requirements.txt

psql
CREATE DATABASE pinterest;
\q

(venv) python3 seed.py

Create .env file with
    region=<s>us-west-1</s>
    AWS_ACCESS_KEY_ID =  accesskey
    AWS_SECRET_ACCESS_KEY =  AWS_SECRET_KEY
    DATABASE_URL = 'postgresql:///pinterest'
    BUCKET_NAME = "binterest-backend"
    SECRET_KEY= SECRET_KEY

Create .gitignore file with
    .env/
    venv/

For Billy:
- add access in IAM > users > user > AmazonS3FullAccess
pip3.10 install -r requirements.txt

For LOCAL development install AWS Toolkit
- https://marketplace.visualstudio.com/items?itemName=AmazonWebServices.aws-toolkit-vscode

    Add a new connection using IAM credentials
    Add region us-west-1
