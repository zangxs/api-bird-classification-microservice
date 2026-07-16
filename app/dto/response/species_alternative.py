from pydantic import BaseModel, ConfigDict, Field

class SpeciesAlternative(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    scientific_name: str  = Field(alias="scientificName")
    confidence: float = Field(alias="specieConfidence")