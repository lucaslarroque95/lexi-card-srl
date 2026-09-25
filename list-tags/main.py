import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import bootstrap
import apigw
from routes.tag import get_tag_service
from schemas.tag import TagRead

_app = None


def handle(service, event, context):
    """Mirrors routes.tag.list_tags (GET /tags/, authenticated)."""
    try:
        user_id = apigw.require_user(event)
    except apigw.NotAuthorized:
        return apigw.message_response(401, "Not authorized")

    tags = service.list_tags(user_id)
    body = [TagRead.model_validate(t, from_attributes=True).model_dump(mode="json") for t in tags]
    return apigw.json_response(200, body)


def handler(event, context):
    global _app
    if _app is None:
        _app = bootstrap.new_app()
    with bootstrap.session_scope(_app) as session:
        return handle(get_tag_service(session), event, context)
