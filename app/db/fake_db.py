from passlib.context import CryptContext

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def seed_users(count=100):
    users = {}
    roles = ["web", "mobile", "api"]
    hashed_pass = pwd_context.hash("pass")
    for i in range(count):
        role = roles[i % 3]
        username = role + "user_" + str(i)
        users[username] = {
            "username": username,
            "hashed_password": hashed_pass,
            "role": role
        }
    return users


USERS = seed_users(100)
SESSIONS = {}


def get_user(username):
    return USERS.get(username)


def verify_password(plain, hashed):
    return pwd_context.verify(plain, hashed)


def create_session(token, username):
    SESSIONS[token] = username


def get_session(token):
    return SESSIONS.get(token)


def delete_session(token):
    SESSIONS.pop(token, None)


def session_count():
    return len(SESSIONS)


def user_count():
    return len(USERS)
