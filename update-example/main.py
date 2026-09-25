import os
import sys
from dataclasses import asdict

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import bootstrap
import apigw
from models.example import Example
from pydantic import ValidationError
from routes.example import get_example_service
from schemas.example import ExampleRead, ExampleUpdate

_app = None


def handle(service, event, context):
    """Mirrors routes.example.update_example (PUT /examples/{example_id}, authenticated)."""
    try:
        user_id = apigw.require_user(event)
    except apigw.NotAuthorized:
        return apigw.message_response(401, "Not authorized")

    example_id = apigw.uuid_path_param(event, "example_id")
    if example_id is None:
        return apigw.error_response(422, "invalid example_id")

    existing = service.get_example(example_id)
    if existing is None or service.get_owner(existing) != user_id:
        return apigw.error_response(404, "Example not found")

    try:
        payload = ExampleUpdate.model_validate_json(event.get("body") or "{}")
    except ValidationError as exc:
        return apigw.error_response(422, exc.errors())

    updated_data = {**asdict(existing), **payload.model_dump(exclude_none=True)}
    updated = service.update_example(example_id, Example(**updated_data))
    return apigw.json_response(200, ExampleRead.model_validate(updated, from_attributes=True).model_dump(mode="json"))


def handler(event, context):
    global _app
    if _app is None:
        _app = bootstrap.new_app()
    with bootstrap.session_scope(_app) as session:
        return handle(get_example_service(session), event, context)
