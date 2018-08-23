import datetime
from flask import Flask, request, render_template, flash, redirect, url_for
# from flask.ext.babel import Babel
from flask_sqlalchemy import SQLAlchemy
from flask_user import current_user, login_required, roles_required, UserManager, UserMixin
# to config
from passes.mail import MailData

# creating test db
import requests
import os
import json
from pprint import pprint
from random import randint
import datetime
from geopy.geocoders import Nominatim

import logging

logging.basicConfig(level=logging.DEBUG)



# Class-based application configuration
class ConfigClass(object):
    """ Flask application config """

    # Flask settings
    SECRET_KEY = 'This is an INSECURE secret!! DO NOT use this in production!!'

    # Flask-SQLAlchemy settings
    SQLALCHEMY_DATABASE_URI = 'sqlite:///db/online_menu.db'  # File-based SQL database
    SQLALCHEMY_TRACK_MODIFICATIONS = False  # Avoids SQLAlchemy warning

    # Flask-Mail SMTP server settings
    MAIL_SERVER = 'smtp.gmail.com'
    MAIL_PORT = 465
    MAIL_USE_SSL = True
    MAIL_USE_TLS = False
    MAIL_USERNAME = MailData.address
    MAIL_PASSWORD = MailData.password
    MAIL_DEFAULT_SENDER = '"Online Menu" <online.menu.071@gmail.com>'

    # Flask-User settings
    USER_APP_NAME = "Online Menu Test"  # Shown in and email templates and page footers
    USER_ENABLE_EMAIL = True  # Enable email authentication
    USER_ENABLE_USERNAME = False  # Disable username authentication
    USER_EMAIL_SENDER_NAME = USER_APP_NAME
    USER_EMAIL_SENDER_EMAIL = MailData.address

""" Flask application factory """

# Create Flask app load app.config
app = Flask(__name__)
app.config.from_object(__name__ + '.ConfigClass')

# Initialize Flask-BabelEx
# babel = Babel(app)

# Initialize Flask-SQLAlchemy
db = SQLAlchemy(app)

auths = db.Table('authorizations',
                 db.Column('user_id', db.Integer, db.ForeignKey("users.id")),
                 db.Column('restaurant_id', db.Integer, db.ForeignKey("restaurants.id")))

# Define the User data-model.
# NB: Make sure to add flask_user UserMixin !!!
class User(db.Model, UserMixin):
    __tablename__ = 'users'
    id = db.Column(db.Integer, primary_key=True)
    active = db.Column('is_active', db.Boolean(), nullable=False, server_default='1')

    # User authentication information. The collation='NOCASE' is required
    # to search case insensitively when USER_IFIND_MODE is 'nocase_collation'.
    email = db.Column(db.String(255, collation='NOCASE'), nullable=False, unique=True)
    email_confirmed_at = db.Column(db.DateTime())
    password = db.Column(db.String(255), nullable=False, server_default='')

    # User information
    user_name = db.Column(db.String(100, collation='NOCASE'), nullable=False, server_default='')
    first_name = db.Column(db.String(100, collation='NOCASE'), nullable=False, server_default='')
    last_name = db.Column(db.String(100, collation='NOCASE'), nullable=False, server_default='')

    # Define the relationship to Role via UserRoles
    roles = db.relationship('Role', secondary='user_roles')
    authorization = db.relationship("Restaurant", secondary=auths, backref=db.backref('authorizations', lazy="dynamic"))

# Define the Role data-model
class Role(db.Model):
    __tablename__ = 'roles'
    id = db.Column(db.Integer(), primary_key=True)
    name = db.Column(db.String(50), unique=True)

# Define the UserRoles association table
class UserRoles(db.Model):
    __tablename__ = 'user_roles'
    id = db.Column(db.Integer(), primary_key=True)
    user_id = db.Column(db.Integer(), db.ForeignKey('users.id', ondelete='CASCADE'))
    role_id = db.Column(db.Integer(), db.ForeignKey('roles.id', ondelete='CASCADE'))

class Restaurant(db.Model):
    __tablename__ = 'restaurants'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(250), nullable=False)
    description = db.Column(db.Text)
    eatstreet_id = db.Column(db.String(50))
    zomato_id = db.Column(db.String(50))
    location = db.relationship('Restaurant_address', backref='restaurant')
    tags = db.relationship('Tag', secondary='restaurant_tags')

class Restaurant_address(db.Model):
    __tablename__ = "restaurant_address"

    id = db.Column(db.Integer, primary_key=True)
    restaurant_id = db.Column(db.Integer, db.ForeignKey('restaurants.id'))
    country = db.Column(db.String(50))
    country_code = db.Column(db.String(10))
    state = db.Column(db.String(50))
    county = db.Column(db.String(50))
    city = db.Column(db.String(50))
    suburb = db.Column(db.String(50))
    neighbourhood = db.Column(db.String(50))
    street = db.Column(db.String(50))
    house_number = db.Column(db.String(20))
    postcode = db.Column(db.String(20))
    lat = db.Column(db.Float)
    lon = db.Column(db.Float)

# Define the Role data-model
class Tag(db.Model):
    __tablename__ = 'tags'
    id = db.Column(db.Integer(), primary_key=True)
    name = db.Column(db.String(50), unique=True)

# Define the UserRoles association table
class Restaurant_tags(db.Model):
    __tablename__ = 'restaurant_tags'
    id = db.Column(db.Integer(), primary_key=True)
    restaurant_id = db.Column(db.Integer(), db.ForeignKey('restaurants.id', ondelete='CASCADE'))
    tag_id = db.Column(db.Integer(), db.ForeignKey('tags.id', ondelete='CASCADE'))

class MenuItem(db.Model):
    __tablename__ = 'menu_items'

    name = db.Column(db.String(80), nullable=False)
    id = db.Column(db.Integer, primary_key=True)
    description = db.Column(db.String(250))
    price = db.Column(db.Float)
    course = db.Column(db.String(250))
    restaurant_id = db.Column(db.Integer, db.ForeignKey('restaurants.id'))
    restaurant = db.relationship(Restaurant)


class Post(db.Model):
    __tablename__ = 'posts'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer(), db.ForeignKey('users.id', ondelete='CASCADE'))
    user = db.relationship(User)
    restaurant_id = db.Column(db.Integer, db.ForeignKey('restaurants.id', ondelete='CASCADE'))
    restaurant = db.relationship(Restaurant)
    content = db.Column(db.Text)
    rating = db.Column(db.Integer())
    posted_at = db.Column(db.DateTime())


user_manager = UserManager(app, db, User)

def create_basic_users():
    if not Role.query.filter(Role.name == 'Admin').first():
        admin_role = Role(name='Admin')
        db.session.add(admin_role)
        db.session.commit()

    if not Role.query.filter(Role.name == 'Owner').first():
        owner_role = Role(name="Owner")
        db.session.add(owner_role)
        db.session.commit()


    # Create 'admin@example.com' user with 'Admin' and 'Agent' roles
    if not User.query.filter(User.email == 'admin@example.com').first():
        user1 = User(
            email='admin@example.com',
            email_confirmed_at=datetime.datetime.utcnow(),
            password=user_manager.hash_password('Password1'),
        )
        user1.roles.append(admin_role)
        db.session.add(user1)
        db.session.commit()


    # Create 'member@example.com' user with no roles
    if not User.query.filter(User.email == 'member@example.com').first():
        user2 = User(
            email='member@example.com',
            email_confirmed_at=datetime.datetime.utcnow(),
            password=user_manager.hash_password('Password1'),
        )
        db.session.add(user2)
        db.session.commit()

def get_value(dict, key):
    value = dict[key] if key in dict.keys() else ""
    return value

def create_test_db(path="_external_APIs/data/restaurants/"):
    temp_incrementation = 0


    for file in os.listdir(path):
        logging.info("Preparing to extract data from: {}".format(file))

        with open(path + file) as fp:
            restaurant_data = json.load(fp)

        # pprint(restaurant_data)

        # Restaurant class input
        name = restaurant_data["name"]
        eatstreet_id = restaurant_data["apiKey"]
        if "zomato_id" in restaurant_data.keys():
            zomato_id = restaurant_data["zomato_id"]
        else:
            zomato_id = ""
        restaurant = Restaurant(name=name,
                                eatstreet_id=eatstreet_id,
                                zomato_id=zomato_id)
        db.session.add(restaurant)
        db.session.commit()

        # address input
        location_data = restaurant_data["full_location"]
        restaurant_location = Restaurant_address(restaurant=restaurant,
                                                 country= get_value(dict=location_data, key="country"),
                                                 country_code = get_value(dict=location_data, key="country_code"),
                                                 state = get_value(dict=location_data, key="state"),
                                                 county = get_value(dict=location_data, key="county"),
                                                 city = restaurant_data["city"],
                                                 suburb = get_value(dict=location_data, key="suburb"),
                                                 neighbourhood = get_value(dict=location_data, key="neighbourhood"),
                                                 street = get_value(dict=location_data, key="road"),
                                                 house_number = get_value(dict=location_data, key="house_number"),
                                                 postcode = get_value(dict=location_data, key="postcode"),
                                                 lat=restaurant_data["latitude"],
                                                 lon=restaurant_data["longitude"]
                                                 )
        db.session.add(restaurant_location)
        db.session.commit()

        # Tags input
        for e in restaurant_data["foodTypes"]:
            if not Tag.query.filter(Tag.name == e).first():
                tag = Tag(name=e)
            else:
                tag = Tag.query.filter(Tag.name == e).first()
            restaurant.tags.append(tag)
            db.session.add(restaurant)
            db.session.commit()

        # adding menu items
        for e in restaurant_data["menu"]:
            n = 0
            limit = randint(2, 5)
            course = e["name"]
            for item in e["items"]:
                name = item["name"]
                price = item["basePrice"]
                if "description" in item.keys():
                    description = item["description"]
                else:
                    description = ""
                menu_item = MenuItem(name=name,
                                     description=description,
                                     price=price,
                                     course=course,
                                     restaurant=restaurant)
                db.session.add(menu_item)
                db.session.commit()
                n += 1
                if n >= limit:
                    break

        if "reviews" in restaurant_data.keys():
            logging.info("gathering reviews from: {}".format(restaurant_data["name"]))
            for e in restaurant_data["reviews"]:
                user = e["review"]["user"]["name"]
                if not User.query.filter(User.user_name == user).first():
                    user = User(
                        user_name=user,
                        email='fake_member_{}@example.com'.format(temp_incrementation),
                        email_confirmed_at=datetime.datetime.utcnow(),
                        password=user_manager.hash_password('Password1')
                    )
                    temp_incrementation += 1
                else:
                    user = User.query.filter(User.user_name == user).first()
                content = e["review"]["review_text"]
                rating = e["review"]["rating"] if type(e["review"]["review_text"]) == int and e["review"]["review_text"] > 0 else randint(1,5)
                posted_at = datetime.datetime.utcfromtimestamp(e["review"]["timestamp"])

                post = Post(content=content,
                            rating=rating,
                            posted_at=posted_at,
                            user=user,
                            restaurant=restaurant)
                db.session.add(post)
                db.session.commit()
        else:
            continue




if __name__ == "__main__":
    # Create all database tables
    db.create_all()

    create_basic_users()
    create_test_db()



