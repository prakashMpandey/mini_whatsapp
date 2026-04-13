from src import io
from flask_socketio import join_room
from flask import session
from src.models.models import Message, User, Notification, Status
from src import db
from flask import request, session
import jwt
import os
from datetime import datetime, timezone
from src import r


## connection event
@io.on("connect")
def handle_connect():
    print("user connected")

    token = (
        request.headers.get("Authorization").split(" ")[1]
        if request.headers.get("Authorization")
        else None
    )

    if not token:
        return False

    try:
        decoded_token = jwt.decode(
            token, os.getenv("JWT_SECRET_KEY"), algorithms=["HS256"], verify=True
        )

        if not decoded_token:
            return False

        user_id = decoded_token.get("sub")
        session["user_id"] = user_id
        print(f"{user_id} connected")

        return "success", 200
    except Exception as e:
        print(e)
        return False


## join event
@io.on("join")
def handle_join(*args):
    sid = request.sid
    user_id = session.get("user_id")

    if not user_id:
        return "failure", 400

    join_room(f"user_{user_id}")

    r.set(f"user:{user_id}", sid)
    print(f"user {user_id} is online")

    unread_messages = Message.query.filter_by(
        receiver_id=user_id, status=Status.SENT
    ).all()

    if unread_messages:
        messages = []
        senders_to_notify = set()
        for m in unread_messages:
            new_message = {
                "sender_id": m.sender_id,
                "message": m.message,
                "status": str(m.status.value),
            }
            messages.append(new_message)
            senders_to_notify.add(m.sender_id)

        io.emit("notification", {"message": "new message arrived"}, room=request.sid)
        io.emit(
            "fetch_offline_messages", {"messages": messages}, room=f"user_{user_id}"
        )

        for m in unread_messages:
            m.status = Status.DELIVERED

        for sender in senders_to_notify:
            io.emit(
                "message_delivered",
                {"receiver_id": user_id, "status": "delivered"},
                room=f"user_{sender}",
            )  
    return "success", 200
   
          


## send message event
@io.on("send_message")
def handle_message(data):
    msg = data.get("message")
    receiver_id = data.get("receiver_id")
    sender_id = session.get("user_id")

    if not sender_id or sender_id == receiver_id or not receiver_id:
        return False, 400

    message = Message(sender_id=sender_id, receiver_id=receiver_id, message=msg)
    
    db.session.add(message)
    db.session.commit()
    db.session.refresh(message)

    receiver_sid = r.get(f"user:{receiver_id}")

    ## checking if user is online or not
    if receiver_sid != None:
        message.status = Status.DELIVERED
        db.session.commit()
        # print(message.__dict__)

        new_message = {
            "id": message.id,
            "sender_id": message.sender_id,
            "message": message.message,
            "status": str(message.status.value),
            "created_at": str(message.created_at),
        }
        ## send msg to recevier
        io.emit("receive_message", new_message, room=f"user_{receiver_id}")

        ## increase unread count
        r.incr(f"unread:{receiver_id}:{sender_id}", 1)

        io.emit(
            "inc_unread_msg",
            {
                "sender_id": sender_id,
                "count": int(r.get(f"unread:{receiver_id}:{sender_id}")),
            },
            room=f"user_{receiver_id}",
        )
        ## send message staus
        io.emit(
            "message_delivered",
            {"id": message.id, "status": "delivered"},
            room=f"user_{sender_id}",
        )
        
        new_notification = Notification(
            user_id=receiver_id, message="you have a new message"
        )
        db.session.add(new_notification)
        db.session.commit()
        db.session.refresh(new_notification)
        io.emit(
            "notification",
            {"id": new_notification.id, "message": new_notification.message},
            room=f"user_{receiver_id}",
        )
        return 'success',200
    else:
        io.emit(
            "message_delivered",
            {"id": message.id, "status": "sent"},
            room=f"user_{sender_id}",
        )
        return 'success',200


## read message event
@io.on("message_read")
def handle_message_read(data):
    current_user = session.get("user_id")
    sender_id = data.get("sender_id")

    if not sender_id:
        return False, 400

    try:
        Message.query.filter(
            Message.receiver_id == current_user,
            Message.sender_id == sender_id,
            Message.status == Status.DELIVERED,
        ).update({Message.status: Status.READ})

        db.session.commit()
        r.delete(f"unread:{current_user}:{sender_id}")
        io.emit(
            "inc_unread_msg",
            {"sender_id": sender_id, "count": 0},
            room=f"user_{current_user}",
        )
        io.emit(
            "message_read",
            {"reader_id": current_user, "sender_id": sender_id, "status": "read"},
            room=f"user_{sender_id}",
        )
        return "success", 200

    except Exception as e:
        db.session.rollback()
        return False,400


## typing event
@io.on("typing")
def handle_typing(data):
    receiver_id = data.get("receiver_id")
    is_online = r.get(f"user:{receiver_id}")

    if is_online:
        io.emit("typing", {"typing": True}, room=f"user_{receiver_id}")
        return 'success',200


## disconnect event
@io.on("disconnect")
def handle_disconnect():
    try:
        user_id = session.get("user_id")
        if not user_id:
            print("client disconnected")

        user = User.query.filter_by(id=user_id).first()

        if user:
            user.last_seen = datetime.now(timezone.utc)
            db.session.commit()

        r.delete(f"user:{user_id}")

        print(f"user  {user_id} is offline")
        return "success", 200
    except Exception as e:
        print(e)
