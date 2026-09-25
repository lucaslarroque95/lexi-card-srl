import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import bootstrap
import apigw
from models.language import Language
from pydantic import ValidationError
from routes.language import get_language_service
from schemas.language import LanguageCreate, LanguageRead

_app = None


def handle(service, event, context):
    """Mirrors routes.language.create_language (POST /languages/, authenticated)."""
    try:
        user_id = apigw.require_user(event)
    except apigw.NotAuthorized:
        return apigw.message_response(401, "Not authorized")

    try:
        payload = LanguageCreate.model_validate_json(event.get("body") or "{}")
    except ValidationError as exc:
        return apigw.error_response(422, exc.errors())

    language = Language(user_id=user_id, name=payload.name, code=payload.code)
    created = service.create_language(language, user_id, payload.started_at)
    return apigw.json_response(201, LanguageRead.model_validate(created, from_attributes=True).model_dump(mode="json"))


def handler(event, context):
    global _app
    if _app is None:
        _app = bootstrap.new_app()
    with bootstrap.session_scope(_app) as session:
        return handle(get_language_service(session), event, context)
