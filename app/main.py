import asyncio

import aio_pika
from app.config.config import Config
from app.messaging.consumer import start_consumer


async def main():
    Config.validate()
    connection = await aio_pika.connect_robust(Config.RABBITMQ_URL)
    try:
        await start_consumer(connection)
        print("Bird classification consumer started, waiting for messages...")
        await asyncio.Event().wait()
    finally:
        await connection.close()


if __name__ == "__main__":
    asyncio.run(main())
