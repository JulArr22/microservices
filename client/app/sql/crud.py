# -*- coding: utf-8 -*-
"""Functions that interact with the database."""
import logging
from datetime import datetime
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from . import models
import json
from routers.rabbitmq import publish_event

logger = logging.getLogger(__name__)


# Generic functions #################################################################################
# READ
async def get_list(db: AsyncSession, model):
    """Retrieve a list of elements from database"""
    result = await db.execute(select(model))
    item_list = result.unique().scalars().all()
    return item_list


async def get_list_statement_result(db: AsyncSession, stmt):
    """Execute given statement and return list of items."""
    result = await db.execute(stmt)
    item_list = result.unique().scalars().all()
    return item_list


async def get_element_statement_result(db: AsyncSession, stmt):
    """Execute statement and return a single items"""
    result = await db.execute(stmt)
    item = result.scalar()
    return item


async def get_element_by_id(db: AsyncSession, model, element_id):
    """Retrieve any DB element by id."""
    if element_id is None:
        return None
    element = await db.get(model, element_id)
    return element

async def get_element_by_username_and_pass(db: AsyncSession, model, username, password):
    """Retrieve any DB element by id."""
    if username is None:
        return None
    """Obtener un cliente por nombre de usuario y contraseña."""
    stmt = select(model).filter(model.username == username, model.password == password)
    element = await get_element_statement_result(db, stmt)
    return element

# DELETE
async def delete_element_by_id(db: AsyncSession, model, element_id):
    """Delete any DB element by id."""
    element = await get_element_by_id(db, model, element_id)
    if element is not None:
        await db.delete(element)
        await db.commit()
    return element


# Client functions ##################################################################################
async def get_client_list(db: AsyncSession):
    """Load all the clients from the database."""
    stmt = select(models.Client)
    clients = await get_list_statement_result(db, stmt)
    return clients


async def get_client(db: AsyncSession, client_id):
    """Load a client from the database."""
    return await get_element_by_id(db, models.Client, client_id)

async def get_client_by_username_and_pass(db: AsyncSession, username, password):
    """Load a client from the database."""
    return await get_element_by_username_and_pass(db, models.Client, username, password)


async def create_client(db: AsyncSession, client):
    """Persist a new client into the database."""
    db_client = models.Client(
        username=client.username,
        email=client.email,
        password=client.password,
        address=client.address,
        postal_code=client.postal_code,
        role = client.role
    )
    db.add(db_client)
    await db.commit()
    await db.refresh(db_client)
    data = {
        "id_client": db_client.id_client,
        "address": db_client.address,
        "postal_code": db_client.postal_code
    }
    message_body = json.dumps(data)
    routing_key = "client.created"
    await publish_event(message_body, routing_key)
    return db_client


async def update_client(db: AsyncSession, client_id, client):
    """Modify a client of the database."""
    db_client = await get_client(db, client_id)
    db_client.email = client.email
    db_client.address = client.address
    db_client.postal_code = client.postal_code
    await db.commit()
    await db.refresh(db_client)
    data = {
        "id_client": db_client.id_client,
        "address": db_client.address,
        "postal_code": db_client.postal_code
    }
    message_body = json.dumps(data)
    routing_key = "client.updated"
    await publish_event(message_body, routing_key)
    return db_client
