from contextlib import asynccontextmanager
from app.messaging.consumer import start_consumer
import aio_pika
from app.config.config import Config
from app.messaging.publisher import Publisher


@asynccontextmanager
async def lifespan():
    connection = await aio_pika.connect_robust(Config.RABBITMQ_URL)
    channel = await connection.channel()

    result_publisher = Publisher(channel)
    await start_consumer(connection)

    yield
    await connection.close()