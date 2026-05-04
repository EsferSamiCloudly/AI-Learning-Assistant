from pydantic import BaseModel


class QAPair(BaseModel):
    question: str
    student_answer: str
    reference_answer: str | None = None


class EvaluateRequest(BaseModel):
    pairs: list[QAPair]
    reference_content: str | None = None
    document_id: str | None = None
    mode: str = "single"


class AnswerResult(BaseModel):
    question: str
    student_answer: str
    score: float
    feedback: str


class EvaluateResponse(BaseModel):
    id: str
    mode: str
    results: list[AnswerResult]
    total_score: float