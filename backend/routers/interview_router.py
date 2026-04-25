from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from database import get_db
from models import Interview, Message, Question, User
from schemas import StartInterview, StartInterviewResponse, SendAnswer, SendAnswerResponse
from services.question_service import get_random_questions
from services.gigachat_service import gigachat_service
from auth import get_current_user
from uuid import UUID, uuid4
from datetime import datetime
import json

router = APIRouter(prefix="/interviews", tags=["interviews"])

# In-memory storage for interview questions (can be replaced with Redis or DB column)
interview_questions = {}  # interview_id -> list of Question objects


@router.post("/start", response_model=StartInterviewResponse)
def start_interview(
    interview_data: StartInterview,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Start a new interview"""
    # Get 5 random questions
    questions = get_random_questions(
        db,
        interview_data.stack,
        interview_data.difficulty,
        limit=5
    )
    
    if not questions:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"No questions found for stack='{interview_data.stack}' and difficulty='{interview_data.difficulty}'"
        )
    
    # Create interview record
    interview = Interview(
        user_id=current_user.id,
        stack=interview_data.stack,
        difficulty=interview_data.difficulty,
        status="active"
    )
    db.add(interview)
    db.commit()
    db.refresh(interview)
    
    # Store questions in memory
    interview_questions[str(interview.id)] = questions
    
    # Get first question
    first_question = questions[0]
    
    # Create assistant message with the question
    message = Message(
        interview_id=interview.id,
        role="assistant",
        content=f"Привет! Начнём. Первый вопрос: {first_question.text}",
        question_id=first_question.id
    )
    db.add(message)
    db.commit()
    
    return StartInterviewResponse(
        interview_id=str(interview.id),
        question_number=1,
        total_questions=5,
        message=message.content
    )


@router.post("/send", response_model=SendAnswerResponse)
async def send_answer(
    answer_data: SendAnswer,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Send an answer to the current question"""
    interview_id = answer_data.interview_id
    
    # Find interview
    interview = db.query(Interview).filter(
        Interview.id == UUID(interview_id),
        Interview.user_id == current_user.id
    ).first()
    
    if not interview:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Interview not found"
        )
    
    if interview.status != "active":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Interview is not active"
        )
    
    # Get questions for this interview
    questions = interview_questions.get(interview_id)
    if not questions:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Interview questions not found"
        )
    
    # Count user answers to determine current question number
    user_answers_count = db.query(Message).filter(
        Message.interview_id == UUID(interview_id),
        Message.role == "user"
    ).count()
    
    current_question_index = user_answers_count
    current_question = questions[current_question_index]
    
    # Save user's answer
    user_message = Message(
        interview_id=interview.id,
        role="user",
        content=answer_data.answer,
        question_id=current_question.id
    )
    db.add(user_message)
    
    # Evaluate answer using GigaChat
    evaluation = await gigachat_service.evaluate_answer(
        current_question.text,
        current_question.answer_hint or "No hint available",
        answer_data.answer
    )
    
    # Save AI evaluation
    assistant_message = Message(
        interview_id=interview.id,
        role="assistant",
        content=evaluation,
        question_id=current_question.id
    )
    db.add(assistant_message)
    db.commit()
    
    # Check if there are more questions
    next_question_index = current_question_index + 1
    
    if next_question_index >= len(questions):
        # Interview completed
        interview.status = "completed"
        interview.finished_at = datetime.utcnow()
        db.commit()
        
        return SendAnswerResponse(
            type="finished",
            ai_reaction=evaluation,
            question_number=len(questions)
        )
    else:
        # Return next question
        next_question = questions[next_question_index]
        
        # Create message for next question
        next_message = Message(
            interview_id=interview.id,
            role="assistant",
            content=next_question.text,
            question_id=next_question.id
        )
        db.add(next_message)
        db.commit()
        
        return SendAnswerResponse(
            type="question",
            ai_reaction=evaluation,
            next_question=next_question.text,
            question_number=next_question_index + 1
        )


@router.get("/my")
def get_user_interviews(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get all interviews for the current user"""
    from models import Feedback
    
    interviews = (
        db.query(Interview)
        .filter(Interview.user_id == current_user.id)
        .order_by(Interview.started_at.desc())
        .all()
    )
    
    result = []
    for interview in interviews:
        # Get feedback if exists
        feedback = db.query(Feedback).filter(
            Feedback.interview_id == interview.id
        ).first()
        
        result.append({
            "id": str(interview.id),
            "stack": interview.stack,
            "difficulty": interview.difficulty,
            "status": interview.status,
            "started_at": interview.started_at,
            "finished_at": interview.finished_at,
            "score": feedback.score if feedback else None
        })
    
    return result
