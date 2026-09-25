import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import bootstrap
import apigw
from routes.deck import get_deck_service
from schemas.deck import DeckRead

_app = None


def handle(service, event, context):
    """Mirrors routes.deck.list_decks (GET /decks/, authenticated)."""
    try:
        user_id = apigw.require_user(event)
    except apigw.NotAuthorized:
        return apigw.message_response(401, "Not authorized")

    decks = service.list_decks(user_id)
    body = [DeckRead.model_validate(d, from_attributes=True).model_dump(mode="json") for d in decks]
    return apigw.json_response(200, body)


def handler(event, context):
    global _app
    if _app is None:
        _app = bootstrap.new_app()
    with bootstrap.session_scope(_app) as session:
        return handle(get_deck_service(session), event, context)
