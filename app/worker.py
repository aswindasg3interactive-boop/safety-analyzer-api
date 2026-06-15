from app.analyzer import analyze_video
from app.job_status import save_job_status


def process_job(
    video_path,
    safe_zones,
    restricted_zones,
    output_dir,
    callback_url=None
):

    try:

        save_job_status(output_dir, "processing")

        analyze_video(
            video_path=video_path,
            safe_zones=safe_zones,
            restricted_zones=restricted_zones,
            output_dir=str(output_dir)
        )

        save_job_status(output_dir, "completed")

    except Exception as e:

        save_job_status(
            output_dir,
            "failed",
            str(e)
        )