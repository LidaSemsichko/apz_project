import os
from datetime import datetime

from sqlalchemy import Column, DateTime, Integer, String
from sqlalchemy.exc import IntegrityError

from common.errors import ConflictError
from common.logging_utils import configure_logging
from common.sqlalchemy import (
    create_base,
    check_database,
    create_db_engine,
    create_session_factory,
    init_schema_with_lock,
    session_scope,
)


DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "postgresql://auth_user:auth_pass@auth-db:5432/auth_db",
)

engine = create_db_engine(DATABASE_URL)
SessionLocal = create_session_factory(engine)
Base = create_base()
LOGGER = configure_logging("auth-service")


class UserDB(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, unique=True, index=True, nullable=False)
    username = Column(String, unique=True, index=True, nullable=False)
    password_hash = Column(String, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)


def init_db():
    init_schema_with_lock(engine, Base.metadata, 1001, "AUTH")
    LOGGER.info("event=database_initialized")


def get_database_health() -> str:
    return check_database(engine)


def create_user(email: str, username: str, password_hash: str) -> UserDB:
    with session_scope(SessionLocal) as db:
        user = UserDB(
            email=email,
            username=username,
            password_hash=password_hash,
        )
        db.add(user)
        try:
            db.commit()
            db.refresh(user)
        except IntegrityError as error:
            db.rollback()
            raise ConflictError("Email or username already exists") from error
        return user


def get_user_by_email(email: str):
    with session_scope(SessionLocal) as db:
        return db.query(UserDB).filter(UserDB.email == email).first()


def get_user_by_username(username: str):
    with session_scope(SessionLocal) as db:
        return db.query(UserDB).filter(UserDB.username == username).first()


def get_all_users():
    with session_scope(SessionLocal) as db:
        return db.query(UserDB).order_by(UserDB.id.asc()).all()


def get_user_by_id(user_id: int):
    with session_scope(SessionLocal) as db:
        return db.query(UserDB).filter(UserDB.id == user_id).first()
