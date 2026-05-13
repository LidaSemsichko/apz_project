from contextlib import contextmanager
from collections.abc import Iterator
import logging

from sqlalchemy import create_engine
from sqlalchemy.exc import OperationalError
from sqlalchemy.orm import declarative_base, sessionmaker

from common.retry import retry


def create_base():
    return declarative_base()


def create_db_engine(database_url: str):
    return create_engine(database_url, pool_pre_ping=True)


def create_session_factory(engine, *, expire_on_commit: bool = False):
    return sessionmaker(
        autocommit=False,
        autoflush=False,
        bind=engine,
        expire_on_commit=expire_on_commit,
    )


@contextmanager
def session_scope(session_factory) -> Iterator:
    db = session_factory()
    try:
        yield db
    finally:
        db.close()


def init_schema_with_lock(engine, metadata, lock_id: int, service_label: str) -> None:
    logger = logging.getLogger(service_label.lower())

    def operation() -> None:
        with engine.begin() as connection:
            connection.exec_driver_sql(f"SELECT pg_advisory_lock({lock_id})")
            try:
                metadata.create_all(bind=connection)
            finally:
                connection.exec_driver_sql(f"SELECT pg_advisory_unlock({lock_id})")

    retry(
        operation,
        attempts=15,
        delay_seconds=2,
        exceptions=(OperationalError,),
        on_retry=lambda attempt, error: logger.warning(
            "event=database_not_ready attempt=%s max_attempts=15 error=%s",
            attempt,
            error,
        ),
    )


def check_database(engine) -> str:
    try:
        with engine.connect() as connection:
            connection.exec_driver_sql("SELECT 1")
        return "ok"
    except Exception:
        return "unavailable"
