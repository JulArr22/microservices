# -*- coding: utf-8 -*-
"""Classes for Request/Response schema definitions."""
# pylint: disable=too-few-public-methods
from typing import List, Optional
from pydantic import BaseModel, Field  # pylint: disable=no-name-in-module


class Message(BaseModel):
    """Message schema definition."""
    detail: Optional[str] = Field(example="error or success message.")


class ClientBase(BaseModel):
    """Client base schema definition."""
    username: str = Field(
        description="The username of the client.",
        default=None,
        example="itziariraarr"
    )
    email: str = Field(
        description="The email of the client.",
        default="example@gmail.com",
        example="example@gmail.com"
    )
    address: str = Field(
        description="The address of the client.",
        default="puticlub manoli",
        example="puticlub manoli"
    )
    postal_code: str = Field(
        description="The postal code of the client.",
        default="20000",
        example="20000"
    )
    role: int = Field(
        description="The role of the client.", # 0 === CLIENT
        default=0,                           # 1 === ADMIN
        example=0
    )


class Client(ClientBase):
    """Client schema definition."""
    id_client: int = Field(
        description="Primary key/identifier of the client.",
        default=None,
        example=1
    )

    class Config:
        """ORM configuration."""
        orm_mode = True


class ClientPost(ClientBase):
    """Schema definition to create a new client."""
    password: str = Field(
        description="The password of the client.",
        default="asdfasdf3423",
        example="asdfasdf3423"
    )


class ClientUpdatePost(BaseModel):
    """Schema definition to update a client."""
    email: str = Field(
        description="The email of the client.",
        default="example@gmail.com",
        example="example@gmail.com"
    )
    address: str = Field(
        description="The address of the client.",
        default="puticlub manoli",
        example="puticlub manoli"
    )
    postal_code: str = Field(
        description="The postal code of the client.",
        default="20000",
        example="20000"
    )


class TokenRequest(BaseModel):
    """Client base schema definition."""
    username: str = Field(
        description="The username of the client.",
        default=None,
        example="itziariraarr"
    )
    password: str = Field(
        description="The email of the client.",
        default="example@gmail.com",
        example="example@gmail.com"
    )