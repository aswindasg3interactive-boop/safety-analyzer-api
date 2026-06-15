import requests


def send_success_callback(
    callback_url: str,
    job_id: str
):

    payload = {
        "status": "completed",
        "job_id": job_id
    }

    response = requests.post(
        callback_url,
        json=payload,
        timeout=10
    )

    return response.status_code


def send_failure_callback(
    callback_url: str,
    job_id: str,
    error_message: str
):

    payload = {
        "status": "failed",
        "job_id": job_id,
        "error": error_message
    }

    response = requests.post(
        callback_url,
        json=payload,
        timeout=10
    )

    return response.status_code