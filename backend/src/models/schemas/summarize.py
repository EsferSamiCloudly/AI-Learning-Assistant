from pydantic import BaseModel


class SummarizeTextRequest(BaseModel):
    content: str
    mode: str = "short"


class SummarizePDFRequest(BaseModel):
    document_id: str
    mode: str = "short"


class SummarizeResponse(BaseModel):
    id: str
    content: str
    mode: str