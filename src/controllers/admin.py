from src.models.models import Notification, User, Role
from src import db, io
from flask import request, Blueprint
from src.utils.responses import success_response, error_response
from src.middlewares.isAdmin import admin_required


admin_bp = Blueprint("admin_bp", __name__, url_prefix="/admin")


@admin_bp.post("/create")
def create_admin():
    data = request.json
    username = data.get("username")
    email = data.get("email")
    password = data.get("password")

    if not all([username, email, password]):
        return error_response(400, "Username, email, and password are all required")

    existing_user = User.query.filter(
        (User.username == username) | (User.email == email)
    ).first()

    if existing_user:
        return error_response(400, "admin with this email already exists")

    try:
        user = User(username=username, email=email, role=Role.ADMIN)
        user.set_password(password)
        db.session.add(user)
        db.session.commit()
        return success_response(status_code=201, message="user created successfully")
    except Exception as e:
        db.session.rollback()
        print(e)
        return error_response(500, "server error")


@admin_bp.post("/broadcast")
@admin_required
def broadcast_message():
    data = request.json
    msg = data.get("message")

    if not msg:
        return error_response(400, "no message found")

    try:
        users = User.query.all()
        for user in users:
            notification = Notification(message=msg, user_id=user.id)
            db.session.add(notification)
        db.session.commit()
    except Exception as e:
        db.session.rollback()
        return error_response(500)

    io.emit("notification", {"message": msg, "sender": "admin"})
    return success_response(status_code=200, message="success")
