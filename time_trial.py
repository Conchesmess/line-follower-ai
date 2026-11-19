# SPDX-License-Identifier: PolyForm-Noncommercial-1.0.0  (see LICENSE-CODE)
"""
TIME TRIAL — ONE CAR, ONE LAP
==============================
Scenario 2 of the simulation. Nothing is learned here: a single car with the
trained brain from best_weights.json drives one lap and we record how long
it took. This is the simulated version of the race on the real track.

Scenario 1 (training many cars over many generations) lives in
line_follower_ai.py. Run that first to create best_weights.json.

HOW TO USE
----------
1. Train first (menu.py option 1, or run line_follower_ai.py directly).
2. Run this file. The car starts on the start line and the clock runs until
   it has driven all the way around and crossed the start/finish line again.
3. Press R to run again, T to switch between Track A (the one the cars
   trained on) and Track B (a track they have never seen), or Esc / close
   the window to leave.
4. Change the speed with the slider at the bottom (drag it, or use the
   left/right arrow keys). Faster laps are quicker but harder: the car
   still steers at the same rate, so at high speed it takes wider turns and
   is more likely to leave the track. Your fastest lap at each speed is
   remembered in progress.json.

(This is also option 2 in menu.py.) To time a different weights file when
running this file directly, pass its name:
    python time_trial.py my_weights.json

FAIR TIMING
-----------
The clock advances by a fixed step every frame (FIXED_DT), not by however
much real time the laptop took to draw the frame. Training uses the very same
step, so the same weights always drive the same way, and give the same lap
time, on any computer.
"""

import json
import math
import sys

import pygame

import progress
from hover_tips import HoverTips

from line_follower_ai import (
    SCREEN_W, SCREEN_H, BLACK, NUM_SENSORS, HIDDEN_NODES,
    SIM_DT, BG_COLOR, build_track_surface, NeuralNet, Car, TRACK_NAMES,
)

FIXED_DT = SIM_DT          # same step as training, so a brain drives here as it did there
TIME_LIMIT = 120.0         # give up after this many sim seconds at 1x speed (DNF)
STUCK_LIMIT = 15.0         # ...or after this long without a new checkpoint at 1x speed
# Both limits are stretched by 1/speed, so a slow car gets proportionally more
# time and is never penalised just for going slowly.

SPEEDS = [0.5 + 0.25 * i for i in range(11)]   # 0.5x ... 3x
DEFAULT_SPEED_INDEX = SPEEDS.index(1.0)
SLIDER_X0, SLIDER_X1, SLIDER_Y = 250, 650, 674


def check_weights(weights):
    expected = NUM_SENSORS * HIDDEN_NODES + HIDDEN_NODES
    if len(weights) != expected:
        raise ValueError(f"the saved weights have {len(weights)} numbers but this "
                         f"simulation needs {expected}. Retrain to fix this.")


def start_state(track_points):
    start_pos = track_points[0]
    nx, ny = track_points[1]
    start_angle = math.degrees(math.atan2(ny - start_pos[1], nx - start_pos[0]))
    return start_pos, start_angle


def draw_start_line(screen, track_points):
    """A short bar across the track at the start/finish point."""
    (x, y), (nx, ny) = track_points[0], track_points[1]
    heading = math.atan2(ny - y, nx - x)
    px, py = -math.sin(heading), math.cos(heading)   # perpendicular to the track
    half = 32
    pygame.draw.line(screen, (0, 170, 0), (x - px * half, y - py * half), (x + px * half, y + py * half), 4)


def slider_index_at(mouse_x):
    """Nearest speed step for a mouse x position along the slider."""
    frac = (mouse_x - SLIDER_X0) / (SLIDER_X1 - SLIDER_X0)
    return max(0, min(len(SPEEDS) - 1, round(frac * (len(SPEEDS) - 1))))


def draw_slider(screen, font, speed_index, tips=None):
    pygame.draw.rect(screen, BG_COLOR, (0, SLIDER_Y - 22, SCREEN_W, 44))
    pygame.draw.line(screen, (150, 150, 150), (SLIDER_X0, SLIDER_Y), (SLIDER_X1, SLIDER_Y), 4)
    for i in range(len(SPEEDS)):
        x = SLIDER_X0 + (SLIDER_X1 - SLIDER_X0) * i / (len(SPEEDS) - 1)
        pygame.draw.line(screen, (150, 150, 150), (x, SLIDER_Y - 6), (x, SLIDER_Y + 6), 2)
    knob_x = SLIDER_X0 + (SLIDER_X1 - SLIDER_X0) * speed_index / (len(SPEEDS) - 1)
    pygame.draw.circle(screen, (40, 90, 200), (knob_x, SLIDER_Y), 10)
    label = screen.blit(font.render("Speed", True, BLACK), (SLIDER_X0 - 80, SLIDER_Y - 10))
    if tips is not None:
        tips.add(label, "Speed multiplier")
    screen.blit(font.render(f"{SPEEDS[speed_index]:g}x", True, BLACK), (SLIDER_X1 + 20, SLIDER_Y - 10))


def run_time_trial(screen, weights, record=True):
    """Runs laps until the player leaves. Returns True if they closed the
    window (the caller should quit), False for Esc (back to the menu).
    record=False skips saving lap times to progress.json.
    weights=None runs an UNTRAINED car: a fresh random brain every run, which
    is what generation 1 of training starts with. It never records a time."""
    untrained = weights is None
    if untrained:
        record = False
    pygame.display.set_caption("Line Follower AI — time trial")
    clock = pygame.time.Clock()
    font = pygame.font.SysFont("consolas,menlo,dejavusansmono,couriernew,monospace", 18)
    big_font = pygame.font.SysFont("consolas,menlo,dejavusansmono,couriernew,monospace", 40, bold=True)

    track = "A"
    track_surface, track_points = build_track_surface(track)
    start_pos, start_angle = start_state(track_points)
    lap_checkpoints = len(track_points)   # passing every waypoint once = one full lap

    speed_index = DEFAULT_SPEED_INDEX
    dragging = False
    tips = HoverTips()          # glossary hover tips and links on this screen

    def new_run():
        brain = NeuralNet() if untrained else NeuralNet(list(weights))
        return Car(start_pos, start_angle, brain, track_points,
                   speed_scale=SPEEDS[speed_index]), 0.0

    last_checkpoints, last_progress_time = 0, 0.0

    car, sim_time = new_run()
    result = None   # None while running, else ("finished" | "crashed" | "stuck" | "timeout", seconds)
    all_best = progress.load_progress()
    best_times = all_best[progress.times_field(track)]   # fastest lap at each speed on this track, across sessions
    new_record = False
    window_closed = False

    running = True
    while running:
        clock.tick(60)
        restart = False
        for event in pygame.event.get():
            if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                closed = tips.click(screen, event.pos)           # a glossary term was clicked?
                if closed is not None:
                    if closed:
                        running, window_closed = False, True
                    continue
            if event.type == pygame.QUIT:
                running = False
                window_closed = True
            elif event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
                running = False
            elif event.type == pygame.KEYDOWN and event.key == pygame.K_r:
                restart = True
            elif event.type == pygame.KEYDOWN and event.key == pygame.K_t:
                track = "B" if track == "A" else "A"
                track_surface, track_points = build_track_surface(track)
                start_pos, start_angle = start_state(track_points)
                lap_checkpoints = len(track_points)
                best_times = all_best[progress.times_field(track)]
                restart = True
            elif event.type == pygame.KEYDOWN and event.key in (pygame.K_LEFT, pygame.K_DOWN):
                if speed_index > 0:
                    speed_index -= 1
                    restart = True
            elif event.type == pygame.KEYDOWN and event.key in (pygame.K_RIGHT, pygame.K_UP):
                if speed_index < len(SPEEDS) - 1:
                    speed_index += 1
                    restart = True
            elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1 \
                    and abs(event.pos[1] - SLIDER_Y) < 20 and SLIDER_X0 - 15 < event.pos[0] < SLIDER_X1 + 15:
                dragging = True
            elif event.type == pygame.MOUSEBUTTONUP and event.button == 1:
                dragging = False
            if dragging and event.type in (pygame.MOUSEBUTTONDOWN, pygame.MOUSEMOTION):
                new_index = slider_index_at(event.pos[0])
                if new_index != speed_index:
                    speed_index = new_index
                    restart = True

        if restart:
            car, sim_time = new_run()
            last_checkpoints, last_progress_time = 0, 0.0
            result = None
            new_record = False

        if result is None:
            car.update(FIXED_DT, track_surface)
            sim_time += FIXED_DT
            if car.checkpoints_passed > last_checkpoints:
                last_checkpoints, last_progress_time = car.checkpoints_passed, sim_time
            if car.checkpoints_passed >= lap_checkpoints:
                result = ("finished", sim_time)
                speed_name = progress.speed_key(SPEEDS[speed_index])
                best_time = best_times.get(speed_name)
                new_record = best_time is None or sim_time < best_time
                if new_record:
                    best_times[speed_name] = sim_time
                    if record:
                        progress.record_lap_time(sim_time, SPEEDS[speed_index], track)
                print(f"Lap time: {sim_time:.2f} seconds" + ("  (new best!)" if new_record else ""))
            elif not car.alive:
                result = ("crashed", sim_time)
                print(f"Left the track after {sim_time:.2f} seconds (no lap time).")
            elif sim_time - last_progress_time >= STUCK_LIMIT / SPEEDS[speed_index]:
                result = ("stuck", sim_time)
                print(f"Stuck: no progress for {STUCK_LIMIT / SPEEDS[speed_index]:.0f} seconds (no lap time).")
            elif sim_time >= TIME_LIMIT / SPEEDS[speed_index]:
                result = ("timeout", sim_time)
                print(f"Did not finish within {TIME_LIMIT / SPEEDS[speed_index]:.0f} seconds.")

        screen.blit(track_surface, (0, 0))
        tips.begin()
        draw_start_line(screen, track_points)
        car.draw(screen)

        lap_fraction = min(car.checkpoints_passed, lap_checkpoints) / lap_checkpoints
        hud = [(TRACK_NAMES[track], "Track A / Track B"),
               (f"Time {sim_time:6.2f}s", "Lap time"),
               (f"lap {lap_fraction:4.0%}", "Lap")]
        best_here = best_times.get(progress.speed_key(SPEEDS[speed_index]))
        if best_here is not None:
            hud.append((f"best at {SPEEDS[speed_index]:g}x: {best_here:.2f}s", "Lap time"))
        tips.segments(screen, font, hud, (10, 10))
        controls = "Left/Right = speed    T = other track    R = run again    Esc = back"
        if untrained:
            controls = controls.replace("run again", "new random brain")
        screen.blit(font.render(controls, True, BLACK), (10, 34))
        if untrained:
            tips.add(screen.blit(font.render("UNTRAINED (random weights)", True, (200, 0, 0)), (10, 56)), "Untrained")
        draw_slider(screen, font, speed_index, tips)

        if result is not None:
            kind, seconds = result
            if kind == "finished":
                headline, color = f"Lap time: {seconds:.2f} s", (0, 120, 0)
                if new_record:
                    headline += "  New best!"
            elif kind == "crashed":
                headline, color = "Left the track — no time", (200, 0, 0)
            elif kind == "stuck":
                headline, color = "Stuck — no time", (200, 0, 0)
            else:
                headline, color = "Did not finish", (200, 0, 0)
            text = big_font.render(headline, True, color)
            tips.add(screen.blit(text, text.get_rect(center=(SCREEN_W // 2, SCREEN_H // 2))),
                     {"finished": "Lap time", "crashed": "Crashed", "stuck": "Stuck", "timeout": "Timeout"}[kind])

        tips.draw(screen)
        pygame.display.flip()

    return window_closed


def main():
    weights_path = sys.argv[1] if len(sys.argv) > 1 else progress.WEIGHTS_PATH
    try:
        with open(weights_path) as f:
            weights = json.load(f)
        check_weights(weights)
    except FileNotFoundError:
        sys.exit(f"Couldn't find {weights_path}. Train a car first (menu.py, option 1).")
    except ValueError as err:
        sys.exit(f"Problem with {weights_path}: {err}")

    pygame.init()
    screen = pygame.display.set_mode((SCREEN_W, SCREEN_H), pygame.SCALED | pygame.RESIZABLE)
    # A custom weights file isn't the student's own brain, so only the
    # default file's laps count toward their saved best time.
    run_time_trial(screen, weights, record=(weights_path == progress.WEIGHTS_PATH))
    pygame.quit()


if __name__ == "__main__":
    main()
