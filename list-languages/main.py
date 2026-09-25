import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import bootstrap
import apigw
from routes.language import get_language_service
from schemas.language import LanguageRead

_app = None


def handle(service, event, context):
    """Mirrors routes.language.list_languages (GET /languages/, authenticated)."""
    try:
        user_id = apigw.require_user(event)
    except apigw.NotAuthorized:
        return apigw.message_response(401, "Not authorized")

    languages = service.list_languages(user_id)
    body = [LanguageRead.model_validate(lang, from_attributes=True).model_dump(mode="json") for lang in languages]
    return apigw.json_response(200, body)


def handler(event, context):
    global _app
    if _app is None:
        _app = bootstrap.new_app()
    with bootstrap.session_scope(_app) as session:
        return handle(get_language_service(session), event, context)
