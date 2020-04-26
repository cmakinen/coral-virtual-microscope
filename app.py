#!/usr/bin/env python
#
# deepzoom_multiserver - Example web application for viewing multiple slides
#
# Copyright (c) 2010-2015 Carnegie Mellon University
#
# This library is free software; you can redistribute it and/or modify it
# under the terms of version 2.1 of the GNU Lesser General Public License
# as published by the Free Software Foundation.
#
# This library is distributed in the hope that it will be useful, but
# WITHOUT ANY WARRANTY; without even the implied warranty of MERCHANTABILITY
# or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU Lesser General Public
# License for more details.
#
# You should have received a copy of the GNU Lesser General Public License
# along with this library; if not, write to the Free Software Foundation,
# Inc., 51 Franklin Street, Fifth Floor, Boston, MA 02110-1301 USA.
#

import flask
from flask import Flask, request, abort, make_response, render_template, url_for, redirect
from flask_login import LoginManager, UserMixin, login_required, login_user, logout_user
from flask_wtf import FlaskForm
from wtforms import StringField, BooleanField
from wtforms.validators import DataRequired
from is_safe_url import is_safe_url

from optparse import OptionParser
import json
import sqlite3
from flask_wtf.csrf import CSRFProtect
from waitress import serve

SLIDE_DIR = '.'

app = Flask(__name__)
app.config.from_object(__name__)
app.config["SECRET_KEY"] = "ITSASECRET"
login_manager = LoginManager()
login_manager.init_app(app)
CSRFProtect(app)

class LoginForm(FlaskForm):
    email = StringField('email', validators=[DataRequired()])
    password = StringField('password', validators=[DataRequired()])
    remember_me = BooleanField('remember_me', default=False)

class User():
    # proxy for a database of users
    def __init__(self, email, password):
        self.email = email
        self.password = password

    # Flask-Login integration
    def is_authenticated(self):
        return True

    def is_active(self): # line 37
        return True

    def is_anonymous(self):
        return False

    def get_id(self):
        return self.email

    @classmethod
    def get(cls,email):
        return user_database.get(email)

user_database = {"JohnDoe@jd.com": User("JohnDoe@jd.com", "John"),
                 "JaneDoe@jd.com": User("JaneDoe@jd.com", "Jane")}

@login_manager.user_loader
def load_user(user_id):
    #return None if no match
    return User.get(user_id)

@app.route("/protected/",methods=["GET"])
@login_required
def protected():
    return make_response("Hello Protected World!")

@app.route('/login', methods=['POST'])
def login():
    # Here we use a class of some kind to represent and validate our
    # client-side form data. For example, WTForms is a library that will
    # handle this for us, and we use a custom LoginForm to validate.
    form = LoginForm()
    if form.validate_on_submit():
        print("login called2")
        # Login and validate the user.
        # user should be an instance of your `User` class
        user = load_user(request.form['email'])
        login_user(user)
        flask.flash('Logged in successfully.')

        next = flask.request.args.get('next')
        # is_safe_url should check if the url is safe for redirects.
        # See http://flask.pocoo.org/snippets/62/ for an example.
        if not is_safe_url(next, {"localhost"}):
            return flask.abort(400)

        return flask.redirect(next or flask.url_for('index'))
    return redirect(flask.request.environ["HTTP_REFERER"])

@app.route("/logout")
@login_required
def logout():
    logout_user()
    return redirect(flask.request.environ["HTTP_REFERER"])

@app.route('/slides')
def slides():
    return render_template('files.html')

@app.route('/home')
def home():
    return render_template('home.html')

@app.route('/')
def index():
    return render_template('home.html')

@app.route('/courses')
def courses():
    return render_template('courses.html')

@app.route('/course')
def course():
    return render_template('course.html')

@app.route('/<path:path>')
def slide(path):
    dzi_path = path[:-3] + 'dzi' if path.endswith('svs') else path

    conn = sqlite3.connect('all_slides.db')
    c = conn.cursor()
    c.execute("select * from slides where filename = ?", (path,))
    records = c.fetchall()
    properties = {}
    for row in records:
        i = 0
        for key in c.description:
            properties[key[0].title()] = row[i]
            i = i + 1

    conn.close()

    return render_template('slide-fullpage.html', slide_url=dzi_path, properties=properties)

@app.route('/full/<path:path>')
def slide_full(path):
    print(path)

    dzi_path = path[:-3] + 'dzi' if path.endswith('svs') else path

    conn = sqlite3.connect('all_slides.db')
    c = conn.cursor()
    c.execute("select * from slides where filename = ?", (path,))
    records = c.fetchall()
    properties = {}
    for row in records:
        i = 0
        for key in c.description:
            properties[key[0].title()] = row[i]
            i = i + 1

    conn.close()

    return render_template('slide-multipane.html', slide_url=dzi_path, properties=properties)

@app.route("/search")
def search():
    text = request.args.get("searchText") # get the text to search for
    if text is None:
        text = ""
    conn = sqlite3.connect('all_slides.db')
    c = conn.cursor()
    qs = '%'+text+'%'
    t = (qs,qs,qs,qs,qs,qs,qs,qs,qs,)
    c.execute("""select * from slides where filename LIKE ? OR number LIKE ? OR genus LIKE ? OR species LIKE ?
                 OR source LIKE ? OR contributor LIKE ? OR comments LIKE ? OR collection_site LIKE ? OR histopathologic_description LIKE ?"""
              ,t)

    records = c.fetchall()
    data = []
    for row in records:
        i = 0
        slide = {}
        for key in c.description:
            slide[key[0]] = row[i]
            i = i + 1
        # if path.exists(app.basedir + "/" + slide["filename"]):
            slide["file_exists"] = True
        # else:
        #     slide["file_exists"] = False
        slide["view"] = slide["filename"]
        data.append(slide)

    conn.close()

    # return as JSON
    return json.dumps({'data': data})

if __name__ == '__main__':
    parser = OptionParser(usage='Usage: %prog [options] [slide-directory]')
    parser.add_option('-B', '--ignore-bounds', dest='DEEPZOOM_LIMIT_BOUNDS',
                default=True, action='store_false',
                help='display entire scan area')
    parser.add_option('-c', '--config', metavar='FILE', dest='config',
                help='config file')
    parser.add_option('-d', '--debug', dest='DEBUG', action='store_true',
                help='run in debugging mode (insecure)')
    parser.add_option('-e', '--overlap', metavar='PIXELS',
                dest='DEEPZOOM_OVERLAP', type='int',
                help='overlap of adjacent tiles [1]')
    parser.add_option('-f', '--format', metavar='{jpeg|png}',
                dest='DEEPZOOM_FORMAT',
                help='image format for tiles [jpeg]')
    parser.add_option('-l', '--listen', metavar='ADDRESS', dest='host',
                default='127.0.0.1',
                help='address to listen on [127.0.0.1]')
    parser.add_option('-p', '--port', metavar='PORT', dest='port',
                type='int', default=5000,
                help='port to listen on [5000]')
    parser.add_option('-Q', '--quality', metavar='QUALITY',
                dest='DEEPZOOM_TILE_QUALITY', type='int',
                help='JPEG compression quality [75]')
    parser.add_option('-s', '--size', metavar='PIXELS',
                dest='DEEPZOOM_TILE_SIZE', type='int',
                help='tile size [254]')

    (opts, args) = parser.parse_args()
    # Load config file if specified
    if opts.config is not None:
        app.config.from_pyfile(opts.config)
    # Overwrite only those settings specified on the command line
    for k in dir(opts):
        if not k.startswith('_') and getattr(opts, k) is None:
            delattr(opts, k)
    app.config.from_object(opts)
    # Set slide directory
    try:
        app.config['SLIDE_DIR'] = args[0]
    except IndexError:
        pass

    serve(app, host=opts.host, port=opts.port, threads=8)
