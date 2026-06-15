from fastapi import FastAPI, HTTPException

from app.analyzer import analyze_video
from app.schemas import AnalyzeRequest
from app.config import MODEL_PATH, VIDEOS_DIR, OUTPUTS_DIR


app = FastAPI(
    title="Video Safety Analyzer API",
    version="1.0.0"
)


VIDEOS_DIR.mkdir(
    parents=True,
    exist_ok=True)

OUTPUTS_DIR.mkdir(
    parents=True,
    exist_ok=True)




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

    try:

        video_path = VIDEOS_DIR / f"{request.video_id}.mp4"

        if not video_path.exists():
            raise HTTPException(
                status_code=404,
                detail=f"Video not found: {request.video_id}"
            )

        job_output_dir = OUTPUTS_DIR / request.job_id

        job_output_dir.mkdir(
            parents=True,
            exist_ok=True
        )

        result = analyze_video(
            video_path=str(video_path),
            safe_zones=request.safe_zones,
            restricted_zones=request.restricted_zones,
            output_dir=str(job_output_dir)
        )

        return result

    except HTTPException:
        raise

    except Exception as e:

        raise HTTPException(
            status_code=500,
            detail=str(e)
        )