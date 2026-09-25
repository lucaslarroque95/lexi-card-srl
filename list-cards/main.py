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
    """Mirrors routes.card.list_cards (GET /cards/, authenticated)."""
    try:
        user_id = apigw.require_user(event)
    except apigw.NotAuthorized:
        return apigw.message_response(401, "Not authorized")

    body = [
        _to_read(card, service.get_tags(card.id), concept_service, rule_service).model_dump(mode="json")
        for card in service.list_cards(user_id)
    ]
    return apigw.json_response(200, body)


def handler(event, context):
    global _app
    if _app is None:
        _app = bootstrap.new_app()
    with bootstrap.session_scope(_app) as session:
        return handle(
            get_card_service(session), get_concept_service(session), get_rule_service(session), event, context
        )
