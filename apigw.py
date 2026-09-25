"""Request/response helpers for API Gateway v2 (HTTP API) Lambda handlers —
the Python analog of AuthMiddleware/get_current_user_id from
middlewares/auth.py and auth/dependencies.py, since there's
no ASGI request/response cycle here to hang state on.
"""

import json
import uuid
from typing import Any, Optional

from auth.jwt import InvalidTokenError, verify_token


class NotAuthorized(Exception):
    """Raised by require_user; every handler turns this into a 401, same shape AuthMiddleware returns."""


def get_header(event: dict, name: str) -> Optional[str]:
    headers = event.get("headers") or {}
    return headers.get(name.lower())


def path_param(event: dict, name: str) -> str:
    return (event.get("pathParameters") or {}).get(name, "")


def uuid_path_param(event: dict, name: str) -> Optional[uuid.UUID]:
    try:
        return uuid.UUID(path_param(event, name))
    except ValueError:
        return None


def require_user(event: dict) -> uuid.UUID:
    """Mirrors AuthMiddleware + get_current_user_id: verifies the JWT from the
    Authorization header and returns the caller's user_id."""
    token = get_header(event, "authorization")
    if not token:
        raise NotAuthorized()

    try:
        user = verify_token(token)
    except InvalidTokenError:
        raise NotAuthorized()

    try:
        return uuid.UUID(user.user_id)
    except ValueError:
        raise NotAuthorized()


def json_response(status: int, body: Any) -> dict:
    return {
        "statusCode": status,
        "headers": {"Content-Type": "application/json"},
        "body": json.dumps(body, default=str),
    }


def empty_response(status: int) -> dict:
    return {"statusCode": status, "body": ""}


def error_response(status: int, detail: Any) -> dict:
    """Mirrors FastAPI's default HTTPException handler: {"detail": ...}."""
    return json_response(status, {"detail": detail})


def message_response(status: int, message: str) -> dict:
    """Mirrors AuthMiddleware's JSONResponse({"message": ...}) on auth failure."""
    return json_response(status, {"message": message})
