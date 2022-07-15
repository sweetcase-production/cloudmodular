from sqlalchemy import Column, ForeignKey, Integer
from sqlalchemy.orm import relationship, backref

from system.connection.generators import DatabaseGenerator

Base = DatabaseGenerator.get_base()

class DataTag(Base):
    __tablename__ = 'dataTag'

    id = Column(Integer, primary_key=True, autoincrement=True)
    datainfo_id = Column(Integer, ForeignKey('datainfo.id'), nullable=False)
    tag_id = Column(Integer, ForeignKey('tag.id', ondelete='CASCADE'), unique=True, nullable=False)
    tag = relationship('Tag', backref=backref('tag', cascade='delete'))
