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

import os
import flask
from flask import Flask, request, abort, make_response, render_template, url_for, redirect
from flask_login import LoginManager, UserMixin, login_required, login_user, logout_user
from flask_wtf import FlaskForm
from wtforms import StringField, BooleanField
from wtforms.validators import DataRequired
from is_safe_url import is_safe_url

from optparse import OptionParser
import json
from flask_wtf.csrf import CSRFProtect
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import or_
from urllib.parse import urlparse

from datetime import datetime, timedelta, timezone

from azure.storage.blob.models import ContainerPermissions, ContentSettings
from azure.storage.blob.blockblobservice import BlockBlobService

app = Flask(__name__)
app.config.from_object(os.environ['APP_SETTINGS'])
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)

from models import *


print(os.environ)
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

@app.route('/login', methods=["GET"])
def login_get():
    parsedUrl = urlparse(request.referrer)
    return render_template('nav/login.html', referer_path=parsedUrl.path)

@app.route('/login', methods=['POST'])
def login():
    # Here we use a class of some kind to represent and validate our
    # client-side form data. For example, WTForms is a library that will
    # handle this for us, and we use a custom LoginForm to validate.
    form = LoginForm()
    if form.validate_on_submit():
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
    return render_template('slide/files.html')

@app.route('/home')
def home():
    return render_template('home.html')

@app.route('/')
def index():
    return render_template('home.html')

@app.route('/courses')
def courses():
    courses = Courses.query.all()
    courses_map ={}
    for course in courses:
        courses_map[course.id] = course.prop_map()
    return render_template('course/courses.html', courses_map=courses_map)

@app.route('/course')
def course():
    id = request.args.get("id")
    if not id:
        return render_template('nav/404.html', error_msg="The course you're looking for does not exist"), 404
    try:
        course = Courses.query.filter(Courses.id == id).one()
        course_map = course.prop_map()

        lessons = Lessons.query.filter(Lessons.course_id == id)
        lessons_map ={}
        for lesson in lessons:
            lessons_map[lesson.id] = lesson.prop_map()
    except:
        print(f'Invalid course number requested: {id}')
        return render_template('nav/404.html', error_msg="The course you're looking for does not exist"), 404
    return render_template('course/course.html', lessons_map=lessons_map, course_map=course_map)

@app.route('/lesson')
def lesson():
    id = request.args.get("id")
    if not id:
        return render_template('nav/404.html', error_msg="The lesson you're looking for does not exist"), 404
    try:
        lesson = Lessons.query.filter(Lessons.id == id).one()
        lesson_map = lesson.prop_map()
    except:
        print(f'Invalid lesson number requested: {id}')
        return render_template('nav/404.html', error_msg="The lesson you're looking for does not exist"), 404

    lesson_slides = LessonSlides.query.filter(LessonSlides.lesson_id == id)
    lesson_slides_map ={}
    for lesson_slide in lesson_slides:
        slide = Slides.query.filter(Slides.id == lesson_slide.slide_id).one()
        lesson_slide_prop_map = lesson_slide.prop_map()
        lesson_slide_prop_map ["slide_filename"] = slide.filename
        lesson_slides_map[lesson_slide.id] = lesson_slide_prop_map

    return render_template('course/lesson.html', lesson_slides_map=lesson_slides_map, lesson_map=lesson_map)

@app.route('/<path:path>')
def slide(path):
    dzi_path = path[:-3] + 'dzi' if path.endswith('svs') else path

    fields_to_remove = {"id"}

    try:
        slide = Slides.query.filter(Slides.filename == path).one()
        prop_map = slide.prop_map()
        for field_to_remove in fields_to_remove:
            prop_map.pop(field_to_remove)

    except:
        print(f'No such slide exists: {path}')
        return render_template('nav/404.html', error_msg="The slide you're looking for does not exist"), 404

    return render_template('slide/slide-fullpage.html', slide_base_url=app.config["SLIDE_BASE_URL"], slide_url=dzi_path, properties=prop_map)

@app.route('/full/<path:path>')
def slide_full(path):
    dzi_path = path[:-3] + 'dzi' if path.endswith('svs') else path
    fields_to_remove = {"id"}

    try:
        slide = Slides.query.filter(Slides.filename == path).one()
        prop_map = slide.prop_map()
        for field_to_remove in fields_to_remove:
            prop_map.pop(field_to_remove)

    except:
        print(f'No such slide exists: {path}')
        return render_template('nav/404.html', error_msg="The slide you're looking for does not exist"), 404

    return render_template('slide/slide-multipane.html', slide_base_url=app.config["SLIDE_BASE_URL"], slide_url=dzi_path, properties=prop_map)

@app.route('/edit/<path:path>')
@login_required
def slide_edit_get(path):
    dzi_path = path[:-3] + 'dzi' if path.endswith('svs') else path

    textarea_fields = {"comments", "histopathologic_description", "attachment"}
    fields_to_remove = {"id"}
    disabled_fields= {"filename"}
    try:
        slide = Slides.query.filter(Slides.filename == path).one()
        prop_map = slide.prop_map()
        for field_to_remove in fields_to_remove:
            prop_map.pop(field_to_remove)

    except:
        print(f'No such slide exists: {path}')
        return render_template('nav/404.html', error_msg="The slide you're looking for does not exist"), 404

    return render_template('slide/slide-multipane-edit.html', slide_base_url=app.config["SLIDE_BASE_URL"], slide_url=dzi_path,
                           properties=prop_map, svs_path=slide.filename,
                           textarea_fields=textarea_fields, disabled_fields=disabled_fields)

@app.route('/edit/<path:path>', methods =['POST'])
@login_required
def slide_edit(path):
    dzi_path = path[:-3] + 'dzi' if path.endswith('svs') else path

    filename = request.values.get("filename")
    if filename is None:
        return render_template('nav/404.html', error_msg="The slide you're looking for does not exist"), 404

    textarea_fields = {"comments", "histopathologic_description", "attachment"}
    fields_to_remove = {"id"}
    disabled_fields= {"filename"}

    try:
        slide = Slides.query.filter(Slides.filename == filename).one()
        for key, value in request.form.to_dict().items():
            if key in slide.prop_map().keys():
                setattr(slide, key, value)
        db.session.commit()
        prop_map = slide.prop_map()
        for field_to_remove in fields_to_remove:
            prop_map.pop(field_to_remove)

    except Exception as e:
        print(e)
        print(f'No such slide exists: {path}')
        return render_template('nav/404.html', error_msg="The slide you're looking for does not exist"), 404

    return render_template('slide/slide-multipane-edit.html', slide_base_url=app.config["SLIDE_BASE_URL"],
                            slide_url=dzi_path, properties=prop_map, svs_path=slide.filename,
                            textarea_fields=textarea_fields, disabled_fields=disabled_fields)

@app.route('/upload')
@login_required
def upload_slide():
    # TODO: If this config is not present, disable upload instead of failing to load
    accountName = app.config["AZURE_STORAGE_ACCOUNT_NAME"]
    containerName = app.config["AZURE_STORAGE_ACCOUNT_SVSUPLOAD_CONTAINER_NAME"]
    accountKey = app.config["AZURE_STORAGE_ACCOUNT_KEY"]
    blob_service = BlockBlobService(account_name=accountName, account_key=accountKey)

    permission = ContainerPermissions(write=True)

    now = datetime.now(timezone.utc)
    expiry = now + timedelta(hours=2)
    sasToken = blob_service.generate_container_shared_access_signature(container_name=containerName, permission=permission,
                                                             protocol='https', start=now, expiry=expiry)
    container_url = f'https://{accountName}.blob.core.windows.net/{containerName}?{sasToken}'
    return render_template('slide/upload.html', container_url=container_url)

@app.route("/allslides")
def allslides():
    slides = Slides.query.all()
    data = []
    for slide in slides:
        prop_map = slide.prop_map()
        prop_map["view"] = prop_map["filename"]
        data.append(prop_map)

    return json.dumps({'data': data})

@app.route("/search")
def search():
    text = request.args.get("searchText") # get the text to search for
    if text is None:
        text = ""

    searchText = "%"+text+"%"
    print(searchText)
    slides = Slides.query.filter(or_(Slides.filename.ilike(searchText),
                                      Slides.number.ilike(searchText),
                                      Slides.genus.ilike(searchText),
                                      Slides.species.ilike(searchText),
                                      Slides.source.ilike(searchText),
                                      Slides.contributor.ilike(searchText),
                                      Slides.comments.ilike(searchText),
                                      Slides.collection_site.ilike(searchText),
                                      Slides.histopathologic_description.ilike(searchText),
                                      Slides.attachment.ilike(searchText)
                                      )).all()
    data = []
    print(slides)
    for slide in slides:
        print(slide)
        prop_map = slide.prop_map()
        prop_map["view"] = prop_map["filename"]
        data.append(prop_map)

    return json.dumps({'data': data})

if __name__ == '__main__':
    parser = OptionParser(usage='Usage: %prog [options] [slide-directory]')
    parser.add_option('-c', '--config', metavar='FILE', dest='config',
                help='config file')
    parser.add_option('-d', '--debug', dest='DEBUG', action='store_true',
                help='run in debugging mode (insecure)')
    parser.add_option('-l', '--listen', metavar='ADDRESS', dest='host',
                default='127.0.0.1',
                help='address to listen on [127.0.0.1]')
    parser.add_option('-p', '--port', metavar='PORT', dest='port',
                type='int', default=5000,
                help='port to listen on [5000]')

    (opts, args) = parser.parse_args()
    # Load config file if specified
    if opts.config is not None:
        app.config.from_pyfile(opts.config)
    # Overwrite only those settings specified on the command line
    for k in dir(opts):
        if not k.startswith('_') and getattr(opts, k) is None:
            delattr(opts, k)
    app.config.from_object(opts)

    app.run(host=opts.host, port=opts.port, threaded=True)
