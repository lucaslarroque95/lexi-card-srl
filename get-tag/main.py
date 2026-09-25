import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import bootstrap
import apigw
from routes.tag import get_tag_service
from schemas.tag import TagRead

_app = None


def handle(service, event, context):
    """Mirrors routes.tag.get_tag (GET /tags/{tag_id}, authenticated)."""
    try:
        user_id = apigw.require_user(event)
    except apigw.NotAuthorized:
        return apigw.message_response(401, "Not authorized")

    tag_id = apigw.uuid_path_param(event, "tag_id")
    if tag_id is None:
        return apigw.error_response(422, "invalid tag_id")

    tag = service.get_tag(tag_id)
    if tag is None or tag.user_id != user_id:
        return apigw.error_response(404, "Tag not found")

    return apigw.json_response(200, TagRead.model_validate(tag, from_attributes=True).model_dump(mode="json"))


def handler(event, context):
    global _app
    if _app is None:
        _app = bootstrap.new_app()
    with bootstrap.session_scope(_app) as session:
        return handle(get_tag_service(session), event, context)
