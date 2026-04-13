from gevent import monkey

monkey.patch_all()

import os
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from dotenv import load_dotenv
from src.config.config import Config
from flask_jwt_extended import JWTManager
from flask_socketio import SocketIO
import redis


REDIS_URL = "redis://localhost:6379/0"


r = redis.Redis(host="localhost", port=6379, decode_responses=True)

db = SQLAlchemy()
migrate = Migrate()
jwt = JWTManager()
io = SocketIO(message_queue=REDIS_URL, cors_allowed_origins="*", async_mode="gevent")


def create_app():
    load_dotenv()

    app = Flask(__name__)

    app.config.from_object(Config().dev_config)

    app.config["SQLALCHEMY_DATABASE_URI"] = os.getenv("SQLALCHEMY_DATABASE_URI")
    app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
    app.config["JWT_SECRET_KEY"] = os.getenv("JWT_SECRET_KEY")

    db.init_app(app)
    jwt.init_app(app)
    io.init_app(app)

    from src.models.models import User, Message, Notification

    migrate.init_app(app, db)

    from src.controllers.users import user_bp
    from src.controllers.admin import admin_bp
    from src.controllers.notifications import notif_bp
    from src.sockets import events

    app.register_blueprint(user_bp)
    app.register_blueprint(admin_bp)
    app.register_blueprint(notif_bp)

    return app
