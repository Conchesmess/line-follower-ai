"""
LINE FOLLOWER AI — MAIN MENU
=============================
Run this file to get started. Choose:

  1) Train weights  - many cars evolve over generations (line_follower_ai.py)
  2) Time trial     - one car runs one lap for a time   (time_trial.py)
  3) Start over     - delete the trained weights and all progress
  4) Rules vs weights - compare the rule you wrote with your trained weights
  5) Glossary       - look up a word used in this unit
  6) Copy to Spike Robot Code - write the weights into spike_line_follower.py (later in the year)

Pick with the 1-6 keys, the arrow keys + Enter, or a mouse click.
The panel at the bottom is your written evidence: whether trained weights
exist, how much training produced them, your fastest lap at each speed, and
whether the robot file has your latest weights.
"""

import os
import sys
from datetime import datetime

try:
    import pygame
except ImportError:
    sys.exit("The pygame library isn't installed yet.\n"
             "In the VS Code terminal type:  py -m pip install -r requirements.txt\n"
             "(Mac/Linux: python3 -m pip install -r requirements.txt)\n"
             "Then run check_setup.py to confirm everything is ready.")

import progress
import time_trial
import brain_viewer
import glossary_viewer
from line_follower_ai import SCREEN_W, SCREEN_H, BG_COLOR, BLACK, train

GREY = (130, 130, 130)
GREEN = (0, 120, 0)
RED = (200, 0, 0)
HIGHLIGHT = (225, 235, 250)

OPTIONS = [
    ("1", "Train weights", "Cars evolve over many generations. Esc saves and returns here."),
    ("2", "Time trial", "One car drives one lap. Press T for Track B, a track it never trained on."),
    ("3", "Start over", "Delete your trained weights and best times."),
    # CLASS-SPECIFIC: option 4 refers to "the rule you wrote" (see CLASS-SPECIFIC.md)
    ("4", "Rules vs weights", "See how the rule you wrote and your trained weights make the same decision."),
    ("5", "Glossary", "Look up a word used in this unit."),
    ("6", "Copy to Spike Robot Code", "Write your trained weights into spike_line_follower.py."),
]
ROW_TOP, ROW_H = 106, 54


def weights_summary():
    """Returns (lines, has_weights) describing what's on disk, for the panel."""
    weights = progress.load_weights()
    info = progress.load_progress()
    lines = []
    if weights is None:
        lines.append(("No trained weights yet — choose 1 to train.", GREY))
    else:
        lines.append((f"Trained weights saved: {len(weights)} numbers in best_weights.json", GREEN))
        if info["training_sessions"]:
            when = datetime.fromisoformat(info["trained_at"]).strftime("%b %d, %I:%M %p").replace(" 0", " ")
            lines.append((f"Trained for {info['generations_trained']} generations over "
                          f"{info['training_sessions']} training session(s)", BLACK))
            lines.append((f"Best fitness {info['best_fitness']:.0f}  |  last saved {when}", BLACK))
        else:
            lines.append(("(saved before progress tracking began, so no training history)", GREY))
    if weights is not None:
        in_robot = progress.read_spike_weights()
        if in_robot is None:
            lines.append(("spike_line_follower.py: not found next to menu.py", RED))
        elif in_robot == weights:
            lines.append(("spike_line_follower.py: has your saved weights", GREEN))
        else:
            lines.append(("spike_line_follower.py: does NOT have your saved weights yet (choose 6)", RED))
    for track, label in (("A", "Track A laps: "), ("B", "Track B laps: ")):
        times = sorted((float(k), v) for k, v in info[progress.times_field(track)].items())
        if not times:
            hint = "none yet" if track == "A" else "none yet (time trial, press T)"
            lines.append((label + hint, GREY))
        else:
            entries = [f"{speed:g}x {seconds:.2f}s" for speed, seconds in times]
            for i in range(0, len(entries), 4):
                prefix = label if i == 0 else " " * len(label)
                lines.append((prefix + "   ".join(entries[i:i + 4]), BLACK))
    return lines, weights


def draw_menu(screen, fonts, selected, confirming, message):
    title_font, font, small_font = fonts
    screen.fill(BG_COLOR)
    screen.blit(title_font.render("Line Follower AI", True, BLACK), (60, 50))

    lines, weights = weights_summary()
    has_weights = weights is not None

    for i, (key, label, desc) in enumerate(OPTIONS):
        rect = pygame.Rect(50, ROW_TOP + i * ROW_H, SCREEN_W - 100, ROW_H - 6)
        disabled = (label == "Copy to Spike Robot Code" and not has_weights) or (label == "Start over" and not progress_exists())
        if i == selected and not confirming:
            pygame.draw.rect(screen, HIGHLIGHT, rect, border_radius=8)
        color = GREY if disabled else BLACK
        screen.blit(font.render(f"{key})  {label}", True, color), (rect.x + 15, rect.y + 8))
        screen.blit(small_font.render(desc, True, GREY), (rect.x + 50, rect.y + 34))

    # written evidence panel
    panel = pygame.Rect(50, ROW_TOP + len(OPTIONS) * ROW_H + 8, SCREEN_W - 100, 208)
    pygame.draw.rect(screen, (255, 255, 255), panel, border_radius=8)
    pygame.draw.rect(screen, GREY, panel, 1, border_radius=8)
    y = panel.y + 12
    for text, color in lines:
        screen.blit(small_font.render(text, True, color), (panel.x + 15, y))
        y += 20
    if has_weights:
        y += 6
        for row in range(0, len(weights), 8):
            chunk = "  ".join(f"{w:6.2f}" for w in weights[row:row + 8])
            screen.blit(small_font.render(chunk, True, GREY), (panel.x + 15, y))
            y += 20

    if confirming:
        text = "Delete weights and best times?  Y = yes, N = no"
        screen.blit(font.render(text, True, RED), (50, SCREEN_H - 36))
    elif message:
        screen.blit(font.render(message[0], True, message[1]), (50, SCREEN_H - 36))
    pygame.display.flip()


def progress_exists():
    return os.path.exists(progress.PROGRESS_PATH) or os.path.exists(progress.WEIGHTS_PATH)


def main():
    pygame.init()
    screen = pygame.display.set_mode((SCREEN_W, SCREEN_H), pygame.SCALED | pygame.RESIZABLE)
    clock = pygame.time.Clock()
    fonts = (pygame.font.SysFont("consolas,menlo,dejavusansmono,couriernew,monospace", 40, bold=True),
             pygame.font.SysFont("consolas,menlo,dejavusansmono,couriernew,monospace", 24, bold=True),
             pygame.font.SysFont("consolas,menlo,dejavusansmono,couriernew,monospace", 16))

    selected = 0
    confirming = False
    message = None

    def activate(index):
        """Runs option `index`. Returns True if the window was closed."""
        nonlocal confirming, message
        message = None
        name = OPTIONS[index][1]       # act on the option's name, so reordering the menu is safe
        if name == "Train weights":
            return train(screen)
        if name == "Time trial":
            weights = progress.load_weights()
            if weights is None:
                # No brain yet: run an untrained (random) car, a handy example of a failed run.
                return time_trial.run_time_trial(screen, None)
            try:
                time_trial.check_weights(weights)
            except ValueError as err:
                message = (f"Can't time trial: {err}", RED)
                return False
            return time_trial.run_time_trial(screen, weights)
        if name == "Copy to Spike Robot Code":
            weights = progress.load_weights()
            if weights is None:
                message = ("No trained weights yet — run option 1 first.", RED)
            elif progress.export_spike_weights(weights):
                message = (f"Copied {len(weights)} weights into spike_line_follower.py", GREEN)
            else:
                message = ("Couldn't find spike_line_follower.py next to menu.py", RED)
            return False
        if name == "Start over":
            if progress_exists():
                confirming = True
            else:
                message = ("Nothing to delete.", GREY)
        if name == "Rules vs weights":
            return brain_viewer.run_brain_viewer(screen, progress.load_weights())
        if name == "Glossary":
            return glossary_viewer.run_glossary_viewer(screen)
        return False

    running = True
    while running:
        clock.tick(30)
        pygame.display.set_caption("Line Follower AI — menu")
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            elif event.type == pygame.KEYDOWN:
                if confirming:
                    if event.key == pygame.K_y:
                        progress.start_over()
                        confirming = False
                        message = ("Started over. Weights and best times deleted.", GREEN)
                    elif event.key in (pygame.K_n, pygame.K_ESCAPE):
                        confirming = False
                    continue
                if event.key in (pygame.K_1, pygame.K_2, pygame.K_3, pygame.K_4, pygame.K_5, pygame.K_6):
                    selected = event.key - pygame.K_1
                    running = not activate(selected)
                elif event.key == pygame.K_UP:
                    selected = (selected - 1) % len(OPTIONS)
                elif event.key == pygame.K_DOWN:
                    selected = (selected + 1) % len(OPTIONS)
                elif event.key in (pygame.K_RETURN, pygame.K_KP_ENTER):
                    running = not activate(selected)
                elif event.key == pygame.K_ESCAPE:
                    running = False
            elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1 and not confirming:
                for i in range(len(OPTIONS)):
                    if pygame.Rect(50, ROW_TOP + i * ROW_H, SCREEN_W - 100, ROW_H - 6).collidepoint(event.pos):
                        selected = i
                        running = not activate(i)
            if not running:
                break

        if running:
            draw_menu(screen, fonts, selected, confirming, message)

    pygame.quit()


if __name__ == "__main__":
    main()
