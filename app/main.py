from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse


from pathlib import Path
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


@app.get("/videos")
def list_videos():

    videos = []

    for file in VIDEOS_DIR.glob("*.mp4"):
        videos.append(file.stem)

    return {
        "videos": sorted(videos)
    }


@app.get("/videos/{video_id}")
def get_video(video_id: str):

    video_path = VIDEOS_DIR / f"{video_id}.mp4"

    if not video_path.exists():
        raise HTTPException(
            status_code=404,
            detail=f"Video not found: {video_id}"
        )

    return FileResponse(
        path=str(video_path),
        media_type="video/mp4",
        filename=video_path.name
    )



@app.get("/jobs/{job_id}")
def get_job(job_id: str):

    job_dir = OUTPUTS_DIR / job_id

    if not job_dir.exists():
        raise HTTPException(
            status_code=404,
            detail=f"Job not found: {job_id}"
        )

    tracked_video = job_dir / "tracked.mp4"
    events_json = job_dir / "events.json"
    snapshots_dir = job_dir / "snapshots"

    snapshots = []

    if snapshots_dir.exists():
        snapshots = sorted([
            file.name
            for file in snapshots_dir.glob("*.jpg")
        ])

    return {
        "job_id": job_id,
        "status": "completed",
        "tracked_video_url": f"/jobs/{job_id}/tracked-video",
        "events_url": f"/jobs/{job_id}/events",
        "snapshots": snapshots}


@app.get("/jobs/{job_id}/tracked-video")
def get_tracked_video(job_id: str):

    video_path = OUTPUTS_DIR / job_id / "tracked.mp4"

    if not video_path.exists():
        raise HTTPException(
            status_code=404,
            detail=f"Tracked video not found for job: {job_id}"
        )

    return FileResponse(
        path=str(video_path),
        media_type="video/mp4",
        filename="tracked.mp4"
    )


@app.get("/jobs/{job_id}/events")
def get_events(job_id: str):

    events_path = OUTPUTS_DIR / job_id / "events.json"

    if not events_path.exists():
        raise HTTPException(
            status_code=404,
            detail=f"Events file not found for job: {job_id}"
        )

    return FileResponse(
        path=str(events_path),
        media_type="application/json",
        filename="events.json"
    )





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