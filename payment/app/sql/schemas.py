# -*- coding: utf-8 -*-
"""Classes for Request/Response schema definitions."""
# pylint: disable=too-few-public-methods
from typing import List, Optional
from pydantic import BaseModel, Field  # pylint: disable=no-name-in-module
from sqlalchemy import Float


# from datetime import datetime

class Message(BaseModel):
    """Message schema definition."""
    detail: Optional[str] = Field(example="error or success message")


class PaymentBase(BaseModel):
    """Payment base schema definition."""
    id_client: str = Field(
        description="The ID of the client.",
        default=None
    )
    movement: str = Field(
        description="The movement of the client."
    )


class Payment(PaymentBase):
    """Payment schema definition."""
    id_payment: int = Field(
        description="Primary key/identifier of the payment."
    )
    id_order: int = Field(
        description="The ID of the order.",
        example="-1"
    )

    # date: DateTime = Field(
    #    description="Date and time of the payment."
    # )

    class Config:
        """ORM configuration."""
        orm_mode = True
