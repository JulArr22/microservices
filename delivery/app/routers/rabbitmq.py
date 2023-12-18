import asyncio
import aio_pika
import json
from sql.database import SessionLocal # pylint: disable=import-outside-toplevel
from sql import crud, models
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


async def on_client_created_message(message):
    async with message.process():
        client = json.loads(message.body)
        db = SessionLocal()
        info_client = models.Client(
            id_client=client['id_client'],
            address=client['address'],
            postal_code=client['postal_code']
        )
        db_client = await crud.store_client(db, info_client)
        await db.close()


async def subscribe_client_created():
    # Create a queue
    queue_name = "client.created"
    queue = await channel.declare_queue(name=queue_name, exclusive=True)
    # Bind the queue to the exchange
    routing_key = "client.created"
    await queue.bind(exchange=exchange_events_name, routing_key=routing_key)
    # Set up a message consumer
    async with queue.iterator() as queue_iter:
        async for message in queue_iter:
            await on_client_created_message(message)


async def on_client_updated_message(message):
    async with message.process():
        client = json.loads(message.body)
        db = SessionLocal()
        info_client = models.Client(
            id_client=client['id_client'],
            address=client['address'],
            postal_code=client['postal_code']
        )
        db_client = await crud.update_client(db, info_client)
        await db.close()


async def subscribe_client_updated():
    # Create a queue
    queue_name = "client.updated"
    queue = await channel.declare_queue(name=queue_name, exclusive=True)
    # Bind the queue to the exchange
    routing_key = "client.updated"
    await queue.bind(exchange=exchange_events_name, routing_key=routing_key)
    # Set up a message consumer
    async with queue.iterator() as queue_iter:
        async for message in queue_iter:
            await on_client_updated_message(message)



async def on_produced_message(message):
    async with message.process():
        order = json.loads(message.body)
        db = SessionLocal()
        db_delivery = await crud.get_delivery_by_order(db, order['id_order'])
        db_delivery = await crud.change_delivery_status(db, db_delivery.id_delivery, models.Delivery.STATUS_DELIVERING)
        await db.close()
        asyncio.create_task(send_product(db_delivery))


async def subscribe_produced():
    # Create queue
    queue_name = "order.produced"
    queue = await channel.declare_queue(name=queue_name, exclusive=True)
    # Bind the queue to the exchange
    routing_key = "order.produced"
    await queue.bind(exchange=exchange_events_name, routing_key=routing_key)
    # Set up a message consumer
    async with queue.iterator() as queue_iter:
        async for message in queue_iter:
            await on_produced_message(message)


async def send_product(delivery):
    data = {
        "id_order": delivery.id_order
    }
    message_body = json.dumps(data)
    routing_key = "order.delivering"
    await publish_event(message_body, routing_key)
    await asyncio.sleep(10)
    db = SessionLocal()
    db_delivery = await crud.get_delivery(db, delivery.id_delivery)
    db_delivery = await crud.change_delivery_status(db, db_delivery.id_delivery, models.Delivery.STATUS_DELIVERED)
    await db.close()
    routing_key = "order.delivered"
    await publish_event(message_body, routing_key)


async def on_message_delivery_check(message):
    async with message.process():
        order = json.loads(message.body)
        db = SessionLocal()
        db_client = await crud.get_client(db, order['id_client'])
        address_check = await crud.check_address(db, db_client)
        data = {
            "id_order": order['id_order'],
            "status": address_check
        }
        if address_check:
            status_delivery_address_check = models.Delivery.STATUS_CREATED
        else:
            status_delivery_address_check = models.Delivery.STATUS_CANCELED
        db_delivery = models.Delivery(
            id_order=order['id_order'],
            status_delivery=status_delivery_address_check,
            address=db_client.address,
            postal_code=db_client.postal_code
        )
        await crud.create_delivery(db, db_delivery)
        await db.close()
        message_body = json.dumps(data)
        routing_key = "delivery.checked"
        await publish_response(message_body, routing_key)


async def subscribe_delivery_check():
    # Create queue
    queue_name = "delivery.check"
    queue = await channel.declare_queue(name=queue_name, exclusive=True)
    # Bind the queue to the exchange
    routing_key = "delivery.check"
    await queue.bind(exchange=exchange_commands_name, routing_key=routing_key)
    # Set up a message consumer
    async with queue.iterator() as queue_iter:
        async for message in queue_iter:
            await on_message_delivery_check(message)


async def on_message_delivery_cancel(message):
    async with message.process():
        order = json.loads(message.body)
        db = SessionLocal()
        delivery = await crud.get_delivery_by_order(db, order['id_order'])
        delivery = await crud.change_delivery_status(db, delivery.id_delivery, models.Delivery.STATUS_CANCELED)
        await db.close()
        data = {
            "id_order": order['id_order']
        }
        message_body = json.dumps(data)
        routing_key = "delivery.canceled"
        await publish_response(message_body, routing_key)


async def subscribe_delivery_cancel():
    # Create queue
    queue_name = "delivery.cancel"
    queue = await channel.declare_queue(name=queue_name, exclusive=True)
    # Bind the queue to the exchange
    routing_key = "delivery.cancel"
    await queue.bind(exchange=exchange_commands_name, routing_key=routing_key)
    # Set up a message consumer
    async with queue.iterator() as queue_iter:
        async for message in queue_iter:
            await on_message_delivery_cancel(message)


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
    queue_name = "client.key_created_delivery"
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
        delivery = json.loads(message.body)
        # db = SessionLocal()
        # db_order = await crud.change_order_status(db, delivery['id_order'], models.Order.STATUS_DELIVERED)
        # await db.close()
        await security.get_public_key()
