import os
from sqlmodel import Session, create_engine
from typing import Generator

DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///data/taskwall.db")

engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})

def get_db() -> Generator[Session, None, None]:
    with Session(engine) as session:
        yield session