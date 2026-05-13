from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from database import get_db
from models import Interview, Message, Feedback, User
from schemas import GenerateFeedback, FeedbackResponse, FeedbackAnalysis
from services.gigachat_service import gigachat_service
from auth import get_current_user
from uuid import UUID
import json

router = APIRouter(prefix="/feedbacks", tags=["feedbacks"])


@router.post("/generate", response_model=FeedbackResponse)
async def generate_feedback(
    feedback_data: GenerateFeedback,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Generate final interview feedback using GigaChat"""
    interview_id = feedback_data.interview_id
    
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
    
    if interview.status != "completed":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Interview is not completed yet"
        )
    
    # Check if feedback already exists
    
    existing_feedback = db.query(Feedback).filter(
        Feedback.interview_id == UUID(interview_id)
    ).first()
    
    if existing_feedback:
        return FeedbackResponse(
            id=str(existing_feedback.id),
            score=existing_feedback.score,
            analysis=FeedbackAnalysis(**existing_feedback.analysis),
            created_at=existing_feedback.created_at
        )
    
    # Get all messages for this interview
    messages = (
        db.query(Message)
        .filter(Message.interview_id == UUID(interview_id))
        .order_by(Message.timestamp)
        .all()
    )
    
    # Build transcript
    transcript_lines = []
    for msg in messages:
        role_label = "Интервьюер" if msg.role == "assistant" else "Кандидат"
        transcript_lines.append(f"{role_label}: {msg.content}")
    
    transcript = "\n\n".join(transcript_lines)
    
    # Call GigaChat to generate report
    report_text = await gigachat_service.generate_final_report(transcript)
    # print("GigaChat response:", report_text)  # Debugging log
    # Parse JSON from GigaChat response
    try:
        # Try to extract JSON from the response
        # Remove any markdown code blocks if present
        if "```" in report_text:
            # Extract JSON from code block
            start = report_text.find("{")
            end = report_text.rfind("}") + 1
            report_text = report_text[start:end]
        
        analysis = json.loads(report_text)
    except json.JSONDecodeError as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to parse GigaChat response as JSON: {str(e)}"
        )
    

    analysis_to_save = {
            "score": analysis.get("score", 0),
            "pros": analysis.get("pros", []),
            "cons": analysis.get("cons", []),
            # Проверяем оба варианта имени поля
            "recommendations": analysis.get("recommendations", analysis.get("improvements", []))
        }

    feedback = Feedback(
        interview_id=interview.id,
        score=analysis.get("score", 0),
        analysis=analysis_to_save  # Сохраняем полный словарь
    )

    # Save feedback
    # feedback = Feedback(
    #     interview_id=interview.id,
    #     score=analysis.get("score", 0),
    #     analysis={
    #         "pros": analysis.get("pros", []),
    #         "cons": analysis.get("cons", []),
    #         "recommendations": analysis.get("recommendations", [])
    #     }
    # )
    db.add(feedback)
    db.commit()
    db.refresh(feedback)
    
    return FeedbackResponse(
        id=str(feedback.id),
        score=feedback.score,
        analysis=FeedbackAnalysis(**feedback.analysis),
        created_at=feedback.created_at
    )
