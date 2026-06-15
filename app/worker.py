from app.analyzer import analyze_video
from app.job_status import save_job_status
from app.callbacks import (
    send_success_callback,
    send_failure_callback
)


def process_job(
    job_id,
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

        if callback_url:
            send_success_callback(
                callback_url,
                job_id
            )

    except Exception as e:

        save_job_status(
            output_dir,
            "failed",
            str(e)
        )

        if callback_url:
            send_failure_callback(
                callback_url,
                job_id,
                str(e)
            )