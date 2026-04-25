from sqlalchemy.orm import Session
from sqlalchemy import func
from models import Question
from typing import List


def get_random_questions(db: Session, stack: str, difficulty: str, limit: int = 5) -> List[Question]:
    """
    Get random questions from the database based on stack and difficulty.
    """
    questions = (
        db.query(Question)
        .filter(Question.stack == stack, Question.difficulty == difficulty)
        .order_by(func.random())
        .limit(limit)
        .all()
    )
    return questions


def get_question_by_id(db: Session, question_id) -> Question:
    """
    Get a specific question by ID.
    """
    return db.query(Question).filter(Question.id == question_id).first()
