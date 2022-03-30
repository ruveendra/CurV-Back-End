from flask import Flask


from src.analytics import analytics
from src.settings import settings
from src.user import user
from src.auth import auth
from src.devices import devices
from src.main_sensor import mainsensor
from src.sensor import sensor
from src.database import db, User, Admin
from flask_jwt_extended import JWTManager
from src.admin import admin

from flask_login import LoginManager, current_user, login_user, logout_user, login_required, login_manager

def create_app(test_config=None):
    app = Flask(__name__, instance_relative_config=True)

    if test_config is None:

        app.config['SECRET_KEY'] = "dev"
        # app.config['SQLALCHEMY_DATABASE_URI'] = 'mysql+pymysql://root:XC.Kjs5563@localhost:3306/smartmeter'
        app.config['SQLALCHEMY_DATABASE_URI'] = 'mysql+pymysql://root:1@localhost:3306/smartmeter'

        # app.config['SECRET_KEY'] = os.environ.get("SECRET_KEY")
        # app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get("SQLALCHEMY_DB_URI")

        # SQLALCHEMY_DB_URI=os.environ.get("SQLALCHEMY_DB_URI"),
        # SQLALCHEMY_DATABASE_URI='mysql://root:1@localhost:3306/bookmark',
        # SQLALCHEMY_DATABASE_URI='sqlite:///bookmarks.db',
        app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
        # JWT_SECRET_KEY = os.environ.get('JWT_SECRET_KEY')
        JWT_SECRET_KEY = 'JWT_SECRET_KEY'


    else:
        app.config.from_mapping(test_config)

    db.app = app
    db.init_app(app)

    login_manager = LoginManager()
    login_manager.login_view = 'admin.admin_login'
    login_manager.init_app(app)

    JWTManager(app)

    app.register_blueprint(auth)
    app.register_blueprint(admin)
    app.register_blueprint(devices)
    app.register_blueprint(mainsensor)
    app.register_blueprint(sensor)
    app.register_blueprint(user)
    app.register_blueprint(analytics)
    app.register_blueprint(settings)

    @login_manager.user_loader
    def load_user(user_id):
        return Admin.query.get(int(user_id))

    return app


def current_app():
    return None

