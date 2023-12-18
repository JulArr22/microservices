import aio_pika
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
    
    global exchange_logs_name
    exchange_logs_name = 'logs'
    global exchange_logs
    exchange_logs = await channel.declare_exchange(name=exchange_logs_name, type='topic', durable=True)


async def on_event_log_message(message):
    async with message.process():
        log = models.Log(
            #exchange=message.exchange,
            exchange=exchange_events_name,
            routing_key=message.routing_key,
            data=message.body
        )
        db = SessionLocal()
        await crud.create_log(db, log)
        await db.close()


async def subscribe_events_logs():
    # Create a queue
    queue_name = "events_logs"
    queue = await channel.declare_queue(name=queue_name, exclusive=True)
    # Bind the queue to the exchange
    routing_key = "#"
    await queue.bind(exchange=exchange_events, routing_key=routing_key)
    # Set up a message consumer
    async with queue.iterator() as queue_iter:
        async for message in queue_iter:
            await on_event_log_message(message)


async def on_command_log_message(message):
    async with message.process():
        log = models.Log(
            #exchange=message.exchange,
            exchange=exchange_commands_name,
            routing_key=message.routing_key,
            data=message.body
        )
        db = SessionLocal()
        await crud.create_log(db, log)
        await db.close()


async def subscribe_commands_logs():
    # Create a queue
    queue_name = "commands_logs"
    queue = await channel.declare_queue(name=queue_name, exclusive=True)
    # Bind the queue to the exchange
    routing_key = "#"
    await queue.bind(exchange=exchange_commands, routing_key=routing_key)
    # Set up a message consumer
    async with queue.iterator() as queue_iter:
        async for message in queue_iter:
            await on_command_log_message(message)


async def on_response_log_message(message):
    async with message.process():
        log = models.Log(
            #exchange=message.exchange,
            exchange=exchange_responses_name,
            routing_key=message.routing_key,
            data=message.body
        )
        db = SessionLocal()
        await crud.create_log(db, log)
        await db.close()


async def subscribe_responses_logs():
    # Create a queue
    queue_name = "responses_logs"
    queue = await channel.declare_queue(name=queue_name, exclusive=True)
    # Bind the queue to the exchange
    routing_key = "#"
    await queue.bind(exchange=exchange_responses, routing_key=routing_key)
    # Set up a message consumer
    async with queue.iterator() as queue_iter:
        async for message in queue_iter:
            await on_response_log_message(message)


async def on_log_log_message(message):
    async with message.process():
        log = models.Log(
            #exchange=message.exchange,
            exchange=exchange_logs_name,
            routing_key=message.routing_key,
            data=message.body
        )
        db = SessionLocal()
        await crud.create_log(db, log)
        await db.close()


async def subscribe_logs_logs():
    # Create a queue
    queue_name = "logs_logs"
    queue = await channel.declare_queue(name=queue_name, exclusive=True)
    # Bind the queue to the exchange
    routing_key = "#"
    await queue.bind(exchange=exchange_logs, routing_key=routing_key)
    # Set up a message consumer
    async with queue.iterator() as queue_iter:
        async for message in queue_iter:
            await on_log_log_message(message)

async def subscribe_key_created():
    # Create a queue
    queue_name = "client.key_created_logs"
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
