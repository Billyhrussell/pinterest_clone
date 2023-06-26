from csv import DictReader
from app import db
from models import User, Collections, Pins, Follows, CollectionsAndPins

db.drop_all()
db.create_all()

with open('generator/users.csv') as users:
    db.session.bulk_insert_mappings(User, DictReader(users))

with open('generator/collections.csv') as collections:
    db.session.bulk_insert_mappings(Collections, DictReader(collections))

with open('generator/pins.csv') as pins:
    db.session.bulk_insert_mappings(Pins, DictReader(pins))

with open('generator/follows.csv') as follows:
    db.session.bulk_insert_mappings(Follows, DictReader(follows))

# with open('generator/collectionsAndPins.csv') as collectionsAndPins:
#     db.session.bulk_insert_mappings(CollectionsAndPins, DictReader(collectionsAndPins))

db.session.commit()
