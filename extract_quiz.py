from pydantic import BaseModel
from openai import OpenAI

class QuizQuestion(BaseModel):
        question: str
        corect_answer: int
        answers: list[str]

class Quiz(BaseModel):
    topic: str
    source_document: str
    questions: list[QuizQuestion]        

client = OpenAI()


def extract_quiz(text):
    completion = client.beta.chat.completions.parse(
        model="gpt-4o-2024-08-06",
        messages=[
            {"role": "system", "content": "Extract quiz questions."},
            {"role": "user", "content": text},
        ],
    response_format=Quiz,
    )
    return completion.choices[0].message.parsed