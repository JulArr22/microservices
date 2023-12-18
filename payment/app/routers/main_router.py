# -*- coding: utf-8 -*-
"""FastAPI router definitions."""
import logging
from typing import List
from fastapi import APIRouter, Depends, status, Header, Query
from sqlalchemy.ext.asyncio import AsyncSession
from dependencies import get_db
from sql import crud, schemas
from routers import security, rabbitmq_publish_logs
from routers.router_utils import raise_and_log_error


logger = logging.getLogger(__name__)
router = APIRouter()


@router.get(
    "/payment/health",
    summary="Health check endpoint",
    response_model=schemas.Message,
)
async def health_check():
    """Endpoint to check if everything started correctly."""
    logger.debug("GET '/payment/health' endpoint called.")
    if await security.isTherePublicKey():
        return {"detail": "Service Healthy."}
    else:
        raise_and_log_error(logger, status.HTTP_503_SERVICE_UNAVAILABLE, "Service Unavailable.")


@router.post(
    "/payment/deposit",
    response_model=schemas.Payment,
    summary="Create single deposit",
    status_code=status.HTTP_201_CREATED,
    tags=["Payment"]
)
async def create_payment(
        payment_schema: schemas.PaymentBase,
        db: AsyncSession = Depends(get_db),
        token: str = Header(..., description="JWT Token in the Header")
):
    """Create single deposit endpoint."""
    logger.debug("POST '/payment/deposit' endpoint called.")
    try:
        payload = security.decode_token(token)
        # validar fecha expiración del token
        is_expirated = security.validar_fecha_expiracion(payload)
        if(is_expirated):

            message="ERROR : The token is expired, please log in again"
            routing_key = "payment.mainrouter_payment_deposit.error"
            await rabbitmq_publish_logs.send_message_log(message, routing_key)

            raise_and_log_error(logger, status.HTTP_409_CONFLICT, f"The token is expired, please log in again")

        payment_schema.id_client = payload["id_client"]
        db_payment = await crud.create_deposit(db, payment_schema)
        return db_payment
    except Exception as exc:  # @ToDo: To broad exception

        message=f"ERROR : Error creating deposit: {exc}"
        routing_key = "payment.mainrouter_payment_deposit.error"
        await rabbitmq_publish_logs.send_message_log(message, routing_key)

        raise_and_log_error(logger, status.HTTP_409_CONFLICT, f"Error creating deposit: {exc}")


# @router.get(
#     "/payment",
#     response_model=List[schemas.Payment],
#     summary="Retrieve payment list",
#     tags=["Payment", "List"]  # Optional so it appears grouped in documentation
# )
# async def get_payment_list(
#         db: AsyncSession = Depends(get_db),
#         token: str = Header(..., description="JWT Token in the Header")
# ):
#     """Retrieve payment list"""
#     logger.debug("GET '/payment' endpoint called.")
#     try:
#         payload = security.decode_token(token)
#         # validar fecha expiración del token
#         is_expirated = security.validar_fecha_expiracion(payload)
#         if(is_expirated):

#             message="ERROR : The token is expired, please log in again"
#             routing_key = "payment.mainrouter_list.error"
#             await rabbitmq_publish_logs.send_message_log(message, routing_key)

#             raise_and_log_error(logger, status.HTTP_409_CONFLICT, f"The token is expired, please log in again")
#         else:
#             es_admin = security.validar_es_admin(payload)
#             if(es_admin==False):

#                 message="ERROR : You don't have permissions"
#                 routing_key = "payment.mainrouter_list.error"
#                 await rabbitmq_publish_logs.send_message_log(message, routing_key)

#                 raise_and_log_error(logger, status.HTTP_409_CONFLICT, f"You don't have permissions")
#         payment_list = await crud.get_payments_list(db)
#         return payment_list
#     except Exception as exc:  # @ToDo: To broad exception

#         message=f"ERROR : Error payment list: {exc}"
#         routing_key = "payment.mainrouter_list.error"
#         await rabbitmq_publish_logs.send_message_log(message, routing_key)

#         raise_and_log_error(logger, status.HTTP_409_CONFLICT, f"Error payment list: {exc}")

    


@router.get(
    "/payment",
    summary="Retrieve single payment by id",
    responses={
        status.HTTP_200_OK: {
            "model": schemas.Payment,
            "description": "Requested Payment."
        },
        status.HTTP_404_NOT_FOUND: {
            "model": schemas.Message, "description": "Payment not found"
        }
    },
    tags=['Payment']
)
async def get_single_payment(
        payment_id: int = Query(None, description="Client ID"),
        client_id: int = Query(None, description="Client ID"),
        db: AsyncSession = Depends(get_db),
        token: str = Header(..., description="JWT Token in the Header")
):
    """Retrieve single payment by id"""
    logger.debug("GET '/payment' endpoint called.", payment_id)

    if payment_id is None and client_id is None:
        try:
            payload = security.decode_token(token)
            # validar fecha expiración del token
            is_expirated = security.validar_fecha_expiracion(payload)
            if(is_expirated):

                message="ERROR : The token is expired, please log in again"
                routing_key = "payment.mainrouter_list.error"
                await rabbitmq_publish_logs.send_message_log(message, routing_key)

                raise_and_log_error(logger, status.HTTP_409_CONFLICT, f"The token is expired, please log in again")
            else:
                es_admin = security.validar_es_admin(payload)
                if(es_admin==False):

                    message="ERROR : You don't have permissions"
                    routing_key = "payment.mainrouter_list.error"
                    await rabbitmq_publish_logs.send_message_log(message, routing_key)

                    raise_and_log_error(logger, status.HTTP_409_CONFLICT, f"You don't have permissions")
            payment_list = await crud.get_payments_list(db)
            return payment_list
        except Exception as exc:  # @ToDo: To broad exception

            message=f"ERROR : Error payment list: {exc}"
            routing_key = "payment.mainrouter_list.error"
            await rabbitmq_publish_logs.send_message_log(message, routing_key)

            raise_and_log_error(logger, status.HTTP_409_CONFLICT, f"Error payment list: {exc}")

    if payment_id is not None and client_id is None:
        try:
            payload = security.decode_token(token)
            # validar fecha expiración del token
            is_expirated = security.validar_fecha_expiracion(payload)
            if(is_expirated):

                message="ERROR: The token is expired, please log in again"
                routing_key = "payment.mainrouter_payment_id.error"
                await rabbitmq_publish_logs.send_message_log(message, routing_key)

                raise_and_log_error(logger, status.HTTP_409_CONFLICT, f"The token is expired, please log in again")
            else:
                es_admin = security.validar_es_admin(payload)
                client_id = payload["id_client"]
                payment = await crud.get_payment(db, payment_id)
                if(es_admin==False and payment.id_client!=client_id):

                    message=f"ERROR: You don't have permissions"
                    routing_key = "payment.mainrouter_payment_id.error"
                    await rabbitmq_publish_logs.send_message_log(message, routing_key)

                    raise_and_log_error(logger, status.HTTP_409_CONFLICT, f"You don't have permissions")
            payment = await crud.get_payment(db, payment_id)
            if not payment:

                message=f"ERROR: Payment {payment_id} not found"
                routing_key = "payment.mainrouter_payment_id.error"
                await rabbitmq_publish_logs.send_message_log(message, routing_key)

                raise_and_log_error(logger, status.HTTP_404_NOT_FOUND, f"Payment {payment_id} not found")
            return payment
        except Exception as exc:  # @ToDo: To broad exception
            message=f"ERROR : Error getting payment by Id: {exc}"
            routing_key = "payment.mainrouter_payment_id.error"
            await rabbitmq_publish_logs.send_message_log(message, routing_key)

            raise_and_log_error(logger, status.HTTP_409_CONFLICT, f"Error getting payment by Id: {exc}")
    if payment_id is None and client_id is not None:
        try:
            payload = security.decode_token(token)
            # validar fecha expiración del token
            is_expirated = security.validar_fecha_expiracion(payload)
            if(is_expirated):

                message="ERROR : The token is expired, please log in again"
                routing_key = "payment.mainrouter_payment_client_id.error"
                await rabbitmq_publish_logs.send_message_log(message, routing_key)

                raise_and_log_error(logger, status.HTTP_409_CONFLICT, f"The token is expired, please log in again")
            else:
                es_admin = security.validar_es_admin(payload)
                client_id_token = payload["id_client"]
                if(es_admin==False and client_id!=client_id_token):

                    message=f"ERROR: You don't have permissions"
                    routing_key = "payment.mainrouter_payment_client_id.error"
                    await rabbitmq_publish_logs.send_message_log(message, routing_key)

                    raise_and_log_error(logger, status.HTTP_409_CONFLICT, f"You don't have permissions")
            payments = await crud.get_clients_payments(db, client_id)
            if not payments:
                raise_and_log_error(logger, status.HTTP_404_NOT_FOUND, f"Client {client_id}'s payments not found")
            return payments
        except Exception as exc:
            message=f"ERROR : Error getting payments by client: {exc}"
            routing_key = "payment.mainrouter_payment_client_id.error"
            await rabbitmq_publish_logs.send_message_log(message, routing_key)

            raise_and_log_error(logger, status.HTTP_409_CONFLICT, f"Error Error getting payments by client: {exc}")


# @router.get(
#     "/payment/client/{client_id}",
#     summary="Retrieve client's payments by id",
#     responses={
#         status.HTTP_200_OK: {
#             "model": schemas.Payment,
#             "description": "Requested Payments."
#         },
#         status.HTTP_404_NOT_FOUND: {
#             "model": schemas.Message, "description": "Payments not found"
#         }
#     },
#     tags=['Payments']
# )
# async def get_single_client(
#         client_id: int,
#         db: AsyncSession = Depends(get_db),
#         token: str = Header(..., description="JWT Token in the Header")
# ):
#     """Retrieve client's payments by id"""
#     logger.debug("GET '/payment/client/%i' endpoint called.", client_id)
#     try:
#         payload = security.decode_token(token)
#         # validar fecha expiración del token
#         is_expirated = security.validar_fecha_expiracion(payload)
#         if(is_expirated):

#             message="ERROR : The token is expired, please log in again"
#             routing_key = "payment.mainrouter_payment_client_id.error"
#             await rabbitmq_publish_logs.send_message_log(message, routing_key)

#             raise_and_log_error(logger, status.HTTP_409_CONFLICT, f"The token is expired, please log in again")
#         else:
#             es_admin = security.validar_es_admin(payload)
#             client_id_token = payload["id_client"]
#             if(es_admin==False and client_id!=client_id_token):

#                 message=f"ERROR: You don't have permissions"
#                 routing_key = "payment.mainrouter_payment_client_id.error"
#                 await rabbitmq_publish_logs.send_message_log(message, routing_key)

#                 raise_and_log_error(logger, status.HTTP_409_CONFLICT, f"You don't have permissions")
#         payments = await crud.get_clients_payments(db, client_id)
#         if not payments:
#             raise_and_log_error(logger, status.HTTP_404_NOT_FOUND, f"Client {client_id}'s payments not found")
#         return payments
#     except Exception as exc:
#         message=f"ERROR : Error getting payments by client: {exc}"
#         routing_key = "payment.mainrouter_payment_client_id.error"
#         await rabbitmq_publish_logs.send_message_log(message, routing_key)

#         raise_and_log_error(logger, status.HTTP_409_CONFLICT, f"Error Error getting payments by client: {exc}")
