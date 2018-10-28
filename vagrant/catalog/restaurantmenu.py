from flask import Flask, render_template, request, redirect, jsonify, \
    url_for, flash, make_response
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from database_setup import Base, Restaurant, MenuItem, User

# Login session imports
from flask import session as login_session
import random
import string

# Gconnect imports
from oauth2client.client import flow_from_clientsecrets
from oauth2client.client import FlowExchangeError
import json
import httplib2
import requests


app = Flask(__name__)

# Google client_id
CLIENT_ID = json.loads(
    open('client_secrets.json', 'r').read())['web']['client_id']
APPLICATION_NAME = "Restaurant Menu Application"

# Connect to database
engine = create_engine('sqlite:///restaurantmenu.db?check_same_thread=False')
Base.metadata.bind = engine

# Create session
DBSession = sessionmaker(bind=engine)
session = DBSession()


# Create anti-forgery state token
@app.route('/login')
def showLogin():
    state = ''.join(random.choice(
        string.ascii_uppercase + string.digits) for x in xrange(32))
    login_session['state'] = state
    return render_template('login.html', STATE=state)


# GConnect
@app.route('/gconnect', methods=['POST'])
def gconnect():
    # Validate state token
    if request.args.get('state') != login_session['state']:
        response = make_response(json.dumps('Invalid state parameter.'), 401)
        response.headers['Content-Type'] = 'application/json'
        return response
    # Obtain authorization code
    code = request.data

    try:
        # Upgrade the authorization code into a credentials object
        oauth_flow = flow_from_clientsecrets('client_secrets.json', scope='')
        oauth_flow.redirect_uri = 'postmessage'
        credentials = oauth_flow.step2_exchange(code)
    except FlowExchangeError:
        response = make_response(
            json.dumps('Failed to upgrade the authorization code.'), 401)
        response.headers['Content-Type'] = 'application/json'
        return response

    # Check that the access token is valid.
    access_token = credentials.access_token
    url = (
        'https://www.googleapis.com/oauth2/v1/tokeninfo?access_token=%s'
        % access_token)
    h = httplib2.Http()
    result = json.loads(h.request(url, 'GET')[1])
    # If there was an error in the access token info, abort.
    if result.get('error') is not None:
        response = make_response(json.dumps(result.get('error')), 500)
        response.headers['Content-Type'] = 'application/json'
        return response

    # Verify that the access token is used for the intended user.
    gplus_id = credentials.id_token['sub']
    if result['user_id'] != gplus_id:
        response = make_response(
            json.dumps("Token's user ID doesn't match given user ID."), 401)
        response.headers['Content-Type'] = 'application/json'
        return response

    # Verify that the access token is valid for this app.
    if result['issued_to'] != CLIENT_ID:
        response = make_response(
            json.dumps("Token's client ID does not match app's."), 401)
        print "Token's client ID does not match app's."
        response.headers['Content-Type'] = 'application/json'
        return response

    stored_access_token = login_session.get('access_token')
    stored_gplus_id = login_session.get('gplus_id')
    if stored_access_token is not None and gplus_id == stored_gplus_id:
        response = make_response(
            json.dumps('Current user is already connected.'), 200)
        response.headers['Content-Type'] = 'application/json'
        return response

    # Store the access token in the session for later use.
    login_session['access_token'] = access_token
    login_session['gplus_id'] = gplus_id

    # Get user info
    userinfo_url = "https://www.googleapis.com/oauth2/v1/userinfo"
    params = {'access_token': access_token, 'alt': 'json'}
    answer = requests.get(userinfo_url, params=params)

    data = answer.json()

    login_session['username'] = data['name']
    login_session['picture'] = data['picture']
    login_session['email'] = data['email']

    # ADD PROVIDER TO LOGIN SESSION
    login_session['provider'] = 'google'

    # see if user exists, if it doesn't make a new one
    user_id = getUserID(login_session['email'])
    if not user_id:
        user_id = createUser(login_session)
    login_session['user_id'] = user_id

    output = ''
    output += '<h1>Welcome, '
    output += login_session['username']
    output += '!</h1>'
    output += '<img src="'
    output += login_session['picture']
    output += ' " style = "width: 300px; height: 300px;"> '
    flash("You are now logged in as %s" % login_session['username'])
    return output


# User Helper Functions
def createUser(login_session):
    newUser = User(name=login_session['username'], email=login_session[
        'email'], picture=login_session['picture'])
    session.add(newUser)
    session.commit()
    user = session.query(User).filter_by(
        email=login_session['email']).one_or_none()
    return user.id


def getUserInfo(user_id):
    user = session.query(User).filter_by(id=user_id).one_or_none()
    return user


def getUserID(email):
    try:
        user = session.query(User).filter_by(email=email).one_or_none()
        return user.id
    except:
        return None


# DISCONNECT - Revoke a current user's token and reset their login_session
@app.route('/gdisconnect')
def gdisconnect():
    # Only disconnect a connected user.
    access_token = login_session.get('access_token')
    if access_token is None:
        response = make_response(json.dumps(
            'Current user not connected.'), 401)
        response.headers['Content-Type'] = 'application/json'
        return response
    url = 'https://accounts.google.com/o/oauth2/revoke?token=%s' % access_token
    h = httplib2.Http()
    result = h.request(url, 'GET')[0]
    if result['status'] == '200':
        # Reset the user's sesson.
        del login_session['access_token']
        del login_session['gplus_id']
        del login_session['username']
        del login_session['email']
        del login_session['picture']
        del login_session['user_id']
        response = redirect(url_for('showRestaurants'))
        flash("You have successfully logged out.")
        return response
    else:
        # For whatever reason, the given token was invalid.
        response = make_response(
            json.dumps('Failed to revoke token for given user.', 400))
        response.headers['Content-Type'] = 'application/json'
        return response


# View JSON information
@app.route('/restaurants/<int:restaurant_id>/menu/JSON')
def showMenuJSON(restaurant_id):
    restaurant = session.query(Restaurant).filter_by(
        id=restaurant_id).one_or_none()
    items = session.query(MenuItem).filter_by(
        restaurant_id=restaurant_id).all()
    return jsonify(MenuItems=[i.serialize for i in items])


@app.route('/restaurants/<int:restaurant_id>/menu/<int:menu_id>/JSON')
def menuItemJSON(restaurant_id, menu_id):
    menuItem = session.query(MenuItem).filter_by(id=menu_id).one_or_none()
    return jsonify(MenuItem=menuItem.serialize)


@app.route('/restaurants/JSON')
def restaurantsJSON():
    restaurants = session.query(Restaurant).all()
    return jsonify(restaurants=[r.serialize for r in restaurants])


# Show all restaurants
@app.route('/')
@app.route('/restaurants/')
def showRestaurants():
    restaurants = session.query(Restaurant).all()
    return render_template('restaurants.html', restaurants=restaurants)


# Create a new restaurant
@app.route('/restaurants/new/', methods=['GET', 'POST'])
def newRestaurant():
    if 'username' not in login_session:
        return redirect('/login')
    if request.method == 'POST':
        addRestaurant = Restaurant(
            name=request.form['name'],
            user_id=login_session['user_id'])
        session.add(addRestaurant)
        session.commit()
        return redirect(url_for('showRestaurants'))
    else:
        return render_template('newRestaurant.html')


# Edit a restaurant
@app.route('/restaurants/<int:restaurant_id>/edit/', methods=['GET', 'POST'])
def editRestaurant(restaurant_id):
    if 'username' not in login_session:
        return redirect('/login')
    edRestaurant = session.query(Restaurant).filter_by(
        id=restaurant_id).one_or_none()
    if edRestaurant.user_id != login_session['user_id']:
        flash(
            'You must be the creator of %s restaurant to Edit.'
            % edRestaurant.name)
        return redirect(url_for('showRestaurants'))
    if request.method == 'POST':
        if request.form['name']:
            edRestaurant.name = request.form['name']
            flash(
                'Restaurant name successfully updated to %s'
                % edRestaurant.name)
            return redirect(url_for('showRestaurants'))
    else:
        return render_template('editRestaurant.html', restaurant=edRestaurant)


# Delete a restaurant
@app.route('/restaurants/<int:restaurant_id>/delete/', methods=['GET', 'POST'])
def deleteRestaurant(restaurant_id):
    delRestaurant = session.query(Restaurant).filter_by(
        id=restaurant_id).one_or_none()
    if 'username' not in login_session:
        return redirect('/login')
    if delRestaurant.user_id != login_session['user_id']:
        flash(
            'You must be the creator of %s restaurant to Delete.'
            % delRestaurant.name)
        return redirect(url_for('showRestaurants'))
    if request.method == 'POST':
        session.delete(delRestaurant)
        flash('%s has been successfully deleted.' % delRestaurant.name)
        session.commit()
        return redirect(url_for('showRestaurants'))
    else:
        return render_template(
            'deleteRestaurant.html', restaurant=delRestaurant)


# Show the restaurant menu
@app.route('/restaurants/<int:restaurant_id>/')
@app.route('/restaurants/<int:restaurant_id>/menu/')
def showMenu(restaurant_id):
    restaurant = session.query(Restaurant).filter_by(
        id=restaurant_id).one_or_none()
    items = session.query(MenuItem).filter_by(
        restaurant_id=restaurant_id).all()
    return render_template('menu.html', restaurant=restaurant, items=items)


# Create a new restaurant menu item
@app.route(
    '/restaurants/<int:restaurant_id>/menu/new/',
    methods=['GET', 'POST'])
def newMenuItem(restaurant_id):
    restaurant = session.query(Restaurant).filter_by(
        id=restaurant_id).one_or_none()
    if 'username' not in login_session:
        return redirect('/login')
    if request.method == 'POST':
        addMenuItem = MenuItem(
            name=request.form['name'], description=request.form['description'],
            price=request.form['price'], course=request.form['course'],
            restaurant_id=restaurant_id, user_id=login_session['user_id'])
        session.add(addMenuItem)
        session.commit()
        flash('%s has been added to the current menu.' % addMenuItem.name)
        return redirect(url_for('showMenu', restaurant_id=restaurant_id))
    else:
        return render_template(
            'newMenuItem.html', restaurant_id=restaurant_id,
            restaurant=restaurant)
    return render_template('newMenuItem.html', restaurant=restaurant)


# Edit a restaurant menu item
@app.route(
    '/restaurants/<int:restaurant_id>/<int:menu_id>/edit/',
    methods=['GET', 'POST'])
def editMenuItem(restaurant_id, menu_id):
    if 'username' not in login_session:
        return redirect('/login')
    restaurant = session.query(Restaurant).filter_by(
        id=restaurant_id).one_or_none()
    edMenuItem = session.query(MenuItem).filter_by(id=menu_id).one_or_none()
    if edMenuItem.user_id != login_session['user_id']:
        flash(
            'You must be the creator of the %s menu item to Edit.'
            % edMenuItem.name)
        return redirect(url_for('showMenu', restaurant_id=restaurant_id))
    if request.method == 'POST':
        if request.form['name']:
            edMenuItem.name = request.form['name']
        if request.form['description']:
            edMenuItem.description = request.form['description']
        if request.form['price']:
            edMenuItem.price = request.form['price']
        if request.form['course']:
            edMenuItem.course = request.form['course']
        session.add(edMenuItem)
        session.commit()
        flash('%s has been successfully updated.' % edMenuItem.name)
        return redirect(url_for('showMenu', restaurant_id=restaurant_id))
    else:
        return render_template(
            'editMenuItem.html', restaurant=restaurant,
            restaurant_id=restaurant_id, menu_id=menu_id, item=edMenuItem)


# Delete a restaurant menu item
@app.route(
    '/restaurants/<int:restaurant_id>/<int:menu_id>/delete/',
    methods=['GET', 'POST'])
def deleteMenuItem(restaurant_id, menu_id):
    if 'username' not in login_session:
        return redirect('/login')
    restaurant = session.query(Restaurant).filter_by(
        id=restaurant_id).one_or_none()
    delMenuItem = session.query(MenuItem).filter_by(id=menu_id).one_or_none()
    if delMenuItem.user_id != login_session['user_id']:
        flash(
            'You must be the creator of the %s menu item to Delete.'
            % delMenuItem.name)
        return redirect(url_for('showMenu', restaurant_id=restaurant_id))
    if request.method == 'POST':
        session.delete(delMenuItem)
        session.commit()
        flash(
            '%s has been successfully removed from the menu.'
            % delMenuItem.name)
        return redirect(url_for('showMenu', restaurant_id=restaurant_id))
    else:
        return render_template(
            'deleteMenuItem.html', item=delMenuItem, restaurant=restaurant)


if __name__ == '__main__':
    app.secret_key = 'super_secret_key'
    app.debug = True
    app.run(host='0.0.0.0', port=5000)
