import os
from datetime import datetime

from sqlalchemy import create_engine, Column, Integer, String, DateTime
from sqlalchemy.orm import declarative_base, sessionmaker
import time
from sqlalchemy.exc import OperationalError



DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "postgresql://auth_user:auth_pass@auth-db:5432/auth_db"
)

engine = create_engine(DATABASE_URL, pool_pre_ping=True)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()


class UserDB(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, unique=True, index=True, nullable=False)
    username = Column(String, nullable=False)
    password_hash = Column(String, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)



def init_db():
    max_attempts = 15

    for attempt in range(1, max_attempts + 1):
        try:
            with engine.begin() as connection:
                connection.exec_driver_sql("SELECT pg_advisory_lock(1001)")
                try:
                    Base.metadata.create_all(bind=connection)
                finally:
                    connection.exec_driver_sql("SELECT pg_advisory_unlock(1001)")

            print("[AUTH] Database initialized successfully")
            return

        except OperationalError as error:
            print(f"[AUTH] Database not ready, attempt {attempt}/{max_attempts}")
            time.sleep(2)

    raise RuntimeError("Database is not available after retries")

def create_user(email: str, username: str, password_hash: str) -> UserDB:
    db = SessionLocal()
    try:
        user = UserDB(
            email=email,
            username=username,
            password_hash=password_hash
        )
        db.add(user)
        db.commit()
        db.refresh(user)
        return user
    finally:
        db.close()


def get_user_by_email(email: str):
    db = SessionLocal()
    try:
        return db.query(UserDB).filter(UserDB.email == email).first()
    finally:
        db.close()


def get_user_by_username(username: str):
    db = SessionLocal()
    try:
        return db.query(UserDB).filter(UserDB.username == username).first()
    finally:
        db.close()


def get_all_users():
    db = SessionLocal()
    try:
        return db.query(UserDB).order_by(UserDB.id.asc()).all()
    finally:
        db.close()

        
def get_user_by_id(user_id: int):
    db = SessionLocal()
    try:
        return db.query(UserDB).filter(UserDB.id == user_id).first()
    finally:
        db.close()