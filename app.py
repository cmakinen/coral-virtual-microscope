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

from collections import OrderedDict
import flask
from flask import Flask, request, abort, make_response, render_template, url_for
from flask_login import LoginManager, UserMixin, login_required
from flask_wtf import FlaskForm
from wtforms import StringField, BooleanField
from wtforms.validators import DataRequired

from io import BytesIO
import openslide
from openslide import OpenSlide, OpenSlideError
from openslide.deepzoom import DeepZoomGenerator
import os
from optparse import OptionParser
from threading import Lock
import json
import sqlite3
from flask_wtf.csrf import CSRFProtect

SLIDE_DIR = '.'
SLIDE_CACHE_SIZE = 10
DEEPZOOM_FORMAT = 'jpeg'
DEEPZOOM_TILE_SIZE = 254
DEEPZOOM_OVERLAP = 1
DEEPZOOM_LIMIT_BOUNDS = True
DEEPZOOM_TILE_QUALITY = 75

app = Flask(__name__)
app.config.from_object(__name__)
app.config.from_envvar('DEEPZOOM_MULTISERVER_SETTINGS', silent=True)
app.config["SECRET_KEY"] = "ITSASECRET"
login_manager = LoginManager()
login_manager.init_app(app)
CSRFProtect(app)

class LoginForm(FlaskForm):
    email = StringField('email', validators=[DataRequired()])
    password = StringField('password', validators=[DataRequired()])
    remember_me = BooleanField('remember_me', default=False)

class User(UserMixin):
    # proxy for a database of users
    user_database = {"JohnDoe@jd.com": ("JohnDoe@jd.com", "John"),
                     "JaneDoe@jd.com": ("JaneDoe@jd.com", "Jane")}

    def __init__(self, email, password):
        self.email = email
        self.password = password

    @classmethod
    def get(cls,email):
        return cls.user_database.get(email)

@login_manager.user_loader
def load_user(user_id):
    #return None if no match
    return User.get(user_id)

@app.route("/protected/",methods=["GET"])
@login_required
def protected():
    return make_response("Hello Protected World!")

@app.route('/login', methods=['GET', 'POST'])
def login():
    # Here we use a class of some kind to represent and validate our
    # client-side form data. For example, WTForms is a library that will
    # handle this for us, and we use a custom LoginForm to validate.
    form = LoginForm()
    print("login called")
    print (request.__dict__)
    if form.validate_on_submit():
        print("login called2")
        # Login and validate the user.
        # user should be an instance of your `User` class
        login_user(user)
        print("logged in successfully")

        flask.flash('Logged in successfully.')

        next = flask.request.args.get('next')
        # is_safe_url should check if the url is safe for redirects.
        # See http://flask.pocoo.org/snippets/62/ for an example.
        if not is_safe_url(next):
            return flask.abort(400)

        return flask.redirect(next or flask.url_for('index'))
    return flask.render_template('login.html', form=form)


class PILBytesIO(BytesIO):
    def fileno(self):
        '''Classic PIL doesn't understand io.UnsupportedOperation.'''
        raise AttributeError('Not supported')


class _SlideCache(object):
    def __init__(self, cache_size, dz_opts):
        self.cache_size = cache_size
        self.dz_opts = dz_opts
        self._lock = Lock()
        self._cache = OrderedDict()

    def get(self, path):
        with self._lock:
            if path in self._cache:
                # Move to end of LRU
                slide = self._cache.pop(path)
                self._cache[path] = slide
                return slide

        osr = OpenSlide(path)
        slide = DeepZoomGenerator(osr, **self.dz_opts)
        try:
            mpp_x = osr.properties[openslide.PROPERTY_NAME_MPP_X]
            mpp_y = osr.properties[openslide.PROPERTY_NAME_MPP_Y]
            slide.mpp = (float(mpp_x) + float(mpp_y)) / 2
        except (KeyError, ValueError):
            slide.mpp = 0

        with self._lock:
            if path not in self._cache:
                if len(self._cache) == self.cache_size:
                    self._cache.popitem(last=False)
                self._cache[path] = slide
        return slide


class _Directory(object):
    def __init__(self, basedir, relpath=''):
        self.name = os.path.basename(relpath)
        self.children = []

        conn = sqlite3.connect('all_slides.db')
        c = conn.cursor()
        c.execute("select * from slides")
        records = c.fetchall()
        for row in records:
            i = 0
            slide = {}
            for key in c.description:
                slide[key[0]] = row[i]
                i = i + 1
            self.children.append(_SlideFile(slide))

        conn.close()


class _SlideFile(object):
    def __init__(self, slide):
        self.name = slide['filename']
        self.slide_number = slide['number']
        # self.slide_description = row[4]
        self.genus = slide['genus']
        self.species= slide['species']
        self.stain = slide['stain']
        self.source = slide['source']
        self.contributor = slide['contributor']
        # self.accession_number = slide['accession_number']
        self.processing = slide['processing']
        self.comments = slide['comments']
        self.date_sent_to_aperio = slide['date_sent_to_aperio']
        # self.sample = slide['sample']
        self.infect = slide['infect']
        # self.study = slide['study']
        self.collection_site = slide['collection_site']
        self.histopathologic_description = slide['histopathologic_description']
        self.attachment = "N/A"

        self.url_path = slide['filename']

@app.before_first_request
def _setup():
    app.basedir = os.path.abspath(app.config['SLIDE_DIR'])
    config_map = {
        'DEEPZOOM_TILE_SIZE': 'tile_size',
        'DEEPZOOM_OVERLAP': 'overlap',
        'DEEPZOOM_LIMIT_BOUNDS': 'limit_bounds',
    }
    opts = dict((v, app.config[k]) for k, v in config_map.items())
    app.cache = _SlideCache(app.config['SLIDE_CACHE_SIZE'], opts)


def _get_slide(path):
    path = os.path.abspath(os.path.join(app.basedir, path))
    if not path.startswith(app.basedir + os.path.sep):
        # Directory traversal
        abort(404)
    if not os.path.exists(path):
        abort(404)
    try:
        slide = app.cache.get(path)
        slide.filename = os.path.basename(path)
        return slide
    except OpenSlideError:
        abort(404)

@app.route('/slides')
def slides():
    return render_template('files.html', root_dir=_Directory(app.basedir))

@app.route('/home')
def home():
    return render_template('home.html', root_dir=_Directory(app.basedir))

@app.route('/')
def index():
    return render_template('home.html', root_dir=_Directory(app.basedir))


@app.route('/<path:path>')
def slide(path):
    slide = _get_slide(path)
    slide_url = url_for('dzi', path=path)

    conn = sqlite3.connect('all_slides.db')
    c = conn.cursor()
    c.execute("select * from slides where filename = ?", (path,))
    records = c.fetchall()
    for row in records:
        i = 0
        properties = {}
        for key in c.description:
            properties[key[0]] = row[i]
            i = i + 1

    conn.close()

    return render_template('slide-multipane.html', slide_url=slide_url,
            slide_filename=slide.filename, slide_mpp=slide.mpp, properties=properties)


@app.route('/<path:path>.dzi')
def dzi(path):
    slide = _get_slide(path)
    format = app.config['DEEPZOOM_FORMAT']
    resp = make_response(slide.get_dzi(format))
    resp.mimetype = 'application/xml'
    return resp


@app.route('/<path:path>_files/<int:level>/<int:col>_<int:row>.<format>')
def tile(path, level, col, row, format):
    slide = _get_slide(path)
    format = format.lower()
    if format != 'jpeg' and format != 'png':
        # Not supported by Deep Zoom
        abort(404)
    try:
        tile = slide.get_tile(level, (col, row))
    except ValueError:
        # Invalid level or coordinates
        abort(404)
    buf = PILBytesIO()
    tile.save(buf, format, quality=app.config['DEEPZOOM_TILE_QUALITY'])
    resp = make_response(buf.getvalue())
    resp.mimetype = 'image/%s' % format
    return resp

@app.route("/search")
def search():
    text = request.args['searchText'] # get the text to search for

    conn = sqlite3.connect('all_slides.db')
    c = conn.cursor()
    qs = '%'+text+'%'
    t = (qs,qs,qs,qs,qs,qs,qs,qs,qs,)
    c.execute("""select * from slides where filename LIKE ? OR number LIKE ? OR genus LIKE ? OR species LIKE ?
                 OR source LIKE ? OR contributor LIKE ? OR comments LIKE ? OR collection_site LIKE ? OR histopathologic_description LIKE ?"""
              ,t)

    records = c.fetchall()
    slides = []
    for row in records:
        i = 0
        slide = {}
        for key in c.description:
            slide[key[0]] = row[i]
            i = i + 1
        slides.append(slide)

    conn.close()

    # return as JSON
    return json.dumps({'slides': slides})

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

    app.run(host=opts.host, port=opts.port, threaded=True)
