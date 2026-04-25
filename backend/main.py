from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from routers import auth_router, interview_router, feedback_router

app = FastAPI(
    title="AI Mock Interviewer",
    description="Technical mock interview platform with AI feedback",
    version="1.0.0"
)

# CORS middleware for frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173",
        "http://localhost:3000",
        ],  # Vite default ports
    allow_credentials=True,
    #allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(auth_router.router)
app.include_router(interview_router.router)
app.include_router(feedback_router.router)


@app.get("/")
def root():
    return {"message": "AI Mock Interviewer API", "version": "1.0.0"}


@app.get("/health")
def health_check():
    return {"status": "ok"}
