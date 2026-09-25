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
from models.card import Card, CardType
from models.tag import Tag
from services.card_service import CardService
from services.concept_service import ConceptService
from services.rule_service import RuleService
from services.tag_service import TagService

main = load_sibling_main(__file__)


def make_services():
    card_tag_repo = FakeCardTagRepository()
    tag_repo = FakeTagRepository(card_tag_repo)
    card_repo = FakeCardRepository()
    card_service = CardService(card_repo, card_tag_repo, tag_repo)
    tag_service = TagService(tag_repo)
    concept_service = ConceptService(FakeConceptRepository(), FakeExampleRepository())
    rule_service = RuleService(FakeRuleRepository(), FakeExampleRepository())
    return card_service, card_repo, tag_repo, tag_service, concept_service, rule_service


def test_adds_owned_tags(make_token):
    card_service, card_repo, tag_repo, tag_service, concept_service, rule_service = make_services()
    user_id = uuid.uuid4()
    card = card_repo.create(Card(user_id=user_id, deck_id=uuid.uuid4(), card_type=CardType.VOCAB))
    tag = tag_repo.create(Tag(user_id=user_id, key="level", value="A1"))

    event = {
        "headers": {"authorization": make_token(user_id)},
        "pathParameters": {"card_id": str(card.id)},
        "body": json.dumps({"tag_ids": [str(tag.id)]}),
    }

    resp = main.handle(card_service, tag_service, concept_service, rule_service, event, {})

    assert resp["statusCode"] == 201
    body = json.loads(resp["body"])
    assert [t["id"] for t in body["tags"]] == [str(tag.id)]


def test_tag_owned_by_another_user_returns_404(make_token):
    card_service, card_repo, tag_repo, tag_service, concept_service, rule_service = make_services()
    user_id = uuid.uuid4()
    card = card_repo.create(Card(user_id=user_id, deck_id=uuid.uuid4(), card_type=CardType.VOCAB))
    other_users_tag = tag_repo.create(Tag(user_id=uuid.uuid4(), key="level", value="A1"))

    event = {
        "headers": {"authorization": make_token(user_id)},
        "pathParameters": {"card_id": str(card.id)},
        "body": json.dumps({"tag_ids": [str(other_users_tag.id)]}),
    }

    resp = main.handle(card_service, tag_service, concept_service, rule_service, event, {})

    assert resp["statusCode"] == 404
