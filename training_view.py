"""
TRAINING PROGRESS PANEL
=======================
Draws the "how is training going, and am I done yet?" panel in the middle of
the training window (inside the oval of the track, where no car ever drives).

It shows three things:
  1. A fitness curve: the champion's fitness and the population average,
     one point per generation.
  2. A speed checklist: has the champion completed a lap at each training
     speed? When every box is green, training is SOLVED.
  3. A lap progress bar for the champion at normal speed.

This file only draws. line_follower_ai.py decides what the numbers are.
"""

import pygame

# Panel position/size. Sized to fit inside the track's inner oval.
PANEL_RECT = pygame.Rect(250, 225, 400, 250)

PLATEAU_GENERATIONS = 15      # no gain in the champion's fitness for this many generations

PANEL_BG = (250, 250, 250)
PANEL_BORDER = (160, 160, 160)
TEXT = (20, 20, 20)
MUTED = (110, 110, 110)
GRID = (225, 225, 225)
BEST_COLOR = (0, 140, 60)
AVG_COLOR = (70, 120, 200)
GOOD = (0, 160, 70)
EMPTY = (215, 215, 215)
WARN = (200, 120, 0)


def status_for(history, laps, gens_since_gain):
    """Return (label, color) describing where training stands."""
    if laps and all(laps):
        return "SOLVED - Esc to save", GOOD
    if gens_since_gain >= PLATEAU_GENERATIONS:
        return f"Plateau: no gain in {gens_since_gain} gens", WARN
    if not history:
        return "Waiting for generation 1...", MUTED
    return "Learning...", MUTED


def draw_progress_panel(screen, small, history, speeds, laps, lap_fraction, gens_since_gain, tips=None):
    """
    history          list of (champion_fitness, average_fitness), one per generation
    speeds           the training speed multipliers, e.g. [1.0, 1.5, ...]
    laps             list of bool, one per speed: did the champion finish a lap?
                     (empty before generation 1 has finished)
    lap_fraction     0..1, how much of a lap the champion covered at normal speed
    gens_since_gain  generations since the champion's fitness last improved
    tips             optional HoverTips: terms in this panel link to the glossary
    """
    r = PANEL_RECT
    pygame.draw.rect(screen, PANEL_BG, r, border_radius=8)
    pygame.draw.rect(screen, PANEL_BORDER, r, 2, border_radius=8)

    label, label_color = status_for(history, laps, gens_since_gain)
    def mark(rect, term, click=True):
        if tips is not None:
            tips.add(rect, term, click)

    mark(screen.blit(small.render("Training progress", True, TEXT), (r.x + 12, r.y + 8)), "Training")
    status = small.render(label, True, label_color)
    status_rect = screen.blit(status, (r.right - status.get_width() - 12, r.y + 8))
    if label.startswith("SOLVED"):
        mark(status_rect, "Solved")
    elif label.startswith("Plateau"):
        mark(status_rect, "Plateau")

    # ---- fitness curve ------------------------------------------------
    chart = pygame.Rect(r.x + 52, r.y + 34, r.w - 70, 100)
    pygame.draw.rect(screen, (255, 255, 255), chart)
    pygame.draw.rect(screen, GRID, chart, 1)
    mark(chart, "Fitness", click=False)

    if history:
        values = [v for pair in history for v in pair]
        lo, hi = min(values), max(values)
        if hi - lo < 1:
            hi = lo + 1
        n_x = max(len(history), 10)

        def to_xy(i, v):
            x = chart.x + 6 + (chart.w - 12) * i / max(n_x - 1, 1)
            y = chart.bottom - 6 - (chart.h - 12) * (v - lo) / (hi - lo)
            return (x, y)

        for series, color in ((1, AVG_COLOR), (0, BEST_COLOR)):
            pts = [to_xy(i, pair[series]) for i, pair in enumerate(history)]
            if len(pts) > 1:
                pygame.draw.lines(screen, color, False, pts, 2)
            pygame.draw.circle(screen, color, (int(pts[-1][0]), int(pts[-1][1])), 3)

        screen.blit(small.render(f"{hi:.0f}", True, MUTED), (r.x + 8, chart.y - 2))
        screen.blit(small.render(f"{lo:.0f}", True, MUTED), (r.x + 8, chart.bottom - 14))
    else:
        msg = small.render("fitness curve appears after generation 1", True, MUTED)
        screen.blit(msg, (chart.centerx - msg.get_width() // 2, chart.centery - 8))

    # legend + generation axis label
    ly = chart.bottom + 4
    pygame.draw.line(screen, BEST_COLOR, (chart.x, ly + 8), (chart.x + 16, ly + 8), 2)
    mark(screen.blit(small.render("champion", True, TEXT), (chart.x + 20, ly)), "Champion")
    pygame.draw.line(screen, AVG_COLOR, (chart.x + 100, ly + 8), (chart.x + 116, ly + 8), 2)
    mark(screen.blit(small.render("average", True, TEXT), (chart.x + 120, ly)), "Average fitness")
    gen_label = small.render("generation >", True, MUTED)
    mark(screen.blit(gen_label, (chart.right - gen_label.get_width(), ly)), "Generation")

    # ---- speed checklist ----------------------------------------------
    cy = r.y + 164
    mark(screen.blit(small.render("Champion laps at:", True, TEXT), (r.x + 12, cy)), "Champion")
    box_w, gap = 46, 4
    bx = r.x + 148
    for i, speed in enumerate(speeds):
        done = bool(laps) and laps[i]
        rect = pygame.Rect(bx + i * (box_w + gap), cy - 3, box_w, 22)
        pygame.draw.rect(screen, GOOD if done else EMPTY, rect, border_radius=4)
        mark(rect, "Speed multiplier", click=False)
        text = small.render(f"{speed:g}x", True, (255, 255, 255) if done else MUTED)
        screen.blit(text, (rect.centerx - text.get_width() // 2, rect.y + 3))

    # ---- lap progress bar ---------------------------------------------
    py = r.y + 200
    mark(screen.blit(small.render("Lap (1x):", True, TEXT), (r.x + 12, py)), "Progress bar (Lap)")
    bar = pygame.Rect(r.x + 150, py + 1, r.w - 150 - 62, 16)
    pygame.draw.rect(screen, EMPTY, bar, border_radius=4)
    fill = bar.copy()
    fill.w = int(bar.w * max(0.0, min(1.0, lap_fraction)))
    if fill.w > 0:
        pygame.draw.rect(screen, GOOD, fill, border_radius=4)
    pct = small.render(f"{lap_fraction * 100:.0f}%", True, TEXT)
    screen.blit(pct, (bar.right + 8, py))

    hint = small.render("Done = champion finishes a lap at every speed", True, MUTED)
    screen.blit(hint, (r.x + 12, r.bottom - 22))
