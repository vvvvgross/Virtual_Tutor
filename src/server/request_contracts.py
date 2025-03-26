from pydantic import BaseModel

class TextItem(BaseModel):
    input: str | None = None
    direction: str | None = None

class EmotionItem(BaseModel):
    direction: str | None = None