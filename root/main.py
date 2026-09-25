import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import apigw


def handle(event, context):
    """Mirrors routes.root.root (GET /, public)."""
    return apigw.json_response(200, {"name": "Vocabulary ms", "version": "1.0.0", "message": "API is running"})


def handler(event, context):
    return handle(event, context)
