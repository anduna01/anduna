import os
import tempfile

import pytest

# Aislar los tests: base y almacenamiento temporales, sin claves reales.
_tmp = tempfile.mkdtemp(prefix="vcf-test-")
os.environ["DATABASE_URL"] = f"sqlite:///{_tmp}/test.db"
os.environ["STORAGE_DIR"] = f"{_tmp}/storage"
os.environ["ANTHROPIC_API_KEY"] = ""
os.environ["YOUTUBE_API_KEY"] = ""


@pytest.fixture()
def client():
    from fastapi.testclient import TestClient

    from app.main import create_app

    return TestClient(create_app())
