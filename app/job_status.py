import json
from pathlib import Path


def save_job_status(job_dir: Path, status: str, error: str = None):

    payload = {"status": status}

    if error:
        payload["error"] = error

    with open(job_dir / "status.json", "w") as f:
        json.dump(payload, f, indent=4)


def load_job_status(job_dir: Path):

    status_file = job_dir / "status.json"

    if not status_file.exists():
        return None

    with open(status_file) as f:
        return json.load(f)