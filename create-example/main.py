import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import bootstrap
import apigw
from models.example import Example
from pydantic import ValidationError
from routes.example import get_example_service
from schemas.example import ExampleCreate, ExampleRead

_app = None


def handle(service, event, context):
    """Mirrors routes.example.create_example (POST /examples/, authenticated)."""
    try:
        user_id = apigw.require_user(event)
    except apigw.NotAuthorized:
        return apigw.message_response(401, "Not authorized")

    try:
        payload = ExampleCreate.model_validate_json(event.get("body") or "{}")
    except ValidationError as exc:
        return apigw.error_response(422, exc.errors())

    if (payload.concept_id is None) == (payload.rule_id is None):
        return apigw.error_response(400, "Debe indicarse exactamente uno de concept_id o rule_id")

    example = Example(example=payload.example, concept_id=payload.concept_id, rule_id=payload.rule_id)
    owner = service.get_owner(example)
    if owner is None or owner != user_id:
        return apigw.error_response(404, "Concept or Rule not found")

    created = service.create_example(example)
    return apigw.json_response(201, ExampleRead.model_validate(created, from_attributes=True).model_dump(mode="json"))


def handler(event, context):
    global _app
    if _app is None:
        _app = bootstrap.new_app()
    with bootstrap.session_scope(_app) as session:
        return handle(get_example_service(session), event, context)
