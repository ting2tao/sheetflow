import os
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from app.api.render import router as render_router
from app.api.analytics import router as analytics_router, AnalyticsMiddleware

app = FastAPI(
    title="SheetFlow",
    description="表格分页图片生成器 - Excel to Image",
    version="1.0.0",
)

# CORS for frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Create storage directories
STORAGE_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "storage")
os.makedirs(os.path.join(STORAGE_DIR, "uploads"), exist_ok=True)
os.makedirs(os.path.join(STORAGE_DIR, "jobs"), exist_ok=True)
os.makedirs(os.path.join(STORAGE_DIR, "outputs"), exist_ok=True)
os.makedirs(os.path.join(STORAGE_DIR, "analytics"), exist_ok=True)

# Mount storage for downloads
app.mount("/download", StaticFiles(directory=os.path.join(STORAGE_DIR, "outputs")), name="download")

# Analytics middleware
app.add_middleware(AnalyticsMiddleware)

# Include API routers
app.include_router(render_router, prefix="/api")
app.include_router(analytics_router, prefix="/api")


@app.get("/")
async def root():
    return {"message": "SheetFlow API is running", "version": "1.0.0"}
