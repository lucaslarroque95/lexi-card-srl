import os
import sys
from dataclasses import asdict

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import bootstrap
import apigw
from models.card import Card
from pydantic import ValidationError
from routes.card import _to_read, get_card_service
from routes.concept import get_concept_service
from routes.rule import get_rule_service
from schemas.card import CardUpdate

_app = None


def handle(service, concept_service, rule_service, event, context):
    """Mirrors routes.card.update_card (PUT /cards/{card_id}, authenticated)."""
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
        payload = CardUpdate.model_validate_json(event.get("body") or "{}")
    except ValidationError as exc:
        return apigw.error_response(422, exc.errors())

    updated_data = {**asdict(existing), **payload.model_dump(exclude_none=True)}
    updated = service.update_card(card_id, Card(**updated_data))
    read = _to_read(updated, service.get_tags(card_id), concept_service, rule_service)
    return apigw.json_response(200, read.model_dump(mode="json"))


def handler(event, context):
    global _app
    if _app is None:
        _app = bootstrap.new_app()
    with bootstrap.session_scope(_app) as session:
        return handle(
            get_card_service(session), get_concept_service(session), get_rule_service(session), event, context
        )
