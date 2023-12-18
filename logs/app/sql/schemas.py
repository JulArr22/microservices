# -*- coding: utf-8 -*-
"""Classes for Request/Response schema definitions."""
# pylint: disable=too-few-public-methods
from typing import List, Optional
from pydantic import BaseModel, Field  # pylint: disable=no-name-in-module
from datetime import datetime


class Message(BaseModel):
    """Message schema definition."""
    detail: Optional[str] = Field(example="error or success message")


class LogBase(BaseModel):
    """Log base schema definition."""
    data: str = Field(
        description="The data of the message.",
        default=""
    )
    exchange: str = Field(
        description="The exchange name of the message.",
        default=""
    )
    routing_key: str = Field(
        description="The routing key of the message.",
        default=""
    )
    id_log: int = Field(
        description="Primary key/identifier of the log.",
        default=None
    )

