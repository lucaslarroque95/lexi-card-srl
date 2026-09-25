import importlib.util
import os
import pathlib
import time
import uuid as uuid_lib

# routes/*.py import db.db at module load (for FastAPI's Depends(get_session)
# default), and db.db reads POSTGRES_* eagerly at import time — same issue
# lexi-card-ms/pytest.ini's sibling lexi-rag-ms works around in CI: dummy
# values so importing succeeds, even though these tests never open a real
# connection (they hand handle() a fake-repository-backed service instead).
os.environ.setdefault("POSTGRES_USER", "test")
os.environ.setdefault("POSTGRES_PASSWORD", "test")
os.environ.setdefault("POSTGRES_SERVER", "localhost")
os.environ.setdefault("POSTGRES_PORT", "5432")
os.environ.setdefault("POSTGRES_DB", "test")

import jwt as pyjwt  # noqa: E402
import pytest  # noqa: E402
from rsa_keys import generate_keypair  # noqa: E402

import auth.jwt as auth_jwt  # noqa: E402


@pytest.fixture
def keypair():
    """Disposable RSA pair, same as lexi-card-ms/test/test_auth_jwt.py's own fixture."""
    return generate_keypair()


@pytest.fixture(autouse=True)
def patch_public_key(keypair, monkeypatch):
    """auth.jwt reads its public key from disk at import time; tests swap it
    for one whose matching private half they control, so they can sign
    their own tokens instead of needing lexi-users-ms's real key pair."""
    _, public_pem = keypair
    monkeypatch.setattr(auth_jwt, "_PUBLIC_KEY", public_pem)


@pytest.fixture
def make_token(keypair):
    private_pem, _ = keypair

    def _make(user_id=None, roles: str = "") -> str:
        claims = {
            "userId": str(user_id if user_id is not None else uuid_lib.uuid4()),
            "role": roles,
            "exp": int(time.time()) + 3600,
        }
        return pyjwt.encode(claims, private_pem, algorithm="RS256")

    return _make


def load_sibling_main(test_file: str):
    """Loads the main.py next to a given test file as a uniquely-named
    module. Every endpoint folder has its own main.py, so a plain
    `import main` would collide across them via sys.modules (whichever
    test ran first "wins" and every later test silently imports the wrong
    handler) — loading by explicit path instead sidesteps that entirely."""
    directory = pathlib.Path(test_file).parent
    module_name = f"_lambda_main_{directory.name.replace('-', '_')}"
    spec = importlib.util.spec_from_file_location(module_name, directory / "main.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module
