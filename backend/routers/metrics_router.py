from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from database import get_db
from auth import get_current_user
from models import User, Interview, ProductMetric
from schemas import ProductMetricCreate, ProductMetricResponse, ProductMetricDashboard

router = APIRouter(prefix="/metrics", tags=["Product Metrics"])


@router.post("/submit", response_model=ProductMetricResponse)
def submit_metrics(
    data: ProductMetricCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    if not (1 <= data.csat <= 5):
        raise HTTPException(status_code=400, detail="CSAT must be between 1 and 5")

    if not (1 <= data.ces <= 7):
        raise HTTPException(status_code=400, detail="CES must be between 1 and 7")

    if not (0 <= data.nps <= 10):
        raise HTTPException(status_code=400, detail="NPS must be between 0 and 10")

    interview = db.query(Interview).filter(
        Interview.id == UUID(data.interview_id),
        Interview.user_id == current_user.id
    ).first()

    if not interview:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Interview not found"
        )

    existing_metric = db.query(ProductMetric).filter(
        ProductMetric.interview_id == interview.id,
        ProductMetric.user_id == current_user.id
    ).first()

    if existing_metric:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Metrics for this interview already submitted"
        )

    metric = ProductMetric(
        interview_id=interview.id,
        user_id=current_user.id,
        csat=data.csat,
        ces=data.ces,
        nps=data.nps,
        comment=data.comment
    )

    db.add(metric)
    db.commit()

    return ProductMetricResponse(message="Metrics submitted successfully")


@router.get("/dashboard", response_model=ProductMetricDashboard)
def get_metrics_dashboard(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    metrics = db.query(ProductMetric).all()

    total = len(metrics)

    if total == 0:
        return ProductMetricDashboard(
            total_responses=0,
            csat_percent=0,
            ces_average=0,
            nps_score=0
        )

    csat_positive = len([m for m in metrics if m.csat >= 4])
    csat_percent = (csat_positive / total) * 100

    ces_average = sum(m.ces for m in metrics) / total

    promoters = len([m for m in metrics if m.nps >= 9])
    detractors = len([m for m in metrics if m.nps <= 6])

    nps_score = ((promoters / total) * 100) - ((detractors / total) * 100)

    return ProductMetricDashboard(
        total_responses=total,
        csat_percent=round(csat_percent, 2),
        ces_average=round(ces_average, 2),
        nps_score=round(nps_score, 2)
    )