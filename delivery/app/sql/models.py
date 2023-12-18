# -*- coding: utf-8 -*-
"""Database models definitions. Table representations as class."""
from sqlalchemy import Column, DateTime, Integer, String, TEXT, ForeignKey, Float
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from .database import Base


# from datetime import datetime

class BaseModel(Base):
    """Base database table representation to reuse."""
    __abstract__ = True
    creation_date = Column(DateTime(timezone=True), server_default=func.now())

    def __repr__(self):
        fields = ""
        for column in self.__table__.columns:
            if fields == "":
                fields = f"{column.name}='{getattr(self, column.name)}'"
                # fields = "{}='{}'".format(column.name, getattr(self, column.name))
            else:
                fields = f"{fields}, {column.name}='{getattr(self, column.name)}'"
                # fields = "{}, {}='{}'".format(fields, column.name, getattr(self, column.name))
        return f"<{self.__class__.__name__}({fields})>"
        # return "<{}({})>".format(self.__class__.__name__, fields)

    @staticmethod
    def list_as_dict(items):
        """Returns list of items as dict."""
        return [i.as_dict() for i in items]

    def as_dict(self):
        """Return the item as dict."""
        return {c.name: getattr(self, c.name) for c in self.__table__.columns}


class Delivery(BaseModel):
    """Deliveries database table representation."""
    STATUS_CREATED = "Created"
    STATUS_CANCELED = "Canceled"
    STATUS_DELIVERING = "Delivering"
    STATUS_DELIVERED = "Delivered"

    __tablename__ = "delivery"
    id_delivery = Column(Integer, primary_key=True)
    id_order = Column(Integer, nullable=False)
    address = Column(String(256), nullable=True)
    postal_code = Column(Integer, nullable=True)
    status_delivery = Column(String(256), nullable=False, default=STATUS_CREATED)


class Client(BaseModel):
    """Client database table representation."""
    __tablename__ = "clients"
    id_client = Column(Integer, primary_key=True)
    address = Column(TEXT, nullable=False)
    postal_code = Column(Integer, nullable=False)
