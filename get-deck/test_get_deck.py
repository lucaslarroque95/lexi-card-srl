import json
import uuid

from conftest import load_sibling_main
from fakes import FakeDeckRepository
from models.deck import Deck
from services.deck_service import DeckService

main = load_sibling_main(__file__)


def make_service():
    return DeckService(FakeDeckRepository())


def test_not_found_returns_404(make_token):
    service = make_service()
    event = {
        "headers": {"authorization": make_token()},
        "pathParameters": {"deck_id": str(uuid.uuid4())},
    }

    resp = main.handle(service, event, {})

    assert resp["statusCode"] == 404


def test_other_users_deck_returns_404(make_token):
    service = make_service()
    owner_id = uuid.uuid4()
    deck = service.repository.create(Deck(user_id=owner_id, name="Spanish A1"))

    event = {
        "headers": {"authorization": make_token(uuid.uuid4())},
        "pathParameters": {"deck_id": str(deck.id)},
    }
    resp = main.handle(service, event, {})

    assert resp["statusCode"] == 404


def test_returns_own_deck(make_token):
    service = make_service()
    owner_id = uuid.uuid4()
    deck = service.repository.create(Deck(user_id=owner_id, name="Spanish A1"))

    event = {
        "headers": {"authorization": make_token(owner_id)},
        "pathParameters": {"deck_id": str(deck.id)},
    }
    resp = main.handle(service, event, {})

    assert resp["statusCode"] == 200
    assert json.loads(resp["body"])["name"] == "Spanish A1"


def test_invalid_uuid_returns_422(make_token):
    service = make_service()
    event = {
        "headers": {"authorization": make_token()},
        "pathParameters": {"deck_id": "not-a-uuid"},
    }

    resp = main.handle(service, event, {})

    assert resp["statusCode"] == 422
