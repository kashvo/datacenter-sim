import time
from collections import defaultdict

login_attempts: dict[str, list] = defaultdict(list)

MAX_ATTEMPTS = 20
WINDOW_SECONDS = 60


def is_rate_limited(ip: str) -> bool:
    now = time.time()
    login_attempts[ip] = [
        t for t in login_attempts[ip]
        if now - t < WINDOW_SECONDS
    ]
    if len(login_attempts[ip]) >= MAX_ATTEMPTS:
        return True
    login_attempts[ip].append(now)
    return False


def reset_attempts(ip: str) -> None:
    login_attempts.pop(ip, None)


def get_attempt_count(ip: str) -> int:
    now = time.time()
    return len([
        t for t in login_attempts.get(ip, [])
        if now - t < WINDOW_SECONDS
    ])
