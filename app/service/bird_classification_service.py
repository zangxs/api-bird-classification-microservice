from fastai.vision.all import load_learner, PILImage
from app.dto.request.bird_classification import BirdClassificationRequest
from app.dto.response.bird_classification_response import BirdClassificationResponse

CONFIDENCE_THRESHOLD = 0.80
MODEL_PATH = "app/ml/bird_detector_model.pkl"

class BirdClassificationService:
    def __init__(self):
        self.learn = load_learner(MODEL_PATH)
        print(self.learn.dls.vocab)

    def classificate_bird(self, request: BirdClassificationRequest) -> BirdClassificationResponse:

        response = BirdClassificationResponse(
            image_id = request.image_id,
            specie_id = "",
            specie_confidence = 0
        )

        return response