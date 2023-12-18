# -*- coding: utf-8 -*-
"""Classes for Request/Response schema definitions."""
# pylint: disable=too-few-public-methods
from typing import List, Optional
from pydantic import BaseModel, Field  # pylint: disable=no-name-in-module
from datetime import datetime


class Message(BaseModel):
    """Message schema definition."""
    detail: Optional[str] = Field(example="error or success message")


class DeliveryBase(BaseModel):
    """Delivery base schema definition."""
    address: str = Field(
        description="The address where the packege will be recieved.",
        default="No address",
        example="Calle x, 1B"
    )
    postal_code: int = Field(
        description="The postal code where the packege will be recieved.",
        default="No postal code",
        example="20000"
    )
    id_order: int = Field(
        description="Primary key/identifier of the order.",
        default=None,
        example=1
    )
    #  pieces = relationship("Piece", lazy="joined")


class Delivery(DeliveryBase):
    """Delivery schema definition."""
    id_delivery: int = Field(
        description="Primary key/identifier of the delivery.",
        default=None,
        example=1
    )
    status_delivery: str = Field(
        description="Current status of the delivery.",
        default="Created",
        example="Finished"
    )

    class Config:
        """ORM configuration."""
        orm_mode = True

class ClientBase(BaseModel):
    """Delivery base schema definition."""
    id_client: str = Field(
        description="The name of the person that will recieve the package.",
        default="No name",
        example="Luis"
    )
    address: str = Field(
        description="The address where the packege will be recieved.",
        default="No address",
        example="Calle x, 1B"
    )
    postal_code: int = Field(
        description="The postal code where the packege will be recieved.",
        default="No postal code",
        example="20000"
    )
