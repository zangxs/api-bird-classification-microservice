from pydantic import BaseModel, ConfigDict, Field

class BirdClassificationResponse(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    image_id: str = Field(alias="imageId")
    scientific_name: str = Field(alias="scientificName")
    specie_confidence: float = Field(alias="specieConfidence")
    failure_reason: str = Field(alias="failureReason")