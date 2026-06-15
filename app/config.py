
from pathlib import Path



BASE_DIR = Path(__file__).resolve().parent.parent

# ==========================================
# STORAGE
# ==========================================

VIDEOS_DIR = BASE_DIR / "videos"

OUTPUTS_DIR = BASE_DIR / "outputs"

# ==========================================
# MODEL
# ==========================================

MODEL_PATH = BASE_DIR / "weights" / "best.pt"

# ==========================================
# TRACKING
# ==========================================

TRACK_EVERY_N_FRAMES = 5

MIN_STABLE_FRAMES = 10


# ==========================================
# OUTPUT FILES
# ==========================================

TRACKED_VIDEO_NAME = "tracked.mp4"

EVENTS_JSON_NAME = "events.json"

SNAPSHOTS_DIR_NAME = "snapshots"