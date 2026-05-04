from pydantic import BaseModel


class EssayRequest(BaseModel):
    topic: str
    tone: str = "academic"
    length: str = "medium"
    include_outline: bool = False


class EssayResponse(BaseModel):
    id: str
    topic: str
    content: str