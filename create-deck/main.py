import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import bootstrap
import apigw
from models.deck import Deck
from pydantic import ValidationError
from routes.deck import get_deck_service
from schemas.deck import DeckCreate, DeckRead

_app = None


def handle(service, event, context):
    """Mirrors routes.deck.create_deck (POST /decks/, authenticated)."""
    try:
        user_id = apigw.require_user(event)
    except apigw.NotAuthorized:
        return apigw.message_response(401, "Not authorized")

    try:
        payload = DeckCreate.model_validate_json(event.get("body") or "{}")
    except ValidationError as exc:
        return apigw.error_response(422, exc.errors())

    deck = Deck(user_id=user_id, **payload.model_dump(exclude_none=True))
    created = service.create_deck(deck)
    return apigw.json_response(201, DeckRead.model_validate(created, from_attributes=True).model_dump(mode="json"))


def handler(event, context):
    global _app
    if _app is None:
        _app = bootstrap.new_app()
    with bootstrap.session_scope(_app) as session:
        return handle(get_deck_service(session), event, context)
