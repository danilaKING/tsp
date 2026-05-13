from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from database import get_db
from models import Interview, Message, Question, User
from schemas import StartInterview, StartInterviewResponse, SendAnswer, SendAnswerResponse, HintRequest, HintResponse
from services.question_service import get_random_questions
from services.gigachat_service import gigachat_service
from auth import get_current_user
from uuid import UUID, uuid4
from datetime import datetime, timezone
import json

router = APIRouter(prefix="/interviews", tags=["interviews"])


def get_interview_questions(interview: Interview, db: Session) -> list:
    """Load questions for an interview from database"""
    if not interview.questions:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Interview questions not found"
        )
    
    question_ids = interview.questions
    questions = db.query(Question).filter(
        Question.id.in_([UUID(qid) for qid in question_ids])
    ).all()
    
    if len(questions) != len(question_ids):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Some interview questions were deleted"
        )
    
    # Sort questions by the order they were selected
    question_map = {str(q.id): q for q in questions}
    ordered_questions = [question_map[qid] for qid in question_ids]
    
    return ordered_questions


@router.delete("/{interview_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_interview(
        interview_id: UUID,
        db: Session = Depends(get_db),
        current_user: User = Depends(get_current_user)
):
    interview = db.query(Interview).filter(
        Interview.id == interview_id,
        Interview.user_id == current_user.id
    ).first()

    if not interview:
        raise HTTPException(status_code=404, detail="Interview not found")

    db.delete(interview)
    db.commit()
    return None
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
    
    # Create interview record with questions stored in JSON
    question_ids = [str(q.id) for q in questions]
    interview = Interview(
        user_id=current_user.id,
        stack=interview_data.stack,
        difficulty=interview_data.difficulty,
        status="active",
        questions=question_ids  # Store question IDs in DB
    )
    db.add(interview)
    db.commit()
    db.refresh(interview)
    
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
    
    # Load questions from database
    questions = get_interview_questions(interview, db)
    
    # Count user answers to determine current question number
    user_answers_count = db.query(Message).filter(
        Message.interview_id == UUID(interview_id),
        Message.role == "user"
    ).count()
    
    # Current question index = number of already answered questions
    # First answer (user_answers_count=0) → question index 0
    # Second answer (user_answers_count=1) → question index 1
    current_question_index = user_answers_count
    if current_question_index < 0 or current_question_index >= len(questions):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid question index: {current_question_index} (total questions: {len(questions)}, user answers: {user_answers_count})"
        )
    
    current_question = questions[current_question_index]
    
    # Save user's answer
    user_message = Message(
        interview_id=interview.id,
        role="user",
        content=answer_data.answer,
        question_id=current_question.id
    )
    db.add(user_message)
    
    next_question_index = current_question_index + 1
    is_last_question = next_question_index >= len(questions)

    # Evaluate answer using GigaChat
    evaluation = await gigachat_service.evaluate_answer(
        current_question.text,
        current_question.answer_hint or "No hint available",
        answer_data.answer
    )
    #print(f"GigaChat evaluation: {type(evaluation)} - {evaluation}")
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
    if is_last_question:
        # Interview completed
        interview.status = "completed"
        interview.finished_at = datetime.now(timezone.utc)
        db.commit()
        
        return SendAnswerResponse(
            type="finished",
            ai_reaction=evaluation,
            next_question=None,
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


@router.post("/hint", response_model=HintResponse)
def get_hint(
    hint_data: HintRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    interview_id = hint_data.interview_id

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

    # Load questions from database
    questions = get_interview_questions(interview, db)

    user_answers_count = db.query(Message).filter(
        Message.interview_id == UUID(interview_id),
        Message.role == "user"
    ).count()

    if user_answers_count >= len(questions):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No active question for hint"
        )

    current_question = questions[user_answers_count]

    hint = current_question.answer_hint or "Для этого вопроса подсказка не добавлена."

    return HintResponse(hint=hint)

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


@router.get("/{interview_id}")
def get_interview_details(
    interview_id: UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get full interview details including messages and feedback"""
    from models import Feedback

    interview = db.query(Interview).filter(
        Interview.id == interview_id,
        Interview.user_id == current_user.id
    ).first()

    if not interview:
        raise HTTPException(status_code=404, detail="Interview not found")

    messages = (
        db.query(Message)
        .filter(Message.interview_id == interview_id)
        .order_by(Message.timestamp)
        .all()
    )

    user_answers_count = sum(1 for m in messages if m.role == "user")

    feedback = db.query(Feedback).filter(
        Feedback.interview_id == interview_id
    ).first()

    return {
        "id": str(interview.id),
        "stack": interview.stack,
        "difficulty": interview.difficulty,
        "status": interview.status,
        "messages": [
            {"id": str(m.id), "role": m.role, "content": m.content}
            for m in messages
        ],
        "current_question_number": user_answers_count + 1,
        "total_questions": len(interview.questions or []),
        "feedback": feedback.analysis if feedback else None,
    }
@router.post("/{interview_id}/exit")
def exit_interview(
    interview_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Manually exit/terminate an active interview"""
    try:
        uuid_id = UUID(interview_id)
    except ValueError:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid UUID")

    # Find interview
    interview = db.query(Interview).filter(
        Interview.id == uuid_id,
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

    # Mark as completed (or you could add a 'cancelled' status if preferred)
    interview.status = "completed"
    interview.finished_at = datetime.utcnow()
    db.commit()

    return {"message": "Interview exited successfully"}
    return result
