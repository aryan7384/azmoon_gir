from sqlalchemy import Integer, DateTime, MetaData
from sqlalchemy.orm import mapped_column
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.orm import DeclarativeBase

metadata = MetaData(naming_convention={
    "ix": "ix_%(column_0_label)s",
    "uq": "uq_%(table_name)s_%(column_0_name)s",
    "ck": "ck_%(table_name)s_%(constraint_name)s",
    "fk": "fk_%(table_name)s_%(column_0_name)s_%(referred_table_name)s",
    "pk": "pk_%(table_name)s"
})


class Base(DeclarativeBase):
    metadata = metadata
    pass


db = SQLAlchemy(model_class=Base)


class BaseModel(db.Model):
    __abstract__ = True

    id = mapped_column(Integer, primary_key=True)
    created_at = mapped_column(DateTime, default=db.func.current_timestamp())
    updated_at = mapped_column(DateTime,
                               default=db.func.current_timestamp(),
                               onupdate=db.func.current_timestamp())
