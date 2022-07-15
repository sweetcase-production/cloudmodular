from sqlalchemy import (
    Column,
    Integer, String, UniqueConstraint
)

from system.connection.generators import DatabaseGenerator

Base = DatabaseGenerator.get_base()

class Tag(Base):
    __tablename__ = 'tag'
    __table_args__ = (
        UniqueConstraint('id', 'name'),
    )
    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(32), nullable=False)

