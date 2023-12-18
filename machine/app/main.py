# -*- coding: utf-8 -*-
"""Main file to start FastAPI application."""
import logging
import json
import os
from fastapi import FastAPI
from routers import main_router, rabbitmq, security, rabbitmq_publish_logs
import asyncio
from consulService.BLConsul import register_consul_service

# Configure logging ################################################################################
logger = logging.getLogger(__name__)

# OpenAPI Documentation ############################################################################
APP_VERSION = os.getenv("APP_VERSION", "2.0.0")
logger.info("Running app version %s", APP_VERSION)
DESCRIPTION = """
Machine microservice application.
"""

tag_metadata = [
    {
        "name": "Machine",
        "description": "Endpoints to **CREATE** and **READ** machine.",
    },
]

app = FastAPI(
    redoc_url=None,  # disable redoc documentation.
    title="FastAPI - Machine microservice app",
    description=DESCRIPTION,
    version=APP_VERSION,
    servers=[
        {"url": "/", "description": "Development"}
    ],
    license_info={
        "name": "MIT License",
        "url": "https://choosealicense.com/licenses/mit/"
    },
    openapi_tags=tag_metadata,
)

app.include_router(main_router.router)


@app.on_event("startup")
async def startup_event():
    try:
        """Configuration to be executed when FastAPI server starts."""
        logger.info("Creating database tables")
        await rabbitmq.subscribe_channel()
        await rabbitmq_publish_logs.subscribe_channel()
        asyncio.create_task(rabbitmq.subscribe_key_created())
        await security.get_public_key()
        register_consul_service()
        asyncio.create_task(rabbitmq.subscribe())
        data = {
            "message": "INFO - Servicio Machine inicializado correctamente"
        }
        message_body = json.dumps(data)
        routing_key = "machine.main_startup_event.info"
        await rabbitmq_publish_logs.publish_log(message_body, routing_key)
    except:
        data = {
            "message": "ERROR - Error al inicializar el servicio Machine"
        }
        message_body = json.dumps(data)
        routing_key = "machine.main_startup_event.error"
        await rabbitmq_publish_logs.publish_log(message_body, routing_key)


# Main #############################################################################################
# If application is run as script, execute uvicorn on port 8000
if __name__ == "__main__":
    import uvicorn

    logger.debug("App run as script")
    uvicorn.run(
        app,
        host="0.0.0.0",
        port=8000,
        log_config='logging.yml'
    )
    logger.debug("App finished as script")
