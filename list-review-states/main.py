import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import bootstrap
import apigw
from routes.review_state import get_review_state_service
from schemas.review_state import ReviewStateRead

_app = None


def handle(service, event, context):
    """Mirrors routes.review_state.list_review_states (GET /review-states/, authenticated)."""
    try:
        user_id = apigw.require_user(event)
    except apigw.NotAuthorized:
        return apigw.message_response(401, "Not authorized")

    review_states = service.list_review_states(user_id)
    body = [ReviewStateRead.model_validate(r, from_attributes=True).model_dump(mode="json") for r in review_states]
    return apigw.json_response(200, body)


def handler(event, context):
    global _app
    if _app is None:
        _app = bootstrap.new_app()
    with bootstrap.session_scope(_app) as session:
        return handle(get_review_state_service(session), event, context)
