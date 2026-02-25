import io
import json

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient
from PIL import Image
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.api.v1.endpoints.sessions import router as sessions_router
from app.api.v1.endpoints.themes import router as themes_router
from app.db.base import Base
from app.db.session import get_db
from app.modules.jobs import service as jobs_service
from app.modules.jobs.model import Job
from app.modules.sessions.model import PhotoSession
from app.modules.themes import service as themes_service
from app.modules.themes.model import Theme
from app.modules.users.model import User


def _png_bytes() -> bytes:
    buff = io.BytesIO()
    Image.new("RGB", (8, 8), (20, 20, 20)).save(buff, format="PNG")
    return buff.getvalue()


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
    app.include_router(themes_router, prefix="/api/v1")
    app.include_router(sessions_router, prefix="/api/v1")

    def override_get_db():
        db = db_session_factory()
        try:
            yield db
        finally:
            db.close()

    app.dependency_overrides[get_db] = override_get_db

    with TestClient(app) as c:
        yield c


def test_get_themes_returns_seeded_data_when_table_empty(
    client: TestClient, db_session_factory, tmp_path, monkeypatch
):
    seed_file = tmp_path / "themes.json"
    seed_file.write_text(
        json.dumps(
            [
                {
                    "id": "nostalgia-park",
                    "title": "Nostalgia Park",
                    "thumbnail": "/static/thumbs/nostalgia-park.jpeg",
                    "prompt": "golden hour park portrait",
                    "negative_prompt": "blur",
                    "params": {"aspect_ratio": "2:3"},
                }
            ]
        ),
        encoding="utf-8",
    )
    monkeypatch.setattr(themes_service, "THEMES_JSON", seed_file)

    db = db_session_factory()
    try:
        inserted = themes_service.seed_themes_if_empty(db)
        assert inserted == 1
    finally:
        db.close()

    response = client.get("/api/v1/themes")
    assert response.status_code == 200
    body = response.json()
    assert len(body) == 1
    assert body[0]["id"] == "nostalgia-park"
    assert body[0]["thumbnail_url"] == "/static/thumbs/nostalgia-park.jpeg"


def test_post_themes_creates_theme_and_slug_collision(
    client: TestClient, tmp_path, monkeypatch
):
    thumbs_dir = tmp_path / "thumbs"
    monkeypatch.setattr(themes_service, "THUMBS_DIR", thumbs_dir)

    payload = {
        "title": "Cyber Park",
        "prompt": "cinematic cyber park portrait",
        "negative_prompt": "low quality",
        "aspect_ratio": "2:3",
    }
    files = {"thumbnail": ("thumb.png", _png_bytes(), "image/png")}

    response_1 = client.post("/api/v1/themes", data=payload, files=files)
    assert response_1.status_code == 200
    created_1 = response_1.json()
    assert created_1["id"] == "cyber-park"
    assert created_1["params"]["aspect_ratio"] == "2:3"
    assert created_1["thumbnail_url"].startswith("/static/thumbs/")

    response_2 = client.post("/api/v1/themes", data=payload, files=files)
    assert response_2.status_code == 200
    created_2 = response_2.json()
    assert created_2["id"] == "cyber-park-2"

    saved_files = list(thumbs_dir.glob("*"))
    assert len(saved_files) == 2


def test_get_theme_internal_by_id_returns_theme_and_404(client: TestClient, db_session_factory):
    db = db_session_factory()
    try:
        db.add(
            Theme(
                id="retro-wave",
                title="Retro Wave",
                thumbnail_url="/static/thumbs/retro-wave.png",
                prompt="retro sunset scene",
                negative_prompt="blurry",
                params={"aspect_ratio": "2:3"},
            )
        )
        db.commit()
    finally:
        db.close()

    response = client.get("/api/v1/themes/internal/retro-wave")
    assert response.status_code == 200
    body = response.json()
    assert body["id"] == "retro-wave"
    assert body["prompt"] == "retro sunset scene"
    assert body["negative_prompt"] == "blurry"

    missing = client.get("/api/v1/themes/internal/unknown-theme")
    assert missing.status_code == 404
    assert missing.json()["detail"] == "Theme not found"


def test_get_themes_internal_orders_by_serial_id_ascending(client: TestClient, db_session_factory):
    db = db_session_factory()
    try:
        db.add_all(
            [
                Theme(
                    id="theme-c",
                    serial_id=3,
                    title="Theme C",
                    thumbnail_url="/static/thumbs/theme-c.png",
                    prompt="prompt c",
                    negative_prompt=None,
                    params={"aspect_ratio": "2:3"},
                ),
                Theme(
                    id="theme-a",
                    serial_id=1,
                    title="Theme A",
                    thumbnail_url="/static/thumbs/theme-a.png",
                    prompt="prompt a",
                    negative_prompt=None,
                    params={"aspect_ratio": "2:3"},
                ),
                Theme(
                    id="theme-b",
                    serial_id=2,
                    title="Theme B",
                    thumbnail_url="/static/thumbs/theme-b.png",
                    prompt="prompt b",
                    negative_prompt=None,
                    params={"aspect_ratio": "2:3"},
                ),
            ]
        )
        db.commit()
    finally:
        db.close()

    response = client.get("/api/v1/themes/internal")
    assert response.status_code == 200
    ids = [row["id"] for row in response.json()]
    assert ids == ["theme-a", "theme-b", "theme-c"]


def test_patch_theme_updates_existing_row_without_creating_new(client: TestClient, db_session_factory):
    db = db_session_factory()
    try:
        db.add(
            Theme(
                id="cyber-park",
                title="Cyber Park",
                thumbnail_url="/static/thumbs/cyber-park.png",
                prompt="old prompt",
                negative_prompt="noise",
                params={"aspect_ratio": "2:3"},
            )
        )
        db.commit()
    finally:
        db.close()

    response = client.patch(
        "/api/v1/themes/cyber-park",
        data={
            "title": "Cyber Park Updated",
            "prompt": "new prompt",
            "negative_prompt": "",
            "aspect_ratio": "3:2",
        },
    )
    assert response.status_code == 200
    body = response.json()
    assert body["id"] == "cyber-park"
    assert body["title"] == "Cyber Park Updated"
    assert body["prompt"] == "new prompt"
    assert body["negative_prompt"] is None
    assert body["params"]["aspect_ratio"] == "3:2"
    assert body["thumbnail_url"] == "/static/thumbs/cyber-park.png"

    db_check = db_session_factory()
    try:
        rows = db_check.query(Theme).all()
        assert len(rows) == 1
        assert rows[0].id == "cyber-park"
        assert rows[0].title == "Cyber Park Updated"
    finally:
        db_check.close()


def test_delete_theme_by_id_removes_row_and_returns_404_for_unknown(client: TestClient, db_session_factory):
    db = db_session_factory()
    try:
        db.add_all(
            [
                Theme(
                    id="theme-a",
                    serial_id=1,
                    title="Theme A",
                    thumbnail_url="/static/thumbs/theme-a.png",
                    prompt="prompt a",
                    negative_prompt=None,
                    params={"aspect_ratio": "2:3"},
                ),
                Theme(
                    id="theme-b",
                    serial_id=2,
                    title="Theme B",
                    thumbnail_url="/static/thumbs/theme-b.png",
                    prompt="prompt b",
                    negative_prompt=None,
                    params={"aspect_ratio": "2:3"},
                ),
            ]
        )
        db.commit()
    finally:
        db.close()

    delete_response = client.delete("/api/v1/themes/theme-a")
    assert delete_response.status_code == 204

    list_response = client.get("/api/v1/themes/internal")
    assert list_response.status_code == 200
    ids = [row["id"] for row in list_response.json()]
    assert ids == ["theme-b"]

    missing_response = client.delete("/api/v1/themes/unknown-theme")
    assert missing_response.status_code == 404
    assert missing_response.json()["detail"] == "Theme not found"


def test_patch_session_theme_accepts_created_theme_and_rejects_unknown(
    client: TestClient, db_session_factory
):
    db = db_session_factory()
    try:
        user = User(name="Tester", email="tester@example.com", phone="08123")
        db.add(user)
        db.commit()
        db.refresh(user)

        db.add(
            Theme(
                id="nostalgia-park",
                title="Nostalgia Park",
                thumbnail_url="/static/thumbs/nostalgia-park.jpeg",
                prompt="nostalgia prompt",
                negative_prompt=None,
                params={"aspect_ratio": "2:3"},
            )
        )
        db.commit()

        session = PhotoSession(user_id=user.id, status="draft")
        db.add(session)
        db.commit()
        db.refresh(session)
        session_id = session.id
    finally:
        db.close()

    ok_response = client.patch(
        f"/api/v1/sessions/{session_id}/theme",
        json={"theme_id": "nostalgia-park"},
    )
    assert ok_response.status_code == 200
    assert ok_response.json()["theme_id"] == "nostalgia-park"

    missing_response = client.patch(
        f"/api/v1/sessions/{session_id}/theme",
        json={"theme_id": "unknown-theme"},
    )
    assert missing_response.status_code == 404
    assert missing_response.json()["detail"] == "Theme not found"


def test_job_flow_fetches_prompt_from_database_theme(db_session_factory, tmp_path, monkeypatch):
    db = db_session_factory()
    try:
        user = User(name="Worker", email="worker@example.com", phone="08000")
        db.add(user)
        db.commit()
        db.refresh(user)

        db.add(
            Theme(
                id="neon-city",
                title="Neon City",
                thumbnail_url="/static/thumbs/neon-city.jpeg",
                prompt="Take it to neon city",
                negative_prompt=None,
                params={"aspect_ratio": "2:3"},
            )
        )
        db.commit()

        app_root = tmp_path / "app"
        uploads_dir = app_root / "static" / "uploads"
        uploads_dir.mkdir(parents=True, exist_ok=True)
        (uploads_dir / "capture.jpg").write_bytes(b"capture")

        session = PhotoSession(
            user_id=user.id,
            theme_id="neon-city",
            input_image_path="/static/uploads/capture.jpg",
            status="photo_uploaded",
        )
        db.add(session)
        db.commit()
        db.refresh(session)

        job = Job(session_id=session.id, status="queued", mode="event")
        db.add(job)
        db.commit()
        db.refresh(job)
        job_id = job.id
    finally:
        db.close()

    results_dir = tmp_path / "app" / "static" / "results"
    compressed_dir = tmp_path / "app" / "static" / "compressed"
    results_dir.mkdir(parents=True, exist_ok=True)
    compressed_dir.mkdir(parents=True, exist_ok=True)

    seen = {"prompt": None}

    def fake_generate_event_result(input_abs, prompt, *, logger, started_at):
        seen["prompt"] = prompt
        output = results_dir / "generated.jpg"
        Image.new("RGB", (2400, 3600), (120, 130, 140)).save(output, format="JPEG")
        return output

    monkeypatch.setattr(jobs_service, "SessionLocal", db_session_factory)
    monkeypatch.setattr(jobs_service, "APP_DIR", tmp_path / "app")
    monkeypatch.setattr(jobs_service, "RESULTS_DIR", results_dir)
    monkeypatch.setattr(jobs_service, "COMPRESSED_DIR", compressed_dir)
    monkeypatch.setattr(jobs_service, "_generate_event_result", fake_generate_event_result)
    monkeypatch.setattr(jobs_service, "_attach_drive_info", lambda *args, **kwargs: None)

    jobs_service.process_job_seeddream_safe(job_id, requested_mode="event")

    assert seen["prompt"] == "Take it to neon city"

    db_check = db_session_factory()
    try:
        stored = db_check.query(Job).filter(Job.id == job_id).first()
        assert stored is not None
        assert stored.status == "done"
        assert stored.result_image_path == "/static/results/generated.jpg"
        assert stored.compressed_image_path == "/static/compressed/generated.jpg"
    finally:
        db_check.close()

    compressed_file = compressed_dir / "generated.jpg"
    assert compressed_file.exists()

    with Image.open(compressed_file) as compressed:
        assert compressed.format == "JPEG"
        assert compressed.size == (1200, 1800)
        dpi = compressed.info.get("dpi")
        assert dpi is not None
        assert dpi[0] == pytest.approx(600, abs=1.0)
        assert dpi[1] == pytest.approx(600, abs=1.0)


def test_resolve_drive_upload_path_prefers_compressed_then_falls_back(tmp_path, monkeypatch):
    app_root = tmp_path / "app"
    results_dir = app_root / "static" / "results"
    compressed_dir = app_root / "static" / "compressed"
    results_dir.mkdir(parents=True, exist_ok=True)
    compressed_dir.mkdir(parents=True, exist_ok=True)

    raw_file = results_dir / "sample.png"
    compressed_file = compressed_dir / "sample.jpg"
    raw_file.write_bytes(b"raw")
    compressed_file.write_bytes(b"compressed")

    monkeypatch.setattr(jobs_service, "APP_DIR", app_root)
    monkeypatch.setattr(jobs_service, "DRIVE_UPLOAD_SOURCE", "compressed")

    job = Job(
        session_id=1,
        mode="event",
        status="done",
        result_image_path="/static/results/sample.png",
        compressed_image_path="/static/compressed/sample.jpg",
    )

    selected_path, source = jobs_service._resolve_drive_upload_path(job)
    assert selected_path == compressed_file
    assert source == "compressed"

    compressed_file.unlink()
    selected_path, source = jobs_service._resolve_drive_upload_path(job)
    assert selected_path == raw_file
    assert source == "results"


def test_resolve_drive_upload_path_uses_raw_when_configured(tmp_path, monkeypatch):
    app_root = tmp_path / "app"
    results_dir = app_root / "static" / "results"
    compressed_dir = app_root / "static" / "compressed"
    results_dir.mkdir(parents=True, exist_ok=True)
    compressed_dir.mkdir(parents=True, exist_ok=True)

    raw_file = results_dir / "sample.png"
    compressed_file = compressed_dir / "sample.jpg"
    raw_file.write_bytes(b"raw")
    compressed_file.write_bytes(b"compressed")

    monkeypatch.setattr(jobs_service, "APP_DIR", app_root)
    monkeypatch.setattr(jobs_service, "DRIVE_UPLOAD_SOURCE", "results")

    job = Job(
        session_id=1,
        mode="event",
        status="done",
        result_image_path="/static/results/sample.png",
        compressed_image_path="/static/compressed/sample.jpg",
    )

    selected_path, source = jobs_service._resolve_drive_upload_path(job)
    assert selected_path == raw_file
    assert source == "results"
