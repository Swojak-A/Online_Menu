import datetime
from flask import Flask, request, render_template, flash, redirect, url_for, jsonify, make_response
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
    img_main = db.Column(db.String(50))
    img_thumb = db.Column(db.String(50))

class Restaurant_address(db.Model):
    __tablename__ = "restaurant_address"

    id = db.Column(db.Integer, primary_key=True)
    restaurant_id = db.Column(db.Integer, db.ForeignKey('restaurants.id'))
    country = db.Column(db.String(50))
    country_code = db.Column(db.String(10))
    state = db.Column(db.String(50))
    state_short = db.Column(db.String(10))
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

""" ROUTES """

""" main routes """

@app.route('/')
@app.route('/index')
def mainPage():
    restaurants = Restaurant.query.all()
    restaurants = [i for i in restaurants]
    shuffle(restaurants)

    query = db.session.query(Restaurant_address.city.distinct().label("city"))
    prompt_cities = [row.city for row in query.limit(3)]

    return render_template("index.html", restaurants=restaurants[:9], prompt_cities=prompt_cities)



@app.route('/restaurants')
def restaurants():
    location = request.args.get('location')
    user_input = request.args.get('input')

    location = "" if location == None else location
    user_input = "" if user_input == None else user_input

    app.logger.info("User search in restaurants using parameters: location = {}, input = {}".format(location, user_input))

    query = db.session.query(Restaurant_address.city.distinct().label("city"))
    prompt_cities = [row.city for row in query.limit(3)]

    tags = Tag.query.limit(60)
    tags = [i for i in tags]
    shuffle(tags)

    places = []
    query = db.session.query(Restaurant_address.city.distinct().label("place"))
    for row in query.limit(30):
        if row.place != "":
            places.append(row.place)
    if len(places) < 30:
        query = db.session.query(Restaurant_address.suburb.distinct().label("place"))
        for row in query.limit(30 - len(places)):
            if row.place != "":
                places.append(row.place)
        if len(places) < 30:
            query = db.session.query(Restaurant_address.neighbourhood.distinct().label("place"))
            for row in query.limit(30 - len(places)):
                if row.place != "":
                    places.append(row.place)
            if len(places) < 30:
                query = db.session.query(Restaurant_address.street.distinct().label("place"))
                for row in query.limit(30 - len(places)):
                    if row.place != "":
                        places.append(row.place)
                if len(places) < 30:
                    query = db.session.query(Restaurant_address.state.distinct().label("place"))
                    for row in query.limit(30 - len(places)):
                        if row.place != "":
                            places.append(row.place)

    return render_template("restaurants.html", location=location, user_input=user_input, prompt_cities=prompt_cities, tags=tags[:30], places=places)



@app.route("/_search_results", methods=['GET', 'POST'])
def search_results():

    page = request.args.get('page')
    page = 1 if page == None else int(page)

    location = request.form['location'].lower()
    user_input = request.form['input'].lower()
    app.logger.info("User search in _search_results using parameters: location = {}, input = {}".format(location, user_input))

    if user_input:
        if "tag" in user_input:
            if ":" in user_input:
                separator = ":"
            else:
                separator = " "
            user_input = " ".join(user_input.split(separator)[1:]).lstrip()
            print(user_input)
            restaurants = Restaurant.query.filter(Restaurant.location.any(Restaurant_address.country.like("%{}%".format(location))) \
                                                  | Restaurant.location.any(Restaurant_address.state.like("%{}%".format(location))) \
                                                  | Restaurant.location.any(Restaurant_address.county.like("%{}%".format(location))) \
                                                  | Restaurant.location.any(Restaurant_address.city.like("%{}%".format(location))) \
                                                  | Restaurant.location.any(Restaurant_address.suburb.like("%{}%".format(location))) \
                                                  | Restaurant.location.any(Restaurant_address.neighbourhood.like("%{}%".format(location))) \
                                                  | Restaurant.location.any(Restaurant_address.street.like("%{}%".format(location))) \
                                                  | Restaurant.location.any(Restaurant_address.postcode.like("%{}%".format(location))) \
                                                  , Restaurant.tags.any(Tag.name.like("%{}%".format(user_input)))
                                                  ).paginate(page=page, per_page=5)
        elif "name" in user_input:
            if ":" in user_input:
                separator = ":"
            else:
                separator = " "
            user_input = " ".join(user_input.split(separator)[1:]).lstrip()
            print(user_input)
            restaurants = Restaurant.query.filter(Restaurant.location.any(Restaurant_address.country.like("%{}%".format(location))) \
                                                  | Restaurant.location.any(Restaurant_address.state.like("%{}%".format(location))) \
                                                  | Restaurant.location.any(Restaurant_address.county.like("%{}%".format(location))) \
                                                  | Restaurant.location.any(Restaurant_address.city.like("%{}%".format(location))) \
                                                  | Restaurant.location.any(Restaurant_address.suburb.like("%{}%".format(location))) \
                                                  | Restaurant.location.any(Restaurant_address.neighbourhood.like("%{}%".format(location))) \
                                                  | Restaurant.location.any(Restaurant_address.street.like("%{}%".format(location))) \
                                                  | Restaurant.location.any(Restaurant_address.postcode.like("%{}%".format(location))) \
                                                  , Restaurant.name.like("%{}%".format(user_input))
                                                  ).paginate(page=page, per_page=5)
        else:
            restaurants = Restaurant.query.filter(Restaurant.location.any(Restaurant_address.country.like("%{}%".format(location))) \
                                                  | Restaurant.location.any(Restaurant_address.state.like("%{}%".format(location))) \
                                                  | Restaurant.location.any(Restaurant_address.county.like("%{}%".format(location))) \
                                                  | Restaurant.location.any(Restaurant_address.city.like("%{}%".format(location))) \
                                                  | Restaurant.location.any(Restaurant_address.suburb.like("%{}%".format(location))) \
                                                  | Restaurant.location.any(Restaurant_address.neighbourhood.like("%{}%".format(location))) \
                                                  | Restaurant.location.any(Restaurant_address.street.like("%{}%".format(location))) \
                                                  | Restaurant.location.any(Restaurant_address.postcode.like("%{}%".format(location))) \
                                                  , Restaurant.name.like("%{}%".format(user_input)) \
                                                  | Restaurant.tags.any(Tag.name.like("%{}%".format(user_input)))
                                                  ).paginate(page=page, per_page=5)
    else:
        restaurants = Restaurant.query.filter(Restaurant.location.any(Restaurant_address.country.like("%{}%".format(location))) \
                                                  | Restaurant.location.any(Restaurant_address.state.like("%{}%".format(location))) \
                                                  | Restaurant.location.any(Restaurant_address.county.like("%{}%".format(location))) \
                                                  | Restaurant.location.any(Restaurant_address.city.like("%{}%".format(location))) \
                                                  | Restaurant.location.any(Restaurant_address.suburb.like("%{}%".format(location))) \
                                                  | Restaurant.location.any(Restaurant_address.neighbourhood.like("%{}%".format(location))) \
                                                  | Restaurant.location.any(Restaurant_address.street.like("%{}%".format(location))) \
                                                  | Restaurant.location.any(Restaurant_address.postcode.like("%{}%".format(location))) \
                                                  ).paginate(page=page, per_page=5)

    return render_template("restaurants-search.html", restaurants=restaurants)



@app.route('/restaurants/<int:restaurant_id>', methods=['GET', 'POST'])
def restaurantMenu(restaurant_id):
    restaurant = Restaurant.query.filter_by(id=restaurant_id).one()
    menu_items = MenuItem.query.filter_by(restaurant_id=restaurant_id).all()
    courses = []
    for item in menu_items:
        item.price = format(item.price, '.2f')
        if item.course not in courses:
            courses.append(item.course)
    posts = Post.query.filter_by(restaurant_id=restaurant_id).limit(4).all()

    if request.cookies.get('unfinished_rating_{}'.format(restaurant_id)):
        unfinished_rating = int(request.cookies.get('unfinished_rating_{}'.format(restaurant_id)))
        unfinished_comment = request.cookies.get('unfinished_comment_{}'.format(restaurant_id))
        unfinished_post = {"unfinished_rating": unfinished_rating, "unfinished_comment": unfinished_comment}
    else:
        unfinished_post = {}

    rating_average=None
    if len(posts) > 0:
        rating_sum = 0
        for post in posts:
            rating_sum += post.rating
        rating_average = rating_sum / len(posts)

    if request.method == 'POST':
        if current_user.is_authenticated:
            newPost = Post(content=request.form['post-content'],
                           rating=request.form['rating-value'],
                           posted_at=datetime.datetime.utcnow(),
                           user=current_user,
                           restaurant=restaurant)

            db.session.add(newPost)
            db.session.commit()

            flash("Your comment was successfully submitted!")
            app.logger.info("New post added to database")

            response = make_response(redirect(url_for('restaurantMenu', restaurant_id=restaurant_id)))
            response.set_cookie('unfinished_rating_{}'.format(restaurant_id), "", max_age=15, expires=0)
            response.set_cookie('unfinished_comment_{}'.format(restaurant_id), "", max_age=15, expires=0)

            return response

        else:
            unfinished_rating = request.form['rating-value']
            unfinished_comment = request.form['post-content']

            response = make_response(app.login_manager.unauthorized())
            response.set_cookie('unfinished_rating_{}'.format(restaurant_id), unfinished_rating)
            response.set_cookie('unfinished_comment_{}'.format(restaurant_id), unfinished_comment)

            return response

    return render_template("menu.html", restaurant=restaurant, menu_items=menu_items, courses=courses, posts=posts, avg=rating_average, **unfinished_post)

@app.route('/_more-posts', methods=['GET', 'POST'])
def morePosts():

    comments_count = request.args.get('comments')
    restaurant_id = request.args.get('restaurant')

    comments_count = int(comments_count)
    last_post = int(comments_count + 4)

    posts = Post.query.filter_by(restaurant_id=restaurant_id).slice(comments_count, last_post).all()

    # return jsonify({'result' : "AJAX call successfull"})
    return render_template("menu-comments.html", posts=posts)



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