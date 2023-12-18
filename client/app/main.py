# -*- coding: utf-8 -*-
"""Main file to start FastAPI application."""
import logging
import os
import json
from fastapi import FastAPI
from routers import main_router, rabbitmq, security, rabbitmq_publish_logs
from sql import models, database
from consulService.BLConsul import register_consul_service

# Configure logging ################################################################################
logger = logging.getLogger(__name__)

# OpenAPI Documentation ############################################################################
APP_VERSION = os.getenv("APP_VERSION", "2.0.0")
logger.info("Running app version %s", APP_VERSION)
DESCRIPTION = """
Client microservice application.
"""

tag_metadata = [
    {
        "name": "Client",
        "description": "Endpoints to **CREATE** and **READ** clients.",
    },
]

app = FastAPI(
    redoc_url=None,  # disable redoc documentation.
    title="FastAPI - Client microservice app",
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
    """Configuration to be executed when FastAPI server starts."""
    try:
        logger.info("Creating database tables")
        async with database.engine.begin() as conn:
            await conn.run_sync(models.Base.metadata.create_all)
        ## GENERAR CLAVES
        security.generar_claves()
        await rabbitmq.subscribe_channel()
        await rabbitmq_publish_logs.subscribe_channel()
        register_consul_service()
        data = {
            "message": "public key creado!!"
        }
        message_body = json.dumps(data)
        routing_key = "client.key_created"
        await rabbitmq.publish_event(message_body, routing_key)
        data2 = {
            "message": "INFO - Servicio Delivery inicializado correctamente"
        }
        message_body2 = json.dumps(data2)
        routing_key2 = "delivery.main_startup_event.info"
        await rabbitmq_publish_logs.publish_log(message_body2, routing_key2)
    except:
        data = {
            "message": "ERROR - Error al inicializar el servicio Client"
        }
        message_body = json.dumps(data)
        routing_key = "client.main_startup_event.error"
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
