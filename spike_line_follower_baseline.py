# SPDX-License-Identifier: PolyForm-Noncommercial-1.0.0  (see LICENSE-CODE)
"""
LINE-FOLLOWING — HAND-CODED BASELINE (no AI)
==============================================
The same two-edge-sensor robot as spike_line_follower.py, but steering is
plain if/elif logic a student writes and tunes by hand -- no neural net,
no training, no weights. This is what runs in the "two-sensor line
following" lesson and the speed competition, BEFORE machine learning is
introduced. spike_line_follower.py later replaces just the decide_turn()
logic below with a trained neural network -- everything else (wiring,
motor mixing) stays the same, so the two are a fair side-by-side comparison.

WIRING
------
  Left motor              -> Port A
  Right motor              -> Port E
  Left edge color sensor   -> Port F
  Right edge color sensor  -> Port B

TRACK
-----
Two strips of black tape mark the track's edges; the floor between them
(e.g. linoleum) is the safe driving lane. A sensor reading LIGHT means
it's over the floor (good); reading DARK means it's drifted onto a piece
of edge tape (bad, steer away).

CALIBRATION
-----------
REFLECTION_THRESHOLD decides "over the floor" vs "over the edge tape,"
based on ColorSensor.reflection() (0-100, lower = darker). Test both
sensors on your actual floor and tape before running -- the floor should
read clearly above this number, the tape clearly below it.

TUNING FOR THE RACE
--------------------
BASE_SPEED and TURN_STRENGTH are the two knobs that matter for the
competition: faster BASE_SPEED wins races but overshoots turns more;
higher TURN_STRENGTH corrects harder but can overcorrect and zig-zag.

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

# CLASS-SPECIFIC: ports (motors A and E, sensors F and B) match one class's robot
# build and their block programs. Students may wire differently; change the Port
# letters to match. See CLASS-SPECIFIC.md.
hub = PrimeHub()
left_motor = Motor(Port.A)
right_motor = Motor(Port.E)
left_sensor = ColorSensor(Port.F)
right_sensor = ColorSensor(Port.B)

# CLASS-SPECIFIC: calibrated for one classroom's floor and tape; recalibrate.
REFLECTION_THRESHOLD = 30  # % reflected light ABOVE this = safely on the floor
BASE_SPEED = 200           # deg/sec -- tune for your gearing
TURN_STRENGTH = 0.6        # how hard to correct, 0 (none) to 1 (full pivot)


def decide_turn(left_on_floor, right_on_floor):
    """turn > 0 steers right, turn < 0 steers left, 0 goes straight."""
    if left_on_floor and right_on_floor:
        return 0.0                  # centered -- go straight
    if left_on_floor and not right_on_floor:
        return -TURN_STRENGTH       # right sensor hit the tape -- steer left
    if right_on_floor and not left_on_floor:
        return TURN_STRENGTH        # left sensor hit the tape -- steer right
    return 0.0                      # both sensors on tape (shouldn't normally happen) --
                                     # go straight and hope to recover


def drive_step():
    """Reads sensors, steers for one tick. Returns True once a sensor
    crosses the red finish stripe."""
    if left_sensor.color() == Color.RED or right_sensor.color() == Color.RED:
        return True

    left_on_floor = left_sensor.reflection() > REFLECTION_THRESHOLD
    right_on_floor = right_sensor.reflection() > REFLECTION_THRESHOLD
    turn = decide_turn(left_on_floor, right_on_floor)

    # turn > 0 = steer right = left wheel faster, right wheel slower
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
