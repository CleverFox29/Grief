"""Pytest fixtures for CGAS test suite with MongoDB in-memory mock."""

import sys
from pathlib import Path
import pytest
import mongoengine
import mongomock
from fastapi.testclient import TestClient

# Ensure backend root is on Python path
BASE_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BASE_DIR))

from app.database import get_db
from app.main import app
from app.models import Category, StaffRecord, Student, Admin, UserRole, Ticket
from app.core.security import hash_password

class QueryAdapter:
    def __init__(self, model, qs=None):
        self.model = model
        self.qs = qs if qs is not None else model.objects

    def all(self):
        return list(self.qs)

    def first(self):
        return self.qs.first()

    def count(self):
        return self.qs.count()

    def filter_by(self, **kwargs):
        return QueryAdapter(self.model, self.qs.filter(**kwargs))

    def filter(self, *args, **kwargs):
        return QueryAdapter(self.model, self.qs.filter(*args, **kwargs))

    def __iter__(self):
        return iter(self.qs)

class MongoTestSession:
    """Compatibility session adapter for test fixtures."""
    def __init__(self, conn):
        self.conn = conn
        self._tracked = set()

    def add(self, obj):
        obj.save()
        self._tracked.add(obj)

    def add_all(self, objs):
        for o in objs:
            self.add(o)

    def commit(self):
        for o in list(self._tracked):
            try:
                o.save()
            except Exception:
                pass
        for o in list(Ticket._registry.values()):
            try:
                o.save()
            except Exception:
                pass

    def flush(self):
        self.commit()

    def refresh(self, obj):
        obj.reload()

    def query(self, model):
        return QueryAdapter(model)

    def bulk_save_objects(self, objs):
        for o in objs:
            self.add(o)

    def execute(self, *args, **kwargs):
        pass

@pytest.fixture(scope="function")
def db_session():
    """Provide a fresh, isolated in-memory MongoDB database per test function."""
    mongoengine.disconnect(alias="default")
    conn = mongoengine.connect(
        "test_cgas_db",
        host="mongodb://localhost:27017/test_cgas_db",
        mongo_client_class=mongomock.MongoClient,
        alias="default"
    )
    # Clear registry in Ticket
    Ticket._registry.clear()

    session = MongoTestSession(conn)
    yield session

    conn.drop_database("test_cgas_db")
    mongoengine.disconnect(alias="default")

@pytest.fixture(scope="function")
def client(db_session):
    """Test client overriding database dependency with the test session."""
    def override_get_db():
        try:
            yield mongoengine.connection.get_db()
        finally:
            pass

    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as test_client:
        yield test_client
    app.dependency_overrides.clear()
