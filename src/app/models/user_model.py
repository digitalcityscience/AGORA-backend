from sqlalchemy.orm import relationship
from sqlalchemy.sql.expression import text
from sqlalchemy import (
    Column,
    DateTime,
    Integer,
    MetaData,
    String,
    Table,
    Boolean,
    TIMESTAMP,
    ForeignKey,
)

from app.auth.database import Base

# ALEMBIC command
# After changing models
# alembic revision --autogenerate -m "what you've changed""
# alembic upgrade head


class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True, nullable=False)
    email = Column(String, nullable=False, unique=True)
    password = Column(String, nullable=False)
    created_at = Column(
        TIMESTAMP(timezone=True), nullable=False, server_default=text("now()")
    )
    phone_number = Column(String, nullable=True)
    is_active = Column(Boolean, nullable=False, default=True)
