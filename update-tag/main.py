import os
import sys
from dataclasses import asdict

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import bootstrap
import apigw
from models.tag import Tag
from pydantic import ValidationError
from routes.tag import get_tag_service
from schemas.tag import TagRead, TagUpdate

_app = None


def handle(service, event, context):
    """Mirrors routes.tag.update_tag (PUT /tags/{tag_id}, authenticated)."""
    try:
        user_id = apigw.require_user(event)
    except apigw.NotAuthorized:
        return apigw.message_response(401, "Not authorized")

    tag_id = apigw.uuid_path_param(event, "tag_id")
    if tag_id is None:
        return apigw.error_response(422, "invalid tag_id")

    existing = service.get_tag(tag_id)
    if existing is None or existing.user_id != user_id:
        return apigw.error_response(404, "Tag not found")

    try:
        payload = TagUpdate.model_validate_json(event.get("body") or "{}")
    except ValidationError as exc:
        return apigw.error_response(422, exc.errors())

    updated_data = {**asdict(existing), **payload.model_dump(exclude_none=True)}
    updated = service.update_tag(tag_id, Tag(**updated_data))
    return apigw.json_response(200, TagRead.model_validate(updated, from_attributes=True).model_dump(mode="json"))


def handler(event, context):
    global _app
    if _app is None:
        _app = bootstrap.new_app()
    with bootstrap.session_scope(_app) as session:
        return handle(get_tag_service(session), event, context)
