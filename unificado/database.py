from sqlalchemy import create_engine
from sqlalchemy.orm import Session

from unificado.settings import Settings


def get_engine():
    settings = Settings()  # type: ignore
    try:
        _engine = create_engine(settings.DATABASE_URL)  # pyright: ignore[reportCallIssue]
    except Exception:
        raise

    return _engine


def get_session():
    engine = get_engine()
    with Session(engine) as session:
        yield session
