from flask import jsonify


def success_response(data=None, status_code=200, message="success"):
    response = {"status": "success", "message": message, "data": data}
    return jsonify(response), status_code


def error_response(status_code=400, message="something went wrong"):
    response = {
        "status": "error",
        "message": message,
    }

    return jsonify(response), status_code
