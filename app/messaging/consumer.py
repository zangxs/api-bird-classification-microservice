import json
import aio_pika
import boto3
from app.messaging.publisher import Publisher
from app.config.config import Config
from app.service.bird_classification_service import BirdClassificationService
from app.dto.request.bird_classification import BirdClassificationRequest

s3_client = boto3.client(
    "s3",
    aws_access_key_id=Config.AWS_ACCESS_KEY_ID,
    aws_secret_access_key=Config.AWS_SECRET_ACCESS_KEY,
    region_name=Config.AWS_REGION
)


async def start_consumer(connection: aio_pika.RobustConnection):
    channel = await connection.channel()

    queue = await channel.declare_queue(Config.QUEUE_CLASSIFICATION_NAME, durable=True)

    classification_service = BirdClassificationService()

    exchange = await channel.declare_exchange(
        Config.EXCHANGE_NAME,
        aio_pika.ExchangeType.DIRECT,
        durable=True
    )

    publisher = Publisher(exchange)

    async def handle_message(message: aio_pika.IncomingMessage):
        async with message.process():
            print("message received")
            payload = json.loads(message.body)

            request = BirdClassificationRequest(
                image_id=payload["imageEventId"],
                s3_key=payload["s3Key"],
                image_bytes=download_from_s3(payload["s3Key"])
            )

            response = classification_service.classificate_bird(request)

            await publisher.publish(
                image_event_id=response.image_id,
                scientific_name=response.scientific_name,
                specie_confidence=response.specie_confidence,
                failure_reason=response.failure_reason,
                alternatives=response.alternatives
            )

    await queue.consume(handle_message)



def download_from_s3(s3_key: str) -> bytes:
    obj = s3_client.get_object(Bucket=Config.S3_BUCKET, Key=s3_key)
    return obj["Body"].read()

