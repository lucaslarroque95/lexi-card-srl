import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import bootstrap
import apigw
from routes.language import get_language_service
from schemas.language import LanguageRead

_app = None


def handle(service, event, context):
    """Mirrors routes.language.get_language (GET /languages/{language_id}, authenticated)."""
    try:
        user_id = apigw.require_user(event)
    except apigw.NotAuthorized:
        return apigw.message_response(401, "Not authorized")

    language_id = apigw.uuid_path_param(event, "language_id")
    if language_id is None:
        return apigw.error_response(422, "invalid language_id")

    language = service.get_language(language_id)
    if language is None or language.user_id != user_id:
        return apigw.error_response(404, "Language not found")

    return apigw.json_response(200, LanguageRead.model_validate(language, from_attributes=True).model_dump(mode="json"))


def handler(event, context):
    global _app
    if _app is None:
        _app = bootstrap.new_app()
    with bootstrap.session_scope(_app) as session:
        return handle(get_language_service(session), event, context)
