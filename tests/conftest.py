from pathlib import Path
import os

import pytest


TEST_DATABASE = Path("/tmp/sir_device_pytest.db")
TEST_DATABASE.unlink(missing_ok=True)
os.environ["DATABASE_URL"] = f"sqlite:///{TEST_DATABASE}"
os.environ["AUTO_CREATE_SCHEMA"] = "true"
os.environ["SECRET_KEY"] = "pytest-secret-key-with-more-than-thirty-two-characters"

from app.infrastructure.db.base import Base  # noqa: E402
from app.infrastructure.db.session import SessionLocal, engine  # noqa: E402
import app.infrastructure.db.models  # noqa: E402,F401


@pytest.fixture(autouse=True)
def clean_database():
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)
    yield
    Base.metadata.drop_all(bind=engine)


@pytest.fixture
def db_session():
    with SessionLocal() as session:
        yield session
