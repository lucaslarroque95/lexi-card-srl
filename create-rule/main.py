import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import bootstrap
import apigw
from models.rule import Rule
from pydantic import ValidationError
from routes.rule import get_rule_service, rule_to_read
from schemas.rule import RuleCreate

_app = None


def handle(service, event, context):
    """Mirrors routes.rule.create_rule (POST /rules/, authenticated)."""
    try:
        user_id = apigw.require_user(event)
    except apigw.NotAuthorized:
        return apigw.message_response(401, "Not authorized")

    try:
        payload = RuleCreate.model_validate_json(event.get("body") or "{}")
    except ValidationError as exc:
        return apigw.error_response(422, exc.errors())

    data = payload.model_dump(exclude_none=True, exclude={"examples"})
    rule = Rule(user_id=user_id, **data)
    created = service.create_rule(rule, payload.examples)
    read = rule_to_read(created, service.get_examples(created.id))
    return apigw.json_response(201, read.model_dump(mode="json"))


def handler(event, context):
    global _app
    if _app is None:
        _app = bootstrap.new_app()
    with bootstrap.session_scope(_app) as session:
        return handle(get_rule_service(session), event, context)
