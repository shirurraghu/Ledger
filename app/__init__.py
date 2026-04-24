import logging
from logging.handlers import SMTPHandler, RotatingFileHandler
import os
from flask import Flask, request, session
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
import pymysql
pymysql.install_as_MySQLdb()
from flask_login import LoginManager
from flask_mail import Mail
from flask_moment import Moment
from flask_babel import Babel, _
from config import Config
from language_utils import get_translation_dict, get_locale
from app.locale_utils import get_current_locale
from flask_cors import CORS 

# Extensions
db = SQLAlchemy()
migrate = Migrate()
login = LoginManager()
mail = Mail()
moment = Moment()
babel = Babel()

LANGUAGES = ['en', 'hi', 'ta', 'te', 'ml', 'kn', 'bn']

def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)

    app.config['JSON_AS_ASCII'] = False
    app.config['BABEL_DEFAULT_LOCALE'] = 'en'
    app.config['BABEL_TRANSLATION_DIRECTORIES'] = 'translations'

    CORS(app, supports_credentials=True)

    # Initialize extensions
    db.init_app(app)
    migrate.init_app(app, db)
    
    login.login_view = 'main.login'  # or 'main.login' if inside blueprint
    login.init_app(app)

    mail.init_app(app)
    moment.init_app(app)
    babel.init_app(app)

    # Language selector setup
    @app.before_request
    def set_language_from_query():
        if 'lang' in request.args:
            lang = request.args.get('lang')
            if lang in LANGUAGES:
                session['lang'] = lang

    @babel.localeselector
    def select_locale():
        return session.get('lang') or 'en'

    @app.context_processor
    def inject_translations():
        lang = get_locale()
        t = get_translation_dict(lang)
        return dict(t=t)

    @app.context_processor
    def inject_get_locale():
        return dict(get_locale=get_locale)

    app.jinja_env.globals['get_locale'] = get_current_locale

    # Logging
    if not app.debug:
        if app.config['MAIL_SERVER']:
            auth = None
            if app.config['MAIL_USERNAME'] or app.config['MAIL_PASSWORD']:
                auth = (app.config['MAIL_USERNAME'], app.config['MAIL_PASSWORD'])
            secure = () if app.config['MAIL_USE_TLS'] else None
            mail_handler = SMTPHandler(
                mailhost=(app.config['MAIL_SERVER'], app.config['MAIL_PORT']),
                fromaddr='no-reply@' + app.config['MAIL_SERVER'],
                toaddrs=app.config['ADMINS'], subject='Ledger App Failure',
                credentials=auth, secure=secure)
            mail_handler.setLevel(logging.ERROR)
            app.logger.addHandler(mail_handler)

        if not os.path.exists('logs'):
            os.mkdir('logs')
        file_handler = RotatingFileHandler('logs/microblog.log', maxBytes=10240, backupCount=10)
        file_handler.setFormatter(logging.Formatter(
            '%(asctime)s %(levelname)s: %(message)s [in %(pathname)s:%(lineno)d]'))
        file_handler.setLevel(logging.INFO)
        app.logger.addHandler(file_handler)
        app.logger.setLevel(logging.INFO)
        app.logger.info('Ledger App startup')

    # Register Blueprints
    from app.routes import bp as routes_bp
    app.register_blueprint(routes_bp)

    return app
