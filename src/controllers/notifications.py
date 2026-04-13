from src.models.models import Notification
from src import db
from flask import Blueprint
from src.utils.responses import success_response, error_response
from flask_jwt_extended import jwt_required, get_jwt_identity

notif_bp = Blueprint("notif_bp", __name__, url_prefix="/notifications")


@notif_bp.get("/")
@jwt_required()
def get_all_notifications():
    user_id = get_jwt_identity()
    if not user_id:
        return error_response(400, "user not authenticated")

    notifications = Notification.query.filter_by(user_id=user_id, is_read=False).all()
    output = []

    if len(notifications) > 0:
        for n in notifications:
            output.append(
                {
                    "id": n.id,
                    "message": n.message,
                    "is_read": n.is_read,
                    "created_at": n.created_at.isoformat(),
                }
            )

    return success_response(data=output, status_code=200)


@notif_bp.get("/read-all")
@jwt_required()
def read_all_notifications():
    user_id = get_jwt_identity()

    if not user_id:
        return error_response(400, "user not authenticated")

    try:
        unread_notifications = Notification.query.filter_by(
            user_id=user_id, is_read=False
        ).update({Notification.is_read: True})
        db.session.commit()
    except Exception as e:
        db.session.rollback()
        return error_response(500, "internal server error")

    return success_response(
        message=f"marked {unread_notifications} messages as read", status_code=200
    )
