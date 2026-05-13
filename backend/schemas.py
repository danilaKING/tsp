from pydantic import BaseModel, EmailStr
from typing import Optional, List
from datetime import datetime
from uuid import UUID


# Auth schemas
class UserRegister(BaseModel):
    email: str
    password: str


class UserLogin(BaseModel):
    email: str
    password: str


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"


# Interview schemas
class StartInterview(BaseModel):
    stack: str
    difficulty: str


class StartInterviewResponse(BaseModel):
    interview_id: str
    question_number: int
    total_questions: int
    message: str


class SendAnswer(BaseModel):
    interview_id: str
    answer: str

class HintRequest(BaseModel):
    interview_id: str


class HintResponse(BaseModel):
    hint: str

class SendAnswerResponse(BaseModel):
    type: str  # "question" or "finished"
    ai_reaction: Optional[str] = None
    next_question: Optional[str] = None
    question_number: Optional[int] = None


# Feedback schemas
class GenerateFeedback(BaseModel):
    interview_id: str


class FeedbackAnalysis(BaseModel):
    score: int
    pros: List[str]
    cons: List[str]
    recommendations: List[dict]


class FeedbackResponse(BaseModel):
    id: str
    score: int
    analysis: FeedbackAnalysis
    created_at: datetime


# Question schema
class QuestionSchema(BaseModel):
    id: str
    stack: str
    difficulty: str
    text: str


# Message schema
class MessageSchema(BaseModel):
    id: str
    role: str
    content: str
    timestamp: datetime


# Interview history schema
class InterviewHistoryItem(BaseModel):
    id: str
    stack: str
    difficulty: str
    status: str
    started_at: datetime
    finished_at: Optional[datetime]
    score: Optional[int] = None


class ProductMetricCreate(BaseModel):
    interview_id: str
    csat: int
    ces: int
    nps: int
    comment: Optional[str] = None


class ProductMetricResponse(BaseModel):
    message: str


class ProductMetricDashboard(BaseModel):
    total_responses: int
    csat_percent: float
    ces_average: float
    nps_score: float