"""
LINE-FOLLOWING AI UNIT — TEACHER PROTOTYPE
===========================================
Two-phase project:
  Phase 1 (this file): pygame simulation. A population of virtual cars,
  each controlled by a tiny neural network, evolves over generations
  using a genetic algorithm (GA) until it can follow the track without
  crossing the border lines.

  Phase 2 (bottom of this file, commented template): port the winning
  neural network's weights to a real LEGO SPIKE Prime robot running
  Pybricks/MicroPython, using the same sensor layout and forward-pass math.

HOW TO USE
----------
1. Open this folder in VS Code and pip install pygame.
2. Run menu.py and choose "Train weights" (or run this file directly to
   go straight to training).
3. A window shows a generation of cars driving the track at once. Fitter
   cars (further along, still on track) survive to breed the next
   generation. Watch fitness improve generation over generation — this
   IS the "training."
4. When you're happy with performance, press Esc (or close the window).
   The best genome's weights print to the console and save to
   best_weights.json. Choose "Copy to Spike Robot Code" in the menu to
   bake them into spike_line_follower.py for the SPIKE Prime robot (Phase 2).

TEACHING NOTES
---------------
- A genetic algorithm is much easier for students to reason about than
  gradient-descent RL: "keep the best drivers, breed them, mutate a
  little, repeat" maps onto natural selection they already understand.
- The neural network here is deliberately tiny (2 sensors -> 6 hidden
  nodes -> 1 steering output) so students can print the weight matrix and
  see every number that "is" the trained brain.
- Sensor layout matches the real SPIKE robot: two color sensors mounted
  left/right, one riding each edge of the track, not a forward-facing
  fan. The car steers by noticing when one edge sensor loses the track.
- The sim-to-real bridge works because the sensor abstraction is kept
  identical: N light readings in, 2 motor speeds out. Whatever decided
  steering in pygame is the same math running on the robot.
"""

import pygame
import random
import math
import json
import copy

import progress
import training_view

# ----------------------------------------------------------------------
# CONFIG — tune these with students
# ----------------------------------------------------------------------
SCREEN_W, SCREEN_H = 900, 700
# CLASS-SPECIFIC: the track width and the two sensor settings below were tuned to
# match one class's physical setup (10-inch lane, sensors ~87% of the way to each
# edge). See CLASS-SPECIFIC.md.
TRACK_LINE_WIDTH = 50
POPULATION_SIZE = 40
GENERATION_TIME_LIMIT = 25.0   # seconds of sim time per generation
MUTATION_RATE = 0.12
MUTATION_STRENGTH = 0.4
NUM_SENSORS = 2                # matches the real robot: one sensor per track edge
SENSOR_SPREAD_DEG = 120        # angle between the left and right edge sensors
SENSOR_LENGTH = 25              # distance from car center to each sensor
HIDDEN_NODES = 6
CAR_SPEED = 90                 # pixels/sec forward speed (constant)
TURN_RATE = 140                # max degrees/sec steering
CHECKPOINT_RADIUS = 20         # how close a car must get to a waypoint to "pass" it
CHECKPOINT_BONUS = 50          # fitness reward per checkpoint passed
SIM_DT = 1 / 60                # simulated seconds per step -- the SAME step is used in
                               # training and in the time trial (see train() below)
TRAIN_SPEEDS = [1.0, 1.5, 2.0, 2.5, 3.0]   # every brain is tested at each of these speed
                                           # multiples; its fitness is the average

WHITE = (255, 255, 255)
BLACK = (20, 20, 20)
TRACK_COLOR = (30, 30, 30)
BG_COLOR = (245, 245, 245)


# ----------------------------------------------------------------------
# TRACK — a closed loop of waypoints. Draw as a thick black line on a
# white surface, exactly like a floor-taped LEGO track. Sensors sample
# this surface, the same way a light sensor samples the classroom floor.
# ----------------------------------------------------------------------
TRACK_NAMES = {"A": "Track A (training track)", "B": "Track B (never trained on)"}


def track_waypoints(track="A"):
    """The waypoints (a closed loop) for track "A" or "B"."""
    center_x, center_y = SCREEN_W // 2, SCREEN_H // 2
    points = []
    if track == "A":
        # An oval-ish closed loop with a couple of bends, built from an ellipse
        # warped a bit so it isn't a perfect circle (more interesting to learn).
        for deg in range(0, 360, 2):
            rad = math.radians(deg)
            rx = 340 + 15 * math.sin(rad * 3)
            ry = 250 + 25 * math.cos(rad * 6)
            points.append((center_x + rx * math.cos(rad), center_y + ry * math.sin(rad)))
        return points

    # Track B: a rounded-rectangle loop with a dent in the bottom edge. It has
    # straighter sides and tighter corners than Track A, and it is NEVER used
    # in training, so it shows how a brain copes with a track it hasn't seen.
    dense = []
    for i in range(720):
        t = 2 * math.pi * i / 720
        c, s = math.cos(t), math.sin(t)
        x = 350 * math.copysign(abs(c) ** (2 / 5.0), c)
        y = 245 * math.copysign(abs(s) ** (2 / 5.0), s)
        y -= 95 * math.exp(-((t - math.pi / 2) / 0.35) ** 2) * (1 if y > 0 else 0)   # the dent
        dense.append((center_x + x, center_y + y))
    # Space the waypoints evenly (about 11 px apart), like Track A's.
    lengths = [0.0]
    for i in range(1, len(dense) + 1):
        a, b = dense[i - 1], dense[i % len(dense)]
        lengths.append(lengths[-1] + math.hypot(b[0] - a[0], b[1] - a[1]))
    n_points = round(lengths[-1] / 11)
    j = 0
    for k in range(n_points):
        target = lengths[-1] * k / n_points
        while lengths[j + 1] < target:
            j += 1
        frac = (target - lengths[j]) / (lengths[j + 1] - lengths[j])
        a, b = dense[j], dense[(j + 1) % len(dense)]
        points.append((a[0] + (b[0] - a[0]) * frac, a[1] + (b[1] - a[1]) * frac))
    return points


def build_track_surface(track="A"):
    surface = pygame.Surface((SCREEN_W, SCREEN_H))
    surface.fill(WHITE)
    points = track_waypoints(track)
    pygame.draw.lines(surface, TRACK_COLOR, True, points, TRACK_LINE_WIDTH)
    # pygame.draw.lines doesn't join thick segments at their corners, which
    # leaves triangular notches at every bend once the line gets wide. Stamp
    # a filled circle at each waypoint to round the joints and plug them.
    for (x, y) in points:
        pygame.draw.circle(surface, TRACK_COLOR, (int(x), int(y)), TRACK_LINE_WIDTH // 2)
    return surface, points


# ----------------------------------------------------------------------
# NEURAL NETWORK — pure-python, no numpy required, so students can read
# every operation. Weights are just flat lists of floats (the "genome").
# ----------------------------------------------------------------------
class NeuralNet:
    def __init__(self, weights=None):
        self.n_in = NUM_SENSORS
        self.n_hidden = HIDDEN_NODES
        # One output: how hard to turn (-1..1). 2*6 + 6*1 = 18 weights in all.

        w1_size = self.n_in * self.n_hidden
        w2_size = self.n_hidden
        total = w1_size + w2_size

        if weights is None:
            weights = [random.uniform(-1, 1) for _ in range(total)]
        self.weights = weights

        self.w1 = [weights[i * self.n_in:(i + 1) * self.n_in] for i in range(self.n_hidden)]
        self.w2 = weights[w1_size:w1_size + self.n_hidden]

    @staticmethod
    def tanh(x):
        return math.tanh(x)

    def forward(self, sensor_values):
        hidden = []
        for h_weights in self.w1:
            total = sum(w * s for w, s in zip(h_weights, sensor_values))
            hidden.append(self.tanh(total))

        total = sum(w * h for w, h in zip(self.w2, hidden))
        return self.tanh(total)  # turn: -1 (full left) .. +1 (full right)


# ----------------------------------------------------------------------
# CAR — has two color-sensor "whiskers", one riding each edge of the
# track, matching the real robot's left/right edge sensor mounting.
# Each samples the track surface for black (on-track) vs white (off).
# ----------------------------------------------------------------------
class Car:
    def __init__(self, start_pos, start_angle, brain, track_points, speed_scale=1.0):
        self.speed_scale = speed_scale  # 1.0 in training; the time trial can raise it
        self.x, self.y = start_pos
        self.angle = start_angle  # degrees, 0 = facing right
        self.brain = brain
        self.alive = True
        self.time_alive = 0.0
        self.track_points = track_points
        self.next_checkpoint = 1
        self.checkpoints_passed = 0
        self.last_sensor_readings = [0.0] * NUM_SENSORS

    def get_sensor_positions(self):
        positions = []
        half_spread = SENSOR_SPREAD_DEG / 2
        step = SENSOR_SPREAD_DEG / (NUM_SENSORS - 1) if NUM_SENSORS > 1 else 0
        for i in range(NUM_SENSORS):
            offset_deg = -half_spread + step * i
            rad = math.radians(self.angle + offset_deg)
            sx = self.x + SENSOR_LENGTH * math.cos(rad)
            sy = self.y + SENSOR_LENGTH * math.sin(rad)
            positions.append((sx, sy))
        return positions

    def read_sensors(self, track_surface):
        readings = []
        for (sx, sy) in self.get_sensor_positions():
            if 0 <= sx < SCREEN_W and 0 <= sy < SCREEN_H:
                color = track_surface.get_at((int(sx), int(sy)))
                on_line = 1.0 if color[0] < 100 else 0.0  # dark pixel = on line
            else:
                on_line = 0.0  # off-screen counts as off-track
            readings.append(on_line)
        return readings

    def update(self, dt, track_surface):
        if not self.alive:
            return

        sensor_values = self.read_sensors(track_surface)
        self.last_sensor_readings = sensor_values

        # If NO sensor sees the line at all, the car has left the track.
        if sum(sensor_values) == 0:
            self.alive = False
            return

        turn = self.brain.forward(sensor_values)
        self.angle += turn * TURN_RATE * dt

        rad = math.radians(self.angle)
        speed = CAR_SPEED * self.speed_scale
        self.x += speed * dt * math.cos(rad)
        self.y += speed * dt * math.sin(rad)
        self.time_alive += dt

        # Advance along the track's waypoints as the car reaches them. This is
        # what actually measures line-following progress -- raw distance
        # traveled doesn't, since the car moves at constant speed regardless
        # of steering, so it can't tell a good driver from one that's merely
        # still alive.
        cx, cy = self.track_points[self.next_checkpoint]
        while math.hypot(self.x - cx, self.y - cy) < CHECKPOINT_RADIUS:
            self.checkpoints_passed += 1
            self.next_checkpoint = (self.next_checkpoint + 1) % len(self.track_points)
            cx, cy = self.track_points[self.next_checkpoint]

    def fitness(self):
        cx, cy = self.track_points[self.next_checkpoint]
        dist_to_next = math.hypot(self.x - cx, self.y - cy)
        return self.checkpoints_passed * CHECKPOINT_BONUS - dist_to_next + self.time_alive * 0.1

    def draw(self, screen):
        color = (0, 150, 0) if self.alive else (200, 0, 0)

        for (sx, sy), reading in zip(self.get_sensor_positions(), self.last_sensor_readings):
            ray_color = (0, 200, 0) if reading > 0 else (220, 80, 80)
            pygame.draw.line(screen, ray_color, (self.x, self.y), (sx, sy), 1)

        pygame.draw.circle(screen, color, (int(self.x), int(self.y)), 6)
        rad = math.radians(self.angle)
        end = (self.x + 14 * math.cos(rad), self.y + 14 * math.sin(rad))
        pygame.draw.line(screen, color, (self.x, self.y), end, 2)


# ----------------------------------------------------------------------
# INDIVIDUAL — one brain plus the copies of the car that test it, one per
# training speed. Scoring a brain at several speeds (not just normal speed)
# is what makes it keep improving at high speed: with normal-speed scoring
# alone, evolution fine-tunes to exactly 1x and loses any margin above it.
# ----------------------------------------------------------------------
class Individual:
    def __init__(self, brain, start_pos, start_angle, track_points):
        self.brain = brain
        self.cars = [Car(start_pos, start_angle, brain, track_points, speed_scale=speed)
                     for speed in TRAIN_SPEEDS]

    def fitness(self):
        return sum(car.fitness() for car in self.cars) / len(self.cars)


# ----------------------------------------------------------------------
# GENETIC ALGORITHM
# ----------------------------------------------------------------------
def crossover(parent_a, parent_b):
    child_weights = []
    for a, b in zip(parent_a.weights, parent_b.weights):
        child_weights.append(a if random.random() < 0.5 else b)
    return child_weights


def mutate(weights):
    new_weights = []
    for w in weights:
        if random.random() < MUTATION_RATE:
            w += random.uniform(-MUTATION_STRENGTH, MUTATION_STRENGTH)
        new_weights.append(w)
    return new_weights


def next_generation(individuals):
    ranked = sorted(individuals, key=lambda ind: ind.fitness(), reverse=True)
    survivors = ranked[:max(4, POPULATION_SIZE // 5)]  # top 20%

    new_brains = [NeuralNet(copy.deepcopy(survivors[0].brain.weights))]  # keep champion unmutated
    while len(new_brains) < POPULATION_SIZE:
        parent_a = random.choice(survivors)
        parent_b = random.choice(survivors)
        child_weights = mutate(crossover(parent_a.brain, parent_b.brain))
        new_brains.append(NeuralNet(child_weights))

    return new_brains, ranked[0]


# ----------------------------------------------------------------------
# TRAINING SCENARIO — many cars, many generations. Returns True if the
# player closed the window (so the caller should quit), False if they
# pressed Esc to go back to the menu.
# ----------------------------------------------------------------------
def save_results(best_brain, best_fitness, generations):
    print("\nBest genome weights (copy these to the robot):")
    print(best_brain.weights)
    with open(progress.WEIGHTS_PATH, "w") as f:
        json.dump(best_brain.weights, f)
    progress.record_training(generations, best_fitness)
    print(f"Saved to best_weights.json  (best fitness: {best_fitness:.1f}, "
          f"{generations} generations)")
    print("To put these on your robot, choose 'Copy to Spike Robot Code' in menu.py.")


def train(screen):
    from hover_tips import HoverTips      # imported here: that module imports this one
    tips = HoverTips()                    # glossary hover tips and links on this screen
    pygame.display.set_caption("Line Follower AI — training")
    clock = pygame.time.Clock()
    font = pygame.font.SysFont("consolas,menlo,dejavusansmono,couriernew,monospace", 18)
    small_font = pygame.font.SysFont("consolas,menlo,dejavusansmono,couriernew,monospace", 14)

    track_surface, track_points = build_track_surface()
    start_pos = track_points[0]
    next_pos = track_points[1]
    start_angle = math.degrees(math.atan2(next_pos[1] - start_pos[1], next_pos[0] - start_pos[0]))

    brains = [NeuralNet() for _ in range(POPULATION_SIZE)]
    generation = 1
    best_ever = None
    best_ever_fitness = -1
    window_closed = False
    lap_checkpoints = len(track_points)   # passing every waypoint once = one full lap
    history = []                          # (champion fitness, average fitness) per generation
    laps = []                             # did the champion finish a lap at each training speed?
    lap_fraction = 0.0
    last_gain_gen = 0                     # generation when the champion last improved
    solved_gen = None                     # first generation whose champion lapped at every speed

    running = True
    while running:
        individuals = [Individual(brain, start_pos, start_angle, track_points) for brain in brains]
        all_cars = [car for ind in individuals for car in ind.cars]
        shown_cars = [ind.cars[0] for ind in individuals]   # draw only the normal-speed cars
        gen_timer = 0.0

        while gen_timer < GENERATION_TIME_LIMIT and running:
            # Fixed step, not the real frame time. If the step varied with how
            # fast the laptop drew each frame, evolution would tune cars to
            # that jitter and they'd drive differently in the time trial.
            clock.tick(60)
            dt = SIM_DT
            gen_timer += dt

            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    running = False
                    window_closed = True
                elif event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
                    running = False
                elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                    closed = tips.click(screen, event.pos)       # a glossary term was clicked?
                    if closed:
                        running = False
                        window_closed = True

            for car in all_cars:
                car.update(dt, track_surface)

            if all(not c.alive for c in all_cars):
                break  # everyone crashed, no point waiting out the timer

            screen.blit(track_surface, (0, 0))
            tips.begin()
            for car in shown_cars:
                car.draw(screen)

            alive_count = sum(1 for c in shown_cars if c.alive)
            best_checkpoints = max(c.checkpoints_passed for c in shown_cars)
            tips.segments(screen, font, [
                (f"Gen {generation}", "Generation"),
                (f"alive {alive_count}/{POPULATION_SIZE}", "Population"),
                (f"best-ever fitness {best_ever_fitness:.0f}", "Fitness"),
                (f"checkpoints this gen {best_checkpoints}", "Checkpoint")], (10, 10), BLACK)
            training_view.draw_progress_panel(
                screen, small_font, history, TRAIN_SPEEDS, laps, lap_fraction,
                generation - 1 - last_gain_gen if history else 0, tips)
            tips.segments(screen, font, [
                (f"Also tested at {TRAIN_SPEEDS[1]:g}x-{TRAIN_SPEEDS[-1]:g}x speed (not shown).", "Speed multiplier"),
                ("Esc = save and menu", None)], (10, SCREEN_H - 28), BLACK, sep="   ")
            tips.draw(screen)
            pygame.display.flip()

        if not running:
            break

        scores = [ind.fitness() for ind in individuals]
        brains, gen_best = next_generation(individuals)
        if gen_best.fitness() > best_ever_fitness:
            if gen_best.fitness() > best_ever_fitness + 1e-9:
                last_gain_gen = generation
            best_ever_fitness = gen_best.fitness()
            best_ever = gen_best.brain

        history.append((gen_best.fitness(), sum(scores) / len(scores)))
        laps = [car.checkpoints_passed >= lap_checkpoints for car in gen_best.cars]
        lap_fraction = min(gen_best.cars[0].checkpoints_passed, lap_checkpoints) / lap_checkpoints
        if all(laps) and solved_gen is None:
            solved_gen = generation
            print(f"Solved in generation {generation}: the champion finishes a lap "
                  f"at every training speed.")

        generation += 1

    completed = generation - 1   # the generation in progress when you quit doesn't count
    if best_ever:
        save_results(best_ever, best_ever_fitness, completed)
    else:
        print("\nNo full generation finished, so nothing was saved.")
    return window_closed


def main():
    pygame.init()
    screen = pygame.display.set_mode((SCREEN_W, SCREEN_H), pygame.SCALED | pygame.RESIZABLE)
    train(screen)
    pygame.quit()


if __name__ == "__main__":
    main()


# ========================================================================
# PHASE 2 — SPIKE PRIME PORT TEMPLATE (Pybricks / MicroPython)
# ========================================================================
# This is NOT meant to run as part of the file above — copy it into a
# separate SPIKE Prime project once you have weights from Phase 1.
#
# Key idea: same sensor count in, same forward-pass math, same weights.
# The robot doesn't "train" — it just runs the brain you already evolved.
#
# Wiring assumption: NUM_SENSORS=2 color sensors mounted left/right on the
# front of the car, one riding each edge of the track (not a forward fan).
#
# """
# from pybricks.hubs import PrimeHub
# from pybricks.pupdevices import Motor, ColorSensor
# from pybricks.parameters import Port, Direction, Color
# from pybricks.tools import wait, StopWatch
# import math, json
#
# hub = PrimeHub()
# left_motor = Motor(Port.A)
# right_motor = Motor(Port.E)
# left_sensor = ColorSensor(Port.F)
# right_sensor = ColorSensor(Port.B)
#
# # Paste the printed weights list from best_weights.json here:
# WEIGHTS = [ ... ]
# N_IN = 2      # must match NUM_SENSORS in the simulation
# N_HIDDEN = 6  # must match HIDDEN_NODES in the simulation
# N_OUT = 1
#
# w1_size = N_IN * N_HIDDEN
# W1 = [WEIGHTS[i * N_IN:(i + 1) * N_IN] for i in range(N_HIDDEN)]
# W2 = WEIGHTS[w1_size:w1_size + N_HIDDEN]
#
# def forward(sensor_values):
#     hidden = [math.tanh(sum(w * s for w, s in zip(h_w, sensor_values))) for h_w in W1]
#     return math.tanh(sum(w * h for w, h in zip(W2, hidden)))  # turn
#
# BASE_SPEED = 200  # deg/sec, tune for your gearing
#
# def drive_step():
#     # Tape marks the track's edges; the floor between them is the safe
#     # lane. Reflection ABOVE ~30% is treated as "on the floor" (safe) --
#     # calibrate this threshold to your classroom floor and tape first.
#     if left_sensor.color() == Color.RED or right_sensor.color() == Color.RED:
#         return True
#     readings = [1.0 if left_sensor.reflection() > 30 else 0.0,
#                 1.0 if right_sensor.reflection() > 30 else 0.0]
#     turn = forward(readings)
#     # turn > 0 = steer right (matches the simulation's own convention) =
#     # left wheel faster, right wheel slower
#     left_motor.run(BASE_SPEED * (1 + turn))
#     right_motor.run(BASE_SPEED * (1 - turn))
#     return False
#
# # Robot starts with both sensors on a green start stripe; the clock starts
# # once it's clear of green, and stops the instant a sensor sees red.
# while left_sensor.color() == Color.GREEN or right_sensor.color() == Color.GREEN:
#     drive_step()
#     wait(20)
# watch = StopWatch()
# finished = False
# while not finished:
#     finished = drive_step()
#     wait(20)
# left_motor.brake()
# right_motor.brake()
# print(f"Finished in {watch.time() / 1000:.2f} seconds")
# """
