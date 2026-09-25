import json
import uuid

from conftest import load_sibling_main
from fakes import FakeDeckRepository
from services.deck_service import DeckService

main = load_sibling_main(__file__)


def make_service():
    return DeckService(FakeDeckRepository())


def test_creates_deck(make_token):
    service = make_service()
    user_id = uuid.uuid4()
    event = {
        "headers": {"authorization": make_token(user_id)},
        "body": json.dumps({"name": "Spanish A1"}),
    }

    resp = main.handle(service, event, {})

    assert resp["statusCode"] == 201
    body = json.loads(resp["body"])
    assert body["name"] == "Spanish A1"
    assert body["user_id"] == str(user_id)


def test_no_token_returns_401():
    service = make_service()
    resp = main.handle(service, {"headers": {}, "body": "{}"}, {})

    assert resp["statusCode"] == 401
    assert json.loads(resp["body"]) == {"message": "Not authorized"}


def test_invalid_body_returns_422(make_token):
    service = make_service()
    event = {"headers": {"authorization": make_token()}, "body": "not-json"}

    resp = main.handle(service, event, {})

    assert resp["statusCode"] == 422
