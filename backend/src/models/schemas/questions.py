from pydantic import BaseModel


class GenerateQuestionsRequest(BaseModel):
    content: str | None = None
    document_id: str | None = None
    difficulty: str = "medium"
    count: int = 5
    domain: str | None = None


class Question(BaseModel):
    question: str
    expected_answer: str
    difficulty: str


class QuestionsResponse(BaseModel):
    id: str
    questions: list[Question]
    difficulty: str
    count: int