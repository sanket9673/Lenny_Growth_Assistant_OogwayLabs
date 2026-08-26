from typing import List, Optional
from pydantic import BaseModel, Field, ConfigDict


class SectionOutline(BaseModel):
    model_config = ConfigDict(extra="ignore")

    section_index: int = Field(..., description="Index of the section (1 to 4)")
    title: str = Field(..., description="Section H2 Title adhering to Ship 30 style")
    key_takeaway: str = Field(..., description="Main strategic point covered in this section")
    transcript_citations: List[str] = Field(
        default_factory=list,
        description="List of quote snippets or guest names from transcript context to cite"
    )
    target_word_count: int = Field(default=300, description="Target word count for this section")


class Ship30Outline(BaseModel):
    model_config = ConfigDict(extra="ignore")

    topic: str = Field(..., description="Core topic of the essay")
    target_audience: str = Field(..., description="Target reader (e.g., Growth PMs, Founders)")
    core_thesis: str = Field(..., description="One-sentence central thesis")
    hook_attention: str = Field(..., description="4 A's Hook: Attention statement")
    hook_agitate: str = Field(..., description="4 A's Hook: Agitation of the core pain point")
    hook_articulate: str = Field(..., description="4 A's Hook: Articulation of the core problem")
    hook_action: str = Field(..., description="4 A's Hook: Actionable solution promise")
    sections: List[SectionOutline] = Field(..., description="List of 4 planned sections")
    total_target_words: int = Field(default=1250, description="Total target word count")


class Ship30SectionDraft(BaseModel):
    model_config = ConfigDict(extra="ignore")

    section_index: int
    title: str
    raw_text: str
    word_count: int
    citations_included: List[str]


class Ship30EssayDraft(BaseModel):
    model_config = ConfigDict(extra="ignore")

    topic: str
    hook_text: str
    sections: List[Ship30SectionDraft]
    conclusion_framework: str
    total_word_count: int


class Ship30FinalResult(BaseModel):
    model_config = ConfigDict(extra="ignore")

    essay_markdown: str
    word_count: int
    section_count: int
    has_4a_hook: bool
    has_131_cadence: bool
    citations: List[str]
    is_compliant: bool
