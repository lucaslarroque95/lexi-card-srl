import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import bootstrap
import apigw
from models.review_state import ReviewState
from pydantic import ValidationError
from routes.review_state import get_review_state_service
from schemas.review_state import ReviewStateCreate, ReviewStateRead

_app = None


def handle(service, event, context):
    """Mirrors routes.review_state.create_review_state (POST /review-states/, authenticated)."""
    try:
        user_id = apigw.require_user(event)
    except apigw.NotAuthorized:
        return apigw.message_response(401, "Not authorized")

    try:
        payload = ReviewStateCreate.model_validate_json(event.get("body") or "{}")
    except ValidationError as exc:
        return apigw.error_response(422, exc.errors())

    review_state = ReviewState(user_id=user_id, **payload.model_dump(exclude_none=True))
    created = service.create_review_state(review_state)
    return apigw.json_response(
        201, ReviewStateRead.model_validate(created, from_attributes=True).model_dump(mode="json")
    )


def handler(event, context):
    global _app
    if _app is None:
        _app = bootstrap.new_app()
    with bootstrap.session_scope(_app) as session:
        return handle(get_review_state_service(session), event, context)
