import json
import aio_pika
import boto3
from app.services.bird_detector_service import BirdDetectorService
from app.dto.request.bird_request import BirdRequest
from app.messaging.publisher import Publisher
from app.config.config import Config

s3_client = boto3.client(
    "s3",
    aws_access_key_id=Config.AWS_ACCESS_KEY_ID,
    aws_secret_access_key=Config.AWS_SECRET_ACCESS_KEY,
    region_name=Config.AWS_REGION
)
detector_service = BirdDetectorService()


async def start_consumer(connection: aio_pika.RobustConnection):
    channel = await connection.channel()

    queue = await channel.declare_queue(Config.QUEUE_DETECT_NAME, durable=True)

    detector_service = BirdDetectorService()

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

            request = BirdRequest(
                image_id=payload["imageEventId"],
                s3_key=payload["s3Key"],
                user_id=payload["userId"],
                image_bytes=download_from_s3(payload["s3Key"])
            )

            response = detector_service.detect_bird(request)

            await publisher.publish(
                image_event_id=response.image_id,
                is_bird=response.is_bird,
                confidence=response.confidence
            )

    await queue.consume(handle_message)



def download_from_s3(s3_key: str) -> bytes:
    obj = s3_client.get_object(Bucket=Config.S3_BUCKET, Key=s3_key)
    return obj["Body"].read()

