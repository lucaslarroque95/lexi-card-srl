"""Wires the real Postgres engine once per Lambda cold start.

Each handler's handler() calls new_app() and opens one Session per
invocation over the shared engine — the same lifecycle db.get_session()
gives FastAPI per-request, just with the engine (the expensive part: the
connection pool) cached across warm invocations instead of rebuilt every
time. Tests never call new_app(): they build a service directly around a
fake repository (see test/fakes.py) and hand it straight to a
handler's handle(), so no real Postgres/env vars are needed to run them.
"""

from contextlib import contextmanager
from dataclasses import dataclass
from typing import Any, Iterator


@dataclass
class App:
    engine: Any  # sqlalchemy.Engine — typed loosely so importing this module never needs sqlmodel


def new_app() -> App:
    # Imported here, not at module load: db.db reads POSTGRES_* env vars at
    # import time, which would blow up importing this module under pytest.
    from db.db import create_db_and_tables, engine

    create_db_and_tables()
    return App(engine=engine)


@contextmanager
def session_scope(app: App) -> Iterator[Any]:
    from sqlmodel import Session

    with Session(app.engine) as session:
        yield session
