import aio_pika
import json
from sql.database import SessionLocal # pylint: disable=import-outside-toplevel
from sql import crud
from os import environ

async def subscribe_channel():
    # Define your RabbitMQ server connection parameters directly as keyword arguments
    connection = await aio_pika.connect_robust(
        host=environ.get("RABBITMQ_IP"),
        port=5672,
        virtualhost='/',
        login='user',
        password='user'
    )
    # Create a channel
    global channel
    channel = await connection.channel()
    # Declare the exchange
    global exchange_events_name
    exchange_events_name = 'events'
    global exchange_events
    exchange_events = await channel.declare_exchange(name=exchange_events_name, type='topic', durable=True)


async def publish_event(message_body, routing_key):
    # Publish the message to the exchange
    await exchange_events.publish(
        aio_pika.Message(
            body=message_body.encode(),
            content_type="text/plain"
        ),
        routing_key=routing_key)
