import json
import uuid

from conftest import load_sibling_main
from fakes import FakeConceptRepository, FakeExampleRepository, FakeRuleRepository
from models.concept import Concept
from services.example_service import ExampleService

main = load_sibling_main(__file__)


def make_service():
    concept_repo = FakeConceptRepository()
    rule_repo = FakeRuleRepository()
    return ExampleService(FakeExampleRepository(), concept_repo, rule_repo), concept_repo


def test_requires_exactly_one_of_concept_or_rule(make_token):
    service, _ = make_service()
    event = {
        "headers": {"authorization": make_token()},
        "body": json.dumps({"example": "Ich habe einen Hund"}),
    }

    resp = main.handle(service, event, {})

    assert resp["statusCode"] == 400


def test_both_concept_and_rule_returns_400(make_token):
    service, _ = make_service()
    event = {
        "headers": {"authorization": make_token()},
        "body": json.dumps({"example": "x", "concept_id": str(uuid.uuid4()), "rule_id": str(uuid.uuid4())}),
    }

    resp = main.handle(service, event, {})

    assert resp["statusCode"] == 400


def test_concept_not_owned_by_caller_returns_404(make_token):
    service, concept_repo = make_service()
    concept = concept_repo.create(
        Concept(user_id=uuid.uuid4(), card_id=uuid.uuid4(), language_id=uuid.uuid4(), concept="Hund", explanation="dog")
    )

    event = {
        "headers": {"authorization": make_token(uuid.uuid4())},
        "body": json.dumps({"example": "Ich habe einen Hund", "concept_id": str(concept.id)}),
    }

    resp = main.handle(service, event, {})

    assert resp["statusCode"] == 404


def test_creates_example_for_owned_concept(make_token):
    service, concept_repo = make_service()
    user_id = uuid.uuid4()
    concept = concept_repo.create(
        Concept(user_id=user_id, card_id=uuid.uuid4(), language_id=uuid.uuid4(), concept="Hund", explanation="dog")
    )

    event = {
        "headers": {"authorization": make_token(user_id)},
        "body": json.dumps({"example": "Ich habe einen Hund", "concept_id": str(concept.id)}),
    }

    resp = main.handle(service, event, {})

    assert resp["statusCode"] == 201
    assert json.loads(resp["body"])["example"] == "Ich habe einen Hund"
