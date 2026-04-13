from src.models.models import User, Message
from src import db
from flask import request, Blueprint
from src.utils.responses import success_response, error_response
from flask_jwt_extended import create_access_token, jwt_required, get_jwt_identity
from src import r
from sqlalchemy import func

user_bp = Blueprint("user_bp", __name__, url_prefix="/users")


@user_bp.post("/register")
def register():
    data = request.json

    if not data:
        return error_response(status_code=400, message="data not found")

    username = data.get("username")
    password = data.get("password")
    email = data.get("email")
    # role=data.get('role')

    if not all([username, password, email]):
        return error_response(
            status_code=400, message="username or password is missing"
        )

    existing_user = User.query.filter(
        (User.username == username) | (User.email == email)
    ).first()

    if existing_user:
        return error_response(400, "user already exists")

    try:
        user = User(username=username, email=email)
        user.set_password(password)
        db.session.add(user)
        db.session.commit()
        return success_response(status_code=201, message="user created successfully")
    except Exception as e:
        db.session.rollback()
        print(e)
        return error_response(500, "server error")


@user_bp.post("/login")
def login():
    data = request.get_json()

    username = data.get("username")
    password = data.get("password")

    if not username or not password:
        return error_response(400, "username or password is missing")

    user = User.query.filter_by(username=username).first()

    if not user:
        return error_response(404, "user does not exists")

    if not user.check_password(password):
        return error_response(401, "invalid credentials")

    access_token = create_access_token(identity=str(user.id))
    return success_response(data={"access_token": access_token})


@user_bp.get("/unread")
@jwt_required()
def get_unread_messages():
    user_id = get_jwt_identity()

    messages = (
        db.session.query(
            Message.sender_id, User.username, func.count(Message.id).label("count")
        )
        .join(User, Message.sender_id == User.id)
        .filter(Message.receiver_id == user_id, Message.status == "SENT")
        .group_by(Message.sender_id)
        .all()
    )

    print(messages)
    result = []

    for sender_id, username, count in messages:
        result.append({"sender_id": sender_id, "username": username, "count": count})
        r.set(f"unread:{user_id}:{sender_id}", count)
    print(result)

    return success_response(
        status_code=200, data=result, message="unread messages collected successfully"
    )


## gives current user
@user_bp.get("/me")
@jwt_required(locations=["headers"])
def get_user():
    current_user = get_jwt_identity()
    return success_response(data={"user": current_user})
