from functools import wraps
from flask_jwt_extended import get_jwt_identity, verify_jwt_in_request
from src.models.models import User, Role
from src.utils.responses import error_response


def admin_required(func):
    @wraps(func)
    def wrapper(*args, **kwargs):
        verify_jwt_in_request()

        user_id = get_jwt_identity()

        user = User.query.get(user_id)

        if not user:
            return error_response(401, "unauthorized access")

        if user.role != Role.ADMIN:
            return error_response(401, "unauthorized access")

        return func(*args, **kwargs)

    return wrapper
