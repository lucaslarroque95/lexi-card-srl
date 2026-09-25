import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import bootstrap
import apigw
from routes.example import get_example_service
from schemas.example import ExampleRead

_app = None


def handle(service, event, context):
    """Mirrors routes.example.get_example (GET /examples/{example_id}, authenticated)."""
    try:
        user_id = apigw.require_user(event)
    except apigw.NotAuthorized:
        return apigw.message_response(401, "Not authorized")

    example_id = apigw.uuid_path_param(event, "example_id")
    if example_id is None:
        return apigw.error_response(422, "invalid example_id")

    example = service.get_example(example_id)
    if example is None or service.get_owner(example) != user_id:
        return apigw.error_response(404, "Example not found")

    return apigw.json_response(200, ExampleRead.model_validate(example, from_attributes=True).model_dump(mode="json"))


def handler(event, context):
    global _app
    if _app is None:
        _app = bootstrap.new_app()
    with bootstrap.session_scope(_app) as session:
        return handle(get_example_service(session), event, context)
