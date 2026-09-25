import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import apigw


def handle(event, context):
    """Mirrors routes.health.health (GET /health/, public)."""
    return apigw.json_response(200, {"status": "OK"})


def handler(event, context):
    return handle(event, context)
