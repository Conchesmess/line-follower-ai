# SPDX-License-Identifier: PolyForm-Noncommercial-1.0.0  (see LICENSE-CODE)
"""
BUILD THE STUDENT PACKAGE  (teacher tool; not included in the package)
=====================================================================
Makes dist/LineFollowerAI-student.zip: one folder a student unzips, opens in
VS Code and runs. Run it from this folder:

    python make_student_package.py           build the zip once
    python make_student_package.py --watch   keep running, and rebuild the zip
                                             every time a packaged file changes
                                             (Ctrl+C to stop)

What goes in:  every .py file here (except this one), the student-facing
               documents, the images, requirements.txt and a fresh .vscode
               folder (Run button / F5 launches menu.py).
What stays out: teacher documents, CLASS-SPECIFIC.md, your own .vscode
               settings, __pycache__, and best_weights.json / progress.json
               (those are YOUR training results, not the students').

Note: spike_line_follower.py is packaged as it is now, including whatever
WEIGHTS it holds. Students overwrite them with their own ("6) Copy to Spike
Robot Code").
"""

import hashlib
import json
import os
import sys
import time
import zipfile
from datetime import datetime

HERE = os.path.dirname(os.path.abspath(__file__))
FOLDER = "LineFollowerAI"                       # the folder students get when they unzip
OUT = os.path.join(HERE, "dist", "LineFollowerAI-student.zip")

TEACHER_ONLY_CODE = {"make_student_package.py"}
STUDENT_DOCS = ["README.md", "LICENSE", "LICENSE-CODE", "LICENSE-DOCS", "student-guide.md", "weights-explained.md", "glossary.md", "requirements.txt"]
IMAGE_DIR = "images"

VSCODE_FILES = {
    ".vscode/extensions.json": {"recommendations": ["ms-python.python"]},
    ".vscode/settings.json": {"python.terminal.activateEnvironment": True},
    ".vscode/launch.json": {
        "version": "0.2.0",
        "configurations": [{
            "name": "Run Line Follower AI (menu.py)",
            "type": "debugpy",
            "request": "launch",
            "program": "${workspaceFolder}/menu.py",
            "console": "integratedTerminal",
            "cwd": "${workspaceFolder}",
        }],
    },
}


def files_to_package():
    names = sorted(f for f in os.listdir(HERE) if f.endswith(".py") and f not in TEACHER_ONLY_CODE)
    names += STUDENT_DOCS
    images = os.path.join(HERE, IMAGE_DIR)
    if os.path.isdir(images):
        names += [f"{IMAGE_DIR}/{f}" for f in sorted(os.listdir(images)) if not f.startswith(".")]
    return names


def content_signature(names):
    """{file name: hash of its contents}. Used to spot real changes (not just a touched date)."""
    sig = {}
    for name in names:
        path = os.path.join(HERE, name)
        if os.path.exists(path):
            with open(path, "rb") as f:
                sig[name] = hashlib.sha256(f.read()).hexdigest()
    return sig


def build_id(sig):
    """A short id that changes whenever any packaged file's contents change."""
    return hashlib.sha256(json.dumps(sig, sort_keys=True).encode()).hexdigest()[:8]


def previous_build_id():
    try:
        with zipfile.ZipFile(OUT) as z:
            for line in z.read(f"{FOLDER}/BUILD-INFO.txt").decode().splitlines():
                if line.startswith("Build id:"):
                    return line.split(":", 1)[1].strip()
    except (OSError, KeyError, zipfile.BadZipFile):
        pass
    return None


def build(quiet=False):
    """Builds the zip. Returns the build id."""
    names = files_to_package()
    missing = [n for n in names if not os.path.exists(os.path.join(HERE, n))]
    if missing:
        sys.exit("Can't build: these files are missing: " + ", ".join(missing))

    old_id = previous_build_id()
    new_id = build_id(content_signature(names))
    stamp = datetime.now().strftime("%Y-%m-%d %H:%M")
    info = f"Line Follower AI student package\nBuilt: {stamp}\nBuild id: {new_id}\n"

    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    tmp = OUT + ".tmp"                                # write aside, so a half-built zip never replaces a good one
    with zipfile.ZipFile(tmp, "w", zipfile.ZIP_DEFLATED) as z:
        for name in names:
            z.write(os.path.join(HERE, name), f"{FOLDER}/{name}")
        for name, content in VSCODE_FILES.items():
            z.writestr(f"{FOLDER}/{name}", json.dumps(content, indent=4) + "\n")
        z.writestr(f"{FOLDER}/BUILD-INFO.txt", info)
    os.replace(tmp, OUT)

    if not quiet:
        with zipfile.ZipFile(OUT) as z:
            print(f"Built {OUT}")
            print(f"{len(z.namelist())} files, {os.path.getsize(OUT) / 1024:.0f} KB. Build id {new_id} ({stamp}).")
            if old_id:
                print("(contents unchanged since the last build)" if old_id == new_id
                      else "(contents changed since the last build)")
    return new_id


def watch(interval=2.0):
    """Rebuilds whenever a packaged file's contents change."""
    names_before = files_to_package()
    last = content_signature(names_before)
    build_id_now = build()
    print("\nWatching for changes. Press Ctrl+C to stop.\n")
    try:
        while True:
            time.sleep(interval)
            names = files_to_package()
            now = content_signature(names)
            if now != last:
                changed = sorted(n for n in set(now) | set(last) if now.get(n) != last.get(n))
                print(f"{datetime.now():%H:%M:%S}  changed: {', '.join(changed)}")
                last = now
                time.sleep(0.5)               # let an editor finish saving
                build_id_now = build(quiet=True)
                print(f"           rebuilt: build id {build_id_now}")
    except KeyboardInterrupt:
        print("\nStopped watching.")


def main():
    if "--watch" in sys.argv[1:]:
        watch()
    else:
        build()


if __name__ == "__main__":
    main()
