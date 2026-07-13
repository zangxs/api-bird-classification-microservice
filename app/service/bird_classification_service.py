import io
import torch

from fastai.vision.all import load_learner, PILImage
from app.dto.request.bird_classification import BirdClassificationRequest
from app.dto.response.bird_classification_response import BirdClassificationResponse

CONFIDENCE_THRESHOLD = 0.70
TOP_K = 3
AMBIGUITY_MARGIN = 0.15
MODEL_PATH = "app/ml/bird_species_classifier_latest.pkl"


class BirdClassificationService:
    def __init__(self):
        self.learn = load_learner(MODEL_PATH)
        self.vocab = self.learn.dls.vocab
        print(self.vocab)

    def classificate_bird(self, request: BirdClassificationRequest) -> BirdClassificationResponse:
        image = PILImage.create(io.BytesIO(request.image_bytes))
        pred_label, pred_idx, probs = self.learn.predict(image)
        confidence = float(probs[pred_idx])

        alternatives = self._get_relevant_alternatives(probs, confidence, exclude_idx=pred_idx)

        if confidence < CONFIDENCE_THRESHOLD:
            return BirdClassificationResponse(
                image_id=request.image_id,
                scientific_name="",
                specie_confidence=confidence,
                failureReason="LOW_CONFIDENCE",
                alternatives=alternatives,
            )

        return BirdClassificationResponse(
            image_id=request.image_id,
            scientific_name=str(pred_label).replace('_', ' '),
            specie_confidence=confidence,
            failureReason="",
            alternatives=alternatives,
        )

    def _get_relevant_alternatives(self, probs, top1_confidence: float, exclude_idx: int) -> list[dict]:
        top_k_probs, top_k_idxs = torch.topk(probs, k=min(TOP_K, len(self.vocab)))

        relevant = []
        for prob, idx in zip(top_k_probs, top_k_idxs):
            idx_int = int(idx)
            prob_float = float(prob)

            if idx_int == exclude_idx:
                continue
            if prob_float < (top1_confidence - AMBIGUITY_MARGIN):
                continue

            relevant.append({
                "scientific_name": str(self.vocab[idx_int]).replace('_', ' '),
                "confidence": prob_float,
            })

        return relevant