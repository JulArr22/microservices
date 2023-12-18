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


# Payment functions ##################################################################################
async def get_payments_list(db: AsyncSession):
    """Load all the payments from the database."""
    stmt = select(models.Payment)
    payments = await get_list_statement_result(db, stmt)
    return payments


async def get_payment(db: AsyncSession, payment_id):
    """Load a payment from the database."""
    return await get_element_by_id(db, models.Payment, payment_id)


async def get_clients_payments(db: AsyncSession, client_id):
    """Load all the payments from the database."""
    stmt = select(models.Payment).where(models.Payment.id_client == client_id)
    payments = await get_list_statement_result(db, stmt)
    return payments


async def create_payment(db: AsyncSession, payment):
    """Persist a new payment into the database."""
    """Check if the client has enough balance for the payment, else return False"""
    payment_movement_float = float(payment['movement'])
    if payment_movement_float < 0:
        clients_payments_list = await get_clients_payments(db, payment['id_client'])
        client_balance = 0
        for client_payment in clients_payments_list:
            client_balance += client_payment.movement
        if (payment_movement_float + client_balance) < 0:
            raise Exception("Insufficient balance.")
    db_payment = models.Payment(
        id_client=payment['id_client'],
        id_order=payment['id_order'],
        movement=payment_movement_float
    )
    db.add(db_payment)
    await db.commit()
    await db.refresh(db_payment)
    return db_payment


async def create_deposit(db: AsyncSession, payment):
    """Persist a new deposit into the database."""
    payment_movement_float = float(payment.movement)
    if payment_movement_float <= 0:
        raise Exception("Can not make negative deposit.")
    db_payment = models.Payment(
        id_client=payment.id_client,
        movement=payment_movement_float,
        id_order=-1
    )
    db.add(db_payment)
    await db.commit()
    await db.refresh(db_payment)
    return db_payment