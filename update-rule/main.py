import os
import sys
from dataclasses import asdict

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import bootstrap
import apigw
from models.rule import Rule
from pydantic import ValidationError
from routes.rule import get_rule_service, rule_to_read
from schemas.rule import RuleUpdate

_app = None


def handle(service, event, context):
    """Mirrors routes.rule.update_rule (PUT /rules/{rule_id}, authenticated)."""
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
        payload = RuleUpdate.model_validate_json(event.get("body") or "{}")
    except ValidationError as exc:
        return apigw.error_response(422, exc.errors())

    updated_data = {**asdict(existing), **payload.model_dump(exclude_none=True)}
    updated = service.update_rule(rule_id, Rule(**updated_data))
    read = rule_to_read(updated, service.get_examples(rule_id))
    return apigw.json_response(200, read.model_dump(mode="json"))


def handler(event, context):
    global _app
    if _app is None:
        _app = bootstrap.new_app()
    with bootstrap.session_scope(_app) as session:
        return handle(get_rule_service(session), event, context)
