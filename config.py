import os
BASE_DIR = os.path.abspath(os.path.dirname(__file__))

DATABASE_CONNECT_OPTIONS = {}
SQLALCHEMY_TRACK_MODIFICATIONS = True


class Config:
    DEBUG = True
    CSRF_ENABLED =True
    SECRET_KEY = os.environ.get('SECRET_KEY')
    MAIL_SERVER ='smtp.googlemail.com'
    MAIL_PORT = 587
    MAIL_USE_TLS = True
    MAIL_PASSWORD = os.environ.get('MAIL_PASSWORD')
    MAIL_USERNAME = os.environ.get('MAIL_USERNAME')
    JOKENIA_MAIL_SUBJECT_PREFIX = '[ Jokenia ]'
    JOKENIA_MAIL_SENDER = 'Team@Jokenia'
    JOKENIA_ADMIN = os.environ.get('JOKENIA_ADMIN')
    SECRET_KEY = 'secret'
    CSRF_SESSION_KEY = 'secret'
    # the database am working with
    SQLALCHEMY_DATABASE_URI = 'sqlite:///' + os.path.join(BASE_DIR, 'app.sqlite')
    
    @staticmethod
    def init_app(app):
        pass

config = {
    'default': Config
}
