import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import bootstrap
import apigw
from routes.review_state import get_review_state_service

_app = None


def handle(service, event, context):
    """Mirrors routes.review_state.delete_review_state (DELETE /review-states/{review_state_id}, authenticated)."""
    try:
        user_id = apigw.require_user(event)
    except apigw.NotAuthorized:
        return apigw.message_response(401, "Not authorized")

    review_state_id = apigw.uuid_path_param(event, "review_state_id")
    if review_state_id is None:
        return apigw.error_response(422, "invalid review_state_id")

    existing = service.get_review_state(review_state_id)
    if existing is None or existing.user_id != user_id:
        return apigw.error_response(404, "Review state not found")

    service.delete_review_state(review_state_id)
    return apigw.empty_response(204)


def handler(event, context):
    global _app
    if _app is None:
        _app = bootstrap.new_app()
    with bootstrap.session_scope(_app) as session:
        return handle(get_review_state_service(session), event, context)
