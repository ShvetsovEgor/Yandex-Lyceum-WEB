import sqlalchemy
from sqlalchemy import orm

from .db_session import SqlAlchemyBase


class Types(SqlAlchemyBase):
    __tablename__ = 'types_of_users'

    id = sqlalchemy.Column(sqlalchemy.Integer,
                           primary_key=True, autoincrement=True)
    name = sqlalchemy.Column(sqlalchemy.String, nullable=True)

    user = orm.relation('User')
    # types_of_users = orm.relation("types_of_users",
    #                           secondary="association",
    #                           backref="users")
