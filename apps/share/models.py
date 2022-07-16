from sqlalchemy import Column, ForeignKey, Integer, DateTime, Boolean
from sqlalchemy.orm import relationship, backref
from sqlalchemy.sql import func

from system.connection.generators import DatabaseGenerator

Base = DatabaseGenerator.get_base()

class DataShared(Base):
    __tablename__ = 'dataShared'

    id = Column(Integer, primary_key=True, autoincrement=True)
    share_started = Column(DateTime(timezone=True), server_default=func.now())
    is_active = Column(Boolean, default=True)
    datainfo_id = Column(Integer, ForeignKey('datainfo.id'), unique=True)
    datainfo = relationship('DataInfo', backref=backref('tag', cascade='delete'))
