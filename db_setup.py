import datetime
from flask import Flask, request, render_template, flash, redirect, url_for
# from flask.ext.babel import Babel
from flask_sqlalchemy import SQLAlchemy
from flask_user import current_user, login_required, roles_required, UserManager, UserMixin
# to config
from passes.mail import MailData


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

class Restaurant_address(db.Model):
    __tablename__ = "restaurants_address"

    id = db.Column(db.Integer, primary_key=True)
    restaurant_id = db.Column(db.Integer, db.ForeignKey('restaurants.id'))
    restaurant = db.relationship(Restaurant)
    country = db.Column(db.String(50))
    state = db.Column(db.String(50))
    city = db.Column(db.String(50))
    street_address = db.Column(db.String(50))
    lon = db.Column(db.Float)
    lat = db.Column(db.Float)

class MenuItem(db.Model):
    __tablename__ = 'menu_items'

    name = db.Column(db.String(80), nullable=False)
    id = db.Column(db.Integer, primary_key=True)
    description = db.Column(db.String(250))
    price = db.Column(db.String(8))
    course = db.Column(db.String(250))
    restaurant_id = db.Column(db.Integer, db.ForeignKey('restaurants.id'))
    restaurant = db.relationship(Restaurant)

user_manager = UserManager(app, db, User)



if __name__ == "__main__":
    # Create all database tables
    db.create_all()

    admin_role = Role(name='Admin')
    owner_role = Role(name="Owner")
    db.session.add(admin_role)
    db.session.add(owner_role)
    db.session.commit()


    # Create 'admin@example.com' user with 'Admin' and 'Agent' roles
    if not User.query.filter(User.email == 'admin@example.com').first():
        user = User(
            email='admin@example.com',
            email_confirmed_at=datetime.datetime.utcnow(),
            password=user_manager.hash_password('Password1'),
        )
        user.roles.append(admin_role)
        db.session.add(user)
        db.session.commit()


    # Create 'member@example.com' user with no roles
    if not User.query.filter(User.email == 'member@example.com').first():
        user = User(
            email='member@example.com',
            email_confirmed_at=datetime.datetime.utcnow(),
            password=user_manager.hash_password('Password1'),
        )
        db.session.add(user)
        db.session.commit()

    # Menu for UrbanBurger
    restaurant1 = Restaurant(name="Urban Burger")

    db.session.add(restaurant1)
    db.session.commit()

    menuItem2 = MenuItem(name="Veggie Burger", description="Juicy grilled veggie patty with tomato mayo and lettuce",
                         price="$7.50", course="Entree", restaurant=restaurant1)

    db.session.add(menuItem2)
    db.session.commit()

    menuItem1 = MenuItem(name="French Fries", description="with garlic and parmesan", price="$2.99", course="Appetizer",
                         restaurant=restaurant1)

    db.session.add(menuItem1)
    db.session.commit()

    menuItem2 = MenuItem(name="Chicken Burger", description="Juicy grilled chicken patty with tomato mayo and lettuce",
                         price="$5.50", course="Entree", restaurant=restaurant1)

    db.session.add(menuItem2)
    db.session.commit()

    menuItem3 = MenuItem(name="Chocolate Cake", description="fresh baked and served with ice cream", price="$3.99",
                         course="Dessert", restaurant=restaurant1)

    db.session.add(menuItem3)
    db.session.commit()

    menuItem4 = MenuItem(name="Sirloin Burger", description="Made with grade A beef", price="$7.99", course="Entree",
                         restaurant=restaurant1)

    db.session.add(menuItem4)
    db.session.commit()

    menuItem5 = MenuItem(name="Root Beer", description="16oz of refreshing goodness", price="$1.99", course="Beverage",
                         restaurant=restaurant1)

    db.session.add(menuItem5)
    db.session.commit()

    menuItem6 = MenuItem(name="Iced Tea", description="with Lemon", price="$.99", course="Beverage",
                         restaurant=restaurant1)

    db.session.add(menuItem6)
    db.session.commit()

    menuItem7 = MenuItem(name="Grilled Cheese Sandwich", description="On texas toast with American Cheese",
                         price="$3.49", course="Entree", restaurant=restaurant1)

    db.session.add(menuItem7)
    db.session.commit()

    menuItem8 = MenuItem(name="Veggie Burger", description="Made with freshest of ingredients and home grown spices",
                         price="$5.99", course="Entree", restaurant=restaurant1)

    db.session.add(menuItem8)
    db.session.commit()

    # Menu for Super Stir Fry
    restaurant2 = Restaurant(name="Super Stir Fry")

    db.session.add(restaurant2)
    db.session.commit()

    menuItem1 = MenuItem(name="Chicken Stir Fry", description="With your choice of noodles vegetables and sauces",
                         price="$7.99", course="Entree", restaurant=restaurant2)

    db.session.add(menuItem1)
    db.session.commit()

    menuItem2 = MenuItem(name="Peking Duck",
                         description=" A famous duck dish from Beijing[1] that has been prepared since the imperial era. The meat is prized for its thin, crisp skin, with authentic versions of the dish serving mostly the skin and little meat, sliced in front of the diners by the cook",
                         price="$25", course="Entree", restaurant=restaurant2)

    db.session.add(menuItem2)
    db.session.commit()

    menuItem3 = MenuItem(name="Spicy Tuna Roll",
                         description="Seared rare ahi, avocado, edamame, cucumber with wasabi soy sauce ", price="15",
                         course="Entree", restaurant=restaurant2)

    db.session.add(menuItem3)
    db.session.commit()

    menuItem4 = MenuItem(name="Nepali Momo ", description="Steamed dumplings made with vegetables, spices and meat. ",
                         price="12", course="Entree", restaurant=restaurant2)

    db.session.add(menuItem4)
    db.session.commit()

    menuItem5 = MenuItem(name="Beef Noodle Soup",
                         description="A Chinese noodle soup made of stewed or red braised beef, beef broth, vegetables and Chinese noodles.",
                         price="14", course="Entree", restaurant=restaurant2)

    db.session.add(menuItem5)
    db.session.commit()

    menuItem6 = MenuItem(name="Ramen",
                         description="a Japanese noodle soup dish. It consists of Chinese-style wheat noodles served in a meat- or (occasionally) fish-based broth, often flavored with soy sauce or miso, and uses toppings such as sliced pork, dried seaweed, kamaboko, and green onions.",
                         price="12", course="Entree", restaurant=restaurant2)

    db.session.add(menuItem6)
    db.session.commit()