from src import db
from sqlalchemy.orm import relationship
import enum
from werkzeug.security import generate_password_hash, check_password_hash


class Status(enum.Enum):
    SENT = "sent"
    DELIVERED = "delivered"
    READ = "read"


class Role(enum.Enum):
    ADMIN = "admin"
    USER = "user"


class BaseModel(db.Model):
    __abstract__ = True
    id = db.Column(db.Integer, primary_key=True)
    created_at = db.Column(db.DateTime, server_default=db.func.now())


class User(BaseModel):
    __tablename__ = "users"
    username = db.Column(db.String(50), unique=True, nullable=False)
    email = db.Column(db.String(50), unique=True, nullable=False)
    password = db.Column(db.String(255), nullable=False)
    role = db.Column(db.Enum(Role), default=Role.USER)
    last_seen = db.Column(db.DateTime, server_default=db.func.now())
    sent_messages = relationship(
        "Message", back_populates="sender", foreign_keys="Message.sender_id"
    )
    received_messages = relationship(
        "Message", back_populates="receiver", foreign_keys="Message.receiver_id"
    )
    notifications = relationship("Notification", back_populates="user")

    def set_password(self, password):
        self.password = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password, password)


class Message(BaseModel):
    __tablename__ = "messages"
    message = db.Column(db.Text, nullable=False)
    sender_id = db.Column(
        db.Integer, db.ForeignKey("users.id", ondelete="CASCADE"), index=True
    )
    receiver_id = db.Column(
        db.Integer, db.ForeignKey("users.id", ondelete="CASCADE"), index=True
    )
    status = db.Column(db.Enum(Status), default=Status.SENT)

    sender = relationship(
        "User", foreign_keys="Message.sender_id", back_populates="sent_messages"
    )
    receiver = relationship(
        "User", foreign_keys="Message.receiver_id", back_populates="received_messages"
    )


class Notification(BaseModel):
    __tablename__ = "notifications"

    is_read = db.Column(db.Boolean, default=False)
    message = db.Column(db.String(200), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    user = relationship("User", back_populates="notifications")
