from fastapi import FastAPI
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.api.v1.endpoints.gallery import router as gallery_router
from app.db.base import Base
from app.db.session import get_db
from app.modules.jobs.model import Job
from app.modules.sessions.model import PhotoSession
from app.modules.users.model import User


def _session_factory():
    engine = create_engine(
        "sqlite+pysqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    session_local = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    Base.metadata.create_all(bind=engine)
    return session_local, engine


def _seed_base_entities(db):
    user = User(name="Tester", email="tester-gallery@example.com", phone="08000")
    db.add(user)
    db.commit()
    db.refresh(user)

    session = PhotoSession(user_id=user.id, status="photo_uploaded")
    db.add(session)
    db.commit()
    db.refresh(session)

    return session.id


def test_gallery_prefers_compressed_image_path():
    SessionLocal, engine = _session_factory()
    try:
        app = FastAPI()
        app.include_router(gallery_router, prefix="/api/v1")

        def override_get_db():
            db = SessionLocal()
            try:
                yield db
            finally:
                db.close()

        app.dependency_overrides[get_db] = override_get_db

        db = SessionLocal()
        try:
            session_id = _seed_base_entities(db)
            db.add(
                Job(
                    session_id=session_id,
                    status="done",
                    mode="event",
                    result_image_path="/static/results/raw.png",
                    compressed_image_path="/static/compressed/compressed.jpg",
                )
            )
            db.commit()
        finally:
            db.close()

        with TestClient(app) as client:
            response = client.get("/api/v1/gallery")
            assert response.status_code == 200
            body = response.json()
            assert len(body) == 1
            assert body[0]["url"] == "/static/compressed/compressed.jpg"
    finally:
        engine.dispose()


def test_gallery_falls_back_to_raw_result_image_path():
    SessionLocal, engine = _session_factory()
    try:
        app = FastAPI()
        app.include_router(gallery_router, prefix="/api/v1")

        def override_get_db():
            db = SessionLocal()
            try:
                yield db
            finally:
                db.close()

        app.dependency_overrides[get_db] = override_get_db

        db = SessionLocal()
        try:
            session_id = _seed_base_entities(db)
            db.add(
                Job(
                    session_id=session_id,
                    status="done",
                    mode="event",
                    result_image_path="/static/results/raw-only.png",
                    compressed_image_path=None,
                )
            )
            db.commit()
        finally:
            db.close()

        with TestClient(app) as client:
            response = client.get("/api/v1/gallery")
            assert response.status_code == 200
            body = response.json()
            assert len(body) == 1
            assert body[0]["url"] == "/static/results/raw-only.png"
    finally:
        engine.dispose()
