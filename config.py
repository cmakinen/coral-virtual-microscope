
import os
basedir = os.path.abspath(os.path.dirname(__file__))

class Config(object):
    DEBUG = False
    TESTING = False
    CSRF_ENABLED = True
    SECRET_KEY = 'ITSASECRET'
    SLIDE_BASE_URL = os.environ['SLIDE_BASE_URL']
    SQLALCHEMY_DATABASE_URI = os.environ['DATABASE_URL']
    AZURE_STORAGE_ACCOUNT_KEY= os.environ['AZURE_STORAGE_ACCOUNT_KEY']
    AZURE_STORAGE_ACCOUNT_NAME = os.environ['AZURE_STORAGE_ACCOUNT_NAME']
    AZURE_STORAGE_ACCOUNT_SVSUPLOAD_CONTAINER_NAME = os.environ['AZURE_STORAGE_ACCOUNT_SVSUPLOAD_CONTAINER_NAME']

class ProductionConfig(Config):
    DEBUG = False

class StagingConfig(Config):
    DEVELOPMENT = True
    DEBUG = True

class DevelopmentConfig(Config):
    DEVELOPMENT = True
    DEBUG = True

class TestingConfig(Config):
    TESTING = True
