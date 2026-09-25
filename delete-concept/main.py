import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import bootstrap
import apigw
from routes.concept import get_concept_service

_app = None


def handle(service, event, context):
    """Mirrors routes.concept.delete_concept (DELETE /concepts/{concept_id}, authenticated)."""
    try:
        user_id = apigw.require_user(event)
    except apigw.NotAuthorized:
        return apigw.message_response(401, "Not authorized")

    concept_id = apigw.uuid_path_param(event, "concept_id")
    if concept_id is None:
        return apigw.error_response(422, "invalid concept_id")

    existing = service.get_concept(concept_id)
    if existing is None or existing.user_id != user_id:
        return apigw.error_response(404, "Concept not found")

    service.delete_concept(concept_id)
    return apigw.empty_response(204)


def handler(event, context):
    global _app
    if _app is None:
        _app = bootstrap.new_app()
    with bootstrap.session_scope(_app) as session:
        return handle(get_concept_service(session), event, context)
