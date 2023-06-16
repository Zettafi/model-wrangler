"""Models"""
from enum import Enum
from typing import Annotated

from pydantic import BaseModel, Field


class TextTransformRequest(BaseModel):
    input: Annotated[str, Field(min_length=1, description="Input text")]

    class Config:
        """TextTransformRequest Config"""

        schema_extra = {
            "example": {
                "input": "I am so sorry for being",
            }
        }


class TextTransformResponse(BaseModel):
    generated_text: Annotated[
        str,
        Field(description="The results from the text transform"),
    ]

    class Config:
        """TextTransformResponse Config"""

        schema_extra = {
            "example": {
                "generated_text": "I am so sorry for being so rude to you.",
            }
        }


class ImageFormat(str, Enum):
    """Image format"""

    png = "PNG"
    jpg = "JPEG"
    gif = "GIF"


class ImageGenerateRequest(BaseModel):
    """Request schema for generating images from text"""

    input: Annotated[str, Field(description="Description of the image to generate")]
    format: Annotated[
        ImageFormat, Field(description="Format of the image to return")
    ] = ImageFormat.png

    class Config:
        """ImageGenerateRequest Config"""

        schema_extra = {
            "example": {
                "input": "A cowboy riding a horse through the desert southwest",
                "format": "PNG",
            }
        }


class ImageGenerateResponse(BaseModel):
    """Response schema for generated images"""

    image: Annotated[str, Field(description="Base64 encoded image data")]
    format: Annotated[ImageFormat, Field(description="Format of the image")]

    class Config:
        """ImageGenerateResponse Config"""

        schema_extra = {
            "example": {
                "image": "QSBjb3dib3kgcmlkaW5nIGEgaG9yc2UgdGhyb3VnaCB0aGUgZGVzZXJ0IHNvdXRod2VzdAo",
                "format": "PNG",
            }
        }
