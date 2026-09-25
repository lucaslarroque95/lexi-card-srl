import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import bootstrap
import apigw
from routes.example import get_example_service
from schemas.example import ExampleRead

_app = None


def handle(service, event, context):
    """Mirrors routes.example.list_examples (GET /examples/, authenticated)."""
    try:
        user_id = apigw.require_user(event)
    except apigw.NotAuthorized:
        return apigw.message_response(401, "Not authorized")

    examples = service.list_examples(user_id)
    body = [ExampleRead.model_validate(e, from_attributes=True).model_dump(mode="json") for e in examples]
    return apigw.json_response(200, body)


def handler(event, context):
    global _app
    if _app is None:
        _app = bootstrap.new_app()
    with bootstrap.session_scope(_app) as session:
        return handle(get_example_service(session), event, context)
