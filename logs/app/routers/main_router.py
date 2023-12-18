# -*- coding: utf-8 -*-
"""FastAPI router definitions."""
import logging
from typing import List
from fastapi import APIRouter, Depends, status, Header, Query
from sqlalchemy.ext.asyncio import AsyncSession
from dependencies import get_db
from sql import crud, schemas, models
from routers import security
from routers.router_utils import raise_and_log_error

logger = logging.getLogger(__name__)
router = APIRouter()


@router.get(
    "/logs/health",
    summary="Health check endpoint",
    response_model=schemas.Message,
)
async def health_check():
    """Endpoint to check if everything started correctly."""
    logger.debug("GET '/logs/health' endpoint called.")
    if await security.isTherePublicKey():
        return {"detail": "Service Healthy."}
    else:
        raise_and_log_error(logger, status.HTTP_503_SERVICE_UNAVAILABLE, "Service Unavailable.")


@router.get(
    "/logs",
    summary="Retrieve certain number of logs",
    responses={
        status.HTTP_200_OK: {
            "model": schemas.LogBase,
            "description": "Requested logs."
        },
        status.HTTP_404_NOT_FOUND: {
            "model": schemas.Message, "description": "Logs not found"
        }
    },
    tags=['Logs']
)
async def get_logs(
        number_of_logs: int = Query(..., description="Number of logs to obtain"),
        db: AsyncSession = Depends(get_db),
        token: str = Header(..., description="JWT Token in the Header")
):
    """Retrieve logs"""
    logger.debug("GET '/logs/%i' endpoint called.", number_of_logs)
    payload = security.decode_token(token)
    # validar fecha expiración del token
    is_expirated = security.validar_fecha_expiracion(payload)
    if(is_expirated):
        raise_and_log_error(logger, status.HTTP_409_CONFLICT, f"The token is expired, please log in again")
    else:
        es_admin = security.validar_es_admin(payload)
        if(es_admin==False):
            raise_and_log_error(logger, status.HTTP_409_CONFLICT, f"You don't have permissions")
    logs = await crud.get_logs(db, number_of_logs)
    if not logs:
        raise_and_log_error(logger, status.HTTP_404_NOT_FOUND)
    return logs
