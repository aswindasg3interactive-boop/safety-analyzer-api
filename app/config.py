
from pathlib import Path


# ==========================================
# MODEL
# ==========================================

MODEL_PATH = Path("weights")/"best.pt"


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