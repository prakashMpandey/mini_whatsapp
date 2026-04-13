# Mini WhatsApp Backend (Flask + Socket.IO + MySQL)

Real-time 1-to-1 chat and notification system backend using Flask, Flask-SocketIO, SQLAlchemy, MySQL, JWT, and Redis.

## 1. Tech Stack

- Python 3.13+
- Flask
- Flask-SocketIO (gevent)
- SQLAlchemy + Flask-Migrate
- MySQL (`mysqlclient`)
- JWT (`flask-jwt-extended`)
- Redis (presence + unread counters)

## 2. Project Structure

```text
app.py
src/
  __init__.py
  config/
  controllers/
    users.py
    notifications.py
    admin.py
  middlewares/
    isAdmin.py
  models/
    models.py
  sockets/
    events.py
  utils/
    responses.py
migrations/
```

## 3. Setup

### Prerequisites

- Python 3.13+
- MySQL running
- Redis running on `localhost:6379`

### Environment Variables

Create `.env` in project root:

```env
SQLALCHEMY_DATABASE_URI=mysql://<user>:<password>@localhost:3306/<db_name>
JWT_SECRET_KEY=your_secret_key
```

### Install

```bash
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt

```
    or

 if you are using uv:
 
 Initialize the project (if not already done):

```bash
    uv init
```
Add requirements from the file:
```bash
uv add -r requirements.txt

This command reads the dependencies, adds them to your pyproject.toml, and installs them into the project's local .venv.

```

Sync the environment:
```bash
uv sync 
```

### Migrate DB

```bash
set FLASK_APP=app.py
flask db upgrade
```

or 
### 🐳 Run with Docker (Recommended)
The easiest way to run the entire stack (App + MySQL) is using Docker:
```bash
docker-compose up --build
```

If migrations are not initialized:

```bash
flask db init
flask db migrate -m "init"
flask db upgrade
```

### Run

```bash
python app.py
```

## 4. REST APIs

Base URL: `http://127.0.0.1:5000`

Protected endpoints require:

```text
Authorization: Bearer <JWT>
```

| Method | Endpoint | Purpose | Auth |
| --- | --- | --- | --- |
| `POST` | `/users/register` | Register user | No |
| `POST` | `/users/login` | Login and get access token | No |
| `GET` | `/users/me` | Get current user id | Yes |
| `GET` | `/users/unread` | Unread counts grouped by sender | Yes |
| `GET` | `/notifications/` | List unread notifications | Yes |
| `GET` | `/notifications/read-all` | Mark all notifications read | Yes |
| `POST` | `/admin/create` | Create admin user | No |
| `POST` | `/admin/broadcast` | Broadcast to all users | Yes (admin only) |

## 5. Socket Events

Socket handshake header:

```text
Authorization: Bearer <JWT>
```

| Event | Direction | Payload | Behavior |
| --- | --- | --- | --- |
| `connect` | Client -> Server | JWT in header | Validates token, stores `session['user_id']` |
| `disconnect` | Client/Network -> Server | - | Updates `last_seen`, clears online key in Redis |
| `join` | Client -> Server | - | Joins `user_<id>` room, marks online, delivers pending messages, updates pending to delivered |
| `send_message` | Client -> Server | `{ "receiver_id": 2, "message": "Hi" }` | Persists message, routes instantly if receiver online, emits delivery state |
| `receive_message` | Server -> Client | Message object | Real-time inbound message event |
| `message_delivered` | Server -> Client | `{ "id": 1, "status": "sent|delivered" }` | Tick update to sender |
| `message_read` | Client -> Server -> Client | Client sends `{ "sender_id": 1 }` | Marks delivered messages as read and emits read receipt |
| `typing` | Client -> Server -> Client | `{ "receiver_id": 2 }` | Typing indicator to receiver |
| `notification` | Server -> Client | Notification payload | Real-time app/admin notification |

| `fetch_offline_messages` | Server -> Client | `{ "messages": [...] }` | Delivers queued messages on reconnect/join |

| `inc_unread_msg` | Server -> Client | `{ "sender_id": 1, "count": 3 }` | Real-time unread counter updates |

## 6. Chat Flow (Sent, Delivered, Read)

1. Sender emits `send_message`.
2. Server stores message.
3. If receiver online: receiver gets `receive_message`, sender gets `message_delivered: delivered`.
4. If receiver offline: sender gets `message_delivered: sent`, message is delivered later on `join`.
5. Receiver emits `message_read` when opening chat.
6. Server marks matching messages as read and notifies sender with `message_read`.

## 7. Database Schema (Current Model Layer)

### `users`

- `id` (PK)
- `username` (unique)
- `email` (unique)
- `password`
- `role` (`ADMIN` or `USER`)
- `last_seen`
- `created_at`

### `messages`

- `id` (PK)
- `sender_id` (FK -> users.id)
- `receiver_id` (FK -> users.id)
- `message`
- `status` (`SENT`, `DELIVERED`, `READ` in DB enum)
- `created_at`

### `notifications`

- `id` (PK)
- `user_id` (FK -> users.id)
- `message`
- `is_read`
- `created_at`



---

---