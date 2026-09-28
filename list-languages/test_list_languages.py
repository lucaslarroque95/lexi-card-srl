import json
import uuid

from conftest import load_sibling_main
from fakes import FakeLanguageRepository, FakeUserLanguageRepository
from models.language import Language
from services.common_languages import COMMON_LANGUAGES
from services.language_service import LanguageService

main = load_sibling_main(__file__)


def make_service():
    return LanguageService(FakeLanguageRepository(), FakeUserLanguageRepository())


def list_codes(service, token):
    resp = main.handle(service, {"headers": {"authorization": token}}, {})
    assert resp["statusCode"] == 200
    return [lang["code"] for lang in json.loads(resp["body"])]


def test_new_user_gets_common_languages_in_order(make_token):
    codes = list_codes(make_service(), make_token())

    assert codes == [code for code, _ in COMMON_LANGUAGES]


def test_seeding_is_idempotent(make_token):
    service = make_service()
    token = make_token(uuid.uuid4())

    list_codes(service, token)
    codes = list_codes(service, token)

    assert len(codes) == len(COMMON_LANGUAGES)


def test_keeps_existing_languages_without_duplicating_codes(make_token):
    service = make_service()
    user_id = uuid.uuid4()
    service.language_repository.create(Language(user_id=user_id, name="English", code="en"))
    service.language_repository.create(Language(user_id=user_id, name="Klingon", code="tlh"))

    resp = main.handle(service, {"headers": {"authorization": make_token(user_id)}}, {})
    body = json.loads(resp["body"])

    assert [lang["code"] for lang in body].count("en") == 1
    assert body[0]["name"] == "English"  # the user's own row wins over the seed
    assert body[-1]["code"] == "tlh"  # custom languages go after the common ones


def test_does_not_see_other_users_languages(make_token):
    service = make_service()
    list_codes(service, make_token(uuid.uuid4()))

    codes = list_codes(service, make_token(uuid.uuid4()))

    assert len(codes) == len(COMMON_LANGUAGES)
