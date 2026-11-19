"""
SETUP CHECK
===========
Run this once after installing, and any time the program won't start:

    py check_setup.py          (Windows)
    python3 check_setup.py     (Mac / Linux)

It checks the things that most often go wrong and says what to do about each.
"""

import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
REQUIRED_FILES = ["menu.py", "line_follower_ai.py", "time_trial.py", "brain_viewer.py", "glossary.md",
                  "weights-explained.md", "spike_line_follower.py"]


def check(label, ok, fix=""):
    print(f"  [{'OK' if ok else 'PROBLEM'}] {label}")
    if not ok and fix:
        print(f"           -> {fix}")
    return ok


def main():
    print("Checking your setup...\n")
    good = True

    good &= check(f"Python {sys.version_info.major}.{sys.version_info.minor} is new enough (3.8 or later)",
                  sys.version_info >= (3, 8), "Install a newer Python from python.org.")

    try:
        import pygame
        good &= check(f"pygame {pygame.version.ver} is installed", True)
    except ImportError:
        good &= check("pygame is installed", False,
                      "Type: py -m pip install -r requirements.txt   (Mac/Linux: python3 -m pip install -r requirements.txt)")
        pygame = None

    missing = [f for f in REQUIRED_FILES if not os.path.exists(os.path.join(HERE, f))]
    good &= check("all the project files are here", not missing,
                  "Missing: " + ", ".join(missing) + ". Re-copy the whole folder from your teacher.")

    try:
        test = os.path.join(HERE, ".write_test")
        with open(test, "w") as f:
            f.write("ok")
        os.remove(test)
        writable = True
    except OSError:
        writable = False
    good &= check("this folder can be saved into (your training results go here)", writable,
                  "Move the folder somewhere you can save, like Documents, not a read-only location or inside a zip.")

    if pygame is not None:
        try:
            pygame.init()
            pygame.font.SysFont("consolas,menlo,dejavusansmono,couriernew,monospace", 16).render("ok", True, (0, 0, 0))
            good &= check("pygame can draw text", True)
            pygame.quit()
        except Exception as err:                        # any failure here is worth reporting plainly
            good &= check("pygame can draw text", False, f"{err}")

    info = os.path.join(HERE, "BUILD-INFO.txt")
    if os.path.exists(info):
        with open(info) as f:
            print("\n  Package: " + "  ".join(line.strip() for line in f.read().splitlines()[1:]))

    print()
    if good:
        print("All good. Open menu.py and press the Run button (or F5).")
    else:
        print("Some things need fixing. Fix the PROBLEM lines above, then run this again.")
    return 0 if good else 1


if __name__ == "__main__":
    sys.exit(main())
