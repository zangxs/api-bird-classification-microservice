# api-bird-classification-microservice

Microservicio Python (sin API HTTP, solo consumer) encargado de clasificar la especie de un ave a
partir de una imagen ya confirmada como "ave" por `api-bird-detection-microservice`. Forma parte
del workspace `bird-dex`.

## Qué hace

1. Consume mensajes de la cola `bird_classification.queue` (exchange `bird_detection.exchange`).
2. Descarga la imagen desde S3 usando el `s3Key` del mensaje.
3. Corre un modelo fastai (`app/ml/bird_species_classifier_v1.pkl`) para predecir la especie.
4. Publica el resultado (`scientificName`, `specieConfidence`, `failureReason`) con la routing key
   `bird_classification.result` en el mismo exchange.

Si la confianza de la predicción es menor a `CONFIDENCE_THRESHOLD` (0.70, en
`app/service/bird_classification_service.py`), se publica el resultado con `failureReason =
"LOW_CONFIDENCE"` y `scientificName` vacío.

## Requisitos

- Python 3.12
- Una instancia de RabbitMQ accesible (misma que usan el orquestador y el servicio de detección)
- Credenciales de AWS S3 con acceso al bucket donde se suben las imágenes

## Instalación

```bash
python -m venv env
source env/bin/activate
pip install -r requirements.txt
```

## Configuración

Variables de entorno (ver `app/config/config.py`), definidas en un archivo `.env` en la raíz del
repo (**nunca commitear este archivo, contiene credenciales reales**):

| Variable | Descripción | Default |
|---|---|---|
| `RABBITMQ_URL` | URL de conexión a RabbitMQ | `amqp://user:password@localhost:5672/` |
| `QUEUE_CLASSIFICATION_NAME` | Cola de entrada | `bird_classification.queue` |
| `EXCHANGE_NAME` | Exchange compartido con el resto de servicios | `bird_detection.exchange` |
| `RESULT_ROUTING_KEY` | Routing key para publicar el resultado | `bird_classification.result` |
| `S3_BUCKET` | Bucket donde están las imágenes (requerido) | — |
| `AWS_ACCESS_KEY_ID` | Access key de AWS (requerido) | — |
| `AWS_SECRET_ACCESS_KEY` | Secret key de AWS (requerido) | — |
| `AWS_REGION` | Región de S3 | `us-east-1` |

## Cómo correrlo

```bash
source env/bin/activate
python -m app.main
```

Esto valida la configuración, se conecta a RabbitMQ, arranca el consumer sobre
`bird_classification.queue` y queda escuchando mensajes indefinidamente (no imprime nada más si no
llegan mensajes; eso es esperado). Deténlo con `Ctrl+C`.

No hay servidor HTTP ni Dockerfile en este repo — es un proceso consumer puro.

## Notas

- No hay tests ni configuración de linter en este repo.
- El primer mensaje que llegue tardará algunos segundos extra porque el modelo fastai se carga una
  sola vez al iniciar el proceso (`BirdClassificationService.__init__`).
