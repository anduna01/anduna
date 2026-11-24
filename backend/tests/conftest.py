import os
import tempfile

import pytest

# Aislar los tests: base y almacenamiento temporales, sin claves reales ni worker en segundo plano.
_tmp = tempfile.mkdtemp(prefix="vcf-test-")
os.environ["DATABASE_URL"] = f"sqlite:///{_tmp}/test.db"
os.environ["STORAGE_DIR"] = f"{_tmp}/storage"
os.environ["ANTHROPIC_API_KEY"] = ""
os.environ["YOUTUBE_API_KEY"] = ""
os.environ["JOBS_WORKER_ENABLED"] = "false"


@pytest.fixture()
def client():
    from fastapi.testclient import TestClient

    from app.main import create_app

    with TestClient(create_app()) as c:  # ejecuta lifespan → migraciones
        yield c


@pytest.fixture()
def db(client):
    from app.db.session import SessionLocal

    with SessionLocal() as s:
        yield s


@pytest.fixture(scope="session", autouse=True)
def _migrate():
    from app.db.migrate import upgrade_to_head

    upgrade_to_head()


@pytest.fixture(autouse=True)
def _clean_tables(_migrate):
    yield
    from app.db.session import Base, engine

    with engine.begin() as conn:
        for table in reversed(Base.metadata.sorted_tables):
            conn.execute(table.delete())
