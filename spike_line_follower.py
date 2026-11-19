"""
LINE-FOLLOWING AI — PHASE 2: SPIKE PRIME ROBOT
================================================
Runs the neural network evolved in line_follower_ai.py (Phase 1) on a real
LEGO SPIKE Prime robot. The robot does NOT train anything here — it just
runs the same multiply-add-squash math as the simulation, using the
weights that simulation already evolved (pasted in below from
best_weights.json).

This file only works on the SPIKE hub running Pybricks firmware. It will
not run on a regular computer — the pybricks module doesn't exist there.

WIRING
------
  Left motor              -> Port A
  Right motor              -> Port E
  Left edge color sensor   -> Port F
  Right edge color sensor  -> Port B

Mount the two color sensors side by side at the front of the robot, one
riding each edge of the track, matching the simulation's sensor layout
(NUM_SENSORS=2 in line_follower_ai.py).

TRACK
-----
Two strips of black tape mark the track's edges; the floor between them
(e.g. linoleum) is the safe driving lane. The network was trained on a
1.0 = "safe / in the lane" signal, so a sensor reading LIGHT (over the
floor) must map to 1.0, and DARK (over a piece of edge tape) to 0.0.

CALIBRATION
-----------
REFLECTION_THRESHOLD below decides "over the floor" vs "over the edge
tape," based on ColorSensor.reflection() (0-100, lower = darker). Test
both sensors on your actual floor and tape before running, and adjust
the threshold if the robot won't move or spins in place immediately.

START / FINISH
---------------
The robot starts with both sensors sitting on a green stripe (the start
line) and finishes by driving across a red stripe (the finish line). The
race clock starts the moment the robot is fully clear of the green, and
stops the instant either sensor sees red -- that elapsed time is what
you compare between cars.
"""

from pybricks.hubs import PrimeHub
from pybricks.pupdevices import Motor, ColorSensor
from pybricks.parameters import Port, Color
from pybricks.tools import wait, StopWatch
import math

# CLASS-SPECIFIC: ports (motors A and E, sensors F and B) match one class's robot
# build and their block programs. Students may wire differently; change the Port
# letters to match. See CLASS-SPECIFIC.md.
hub = PrimeHub()
left_motor = Motor(Port.A)
right_motor = Motor(Port.E)
left_sensor = ColorSensor(Port.F)
right_sensor = ColorSensor(Port.B)

# ----------------------------------------------------------------------
# TRAINED BRAIN — copied from best_weights.json, the output of the last
# Phase 1 training run. Re-copy this list any time you retrain.
# ----------------------------------------------------------------------
WEIGHTS = [
    -0.4757381672407086, 0.8903342167976096, -0.3943926408088745,
    0.8515851138442037, 0.0036658781514160577, 0.034672882991120035,
    0.6782552512555216, -0.9959633948359958, -0.2127273721813947,
    -0.01070827391850493, -0.36434696178560855, 0.6674717334690508,
    0.6313945629173208, 0.7348516525354472, 0.17303066738776995,
    -0.06917772476404616, -0.7305794616184684, 0.20549367178878764,
]

N_IN = 2       # left sensor, right sensor -- must match NUM_SENSORS in Phase 1
N_HIDDEN = 6   # must match HIDDEN_NODES in Phase 1
N_OUT = 1      # one output: turn

w1_size = N_IN * N_HIDDEN
W1 = [WEIGHTS[i * N_IN:(i + 1) * N_IN] for i in range(N_HIDDEN)]
W2 = WEIGHTS[w1_size:w1_size + N_HIDDEN]


def forward(sensor_values):
    hidden = [math.tanh(sum(w * s for w, s in zip(h_w, sensor_values))) for h_w in W1]
    return math.tanh(sum(w * h for w, h in zip(W2, hidden)))  # turn: -1 (full left) .. +1 (full right)


# CLASS-SPECIFIC: calibrated for one classroom's floor and tape; recalibrate.
REFLECTION_THRESHOLD = 30  # % reflected light ABOVE this = safely on the floor
BASE_SPEED = 200           # deg/sec -- tune for your gearing


def drive_step():
    """Reads sensors, steers for one tick. Returns True once a sensor
    crosses the red finish stripe."""
    if left_sensor.color() == Color.RED or right_sensor.color() == Color.RED:
        return True

    readings = [
        1.0 if left_sensor.reflection() > REFLECTION_THRESHOLD else 0.0,
        1.0 if right_sensor.reflection() > REFLECTION_THRESHOLD else 0.0,
    ]
    turn = forward(readings)
    # turn > 0 = steer right (matches the simulation's own turn convention) =
    # left wheel faster, right wheel slower
    left_motor.run(BASE_SPEED * (1 + turn))
    right_motor.run(BASE_SPEED * (1 - turn))
    return False


# START: the robot begins with both sensors on the green start stripe.
# Keep steering normally while crossing it, but don't start the clock
# until it's fully clear.
print("On your mark...")
while left_sensor.color() == Color.GREEN or right_sensor.color() == Color.GREEN:
    drive_step()
    wait(20)

print("GO!")
watch = StopWatch()

# RACE: drive until a sensor crosses the red finish stripe.
finished = False
while not finished:
    finished = drive_step()
    wait(20)

left_motor.brake()
right_motor.brake()
elapsed_s = watch.time() / 1000
print(f"Finished in {elapsed_s:.2f} seconds")
