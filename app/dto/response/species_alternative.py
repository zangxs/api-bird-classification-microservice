from pydantic import BaseModel, ConfigDict, Field

class SpeciesAlternative(BaseModel):
    scientific_name: str  = Field(alias="scientificName")
    confidence: float = Field(alias="specieConfidence")