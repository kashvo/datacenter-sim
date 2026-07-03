from fastapi import APIRouter, HTTPException, Depends, Request
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials

from app.models.schemas import LoginRequest, LoginResponse
from app.db.fake_db import get_user, verify_password, session_count
from app.core.security import create_user_session, invalidate_token, validate_token
from app.core.metrics import ACTIVE_SESSIONS, LOGIN_SUCCESS, LOGIN_FAILURE
from app.core.logger import get_logger
from app.core.rate_limiter import is_rate_limited

router = APIRouter()
logger = get_logger()
bearer = HTTPBearer()


@router.post("/login", response_model=LoginResponse)
async def login(request: LoginRequest, req: Request):
    client_ip = req.client.host

    if is_rate_limited(client_ip):
        logger.warning(
            "Rate limit exceeded",
            extra={"endpoint": "/login", "ip": client_ip}
        )
        raise HTTPException(
            status_code=429,
            detail="Too many login attempts - try again in 60 seconds"
        )

    user = get_user(request.username)

    if not user or not verify_password(request.password, user["hashed_password"]):
        LOGIN_FAILURE.inc()
        logger.warning(
            "Login failed",
            extra={"endpoint": "/login", "user": request.username}
        )
        raise HTTPException(status_code=401, detail="Invalid credentials")

    token = create_user_session(request.username)
    ACTIVE_SESSIONS.set(session_count())
    LOGIN_SUCCESS.inc()

    logger.info(
        "Login success",
        extra={
            "endpoint": "/login",
            "user": request.username,
            "user_type": user["role"]
        }
    )

    return LoginResponse(
        token=token,
        username=request.username,
        message="Login successful"
    )


@router.post("/logout")
async def logout(
    credentials: HTTPAuthorizationCredentials = Depends(bearer)
):
    token = credentials.credentials

    username = validate_token(token)
    if not username:
        raise HTTPException(status_code=401, detail="Invalid or expired session")

    invalidate_token(token)
    ACTIVE_SESSIONS.set(session_count())

    logger.info(
        "Logout",
        extra={"endpoint": "/logout", "user": username}
    )

    return {"message": "Logged out successfully"}