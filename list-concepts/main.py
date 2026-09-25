import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import bootstrap
import apigw
from routes.concept import concept_to_read, get_concept_service

_app = None


def handle(service, event, context):
    """Mirrors routes.concept.list_concepts (GET /concepts/, authenticated)."""
    try:
        user_id = apigw.require_user(event)
    except apigw.NotAuthorized:
        return apigw.message_response(401, "Not authorized")

    body = [
        concept_to_read(c, service.get_examples(c.id)).model_dump(mode="json")
        for c in service.list_concepts(user_id)
    ]
    return apigw.json_response(200, body)


def handler(event, context):
    global _app
    if _app is None:
        _app = bootstrap.new_app()
    with bootstrap.session_scope(_app) as session:
        return handle(get_concept_service(session), event, context)
