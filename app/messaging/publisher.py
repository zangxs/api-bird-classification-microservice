import json
import aio_pika
from app.config.config import Config


class Publisher:
    def __init__(self, exchange: aio_pika.Exchange):
        self.exchange = exchange

    async def publish(self, image_event_id: str, scientific_name: str, specie_confidence: float, failure_reason: str):

        payload = {
            "imageEventId": image_event_id,
            "scientificName": scientific_name,
            "specieConfidence": specie_confidence,
            "failureReason": failure_reason
        }

        print("publishing result: ", payload)

        await self.exchange.publish(
            aio_pika.Message(body=json.dumps(payload).encode()),
            routing_key=Config.RESULT_ROUTING_KEY
        )