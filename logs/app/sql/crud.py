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


# Logs functions ##################################################################################
async def get_all_logs(db: AsyncSession):
    """Load all the logs from the database."""
    stmt = select(models.Log)
    deliveries = await get_list_statement_result(db, stmt)
    return deliveries


async def get_log(db: AsyncSession, log_id):
    """Load a log from the database."""
    return await get_element_by_id(db, models.Delivery, log_id)


async def get_logs(db: AsyncSession, number_of_logs):
    """Load a log from the database."""
    stmt = select(models.Log).order_by(models.Log.id_log.desc()).limit(number_of_logs)
    return await get_list_statement_result(db, stmt)


async def create_log(db: AsyncSession, log):
    """Persist a new order into the database."""
    db_log = models.Log(
        exchange=log.exchange,
        routing_key=log.routing_key,
        data=log.data,
    )
    db.add(db_log)
    await db.commit()
    await db.refresh(db_log)
    return db_log


