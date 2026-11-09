"""Tests for Atlas Vector Search duplicate retrieval and API integration."""

import pytest
from app.models import Category, Student, Ticket, TicketStatus
from app.services.deduplication_service import DeduplicationEngine


@pytest.fixture
def seeded_categories(db_session):
    categories = [
        Category(name="Plumbing", description="Plumbing issues"),
        Category(name="Electrical", description="Electrical faults"),
    ]
    db_session.add_all(categories)
    db_session.commit()
    return {category.name: category.id for category in categories}


class FakeCollection:
    def __init__(self, result_ids):
        self.result_ids = result_ids
        self.pipeline = None

    def aggregate(self, pipeline):
        self.pipeline = pipeline
        return [{"_id": item_id} for item_id in self.result_ids]


class FakeDatabase:
    def __init__(self, collection):
        self.collection = collection

    def __getitem__(self, name):
        assert name == Ticket._get_collection_name()
        return self.collection


def test_atlas_search_builds_filtered_vector_query(db_session, seeded_categories, monkeypatch):
    student = Student(user_id="vector-student", name="Vector Student", email="vector@example.com")
    student.set_password("Student@123")
    db_session.add(student)
    ticket = Ticket(
        ticket_id="TKT-VECTOR-1", student_id=student.id,
        category_id=seeded_categories["Plumbing"], location="Hostel 3 Room 204",
        description="Water tap leaking", description_embedding=[0.1, 0.2],
        status=TicketStatus.OPEN.value,
    )
    db_session.add(ticket)
    collection = FakeCollection([ticket.id])
    monkeypatch.setattr("app.services.deduplication_service.settings.MONGODB_VECTOR_INDEX", "tickets_vector")
    monkeypatch.setattr("app.services.deduplication_service.settings.VECTOR_SEARCH_CANDIDATES", 40)

    found = DeduplicationEngine._vector_candidates(
        FakeDatabase(collection), seeded_categories["Plumbing"],
        [TicketStatus.OPEN.value, TicketStatus.IN_PROGRESS.value], [0.1, 0.2],
    )

    vector_stage = collection.pipeline[0]["$vectorSearch"]
    assert vector_stage["index"] == "tickets_vector"
    assert vector_stage["path"] == "description_embedding"
    assert vector_stage["queryVector"] == [0.1, 0.2]
    assert vector_stage["numCandidates"] == vector_stage["limit"] == 40
    assert vector_stage["filter"]["$and"] == [
        {"category_id": {"$eq": seeded_categories["Plumbing"]}},
        {"status": {"$in": [TicketStatus.OPEN.value, TicketStatus.IN_PROGRESS.value]}},
        {"parent_ticket_id": {"$eq": None}},
    ]
    assert [item.id for item in found] == [ticket.id]


def test_atlas_failure_signals_existing_scan_fallback(monkeypatch):
    class BrokenCollection:
        def aggregate(self, _pipeline):
            raise RuntimeError("vector index is not ready")

    monkeypatch.setattr("app.services.deduplication_service.settings.MONGODB_VECTOR_INDEX", "tickets_vector")
    found = DeduplicationEngine._vector_candidates(
        FakeDatabase(BrokenCollection()), 1, [TicketStatus.OPEN.value], [0.1]
    )
    assert found is None


def test_duplicate_check_api_uses_atlas_candidates(client, db_session, student_auth_header, seeded_categories, monkeypatch):
    monkeypatch.setattr(
        "app.services.deduplication_service.EmbeddingProvider.encode",
        classmethod(lambda cls, _text: [0.2, 0.4]),
    )
    student = Student.objects(user_id="25CSB0A22").first()
    ticket = Ticket(
        ticket_id="TKT-API-VECTOR", student_id=student.id,
        category_id=seeded_categories["Plumbing"], location="Hostel 3 Room 204",
        description="Water tap leaking continuously", description_embedding=[0.2, 0.4],
        status=TicketStatus.OPEN.value,
    )
    db_session.add(ticket)
    calls = []

    def atlas_candidates(db, category_id, statuses, query_vector):
        calls.append((db is not None, category_id, statuses, query_vector))
        return [ticket]

    monkeypatch.setattr(DeduplicationEngine, "_vector_candidates", staticmethod(atlas_candidates))
    response = client.post("/api/tickets/check-duplicates", headers=student_auth_header, json={
        "category_id": seeded_categories["Plumbing"],
        "location": "Hostel 3 Room 204",
        "description": "Water tap leaking continuously",
    })

    assert response.status_code == 200
    assert response.json()["has_duplicates"] is True
    assert response.json()["matches"][0]["ticket_id"] == "TKT-API-VECTOR"
    assert len(calls) == 1
    assert calls[0][0] is True
    assert calls[0][1] == seeded_categories["Plumbing"]
    assert calls[0][3] == [0.2, 0.4]
