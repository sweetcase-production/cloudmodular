from sqlalchemy import (
    Boolean, Column, DateTime, ForeignKey,
    Integer, String, Text, UniqueConstraint
)
from sqlalchemy.sql import func

from system.connection.generators import DatabaseGenerator

Base = DatabaseGenerator.get_base()

class Tag:
    pass