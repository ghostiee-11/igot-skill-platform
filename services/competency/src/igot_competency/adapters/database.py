from sqlalchemy import create_engine
from sqlalchemy.orm import DeclarativeBase,sessionmaker
from igot_competency.config import settings
def normalize(u):
    if u.startswith("postgres://"): return u.replace("postgres://","postgresql+psycopg://",1)
    if u.startswith("postgresql://"): return u.replace("postgresql://","postgresql+psycopg://",1)
    return u
DATABASE_URL=normalize(settings.database_url); IS_SQLITE=DATABASE_URL.startswith("sqlite"); SCHEMA=None if IS_SQLITE else settings.database_schema
class Base(DeclarativeBase): pass
engine=create_engine(DATABASE_URL,connect_args={"check_same_thread":False} if IS_SQLITE else {},pool_pre_ping=not IS_SQLITE)
SessionLocal=sessionmaker(bind=engine,autoflush=False,expire_on_commit=False)
def get_db():
    db=SessionLocal()
    try: yield db
    finally: db.close()
