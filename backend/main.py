from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.routers import reports, auth
from app.core.database import init_db

app = FastAPI(
    title="Witness API",
    description="Community safety reporting platform for South Africa",
    version="0.1.0"
)

# Allow Flutter app to talk to this backend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Tighten this in production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Register route groups
app.include_router(auth.router, prefix="/auth", tags=["auth"])
app.include_router(reports.router, prefix="/reports", tags=["reports"])

@app.on_event("startup")
async def startup_event():
    """Create database tables when the app starts."""
    init_db()

@app.get("/")
async def root():
    return {"message": "Witness API is running", "version": "0.1.0"}

@app.get("/health")
async def health():
    return {"status": "ok"}
