import os
from dotenv import load_dotenv

load_dotenv()

class Config():
    #RabbitMQ
    RABBITMQ_URL = os.getenv("RABBITMQ_URL", "amqp://user:password@localhost:5672/")
    QUEUE_CLASSIFICATION_NAME = os.getenv("QUEUE_CLASSIFICATION_NAME", "bird_classification.queue")
    CLASSIFICATION_RESULT_QUEUE_NAME = os.getenv("CLASSIFICATION_RESULT_QUEUE_NAME", "bird_classification.result.queue")
    EXCHANGE_NAME = os.getenv("EXCHANGE_NAME","bird_detection.exchange")
    RESULT_ROUTING_KEY = os.getenv("RESULT_ROUTING_KEY","bird_classification.result")
    CLASSIFICATION_ROUTING_KEY=os.getenv("CLASSIFICATION_ROUTING_KEY","bird_classification.pending")

    
    # AWS S3
    S3_BUCKET = os.getenv("S3_BUCKET")
    AWS_ACCESS_KEY_ID = os.getenv("AWS_ACCESS_KEY_ID")
    AWS_SECRET_ACCESS_KEY = os.getenv("AWS_SECRET_ACCESS_KEY")
    AWS_REGION = os.getenv("AWS_REGION", "us-east-1")
    
    # Validar que las variables críticas existen
    @classmethod
    def validate(cls):
        required_vars = ["AWS_ACCESS_KEY_ID", "AWS_SECRET_ACCESS_KEY", "S3_BUCKET"]
        missing = [var for var in required_vars if not getattr(cls, var)]
        if missing:
            raise ValueError(f"Missing required environment variables: {', '.join(missing)}")