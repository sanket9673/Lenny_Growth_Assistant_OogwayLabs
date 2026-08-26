from typing import List
from pydantic import BaseModel, Field

class SectionPayload(BaseModel):
    header: str = Field(..., description="Header of the section")
    content: str = Field(..., description="Content of the section")

class EssayOutputSchema(BaseModel):
    title: str = Field(..., description="Title of the essay")
    hook: str = Field(..., description="Hook of the essay")
    sections: List[SectionPayload] = Field(..., description="Sections in the essay")
    conclusion: str = Field(..., description="Conclusion of the essay")

class Ship30EssayPipeline:
    """Validator class for Ship30 essay structure rules."""

    def validate_1_3_1_structure(self, text: str) -> bool:
        """
        Validates whether the text adheres to the 1-3-1 cadence structure.
        Ensures paragraphs or lines are separated by double newlines.
        """
        if not text:
            return False
        # Remove empty parts
        parts = [p.strip() for p in text.split("\n\n") if p.strip()]
        return len(parts) >= 3
