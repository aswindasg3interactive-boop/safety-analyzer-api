from fastapi import FastAPI, HTTPException

from app.analyzer import analyze_video
from app.schemas import AnalyzeRequest
from app.config import MODEL_PATH


app = FastAPI(
    title="Video Safety Analyzer API",
    version="1.0.0"
)


@app.get("/")
def home():
    return {
        "message": "Video Analyzer API Running",
        "model": MODEL_PATH,
        "status": "healthy"
    }


@app.get("/health")
def health_check():
    return {
        "status": "healthy"
    }


@app.post("/analyze")
def analyze(request: AnalyzeRequest):
    """
    Analyze a video using the provided zones.
    """

    try:

        result = analyze_video(
            video_path=request.input_video_path,
            safe_zones=request.safe_zones,
            restricted_zones=request.restricted_zones,
            output_dir=request.output_dir
        )

        return result

    except Exception as e:

        raise HTTPException(
            status_code=500,
            detail=str(e)
        )