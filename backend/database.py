from sqlalchemy.orm import Session
from sqlalchemy import create_engine
from sqlalchemy import URL
from backend.config import settings

APP_DATABASE_URL = URL.create(
    drivername="postgresql",
    username=settings.db_user_app,
    password=settings.db_password_app,
    host=settings.db_host,
    port=settings.db_port,
    database=settings.db_name,
)

engine = create_engine(APP_DATABASE_URL)


def get_session():
    with Session(engine) as session:
        yield session
