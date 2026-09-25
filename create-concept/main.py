import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import bootstrap
import apigw
from models.concept import Concept
from pydantic import ValidationError
from routes.concept import concept_to_read, get_concept_service
from schemas.concept import ConceptCreate

_app = None


def handle(service, event, context):
    """Mirrors routes.concept.create_concept (POST /concepts/, authenticated)."""
    try:
        user_id = apigw.require_user(event)
    except apigw.NotAuthorized:
        return apigw.message_response(401, "Not authorized")

    try:
        payload = ConceptCreate.model_validate_json(event.get("body") or "{}")
    except ValidationError as exc:
        return apigw.error_response(422, exc.errors())

    data = payload.model_dump(exclude_none=True, exclude={"examples"})
    concept = Concept(user_id=user_id, **data)
    created = service.create_concept(concept, payload.examples)
    read = concept_to_read(created, service.get_examples(created.id))
    return apigw.json_response(201, read.model_dump(mode="json"))


def handler(event, context):
    global _app
    if _app is None:
        _app = bootstrap.new_app()
    with bootstrap.session_scope(_app) as session:
        return handle(get_concept_service(session), event, context)
