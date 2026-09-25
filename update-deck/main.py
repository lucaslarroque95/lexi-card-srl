import os
import sys
from dataclasses import asdict

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import bootstrap
import apigw
from models.deck import Deck
from pydantic import ValidationError
from routes.deck import get_deck_service
from schemas.deck import DeckRead, DeckUpdate

_app = None


def handle(service, event, context):
    """Mirrors routes.deck.update_deck (PUT /decks/{deck_id}, authenticated)."""
    try:
        user_id = apigw.require_user(event)
    except apigw.NotAuthorized:
        return apigw.message_response(401, "Not authorized")

    deck_id = apigw.uuid_path_param(event, "deck_id")
    if deck_id is None:
        return apigw.error_response(422, "invalid deck_id")

    existing = service.get_deck(deck_id)
    if existing is None or existing.user_id != user_id:
        return apigw.error_response(404, "Deck not found")

    try:
        payload = DeckUpdate.model_validate_json(event.get("body") or "{}")
    except ValidationError as exc:
        return apigw.error_response(422, exc.errors())

    updated_data = {**asdict(existing), **payload.model_dump(exclude_none=True)}
    updated = service.update_deck(deck_id, Deck(**updated_data))
    return apigw.json_response(200, DeckRead.model_validate(updated, from_attributes=True).model_dump(mode="json"))


def handler(event, context):
    global _app
    if _app is None:
        _app = bootstrap.new_app()
    with bootstrap.session_scope(_app) as session:
        return handle(get_deck_service(session), event, context)
