# -*- coding: utf-8 -*-
"""Functions that interact with the database."""
import logging
from datetime import datetime
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from . import models

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


# DELETE
async def delete_element_by_id(db: AsyncSession, model, element_id):
    """Delete any DB element by id."""
    element = await get_element_by_id(db, model, element_id)
    if element is not None:
        await db.delete(element)
        await db.commit()
    return element


# Delivery functions ##################################################################################
async def get_delivery_list(db: AsyncSession):
    """Load all the deliveries from the database."""
    stmt = select(models.Delivery)
    deliveries = await get_list_statement_result(db, stmt)
    return deliveries


async def get_delivery(db: AsyncSession, delivery_id):
    """Load a delivery from the database."""
    return await get_element_by_id(db, models.Delivery, delivery_id)


async def get_client(db: AsyncSession, client_id):
    """Load a client from the database."""
    return await get_element_by_id(db, models.Client, client_id)


async def get_delivery_by_order(db: AsyncSession, order_id):
    """Load a delivery from the database."""
    stmt = select(models.Delivery).where(models.Delivery.id_order == order_id)
    delivery = await get_list_statement_result(db, stmt)
    return delivery[0]


async def store_client(db: AsyncSession, client):
    """Persist a new client into the database."""
    db_client = models.Client(
        id_client=client.id_client,
        address=client.address,
        postal_code=client.postal_code
    )
    db.add(db_client)
    await db.commit()
    await db.refresh(db_client)
    return db_client


async def update_client(db: AsyncSession, client):
    """Update a client of the database."""
    db_client = await get_client(db, client.id_client)
    db_client.address = client.address
    db_client.postal_code = client.postal_code
    await db.commit()
    await db.refresh(db_client)
    return db_client


async def check_address(db: AsyncSession, db_client):
    """Persist a new client into the database."""
    provincia = db_client.postal_code // 1000 # Extraer código de provincia del código postal
    if (provincia == 1 or provincia == 20 or provincia == 48):
        address_check = True
    else:
        address_check = False
    return address_check


async def create_delivery(db: AsyncSession, db_delivery):
    """Persist a new order into the database."""
    db.add(db_delivery)
    await db.commit()
    await db.refresh(db_delivery)
    return db_delivery


async def change_delivery_status(db: AsyncSession, delivery_id, status):
    """Change order status in the database."""
    db_delivery = await get_delivery(db, delivery_id)
    db_delivery.status_delivery = status
    await db.commit()
    await db.refresh(db_delivery)
    return db_delivery


async def add_delivery_info(db: AsyncSession, delivery):
    """Change order status in the database."""
    db_delivery = await get_delivery_by_order(db, delivery.id_order)
    db_delivery.name = delivery.name
    db_delivery.address = delivery.address
    await db.commit()
    await db.refresh(db_delivery)
    return db_delivery
