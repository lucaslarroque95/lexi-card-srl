import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import bootstrap
import apigw
from pydantic import ValidationError
from routes.card import _to_read, get_card_service
from routes.concept import get_concept_service
from routes.rule import get_rule_service
from routes.tag import get_tag_service
from schemas.card import CardAddTags

_app = None


def handle(service, tag_service, concept_service, rule_service, event, context):
    """Mirrors routes.card.add_tags (POST /cards/{card_id}/tags, authenticated)."""
    try:
        user_id = apigw.require_user(event)
    except apigw.NotAuthorized:
        return apigw.message_response(401, "Not authorized")

    card_id = apigw.uuid_path_param(event, "card_id")
    if card_id is None:
        return apigw.error_response(422, "invalid card_id")

    existing = service.get_card(card_id)
    if existing is None or existing.user_id != user_id:
        return apigw.error_response(404, "Card not found")

    try:
        payload = CardAddTags.model_validate_json(event.get("body") or "{}")
    except ValidationError as exc:
        return apigw.error_response(422, exc.errors())

    for tag_id in payload.tag_ids:
        tag = tag_service.get_tag(tag_id)
        if tag is None or tag.user_id != user_id:
            return apigw.error_response(404, f"Tag {tag_id} not found")

    service.add_tags(card_id, payload.tag_ids, user_id)
    read = _to_read(existing, service.get_tags(card_id), concept_service, rule_service)
    return apigw.json_response(201, read.model_dump(mode="json"))


def handler(event, context):
    global _app
    if _app is None:
        _app = bootstrap.new_app()
    with bootstrap.session_scope(_app) as session:
        return handle(
            get_card_service(session),
            get_tag_service(session),
            get_concept_service(session),
            get_rule_service(session),
            event,
            context,
        )
