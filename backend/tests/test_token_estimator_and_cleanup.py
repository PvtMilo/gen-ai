from datetime import datetime

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.api.v1.endpoints import event_maintenance
from app.api.v1.endpoints.event_maintenance import router as event_maintenance_router
from app.api.v1.endpoints.token_estimator import router as token_estimator_router
from app.db.base import Base
from app.db.session import get_db
from app.modules.jobs.model import Job
from app.modules.sessions.model import PhotoSession
from app.modules.users.model import User


@pytest.fixture()
def db_session_factory():
    engine = create_engine(
        "sqlite+pysqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    Base.metadata.create_all(bind=engine)

    try:
        yield SessionLocal
    finally:
        engine.dispose()


@pytest.fixture()
def client(db_session_factory):
    app = FastAPI()
    app.include_router(token_estimator_router, prefix="/api/v1")
    app.include_router(event_maintenance_router, prefix="/api/v1")

    def override_get_db():
        db = db_session_factory()
        try:
            yield db
        finally:
            db.close()

    app.dependency_overrides[get_db] = override_get_db

    with TestClient(app) as c:
        yield c


def _seed_event_data(db_session_factory):
    db = db_session_factory()
    try:
        user_1 = User(name="Alice", email="alice@example.com", phone="081")
        user_2 = User(name="Bob", email="bob@example.com", phone="082")
        db.add_all([user_1, user_2])
        db.commit()
        db.refresh(user_1)
        db.refresh(user_2)

        session_1 = PhotoSession(user_id=user_1.id, status="photo_uploaded")
        session_2 = PhotoSession(user_id=user_2.id, status="photo_uploaded")
        db.add_all([session_1, session_2])
        db.commit()
        db.refresh(session_1)
        db.refresh(session_2)

        # WIB range used in tests: 2026-02-24 00:00:00 to 2026-02-24 23:59:59 (UTC+7).
        # In UTC this is 2026-02-23 17:00:00 to 2026-02-24 16:59:59.
        db.add_all(
            [
                Job(
                    session_id=session_1.id,
                    mode="event",
                    status="done",
                    error_message=None,
                    result_image_path="/static/results/in-range-done.png",
                    created_at=datetime(2026, 2, 24, 1, 0, 0),
                ),
                Job(
                    session_id=session_1.id,
                    mode="event",
                    status="failed",
                    error_message="failed",
                    result_image_path="/static/results/in-range-failed.png",
                    created_at=datetime(2026, 2, 24, 2, 0, 0),
                ),
                Job(
                    session_id=session_2.id,
                    mode="event",
                    status="done",
                    error_message=None,
                    result_image_path="/static/results/out-range-done.png",
                    created_at=datetime(2026, 2, 24, 18, 0, 0),
                ),
            ]
        )
        db.commit()
    finally:
        db.close()


def test_token_estimator_report_filters_event_done_no_error(client: TestClient, db_session_factory):
    _seed_event_data(db_session_factory)

    response = client.get(
        "/api/v1/token-estimator/report",
        params={"start_date": "2026-02-24", "end_date": "2026-02-24"},
    )
    assert response.status_code == 200
    body = response.json()

    assert len(body["rows"]) == 1
    row = body["rows"][0]
    assert row["user_name"] == "Alice"
    assert row["mode"] == "event"
    assert row["error"] is None
    assert row["price_per_req"] == 0.04
    assert row["timestamp"] == "2026-02-24 08:00:00"

    summary = body["summary"]
    assert summary["total_requests"] == 1
    assert summary["price_per_req"] == 0.04
    assert summary["total_cost"] == 0.04
    assert summary["currency"] == "USD"


def test_token_estimator_export_csv_returns_data(client: TestClient, db_session_factory):
    _seed_event_data(db_session_factory)

    response = client.get(
        "/api/v1/token-estimator/export.csv",
        params={"start_date": "2026-02-24", "end_date": "2026-02-24"},
    )
    assert response.status_code == 200
    assert response.headers["content-type"].startswith("text/csv")
    text = response.text
    assert "id,user_name,user_id,mode,error,price_per_req,timestamp" in text
    assert "Alice" in text
    assert "total_requests,1" in text
    assert "total_cost,0.04" in text


def test_event_maintenance_preview_and_execute_delete(
    client: TestClient,
    db_session_factory,
    tmp_path,
    monkeypatch,
):
    _seed_event_data(db_session_factory)

    app_root = tmp_path / "app"
    results_dir = app_root / "static" / "results"
    results_dir.mkdir(parents=True, exist_ok=True)
    (results_dir / "in-range-done.png").write_bytes(b"done")
    (results_dir / "in-range-failed.png").write_bytes(b"failed")

    monkeypatch.setattr(event_maintenance, "APP_DIR", app_root)
    monkeypatch.setattr(event_maintenance, "RESULTS_DIR", results_dir)

    preview_response = client.post(
        "/api/v1/event-maintenance/preview-delete",
        json={
            "start_date": "2026-02-24",
            "end_date": "2026-02-24",
            "password": "event-cleanup-admin",
        },
    )
    assert preview_response.status_code == 200
    preview = preview_response.json()
    assert preview["jobs_count"] == 2
    assert preview["result_files_count"] == 2
    assert preview["sessions_to_delete_count"] == 1
    assert preview["users_to_delete_count"] == 1
    assert preview["missing_files_count"] == 0

    execute_response = client.post(
        "/api/v1/event-maintenance/execute-delete",
        json={
            "start_date": "2026-02-24",
            "end_date": "2026-02-24",
            "password": "event-cleanup-admin",
        },
    )
    assert execute_response.status_code == 200
    body = execute_response.json()
    assert body["jobs_deleted_count"] == 2
    assert body["sessions_deleted_count"] == 1
    assert body["users_deleted_count"] == 1
    assert body["result_files_target_count"] == 2
    assert body["result_files_deleted_count"] == 2
    assert body["missing_files_count"] == 0
    assert body["file_delete_warnings"] == []

    db_check = db_session_factory()
    try:
        jobs = db_check.query(Job).order_by(Job.id.asc()).all()
        assert len(jobs) == 1
        assert jobs[0].result_image_path == "/static/results/out-range-done.png"

        sessions = db_check.query(PhotoSession).order_by(PhotoSession.id.asc()).all()
        assert len(sessions) == 1

        users = db_check.query(User).order_by(User.id.asc()).all()
        assert len(users) == 1
        assert users[0].name == "Bob"
    finally:
        db_check.close()


def test_event_maintenance_execute_delete_includes_compressed_files(
    client: TestClient,
    db_session_factory,
    tmp_path,
    monkeypatch,
):
    _seed_event_data(db_session_factory)

    db = db_session_factory()
    try:
        jobs = db.query(Job).order_by(Job.id.asc()).all()
        for job in jobs:
            if job.result_image_path == "/static/results/in-range-done.png":
                job.compressed_image_path = "/static/compressed/in-range-done.jpg"
            elif job.result_image_path == "/static/results/in-range-failed.png":
                job.compressed_image_path = "/static/compressed/in-range-failed.jpg"
        db.commit()
    finally:
        db.close()

    app_root = tmp_path / "app"
    results_dir = app_root / "static" / "results"
    compressed_dir = app_root / "static" / "compressed"
    results_dir.mkdir(parents=True, exist_ok=True)
    compressed_dir.mkdir(parents=True, exist_ok=True)

    (results_dir / "in-range-done.png").write_bytes(b"done")
    (results_dir / "in-range-failed.png").write_bytes(b"failed")
    (compressed_dir / "in-range-done.jpg").write_bytes(b"compressed-done")
    (compressed_dir / "in-range-failed.jpg").write_bytes(b"compressed-failed")

    monkeypatch.setattr(event_maintenance, "APP_DIR", app_root)
    monkeypatch.setattr(event_maintenance, "RESULTS_DIR", results_dir)
    monkeypatch.setattr(event_maintenance, "COMPRESSED_DIR", compressed_dir)

    preview_response = client.post(
        "/api/v1/event-maintenance/preview-delete",
        json={
            "start_date": "2026-02-24",
            "end_date": "2026-02-24",
            "password": "event-cleanup-admin",
        },
    )
    assert preview_response.status_code == 200
    preview = preview_response.json()
    assert preview["jobs_count"] == 2
    assert preview["result_files_count"] == 4
    assert preview["missing_files_count"] == 0

    execute_response = client.post(
        "/api/v1/event-maintenance/execute-delete",
        json={
            "start_date": "2026-02-24",
            "end_date": "2026-02-24",
            "password": "event-cleanup-admin",
        },
    )
    assert execute_response.status_code == 200
    body = execute_response.json()
    assert body["jobs_deleted_count"] == 2
    assert body["result_files_target_count"] == 4
    assert body["result_files_deleted_count"] == 4
    assert body["missing_files_count"] == 0
    assert body["file_delete_warnings"] == []


def test_event_maintenance_rejects_wrong_password(client: TestClient):
    response = client.post(
        "/api/v1/event-maintenance/preview-delete",
        json={
            "start_date": "2026-02-24",
            "end_date": "2026-02-24",
            "password": "wrong",
        },
    )
    assert response.status_code == 401
    assert response.json()["detail"] == "Invalid password"
