import json
import uuid

from conftest import load_sibling_main
from fakes import (
    FakeCardRepository,
    FakeCardTagRepository,
    FakeConceptRepository,
    FakeExampleRepository,
    FakeRuleRepository,
    FakeTagRepository,
)
from models.tag import Tag
from services.card_service import CardService
from services.concept_service import ConceptService
from services.rule_service import RuleService

main = load_sibling_main(__file__)


def make_services():
    card_tag_repo = FakeCardTagRepository()
    tag_repo = FakeTagRepository(card_tag_repo)
    card_service = CardService(FakeCardRepository(), card_tag_repo, tag_repo)
    concept_service = ConceptService(FakeConceptRepository(), FakeExampleRepository())
    rule_service = RuleService(FakeRuleRepository(), FakeExampleRepository())
    return card_service, tag_repo, concept_service, rule_service


def test_creates_card_with_tags(make_token):
    card_service, tag_repo, concept_service, rule_service = make_services()
    user_id = uuid.uuid4()
    tag = tag_repo.create(Tag(user_id=user_id, key="level", value="A1"))

    event = {
        "headers": {"authorization": make_token(user_id)},
        "body": json.dumps({"deck_id": str(uuid.uuid4()), "card_type": "vocab", "tag_ids": [str(tag.id)]}),
    }

    resp = main.handle(card_service, concept_service, rule_service, event, {})

    assert resp["statusCode"] == 201
    body = json.loads(resp["body"])
    assert body["card_type"] == "vocab"
    assert [t["id"] for t in body["tags"]] == [str(tag.id)]
    assert body["concepts"] == []
    assert body["rules"] == []


def test_no_token_returns_401():
    card_service, _, concept_service, rule_service = make_services()
    resp = main.handle(card_service, concept_service, rule_service, {"headers": {}, "body": "{}"}, {})

    assert resp["statusCode"] == 401
