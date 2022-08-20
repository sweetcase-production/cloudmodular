from sqlalchemy import Column, Integer, String, DateTime, Boolean
from sqlalchemy.sql import func

from system.connection.generators import DatabaseGenerator

Base = DatabaseGenerator.get_base()

class User(Base):
    __tablename__ = 'user'

    id = Column(Integer, primary_key=True, autoincrement=True)
    email = Column(String(128), unique=True, nullable=False)
    name = Column(String(32), unique=True, nullable=False)
    storage_size = Column(Integer, nullable=False)
    passwd = Column(String(255), nullable=False)
    is_admin = Column(Boolean, nullable=False, default=False)
    created = Column(DateTime(timezone=True), server_default=func.now())
