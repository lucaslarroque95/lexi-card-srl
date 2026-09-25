import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import bootstrap
import apigw
from models.tag import Tag
from pydantic import ValidationError
from routes.tag import get_tag_service
from schemas.tag import TagCreate, TagRead

_app = None


def handle(service, event, context):
    """Mirrors routes.tag.create_tag (POST /tags/, authenticated)."""
    try:
        user_id = apigw.require_user(event)
    except apigw.NotAuthorized:
        return apigw.message_response(401, "Not authorized")

    try:
        payload = TagCreate.model_validate_json(event.get("body") or "{}")
    except ValidationError as exc:
        return apigw.error_response(422, exc.errors())

    tag = Tag(user_id=user_id, **payload.model_dump(exclude_none=True))
    created = service.create_tag(tag)
    return apigw.json_response(201, TagRead.model_validate(created, from_attributes=True).model_dump(mode="json"))


def handler(event, context):
    global _app
    if _app is None:
        _app = bootstrap.new_app()
    with bootstrap.session_scope(_app) as session:
        return handle(get_tag_service(session), event, context)
