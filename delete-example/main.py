import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import bootstrap
import apigw
from routes.example import get_example_service

_app = None


def handle(service, event, context):
    """Mirrors routes.example.delete_example (DELETE /examples/{example_id}, authenticated)."""
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

    service.delete_example(example_id)
    return apigw.empty_response(204)


def handler(event, context):
    global _app
    if _app is None:
        _app = bootstrap.new_app()
    with bootstrap.session_scope(_app) as session:
        return handle(get_example_service(session), event, context)
