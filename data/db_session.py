import os

import sqlalchemy as sa
import sqlalchemy.orm as orm
from sqlalchemy.orm import Session
import sqlalchemy.ext.declarative as dec

SqlAlchemyBase = dec.declarative_base()

__factory = None


def global_init():
    global __factory

    if __factory:
        return

        # попробуем взять адрес базы из переменной окружения
    if 'DATABASE_URL' in os.environ:  # сработает на Heroku
        conn_str = os.environ['DATABASE_URL'].replace('postgres://', 'postgresql://')
    else:  # сработает локально
        from config import LOCAL_DB
        conn_str = LOCAL_DB

    engine = sa.create_engine(conn_str, echo=False)

    __factory = orm.sessionmaker(bind=engine)

    from . import __all_models

    SqlAlchemyBase.metadata.create_all(engine)


def create_session() -> Session:
    global __factory
    return __factory()
