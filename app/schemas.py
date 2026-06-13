from pydantic import BaseModel
from typing import List


class Point(BaseModel):
    x: int
    y: int


class Zone(BaseModel):
    id: str
    canvas_width: int
    canvas_height: int
    points: List[Point]


class AnalyzeRequest(BaseModel):
    job_id: str
    input_video_path: str
    output_dir: str

    safe_zones: List[Zone]
    restricted_zones: List[Zone]

    callback_url: str