from sqlalchemy import Boolean, Column, DateTime, ForeignKey, Integer, String, Text, UniqueConstraint
from sqlalchemy.sql import func

from system.connection.generators import DatabaseGenerator

Base = DatabaseGenerator.get_base()

class DataInfo(Base):
    __tablename__ = 'datainfo'
    __table_args__ = (
        UniqueConstraint('root', 'name', 'is_dir'),
    )

    id = Column(Integer, primary_key=True, autoincrement=True)
    root = Column(Text, nullable=False)
    name = Column(String(255), nullable=False)
    is_dir = Column(Boolean, nullable=False)
    created = Column(DateTime(timezone=True), server_default=func.now())
    user_id = Column(
        Integer,
        ForeignKey('user.id'),
        nullable=False,
    )
    
