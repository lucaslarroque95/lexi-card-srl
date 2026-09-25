import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import bootstrap
import apigw
from routes.card import _to_read, get_card_service
from routes.concept import get_concept_service
from routes.rule import get_rule_service

_app = None


def handle(service, concept_service, rule_service, event, context):
    """Mirrors routes.card.get_card (GET /cards/{card_id}, authenticated)."""
    try:
        user_id = apigw.require_user(event)
    except apigw.NotAuthorized:
        return apigw.message_response(401, "Not authorized")

    card_id = apigw.uuid_path_param(event, "card_id")
    if card_id is None:
        return apigw.error_response(422, "invalid card_id")

    card = service.get_card(card_id)
    if card is None or card.user_id != user_id:
        return apigw.error_response(404, "Card not found")

    read = _to_read(card, service.get_tags(card_id), concept_service, rule_service)
    return apigw.json_response(200, read.model_dump(mode="json"))


def handler(event, context):
    global _app
    if _app is None:
        _app = bootstrap.new_app()
    with bootstrap.session_scope(_app) as session:
        return handle(
            get_card_service(session), get_concept_service(session), get_rule_service(session), event, context
        )
