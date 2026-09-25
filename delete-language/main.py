import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import bootstrap
import apigw
from routes.language import get_language_service

_app = None


def handle(service, event, context):
    """Mirrors routes.language.delete_language (DELETE /languages/{language_id}, authenticated)."""
    try:
        user_id = apigw.require_user(event)
    except apigw.NotAuthorized:
        return apigw.message_response(401, "Not authorized")

    language_id = apigw.uuid_path_param(event, "language_id")
    if language_id is None:
        return apigw.error_response(422, "invalid language_id")

    existing = service.get_language(language_id)
    if existing is None or existing.user_id != user_id:
        return apigw.error_response(404, "Language not found")

    service.delete_language(language_id)
    return apigw.empty_response(204)


def handler(event, context):
    global _app
    if _app is None:
        _app = bootstrap.new_app()
    with bootstrap.session_scope(_app) as session:
        return handle(get_language_service(session), event, context)
