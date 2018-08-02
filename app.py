import datetime
from flask import Flask, request, render_template, flash, redirect, url_for
# from flask_babelex import Babel
from flask_sqlalchemy import SQLAlchemy
from flask_user import current_user, login_required, roles_required, UserManager, UserMixin
from passes.mail import MailData
from random import shuffle

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
    location = db.relationship('Restaurant_address', backref='restaurant')

class Restaurant_address(db.Model):
    __tablename__ = "restaurants_address"

    id = db.Column(db.Integer, primary_key=True)
    restaurant_id = db.Column(db.Integer, db.ForeignKey('restaurants.id'))
    country = db.Column(db.String(50))
    state = db.Column(db.String(50))
    city = db.Column(db.String(50))
    street_address = db.Column(db.String(50))
    lat = db.Column(db.Float)
    lon = db.Column(db.Float)


class MenuItem(db.Model):
    __tablename__ = 'menu_items'

    name = db.Column(db.String(80), nullable=False)
    id = db.Column(db.Integer, primary_key=True)
    description = db.Column(db.String(250))
    price = db.Column(db.String(8))
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

""" ROUTES """

""" main routes """

@app.route('/')
@app.route('/index')
def mainPage():
    restaurants = Restaurant.query.all()
    restaurants = [i for i in restaurants]
    shuffle(restaurants)

    return render_template("index.html", restaurants=restaurants[:9])



@app.route('/restaurants')
def restaurants():

    return render_template("restaurants.html")



@app.route("/_search_results", methods=['POST'])
def search_results():

    column = request.form['column'].lower()
    user_input = request.form['input'].lower()
    print("col: {}, input: {}".format(column, user_input))

    if user_input:
        # if user_input in ["edible"]:
        #     fungi = Fungus.query.filter_by(edible=True).all()
        # elif user_input in ["poisonous", "poisonus", "poison"]:
        #     fungi = Fungus.query.filter_by(edible=False).all()
        # else:
        restaurants = Restaurant.query.filter(Restaurant.name.like('%{}%'.format(user_input))).all()
    else:
        restaurants = Restaurant.query.all()


    return render_template("restaurants-search.html", restaurants=restaurants)



@app.route('/restaurants/<int:restaurant_id>')
def restaurantMenu(restaurant_id):
    restaurant = Restaurant.query.filter_by(id=restaurant_id).one()
    menu_items = MenuItem.query.filter_by(restaurant_id=restaurant_id).all()
    posts = Post.query.filter_by(restaurant_id=restaurant_id).all()

    rating_average=None
    if len(posts) > 0:
        rating_sum = 0
        for post in posts:
            rating_sum += post.rating
        rating_average = rating_sum / len(posts)

    return render_template("menu.html", restaurant=restaurant, restaurant_loc=restaurant.location[0], menu_items=menu_items, posts=posts, avg=rating_average)


""" restaurants routes """

@app.route('/restaurants/new', methods=['GET', 'POST'])
@login_required
def newRestaurant():

    if request.method == "POST":
        newRestaurant = Restaurant(name=request.form['restaurant_name'],
                                   description=request.form['restaurant_description'])
        db.session.add(newRestaurant)

        owner_role = Role.query.filter_by(name="Owner").one()
        current_user.roles.append(owner_role)
        current_user.authorization.append(newRestaurant)
        db.session.add(current_user)
        db.session.commit()

        flash("New restaurant: {} created!".format(newRestaurant.name))
        app.logger.info("Restaurant created: {}".format(newRestaurant.name))
        return redirect(url_for('restaurantMenu', restaurant_id=newRestaurant.id))

    return render_template("restaurant-new.html")

@app.route('/restaurants/<int:restaurant_id>/edit', methods=['GET', 'POST'])
@login_required
def editRestaurant(restaurant_id):
    editedRestaurant = Restaurant.query.filter_by(id=restaurant_id).one()

    if editedRestaurant in current_user.authorization:
        if request.method == "POST":
            editedRestaurant.name = request.form['restaurant_name'] if request.form[
                                                                           'restaurant_name'] != "" else editedRestaurant.name
            editedRestaurant.description = request.form['restaurant_description'] if request.form[
                                                                                         'restaurant_description'] != "" else editedRestaurant.description

            db.session.add(editedRestaurant)
            db.session.commit()
            flash("Restaurant successfully edited!")
            app.logger.info("Restaurant edited: {}".format(editedRestaurant.name))
            return redirect(url_for('restaurantMenu', restaurant_id=editedRestaurant.id))

        else:
            return render_template("restaurant-edit.html", restaurant=editedRestaurant)
    else:
        flash("You are not authorized to make changes in this area.")
        return redirect(url_for('restaurantMenu', restaurant_id=restaurant_id))



@app.route('/restaurants/<int:restaurant_id>/delete', methods=['GET', 'POST'])
@login_required
def deleteRestaurant(restaurant_id):
    toBeDeletedRestaurant = Restaurant.query.filter_by(id=restaurant_id).one()

    if toBeDeletedRestaurant in current_user.authorization:
        if request.method == "POST":
            if request.form['confirmation'] == "DELETE":
                db.session.delete(toBeDeletedRestaurant)
                db.session.commit()
                flash("Restaurant successfully deleted!")
                app.logger.info("Restaurant deleted: {}, {}".format(toBeDeletedRestaurant.id, toBeDeletedRestaurant.name))
                return redirect(url_for('mainPage'))
            else:
                flash("Wrong captcha - restaurant could not be deleted")
                return redirect(url_for('deleteRestaurant'))

        else:
            return render_template("restaurant-delete.html", restaurant=toBeDeletedRestaurant)

    else:
        flash("You are not authorized to make changes in this area.")
        return redirect(url_for('restaurantMenu', restaurant_id=restaurant_id))

""" menu item methods """

@app.route('/restaurants/<int:restaurant_id>/item/new', methods=['GET', 'POST'])
@login_required
def newMenuItem(restaurant_id):
    restaurant = Restaurant.query.filter_by(id=restaurant_id).one()

    if restaurant in current_user.authorization:
        if request.method == "POST":
            newItem = MenuItem(name=request.form['name'],
                                        description=request.form['description'],
                                        price=request.form['price'],
                                        course=request.form['course'],
                                        restaurant_id=restaurant.id)
            db.session.add(newItem)
            db.session.commit()
            flash("New menu item created!")
            app.logger.info("Item edited: {}, {}".format(newItem.name, newItem.description,  newItem.course, newItem.price))
            return redirect(url_for('restaurantMenu', restaurant_id=restaurant.id))

        else:
            return render_template("menuitem-new.html", restaurant=restaurant)

    else:
        flash("You are not authorized to make changes in this area.")
        return redirect(url_for('restaurantMenu', restaurant_id=restaurant_id))

@app.route('/restaurants/<int:restaurant_id>/item/<int:item_id>/edit', methods=['GET', 'POST'])
@login_required
def editMenuItem(restaurant_id, item_id):
    restaurant = Restaurant.query.filter_by(id=restaurant_id).one()
    editedItem = MenuItem.query.filter_by(id=item_id).one()

    if restaurant in current_user.authorization:
        if request.method == "POST":
            editedItem.name = request.form['name'] if request.form['name'] != "" else editedItem.name
            editedItem.description = request.form['description'] if request.form['description'] != "" else editedItem.description
            editedItem.price = request.form['price'] if request.form['price'] != "" else editedItem.price
            editedItem.course = request.form['course'] if request.form['course'] != "" else editedItem.course

            db.session.add(editedItem)
            db.session.commit()
            flash("Menu item successfully edited!")
            app.logger.info("Item edited: {}, {}".format(editedItem.name, editedItem.description, editedItem.course, editedItem.price))
            return redirect(url_for('restaurantMenu', restaurant_id=restaurant.id))

        else:
            return render_template("menuitem-edit.html", restaurant=restaurant, item=editedItem)

    else:
        flash("You are not authorized to make changes in this area.")
        return redirect(url_for('restaurantMenu', restaurant_id=restaurant_id))

@app.route('/restaurants/<int:restaurant_id>/item/<int:item_id>/delete', methods=['GET', 'POST'])
@login_required
def deleteMenuItem(restaurant_id, item_id):
    restaurant = Restaurant.query.filter_by(id=restaurant_id).one()
    toBeDeletedItem = MenuItem.query.filter_by(id=item_id).one()

    if restaurant in current_user.authorization:
        if request.method == "POST":
            if request.form['confirmation'] == "DELETE":
                db.session.delete(toBeDeletedItem)
                db.session.commit()
                flash("Menu item successfully erased!")
                app.logger.info("Item deleted: {}, {}".format(toBeDeletedItem.id, toBeDeletedItem.name))
            else:
                flash("Wrong captcha - restaurant could not be deleted")
            return redirect(url_for('restaurantMenu', restaurant_id=restaurant.id))

        else:
            return render_template("menuitem-delete.html", restaurant=restaurant, item=toBeDeletedItem)

    else:
        flash("You are not authorized to make changes in this area.")
        return redirect(url_for('restaurantMenu', restaurant_id=restaurant_id))





if __name__ == "__main__":
	app.run(host="0.0.0.0", port=5050, debug=True)