import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import bootstrap
import apigw
from models.card import Card
from pydantic import ValidationError
from routes.card import _to_read, get_card_service
from routes.concept import get_concept_service
from routes.rule import get_rule_service
from schemas.card import CardCreate

_app = None


def handle(service, concept_service, rule_service, event, context):
    """Mirrors routes.card.create_card (POST /cards/, authenticated)."""
    try:
        user_id = apigw.require_user(event)
    except apigw.NotAuthorized:
        return apigw.message_response(401, "Not authorized")

    try:
        payload = CardCreate.model_validate_json(event.get("body") or "{}")
    except ValidationError as exc:
        return apigw.error_response(422, exc.errors())

    data = payload.model_dump(exclude_none=True, exclude={"tag_ids"})
    card = Card(user_id=user_id, **data)
    created = service.create_card(card, payload.tag_ids)
    read = _to_read(created, service.get_tags(created.id), concept_service, rule_service)
    return apigw.json_response(201, read.model_dump(mode="json"))


def handler(event, context):
    global _app
    if _app is None:
        _app = bootstrap.new_app()
    with bootstrap.session_scope(_app) as session:
        return handle(
            get_card_service(session), get_concept_service(session), get_rule_service(session), event, context
        )
