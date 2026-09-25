import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import bootstrap
import apigw
from routes.rule import get_rule_service, rule_to_read

_app = None


def handle(service, event, context):
    """Mirrors routes.rule.get_rule (GET /rules/{rule_id}, authenticated)."""
    try:
        user_id = apigw.require_user(event)
    except apigw.NotAuthorized:
        return apigw.message_response(401, "Not authorized")

    rule_id = apigw.uuid_path_param(event, "rule_id")
    if rule_id is None:
        return apigw.error_response(422, "invalid rule_id")

    rule = service.get_rule(rule_id)
    if rule is None or rule.user_id != user_id:
        return apigw.error_response(404, "Rule not found")

    read = rule_to_read(rule, service.get_examples(rule_id))
    return apigw.json_response(200, read.model_dump(mode="json"))


def handler(event, context):
    global _app
    if _app is None:
        _app = bootstrap.new_app()
    with bootstrap.session_scope(_app) as session:
        return handle(get_rule_service(session), event, context)
