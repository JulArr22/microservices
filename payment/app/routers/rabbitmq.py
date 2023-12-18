import aio_pika
import json
from sql.database import SessionLocal # pylint: disable=import-outside-toplevel
from sql import crud
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
    global exchange_events_name
    exchange_events_name = 'events'
    global exchange_events
    exchange_events = await channel.declare_exchange(name=exchange_events_name, type='topic', durable=True)
    
    global exchange_commands_name
    exchange_commands_name = 'commands'
    global exchange_commands
    exchange_commands = await channel.declare_exchange(name=exchange_commands_name, type='topic', durable=True)
    
    global exchange_responses_name
    exchange_responses_name = 'responses'
    global exchange_responses
    exchange_responses = await channel.declare_exchange(name=exchange_responses_name, type='topic', durable=True)


async def on_message_payment_check(message):
    async with message.process():
        payment = json.loads(message.body)
        db = SessionLocal()
        try:
            db_payment = await crud.create_payment(db, payment)
            # Crear evento con payment de ID order correcto
            payment_status = True
        except Exception as exc:  # @ToDo: To broad exception
            # Crear evento con payment de ID order incorrecto
            payment_status = False
        await db.close()
        data = {
            "id_order": payment['id_order'],
            "status": payment_status
        }
        message_body = json.dumps(data)
        routing_key = "payment.checked"
        await publish_response(message_body, routing_key)


async def subscribe_payment_check():
    # Create queue
    queue_name = "payment.check"
    queue = await channel.declare_queue(name=queue_name, exclusive=True)
    # Bind the queue to the exchange
    routing_key = "payment.check"
    await queue.bind(exchange=exchange_commands_name, routing_key=routing_key)
    # Set up a message consumer
    async with queue.iterator() as queue_iter:
        async for message in queue_iter:
            await on_message_payment_check(message)


async def publish_event(message_body, routing_key):
    # Publish the message to the exchange
    await exchange_events.publish(
        aio_pika.Message(
            body=message_body.encode(),
            content_type="text/plain"
        ),
        routing_key=routing_key)


async def publish_response(message_body, routing_key):
    # Publish the message to the exchange
    await exchange_responses.publish(
        aio_pika.Message(
            body=message_body.encode(),
            content_type="text/plain"
        ),
        routing_key=routing_key)

async def subscribe_key_created():
    # Create a queue
    queue_name = "client.key_created_payment"
    queue = await channel.declare_queue(name=queue_name, exclusive=True)
    # Bind the queue to the exchange
    routing_key = "client.key_created"
    await queue.bind(exchange=exchange_events_name, routing_key=routing_key)
    # Set up a message consumer
    async with queue.iterator() as queue_iter:
        async for message in queue_iter:
            await on_delivered_message_key_created(message)

async def on_delivered_message_key_created(message):
    async with message.process():
        await security.get_public_key()

async def publish_key(message_body, routing_key):
    # Publish the message to the exchange
    await exchange_events.publish(
        aio_pika.Message(
            body=message_body.encode(),
            content_type="text/plain"
        ),
        routing_key=routing_key)