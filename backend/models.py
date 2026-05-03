import uuid
from datetime import datetime, timezone
from sqlalchemy import Column, String, Integer, Text, DateTime, ForeignKey, Enum, JSON
from sqlalchemy.dialects.postgresql import UUID
from database import Base


class User(Base):
    __tablename__ = "users"
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    email = Column(String(255), unique=True, nullable=False)
    password_hash = Column(String(255), nullable=False)
    role = Column(Enum("user", "admin", name="user_role"), default="user")
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))


class Question(Base):
    __tablename__ = "questions"
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    stack = Column(String(50), nullable=False)  # "Python", "JavaScript", "SQL", ...
    difficulty = Column(String(20), nullable=False)  # "Лёгкий", "Средний", "Сложный"
    text = Column(Text, nullable=False)  # сам вопрос
    answer_hint = Column(Text)  # эталонный ответ (для оценки GigaChat)


class Interview(Base):
    __tablename__ = "interviews"
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    stack = Column(String(50))
    difficulty = Column(String(20))
    status = Column(Enum("active", "completed", "aborted", name="interview_status"), default="active")
    started_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    finished_at = Column(DateTime, nullable=True)


class Message(Base):
    __tablename__ = "messages"
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    interview_id = Column(UUID(as_uuid=True), ForeignKey("interviews.id"), nullable=False)
    role = Column(Enum("user", "assistant", name="message_role"), nullable=False)
    content = Column(Text, nullable=False)
    question_id = Column(UUID(as_uuid=True), ForeignKey("questions.id"), nullable=True)  # какой вопрос задавался
    timestamp = Column(DateTime, default=lambda: datetime.now(timezone.utc))


class Feedback(Base):
    __tablename__ = "feedbacks"
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    interview_id = Column(UUID(as_uuid=True), ForeignKey("interviews.id"), nullable=False)
    score = Column(Integer)  # 0–100
    analysis = Column(JSON)  # {"pros": [...], "cons": [...], "recommendations": [...]}
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))


class ProductMetric(Base):
    __tablename__ = "product_metrics"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    interview_id = Column(UUID(as_uuid=True), ForeignKey("interviews.id"), nullable=False)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)

    csat = Column(Integer, nullable=False)  # 1-5
    ces = Column(Integer, nullable=False)   # 1-7
    nps = Column(Integer, nullable=False)   # 0-10
    comment = Column(Text, nullable=True)

    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))