# optional: create tables / seed
from app.db.base import Base
from app.db.session import engine
from app.modules.users.model import User  # noqa: F401
from app.modules.sessions.model import PhotoSession  # noqa: F401
from app.modules.jobs.model import Job  # noqa: F401
from app.modules.themes.model import Theme  # noqa: F401

def init_db():
    Base.metadata.create_all(bind=engine)
