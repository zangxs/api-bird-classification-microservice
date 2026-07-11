from pydantic import BaseModel, ConfigDict, Field

class BirdClassificationRequest(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    image_id: str = Field(alias="imageId")
    s3_key: str = Field(alias="s3Key")
    image_bytes: bytes