import asyncio
import aio_pika
import json
from routers.crud import set_status_of_machine
from routers import security

async def subscribe_channel():
    # Define your RabbitMQ server connection parameters directly as keyword arguments
    connection = await aio_pika.connect_robust(
        host='rabbitmq',
        port=5672,
        virtualhost='/',
        login='user',
        password='user'
    )
    # Create a channel
    global channel
    channel = await connection.channel()
    # Declare the exchange
    global exchange_name
    exchange_name = 'events'
    global exchange
    exchange = await channel.declare_exchange(name=exchange_name, type='topic', durable=True)


async def on_message(message):
    async with message.process():
        piece = json.loads(message.body)
        await set_status_of_machine("Machine Status: Producing")
        await asyncio.sleep(2)
        await set_status_of_machine("Machine Status: Idle")
        data = {
            "id_piece": piece['id_piece'],
            "id_order": piece['id_order']
        }
        message_body = json.dumps(data)
        routing_key = "piece.produced"
        await publish(message_body, routing_key)

async def subscribe():
    # Create queue
    queue_name = "piece.needed"
    queue = await channel.declare_queue(name=queue_name, exclusive=True)
    # Bind the queue to the exchange
    routing_key = "piece.needed"
    await queue.bind(exchange=exchange_name, routing_key=routing_key)
    # Set up a message consumer
    async with queue.iterator() as queue_iter:
        async for message in queue_iter:
            await on_message(message)

async def publish(message_body, routing_key):
    # Publish the message to the exchange
    await exchange.publish(
        aio_pika.Message(
            body=message_body.encode(),
            content_type="text/plain"
        ),
        routing_key=routing_key)

async def subscribe_key_created():
    # Create a queue
    queue_name = "client.key_created_machine"
    queue = await channel.declare_queue(name=queue_name, exclusive=True)
    # Bind the queue to the exchange
    routing_key = "client.key_created"
    await queue.bind(exchange=exchange_name, routing_key=routing_key)
    # Set up a message consumer
    async with queue.iterator() as queue_iter:
        async for message in queue_iter:
            await on_delivered_message_key_created(message)

async def on_delivered_message_key_created(message):
    async with message.process():
        await security.get_public_key()
