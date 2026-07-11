import io

from fastai.vision.all import load_learner, PILImage
from app.dto.request.bird_classification import BirdClassificationRequest
from app.dto.response.bird_classification_response import BirdClassificationResponse

CONFIDENCE_THRESHOLD = 0.70
MODEL_PATH = "app/ml/bird_species_classifier_v1.pkl"

class BirdClassificationService:
    def __init__(self):
        self.learn = load_learner(MODEL_PATH)
        print(self.learn.dls.vocab)

    def classificate_bird(self, request: BirdClassificationRequest) -> BirdClassificationResponse:
        image = PILImage.create(io.BytesIO(request.image_bytes))
        pred_label, pred_idx, probs = self.learn.predict(image)
        confidence = float(probs[pred_idx])

        if confidence < CONFIDENCE_THRESHOLD:
            return BirdClassificationResponse(
                image_id=request.image_id,
                scientific_name="",
                specie_confidence=confidence,
                failureReason="LOW_CONFIDENCE",
            )

        return BirdClassificationResponse(
            image_id=request.image_id,
            scientific_name=str(pred_label).replace('_', ' '),
            specie_confidence=confidence,
            failureReason="",
        )