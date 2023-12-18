# -*- coding: utf-8 -*-
"""FastAPI router definitions."""
import logging
from typing import List
from fastapi import APIRouter, Depends, status, Header, Query
from sqlalchemy.ext.asyncio import AsyncSession
from dependencies import get_db
from routers import security
from sql import crud, schemas
from routers.router_utils import raise_and_log_error
from routers import rabbitmq_publish_logs

from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric import rsa
import jwt
import json

from datetime import datetime, timedelta

logger = logging.getLogger(__name__)
router = APIRouter()


@router.get(
    "/client/health",
    summary="Health check endpoint",
    response_model=schemas.Message,
)
async def health_check():
    """Endpoint to check if everything started correctly."""
    logger.debug("GET '/client/health' endpoint called.")
    return {"detail": "Service Healthy."}


@router.post(
    "/client",
    response_model=schemas.Client,
    summary="Create single client",
    status_code=status.HTTP_201_CREATED,
    tags=["Client"]
)
async def create_client(
        client_schema: schemas.ClientPost,
        db: AsyncSession = Depends(get_db),
        token: str = Header(..., description="JWT Token in the Header")
):
    """Create single client endpoint."""
    logger.debug("POST '/client' endpoint called.")
    try:
        # Permitir acceso para crear un administrador, en caso de que borremos DB:
        if (client_schema.username == "joxemai" and client_schema.password == "joxemai"):
            client_schema.role = 1
            db_client = await crud.create_client(db, client_schema)
            data = {
                "message": "INFO - Client created"
            }
            message_body = json.dumps(data)
            routing_key = "client.main_router_create_client.info"
            await rabbitmq_publish_logs.publish_log(message_body, routing_key)
            return db_client
        # Decodificar el token
        payload = security.decode_token(token)
        # Validar fecha expiración del token
        is_expirated = security.validar_fecha_expiracion(payload)
        if(is_expirated):
            data = {
                "message": "ERROR - The token is expired, log in again"
            }
            message_body = json.dumps(data)
            routing_key = "client.main_router_create_client.error"
            await rabbitmq_publish_logs.publish_log(message_body, routing_key)
            raise_and_log_error(logger, status.HTTP_409_CONFLICT, f"The token is expired, please log in again")
        else:
            es_admin = security.validar_es_admin(payload)
            if(es_admin):
                db_client = await crud.create_client(db, client_schema)
                data = {
                    "message": "INFO - Client created"
                }
                message_body = json.dumps(data)
                routing_key = "client.main_router_create_client.info"
                await rabbitmq_publish_logs.publish_log(message_body, routing_key)
                return db_client 
            else:
                data = {
                    "message": "ERROR - You don't have permissions"
                }
                message_body = json.dumps(data)
                routing_key = "client.main_router_create_client.error"
                await rabbitmq_publish_logs.publish_log(message_body, routing_key)
                raise_and_log_error(logger, status.HTTP_409_CONFLICT, f"You don't have permissions")
    except Exception as exc:  # @ToDo: To broad exception
        data = {
            "message": "ERROR - Error creating client"
        }
        message_body = json.dumps(data)
        routing_key = "client.main_router_create_client.error"
        await rabbitmq_publish_logs.publish_log(message_body, routing_key)
        raise_and_log_error(logger, status.HTTP_409_CONFLICT, f"Error creating client: {exc}")


@router.post(
    "/client/update",
    response_model=schemas.Client,
    summary="Update single client",
    status_code=status.HTTP_201_CREATED,
    tags=["Client"]
)
async def update_client(
        client_schema: schemas.ClientUpdatePost,
        client_id: int = Query(..., description="Client ID"),
        db: AsyncSession = Depends(get_db),
        token: str = Header(..., description="JWT Token in the Header")
):
    """Update single client endpoint."""
    logger.debug("POST '/client/update' endpoint called.")
    try:
        # Decodificar el token
        payload = security.decode_token(token)
        # Validar fecha expiración del token
        is_expirated = security.validar_fecha_expiracion(payload)
        if(is_expirated):
            data = {
                "message": "ERROR - The token is expired, log in again"
            }
            message_body = json.dumps(data)
            routing_key = "client.main_router_update_client.error"
            await rabbitmq_publish_logs.publish_log(message_body, routing_key)
            raise_and_log_error(logger, status.HTTP_409_CONFLICT, f"The token is expired, please log in again")
        else:
            es_admin = security.validar_es_admin(payload)
            client_id_token = payload["id_client"]
            if(es_admin==False and client_id!=client_id_token):
                data = {
                    "message": "ERROR - You don't have permissions"
                }
                message_body = json.dumps(data)
                routing_key = "client.main_router_update_client.error"
                await rabbitmq_publish_logs.publish_log(message_body, routing_key)
                raise_and_log_error(logger, status.HTTP_409_CONFLICT, f"You don't have permissions")
            db_client = await crud.update_client(db, client_id, client_schema)
            data = {
                "message": "INFO - Client updated"
            }
            message_body = json.dumps(data)
            routing_key = "client.main_router_update_client.info"
            await rabbitmq_publish_logs.publish_log(message_body, routing_key)
            return db_client
    except Exception as exc:  # @ToDo: To broad exception
        data = {
            "message": "ERROR - Error updating client"
        }
        message_body = json.dumps(data)
        routing_key = "client.main_router_update_client.error"
        await rabbitmq_publish_logs.publish_log(message_body, routing_key)
        raise_and_log_error(logger, status.HTTP_409_CONFLICT, f"Error updating client: {exc}")


# @router.get(
#     "/client",
#     response_model=List[schemas.Client],
#     summary="Retrieve client list",
#     tags=["Client", "List"]  # Optional so it appears grouped in documentation
# )
# async def get_client_list(
#         db: AsyncSession = Depends(get_db)
# ):
#     """Retrieve client list"""
#     logger.debug("GET '/client' endpoint called.")
#     client_list = await crud.get_client_list(db)
#     data = {
#         "message": "INFO - Client list obtained"
#     }
#     message_body = json.dumps(data)
#     routing_key = "client.main_router_get_client_list.info"
#     await rabbitmq_publish_logs.publish_log(message_body, routing_key)
#     return client_list


@router.get(
    "/client",
    summary="Retrieve single client by id",
    responses={
        status.HTTP_200_OK: {
            "model": schemas.Client,
            "description": "Requested Client."
        },
        status.HTTP_404_NOT_FOUND: {
            "model": schemas.Message, "description": "Client not found"
        }
    },
    tags=['Client']
)
async def get_single_client(
        client_id: int = Query(None, description="Client ID"),
        db: AsyncSession = Depends(get_db),
        token: str = Header(..., description="JWT Token in the Header")
):
    """Retrieve single client by id"""
    logger.debug("GET '/client/%i' endpoint called.", client_id)

    if client_id is not None:
        payload = security.decode_token(token)
        # validar fecha expiración del token
        is_expirated = security.validar_fecha_expiracion(payload)
        if(is_expirated):
            data = {
                "message": "ERROR - The token is expired, log in again"
            }
            message_body = json.dumps(data)
            routing_key = "client.main_router_get_single_client.error"
            await rabbitmq_publish_logs.publish_log(message_body, routing_key)
            raise_and_log_error(logger, status.HTTP_409_CONFLICT, f"The token is expired, please log in again")
        else:
            es_admin = security.validar_es_admin(payload)
            if(es_admin==False):
                data = {
                    "message": "ERROR - You don't have permissions"
                }
                message_body = json.dumps(data)
                routing_key = "client.main_router_get_single_client.error"
                await rabbitmq_publish_logs.publish_log(message_body, routing_key)
                raise_and_log_error(logger, status.HTTP_409_CONFLICT, f"You don't have permissions")
        client = await crud.get_client(db, client_id)
        if not client:
            data = {
                "message": "ERROR - Client not found"
            }
            message_body = json.dumps(data)
            routing_key = "client.main_router_get_single_client.error"
            await rabbitmq_publish_logs.publish_log(message_body, routing_key)
            raise_and_log_error(logger, status.HTTP_404_NOT_FOUND, f"Client {client_id} not found")
        data = {
            "message": "INFO - Client obtained"
        }
        message_body = json.dumps(data)
        routing_key = "client.main_router_get_single_client.info"
        await rabbitmq_publish_logs.publish_log(message_body, routing_key)
        return client
    else:
        client_list = await crud.get_client_list(db)
        data = {
            "message": "INFO - Client list obtained"
        }
        message_body = json.dumps(data)
        routing_key = "client.main_router_get_client_list.info"
        await rabbitmq_publish_logs.publish_log(message_body, routing_key)
        return client_list


@router.post(
    "/client/auth",
    summary="Obtener token",
    status_code=status.HTTP_200_OK,
    tags=["Client"]
)
async def get_token(
        request_data: schemas.TokenRequest,  # Debes crear un esquema TokenRequest para manejar los datos
        db: AsyncSession = Depends(get_db)
):
    """Obtener token JWT."""
    logger.debug("POST '/auth/token' endpoint called.")
    try:
        username = request_data.username
        password = request_data.password
        # Realiza la autenticación aquí (sustituye esto con tu lógica real)
        client = await crud.get_client_by_username_and_pass(db, username, password)
        if not client:
            authenticated = False
            data = {
                "message": "ERROR - Client not found"
            }
            message_body = json.dumps(data)
            routing_key = "client.main_router_get_token.error"
            await rabbitmq_publish_logs.publish_log(message_body, routing_key)
            raise_and_log_error(logger, status.HTTP_404_NOT_FOUND, f"Client {username} not found")
        else: 
            data = {
                "message": "INFO - Client authenticated"
            }
            message_body = json.dumps(data)
            routing_key = "client.main_router_get_token.info"
            await rabbitmq_publish_logs.publish_log(message_body, routing_key)
            authenticated = True
        if authenticated:
            # Aquí puedes generar un token JWT si la autenticación es exitosa
            with open('private_key.pem', 'rb') as private_key_file:
                private_key_pem = private_key_file.read()
            expiration_time = datetime.utcnow() + timedelta(hours=3)
            expiration_time_serializable = expiration_time.isoformat()
            payload = {'username': client.username, 'id_client':client.id_client, 'email':client.email, 'role': client.role, 'fecha_expiracion': expiration_time_serializable}
            token = jwt.encode(payload, private_key_pem, algorithm='RS256')
            data = {
                "message": "INFO - Token generated"
            }
            message_body = json.dumps(data)
            routing_key = "client.main_router_get_token.info"
            await rabbitmq_publish_logs.publish_log(message_body, routing_key)
            return {"token": token}
        else:
            data = {
                "message": "ERROR - Incorrect credentials generating the token"
            }
            message_body = json.dumps(data)
            routing_key = "client.main_router_get_token.error"
            await rabbitmq_publish_logs.publish_log(message_body, routing_key)
            return {"message": "Credenciales incorrectas"}, 401    
    except Exception as exc:
        data = {
            "message": "ERROR - Error generating the token"
        }
        message_body = json.dumps(data)
        routing_key = "client.main_router_get_token.error"
        await rabbitmq_publish_logs.publish_log(message_body, routing_key)
        raise_and_log_error(logger, status.HTTP_409_CONFLICT, f"Error generando token: {exc}")


@router.get(
    "/client/key",
    summary="Retrieve key",
    responses={
        status.HTTP_200_OK: {
            "model": schemas.Message,
            "description": "Requested Key."
        },
        status.HTTP_404_NOT_FOUND: {
            "model": schemas.Message, "description": "Key not found"
        }
    },
    tags=['Client']
)
async def get_public_key():
    """Retrieve public key"""
    logger.debug("GET '/client/key' endpoint called.")
    return security.get_public_key()


# Función para autenticar al usuario (solo como ejemplo)
def authenticate(username, password):
    # Aquí puedes agregar lógica de autenticación, como verificar en una base de datos
    # Si el usuario y la contraseña son válidos, devuelve True; de lo contrario, False.
    if username == 'usuario' and password == 'password':
        return True
    else:
        return False
