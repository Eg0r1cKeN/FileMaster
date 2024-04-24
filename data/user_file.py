import datetime
import sqlalchemy
from flask_login import UserMixin
from sqlalchemy_serializer import SerializerMixin
from werkzeug.security import generate_password_hash, check_password_hash
from .db_session import SqlAlchemyBase
from sqlalchemy import orm


class UserFile(SqlAlchemyBase, UserMixin, SerializerMixin):
    __tablename__ = 'files'

    id = sqlalchemy.Column(sqlalchemy.Integer, primary_key=True, autoincrement=True)
    filename = sqlalchemy.Column(sqlalchemy.String, nullable=True)
    owner = sqlalchemy.Column(sqlalchemy.Integer)
    directory = sqlalchemy.Column(sqlalchemy.String)
    hash = sqlalchemy.Column(sqlalchemy.String)