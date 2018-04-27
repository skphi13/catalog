from flask import Flask, render_template, request, redirect, jsonify, url_for, flash
from flask import session as login_session
from functools import wraps
import random
import string
app = Flask(__name__)

from sqlalchemy import asc, desc
from sqlalchemy.orm import sessionmaker

from database_setup_catalog import Base, User, Genre, MovieTitle, engine
import database_setup_catalog as db

import time

from oauth2client.client import flow_from_clientsecrets
from oauth2client.client import FlowExchangeError
import httplib2
import json
from flask import make_response
import requests

Base.metadata.bind = engine
DBSession = sessionmaker(bind=engine)
session = DBSession()

CLIENT_ID = json.loads(open('client_secrets.json', 'r').read())['web']['client_id']
APPLICATION_NAME = 'Item Catalog'


def login_required(function):
    @wraps(function)
    def decorated_function(*args, **kwargs):
        if 'username' not in login_session:
            return redirect(url_for('show_login'))
        return function(*args, **kwargs)
    return decorated_function


@app.route('/')
@app.route('/genre')
def main_page():
    """Main page. Show diffrent type of movies."""
    genres = db.get_all_genres()
    titles = session.query(MovieTitle).order_by(desc(MovieTitle.id)).limit(10)

    return render_template(
        'latest_titles.html',
        genres=genres,
        titles=titles
        )


@app.route('/genre/<int:genre_id>/')
def show_genre(genre_id):
    """Specific genre page.  Shows all movies."""
    genres = db.get_all_genres()
    gen = db.get_gen(genre_id)
    titles = session.query(MovieTitle).filter_by(genre_id=gen.id).order_by(asc(MovieTitle.name))
    return render_template(
        'genre.html',
        genres=genres,
        genre=gen,
        titles=titles
        )


@app.route('/genre/<int:genre_id>/<int:title_id>/')
def show_title(genre_id, title_id):
    """Specific title page. Shows plot."""
    genres = db.get_all_genres()
    gen = db.get_gen(gen_id)
    title = db.get_title(title_id)
    return render_template(
        'title.html',
        genres=genres,
        genre=gen,
        title=title
        )


@app.route(
    '/genre/new/',
    defaults={'genre_id': None},
    methods=['GET', 'POST']
    )
@app.route(
    '/genre/new/<int:genre_id>/',
    methods=['GET', 'POST']
    )
@login_required
def new_title(genre_id):
    """Add new title page.  Requires logged in status."""

    genres = db.get_all_genres()

    if request.method == 'POST':
        name = request.form['name']
        plot = request.form['plot']
        genre = request.form['genre']
        field_vals = {}

        user_id = login_session['user_id']

        if name and plot and genre != "None":
            print 'received inputs'
            flash('New title added!')
            gen_id = db.get_gen_id(genre)
            new_title = db.create_title(
                name,
                plot,
                gen_id,
                user_id
                )
            return redirect(url_for(
                'show_title',
                genre_id=gen_id,
                title_id=new_title.id
                )
            )
        elif genre == "None":
            flash('Must enter a genre.')
        else:
            field_vals['default_gen'] = genre
            flash('Invalid input! Must enter values.')

        field_vals['input_name'] = name
        field_vals['input_plot'] = plot
        return render_template('new_title.html', genres=genres, **field_vals)
    else:
        if genre_id:
            gen_name = db.get_gen(genre_id).name
            return render_template('new_title.html', genres=genres, default_gen=gen_name)
        else:
            return render_template('new_title.html', genres=genres)


@app.route(
    '/genre/<int:genre_id>/<int:title_id>/edit/',
    methods=['GET', 'POST']
    )
@login_required
def edit_title(genre_id, title_id):
    """Edit title page. User must have created the title to edit."""

    genres = db.get_all_genres()
    gen = db.get_gen(genre_id)
    title = db.get_title(title_id)
    user_id = login_session['user_id']

    if title.user_id != user_id:
        return redirect(url_for('main_page'))

    if request.method == 'POST':
        name = request.form['name']
        plot = request.form['plot']
        genre = request.form['genre']

        field_vals = {}

        if name and plot:
            flash('Title edited!')
            db.edit_title(title, name, plot, db.get_gen_id(genre))

            time.sleep(1)
            return redirect(url_for(
                'show_title',
                genre_id=genre_id,
                title_id=title_id
                )
            )
        else:
            field_vals['default_gen'] = genre
            flash('Invalid input! Must enter values.')

        field_vals['input_name'] = name
        field_vals['input_plot'] = plot
        return render_template('new_title.html', genres=genres, **field_vals)
    else:
        return render_template(
            'edit_title.html',
            genre_id=genre_id,
            title_id=title_id,
            genres=genres,
            input_name=title.name,
            input_plot=title.plot,
            default_gen=gen.name
            )


@app.route(
    '/genre/<int:genre_id>/<int:title_id>/delete/',
    methods=['GET', 'POST']
    )
@login_required
def delete_title(genre_id, title_id):
    """Delete title page.  User must have created title to delete."""

    gen = db.get_gen(genre_id)
    title = db.get_title(title_id)

    user_id = login_session['user_id']

    if item.user_id != user_id:
        return redirect(url_for('main_page'))

    if request.method == 'POST':
        delete_confirmation = request.form['delete']

        if delete_confirmation == 'yes':
            db.delete_title(title)
            flash('Title entry deleted.')
        return redirect(url_for('show_genre', genre_id=gen.id))
    else:
        return render_template(
            'delete_title.html',
            genre=gen,
            title=title
            )


# Login functions and handling
@app.route('/login')
def show_login():
    """Login page"""
    state = ''.join(random.choice(string.ascii_uppercase + string.digits) for x in xrange(32))
    login_session['state'] = state
    return render_template('login.html', STATE=state)


@app.route('/fbconnect', methods=['POST'])
def fbconnect():
    """FB connect functionality."""
    if request.args.get('state') != login_session['state']:
        response = make_response(json.dumps('Invalid state parameter'), 401)
        response.headers['Content-Type'] = 'application/json'
        return response

    # Exchange client token for long-lived server side token.
    access_token = request.data
    print 'Access token received {token}'.format(token=access_token)

    fb_client_json = open('fb_client_secrets.json', 'r').read()

    app_id = json.loads(fb_client_json)['web']['app_id']
    app_secret = json.loads(fb_client_json)['web']['app_secret']
    token_url = 'https://graph.facebook.com/oauth/access_token?grant_type=fb_exchange_token&client_id={id}&client_secret={secret}&fb_exchange_token={token}'.format(
        id=app_id,
        secret=app_secret,
        token=access_token
        )
    h = httplib2.Http()
    result = h.request(token_url, 'GET')[1]  # Getting long lived token

    base_url = 'https://graph.facebook.com/v2.4/me'

    token = result.split('&')[0]

    userinfo_url = base_url + '?{token}&fields=name,id,email'.format(token=token)
    h = httplib2.Http()
    user_result = h.request(userinfo_url, 'GET')[1]

    user_data = json.loads(user_result)
    login_session['provider'] = 'facebook'
    login_session['username'] = user_data['name']
    login_session['email'] = user_data['email']
    login_session['facebook_id'] = user_data['id']

    stored_token = token.split('=')[1]
    login_session['access_token'] = stored_token

    pic_url = base_url + '/picture?{token}&redirect=0&height=200&width=200'.format(token=token)
    h = httplib2.Http()
    pic_result = h.request(pic_url, 'GET')[1]
    pic_data = json.loads(pic_result)

    login_session['picture'] = pic_data['data']['url']

    # Check if user exists.
    # Gplus login and FB login can generate same user_id, if share same email.
    user_id = db.get_user_id(login_session['email'])
    if not user_id:
        user_id = db.create_user(login_session)

    login_session['user_id'] = user_id

    output = ''
    output += '<h1>Welcome, '
    output += login_session['username']

    output += '!</h1>'
    output += '<img src="'
    output += login_session['picture']
    output += ' " style = "width: 300px; height: 300px;border-radius: 150px;-webkit-border-radius: 150px;-moz-border-radius: 150px;"> '

    flash('Now logged in as {name}'.format(name=login_session['username']))
    return output


@app.route('/fbdisconnect', methods=['POST'])
def fbdisconnect():
    """FB disonnect functionality.  Pairs with universal disconnect function."""
    facebook_id = login_session['facebook_id']
    access_token = login_session['access_token']
    url = 'https://graph.facebook.com/{id}/permissions?access_token={token}'.format(
        id=facebook_id,
        token=access_token
        )
    h = httplib2.Http()
    result = json.loads(h.request(url, 'DELETE')[1])

    if not result.get('success'):
        response = make_response(json.dumps('Failed to revoke token for given user.'), 400)
        response.headers['Content-Type'] = 'application/json'
        return response

    return 'You have been logged out'


@app.route('/gconnect', methods=['POST'])
def gconnect():
    """Google Plus sign in."""
    if request.args.get('state') != login_session['state']:
        response = make_response(json.dumps('Invalid state parameter'), 401)
        response.headers['Content-Type'] = 'application/json'
        return response

    code = request.data  # one-time code from server

    try:
        # Upgrades auth code into credentials object
        oauth_flow = flow_from_clientsecrets('client_secrets.json', scope='')
        oauth_flow.redirect_uri = 'postmessage'
        credentials = oauth_flow.step2_exchange(code)
    except FlowExchangeError:
        response = make_response(json.dumps('Failed to upgrade the authorization code.'), 401)
        response.headers['Content-Type'] = 'application/json'
        return response

    access_token = credentials.access_token

    # Checking validity of access_token
    url = ('https://www.googleapis.com/oauth2/v1/tokeninfo?access_token={token}'.format(token=access_token))
    h = httplib2.Http()
    result = json.loads(h.request(url, 'GET')[1])

    if result.get('error') is not None:
        response = make_response(json.dumps(result.get('error')), 500)
        response.headers['Content-Type'] = 'application/json'

    gplus_id = credentials.id_token['sub']

    # Verifies access_token is for intended user
    if result['user_id'] != gplus_id:
        response = make_response(json.dumps('Token\'s user ID doesn\'t match given user ID.'), 401)
        response.heads['Content-Type'] = 'application/json'
        return response

    # Verifies access token is valid for this app.
    if result['issued_to'] != CLIENT_ID:
        response = make_response(json.dumps('Token\'s client ID does not match app\'s.'), 401)
        print 'Token\'s client ID does not match app\'s.'
        response.headers['Content-Type'] = 'application/json'
        return response

    stored_access_token = login_session.get('access_token')
    stored_gplus_id = login_session.get('gplus_id')
    if stored_access_token is not None and gplus_id == stored_gplus_id:
        response = make_response(json.dumps('Current user is already connected'), 200)
        response.headers['Content-Type'] = 'application/json'
        return response

    login_session['access_token'] = access_token
    login_session['gplus_id'] = gplus_id

    userinfo_url = 'https://www.googleapis.com/oauth2/v1/userinfo'
    params = {
        'access_token': credentials.access_token,
        'alt': 'json'
        }
    answer = requests.get(userinfo_url, params=params)

    data = answer.json()

    login_session['username'] = data['name']
    login_session['picture'] = data['picture']
    login_session['email'] = data['email']
    login_session['provider'] = 'google'

    user_id = db.get_user_id(login_session['email'])

    if user_id is None:
        user_id = db.create_user(login_session)

    login_session['user_id'] = user_id

    output = ''
    output += '<h1>Welcome, '
    output += login_session['username']
    output += '!</h1>'
    output += '<img src="'
    output += login_session['picture']
    output += ' " style = "width: 300px; height: 300px;border-radius: 150px;-webkit-border-radius: 150px;-moz-border-radius: 150px;"> '
    flash('You are now logged in as {name}'.format(name=login_session['username']))
    return output


@app.route('/gdisconnect')
def gdisconnect():
    """Google logout.  Pairs with universal disconnect function."""
    access_token = login_session.get('access_token')
    print 'In gdisconnect, access token is {token}'.format(token=access_token)
    print 'User name is: '
    print login_session.get('username')

    if access_token is None:
        print 'Access token is None'
        response = make_response(json.dumps('Current user not connected'), 401)
        response.headers['Content-Type'] = 'application/json'
        return response

    url = 'https://accounts.google.com/o/oauth2/revoke?token={token}'.format(token=access_token)
    h = httplib2.Http()
    result = h.request(url, 'GET')[0]

    if result['status'] != '200':
        response = make_response(json.dumps('Failed to revoke token for given user.'), 400)
        response.headers['Content-Type'] = 'application/json'
        return response


# Universal disconnect
@app.route('/disconnect')
def disconnect():
    """Disconnects either FB or G+ login"""
    if 'provider' in login_session:
        if login_session['provider'] == 'google':
            gdisconnect()
            del login_session['gplus_id']
        if login_session['provider'] == 'facebook':
            fbdisconnect()
            del login_session['facebook_id']
        del login_session['user_id']
        del login_session['access_token']
        del login_session['username']
        del login_session['email']
        del login_session['picture']
        del login_session['provider']

        flash('You have been successfully logged out.')
    else:
        flash('You were not logged in.')

    return redirect(url_for('main_page'))


# JSON APIs.
@app.route('/genre/JSON')
def genres_json():
    genres = session.query(Genre).all()
    return jsonify(Genres=[gen.serialize for gen in genres])


@app.route('/genre/<int:genre_id>/JSON')
def genre_titles_json(genre_id):
    title_list = db.get_titles_in_genre(genre_id)
    genre = db.get_gen(genre_id)
    return jsonify(Genre=genre.name, Titles=[title.serialize for title in title_list])


@app.route('/genre/<int:genre_id>/<int:title_id>/JSON')
def title_json(genre_id, title_id):
    title = db.get_title(title_id)
    return jsonify(Title=title.serialize)


if __name__ == '__main__':
    app.secret_key = 'super_secret_key'
    app.debug = True
    app.run(host='0.0.0.0', port=5000)
