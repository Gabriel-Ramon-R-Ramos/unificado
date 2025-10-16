import logging

from sqlalchemy import create_engine
from sqlalchemy.orm import Session

from unificado.settings import Settings

logger = logging.getLogger('unificado.database')

# Criar engine de forma lazy para evitar executar Settings() na importação
_engine = None


def get_engine():
    global _engine
    if _engine is not None:
        return _engine

    settings = Settings()  # type: ignore
    try:
        _engine = create_engine(settings.DATABASE_URL)  # pyright: ignore[reportCallIssue]
        try:
            url = _engine.url
            host = getattr(url, 'host', None)
            port = getattr(url, 'port', None)
            database = getattr(url, 'database', None)
            driver = getattr(url, 'drivername', None)
            logger.info(
                'Created SQLAlchemy engine (%s) for %s:%s/%s',
                driver,
                host,
                port,
                database,
            )
        except Exception:
            logger.info('Created SQLAlchemy engine')
    except Exception:
        logger.exception('Failed to create SQLAlchemy engine')
        raise

    return _engine


def get_session():
    logger.debug('Opening DB session')
    engine = get_engine()
    with Session(engine) as session:
        try:
            yield session
        finally:
            logger.debug('DB session closed')
