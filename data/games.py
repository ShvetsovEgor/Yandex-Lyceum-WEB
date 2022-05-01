import datetime
import sqlalchemy
from sqlalchemy import orm

from .db_session import SqlAlchemyBase


class Games(SqlAlchemyBase):
    __tablename__ = 'games'

    id = sqlalchemy.Column(sqlalchemy.Integer,
                           primary_key=True, autoincrement=True)
    title = sqlalchemy.Column(sqlalchemy.String, nullable=True)
    picture = sqlalchemy.Column(sqlalchemy.String, nullable=True)
    genre = sqlalchemy.Column(sqlalchemy.String, nullable=True)

    content = sqlalchemy.Column(sqlalchemy.String, nullable=True)

    added_date = sqlalchemy.Column(sqlalchemy.DateTime,
                                   default=datetime.datetime.now, nullable=True)
    created_date = sqlalchemy.Column(sqlalchemy.Integer)

    platform = sqlalchemy.Column(sqlalchemy.String, nullable=True)
    archive = sqlalchemy.Column(sqlalchemy.String, nullable=True)
    user_id = sqlalchemy.Column(sqlalchemy.Integer,
                                sqlalchemy.ForeignKey("users.id"))

    user = orm.relation('User')
    # categories = orm.relation("Category",
    #                           secondary="association",
    #                           backref="games")
    def __repr__(self):
        return self.title
