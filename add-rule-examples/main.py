import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import bootstrap
import apigw
from pydantic import ValidationError
from routes.rule import get_rule_service, rule_to_read
from schemas.example import ExamplesAdd

_app = None


def handle(service, event, context):
    """Mirrors routes.rule.add_examples (POST /rules/{rule_id}/examples, authenticated)."""
    try:
        user_id = apigw.require_user(event)
    except apigw.NotAuthorized:
        return apigw.message_response(401, "Not authorized")

    rule_id = apigw.uuid_path_param(event, "rule_id")
    if rule_id is None:
        return apigw.error_response(422, "invalid rule_id")

    existing = service.get_rule(rule_id)
    if existing is None or existing.user_id != user_id:
        return apigw.error_response(404, "Rule not found")

    try:
        payload = ExamplesAdd.model_validate_json(event.get("body") or "{}")
    except ValidationError as exc:
        return apigw.error_response(422, exc.errors())

    service.add_examples(rule_id, payload.examples)
    read = rule_to_read(existing, service.get_examples(rule_id))
    return apigw.json_response(201, read.model_dump(mode="json"))


def handler(event, context):
    global _app
    if _app is None:
        _app = bootstrap.new_app()
    with bootstrap.session_scope(_app) as session:
        return handle(get_rule_service(session), event, context)
