# -*- coding: utf-8 -*-
"""FastAPI router definitions."""
import asyncio
import logging
from typing import List
from fastapi import APIRouter, Depends, status, Header, Query
from sqlalchemy.ext.asyncio import AsyncSession
from dependencies import get_db
from sql import crud, schemas, models
from routers.router_utils import raise_and_log_error
from routers import security
from routers.rabbitmq import send_product
from routers import rabbitmq_publish_logs
import json

logger = logging.getLogger(__name__)
router = APIRouter()


@router.get(
    "/delivery/health",
    summary="Health check endpoint",
    response_model=schemas.Message,
)
async def health_check():
    """Endpoint to check if everything started correctly."""
    logger.debug("GET '/delivery/health' endpoint called.")
    if await security.isTherePublicKey():
        return {"detail": "Service Healthy."}
    else:
        raise_and_log_error(logger, status.HTTP_503_SERVICE_UNAVAILABLE, "Service Unavailable.")


@router.get(
    "/delivery",
    summary="Retrieve single delivery by order id",
    responses={
        status.HTTP_200_OK: {
            "model": schemas.Delivery,
            "description": "Requested delivery."
        },
        status.HTTP_404_NOT_FOUND: {
            "model": schemas.Message, "description": "Delivery not found"
        }
    },
    tags=['Delivery']
)
async def get_single_delivery(
        order_id: int = Query(None, description="Order ID"),
        db: AsyncSession = Depends(get_db),
        token: str = Header(..., description="JWT Token in the Header")
):
    """Retrieve single delivery by id"""
    logger.debug("GET '/delivery/%i' endpoint called.", order_id)
    payload = security.decode_token(token)

    if order_id is not None:
        # validar fecha expiración del token
        is_expirated = security.validar_fecha_expiracion(payload)
        if(is_expirated):
            data = {
                "message": "ERROR - Token expired, log in again"
            }
            message_body = json.dumps(data)
            routing_key = "delivery.main_router_get_single_delivery.error"
            await rabbitmq_publish_logs.publish_log(message_body, routing_key)
            raise_and_log_error(logger, status.HTTP_409_CONFLICT, f"The token is expired, please log in again")
        delivery = await crud.get_delivery_by_order(db, order_id)
        
        if not delivery:
            data = {
                "message": "ERROR - Delivery not found"
            }
            message_body = json.dumps(data)
            routing_key = "delivery.main_router_get_single_delivery.error"
            await rabbitmq_publish_logs.publish_log(message_body, routing_key)
            raise_and_log_error(logger, status.HTTP_404_NOT_FOUND, f"Delivery {order_id} not found")
        data = {
            "message": "INFO - Delivery obtained"
        }
        message_body = json.dumps(data)
        routing_key = "delivery.main_router_get_single_delivery.info"
        await rabbitmq_publish_logs.publish_log(message_body, routing_key)
        return delivery
    else:
        # validar fecha expiración del token
        is_expirated = security.validar_fecha_expiracion(payload)
        if(is_expirated):
            data = {
                "message": "ERROR - Token expirated, log in again"
            }
            message_body = json.dumps(data)
            routing_key = "delivery.main_router_get_list_delivery.error"
            await rabbitmq_publish_logs.publish_log(message_body, routing_key)
            raise_and_log_error(logger, status.HTTP_409_CONFLICT, f"The token is expired, please log in again")
        else:
            es_admin = security.validar_es_admin(payload)
            if(es_admin==False):
                data = {
                    "message": "ERROR - You don't have permissions"
                }
                message_body = json.dumps(data)
                routing_key = "delivery.main_router_get_list_delivery.error"
                await rabbitmq_publish_logs.publish_log(message_body, routing_key)
                raise_and_log_error(logger, status.HTTP_409_CONFLICT, f"You don't have permissions")
        delivery_list = await crud.get_delivery_list(db)
        if not delivery_list:
            data = {
                "message": "ERROR - Delivery not found"
            }
            message_body = json.dumps(data)
            routing_key = "delivery.main_router_get_list_delivery.error"
            await rabbitmq_publish_logs.publish_log(message_body, routing_key)
            raise_and_log_error(logger, status.HTTP_404_NOT_FOUND, f"Delivery not found")
        data = {
            "message": "INFO - Delivery list obtained"
        }
        message_body = json.dumps(data)
        routing_key = "delivery.main_router_get_list_delivery.info"
        await rabbitmq_publish_logs.publish_log(message_body, routing_key)
        return delivery_list

# @router.get(
#     "/delivery",
#     summary="Retrieve list delivery",
#     responses={
#         status.HTTP_200_OK: {
#             "model": schemas.Delivery,
#             "description": "Requested delivery."
#         },
#         status.HTTP_404_NOT_FOUND: {
#             "model": schemas.Message, "description": "Delivery not found"
#         }
#     },
#     tags=['Delivery']
# )
# async def get_list_delivery(
#         db: AsyncSession = Depends(get_db),
#         token: str = Header(..., description="JWT Token in the Header")
# ):
#     """Retrieve list delivery"""
#     logger.debug("GET '/delivery' endpoint called.")
#     payload = security.decode_token(token)
#     # validar fecha expiración del token
#     is_expirated = security.validar_fecha_expiracion(payload)
#     if(is_expirated):
#         data = {
#             "message": "ERROR - Token expirated, log in again"
#         }
#         message_body = json.dumps(data)
#         routing_key = "delivery.main_router_get_list_delivery.error"
#         await rabbitmq_publish_logs.publish_log(message_body, routing_key)
#         raise_and_log_error(logger, status.HTTP_409_CONFLICT, f"The token is expired, please log in again")
#     else:
#         es_admin = security.validar_es_admin(payload)
#         if(es_admin==False):
#             data = {
#                 "message": "ERROR - You don't have permissions"
#             }
#             message_body = json.dumps(data)
#             routing_key = "delivery.main_router_get_list_delivery.error"
#             await rabbitmq_publish_logs.publish_log(message_body, routing_key)
#             raise_and_log_error(logger, status.HTTP_409_CONFLICT, f"You don't have permissions")
#     delivery_list = await crud.get_delivery_list(db)
#     if not delivery_list:
#         data = {
#             "message": "ERROR - Delivery not found"
#         }
#         message_body = json.dumps(data)
#         routing_key = "delivery.main_router_get_list_delivery.error"
#         await rabbitmq_publish_logs.publish_log(message_body, routing_key)
#         raise_and_log_error(logger, status.HTTP_404_NOT_FOUND, f"Delivery not found")
#     data = {
#         "message": "INFO - Delivery list obtained"
#     }
#     message_body = json.dumps(data)
#     routing_key = "delivery.main_router_get_list_delivery.info"
#     await rabbitmq_publish_logs.publish_log(message_body, routing_key)
#     return delivery_list
