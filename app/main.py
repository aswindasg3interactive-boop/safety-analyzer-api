from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse

import threading
import shutil

from app.schemas import AnalyzeRequest
from app.config import MODEL_PATH, VIDEOS_DIR, OUTPUTS_DIR
from app.worker import process_job
from app.job_status import (save_job_status,load_job_status)



app = FastAPI(
    title="Video Safety Analyzer API",
    version="1.0.0")


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
            f"/jobs/{job_id}/snapshots/{file.name}" for file in snapshots_dir.glob("*.jpg")])

    status_info = load_job_status(job_dir)

    if status_info is None:
        status_info = {"status": "unknown"}

    return {
        "job_id": job_id,
        "status": status_info.get("status", "unknown"),
        "tracked_video_url": f"/jobs/{job_id}/tracked-video",
        "events_url": f"/jobs/{job_id}/events",
        "snapshots": snapshots
        }


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



@app.get("/jobs/{job_id}/snapshots/{filename}")
def get_snapshot(
    job_id: str,
    filename: str
):

    snapshot_path = (
        OUTPUTS_DIR
        / job_id
        / "snapshots"
        / filename
    )

    if not snapshot_path.exists():
        raise HTTPException(
            status_code=404,
            detail=f"Snapshot not found: {filename}"
        )

    return FileResponse(
        path=str(snapshot_path),
        media_type="image/jpeg",
        filename=filename
    )





@app.post("/analyze")
def analyze(request: AnalyzeRequest):

    video_path = VIDEOS_DIR / f"{request.video_id}.mp4"

    if not video_path.exists():
        raise HTTPException(
            status_code=404,
            detail=f"Video not found: {request.video_id}"
        )

    job_output_dir = OUTPUTS_DIR / request.job_id

    if job_output_dir.exists():
        shutil.rmtree(job_output_dir)

    job_output_dir.mkdir(
        parents=True,
        exist_ok=True
    )

    save_job_status(
        job_output_dir,
        "queued"
    )

    worker_thread = threading.Thread(
        target=process_job,
        args=(
            request.job_id,
            str(video_path),
            request.safe_zones,
            request.restricted_zones,
            job_output_dir,
            request.callback_url
        ),
        daemon=True
    )

    worker_thread.start()

    return {
        "job_id": request.job_id,
        "status": "queued"
    }