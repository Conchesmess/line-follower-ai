"""
PROGRESS TRACKING
=================
Small helper shared by the training, time-trial and menu screens. It keeps a
record of what this student has done so far in progress.json, next to
best_weights.json (the trained brain itself).

Both files live in the same folder as this code, no matter which folder
VS Code happens to launch Python from.
"""

import ast
import json
import os
import re
from datetime import datetime

HERE = os.path.dirname(os.path.abspath(__file__))
WEIGHTS_PATH = os.path.join(HERE, "best_weights.json")
PROGRESS_PATH = os.path.join(HERE, "progress.json")
SPIKE_PATH = os.path.join(HERE, "spike_line_follower.py")
WEIGHT_COUNT = 18        # 2 sensors x 6 hidden + 6 hidden x 1 output
OLD_WEIGHT_COUNT = 24    # the earlier brain had a second (unused) output

_DEFAULTS = {
    "training_sessions": 0,      # times the student has run training
    "generations_trained": 0,    # total generations evolved across all sessions
    "best_fitness": None,        # fitness of the weights currently saved
    "trained_at": None,          # when those weights were saved
    "best_lap_times": {},        # fastest time-trial lap at each speed on Track A, e.g. {"1": 20.77}; kept across retraining
    "best_lap_times_b": {},      # the same for Track B, the track the brain never trained on
}


def speed_key(speed):
    return f"{speed:g}"    # 1.0 -> "1", 1.25 -> "1.25"


def load_progress():
    progress = {k: (dict(v) if isinstance(v, dict) else v) for k, v in _DEFAULTS.items()}
    try:
        with open(PROGRESS_PATH) as f:
            saved = json.load(f)
    except (FileNotFoundError, ValueError):
        return progress
    progress.update(saved)
    # older files kept a single best time, which was always at normal speed
    old_best = progress.pop("best_lap_time", None)
    if old_best is not None:
        progress["best_lap_times"].setdefault(speed_key(1.0), old_best)
    return progress


def save_progress(progress):
    with open(PROGRESS_PATH, "w") as f:
        json.dump(progress, f, indent=2)


def load_weights():
    """Returns the saved weights list, or None if there aren't any yet."""
    try:
        with open(WEIGHTS_PATH) as f:
            weights = json.load(f)
    except (FileNotFoundError, ValueError):
        return None
    if isinstance(weights, list) and len(weights) == OLD_WEIGHT_COUNT:
        # Saved when the brain had a second, unused output. The steering output's
        # weights come first, so dropping the last 6 numbers keeps the same driving.
        weights = weights[:WEIGHT_COUNT]
        with open(WEIGHTS_PATH, "w") as f:
            json.dump(weights, f)
    return weights


def record_training(generations, best_fitness):
    progress = load_progress()
    progress["training_sessions"] += 1
    progress["generations_trained"] += generations
    progress["best_fitness"] = best_fitness
    progress["trained_at"] = datetime.now().isoformat(timespec="seconds")
    save_progress(progress)


def times_field(track="A"):
    """Which progress.json field holds the lap times for this track."""
    return "best_lap_times" if track == "A" else "best_lap_times_b"


def record_lap_time(seconds, speed=1.0, track="A"):
    """Saves the lap time if it's the fastest yet at this speed on this track.
    Returns True for a new record."""
    progress = load_progress()
    key = speed_key(speed)
    field = times_field(track)
    best = progress[field].get(key)
    if best is None or seconds < best:
        progress[field][key] = seconds
        save_progress(progress)
        return True
    return False


def start_over():
    """Deletes the trained weights and all progress."""
    for path in (WEIGHTS_PATH, PROGRESS_PATH):
        try:
            os.remove(path)
        except FileNotFoundError:
            pass


# ----------------------------------------------------------------------
# SPIKE ROBOT FILE — bakes trained weights into spike_line_follower.py so
# each student ends up with a ready-to-copy robot file, no hand-editing a
# raw weights list onto their SPIKE hub.
# ----------------------------------------------------------------------
_WEIGHTS_BLOCK = re.compile(r"WEIGHTS = \[.*?\]", re.DOTALL)


def read_spike_weights(spike_file=SPIKE_PATH):
    """Returns the WEIGHTS list currently in the robot file, or None if the
    file (or its WEIGHTS list) can't be found."""
    try:
        with open(spike_file) as f:
            match = _WEIGHTS_BLOCK.search(f.read())
    except FileNotFoundError:
        return None
    if match is None:
        return None
    return ast.literal_eval(match.group(0)[len("WEIGHTS = "):])


def export_spike_weights(weights, spike_file=SPIKE_PATH):
    """Rewrites the WEIGHTS list in the robot file. Returns False if the file
    or its WEIGHTS list can't be found."""
    try:
        with open(spike_file) as f:
            content = f.read()
    except FileNotFoundError:
        return False

    grouped_lines = []
    for i in range(0, len(weights), 3):
        chunk = ", ".join(repr(w) for w in weights[i:i + 3])
        grouped_lines.append(f"    {chunk},")
    weights_block = "WEIGHTS = [\n" + "\n".join(grouped_lines) + "\n]"

    new_content, n = _WEIGHTS_BLOCK.subn(lambda _: weights_block, content, count=1)
    if n == 0:
        return False

    with open(spike_file, "w") as f:
        f.write(new_content)
    return True
