# Teacher Setup Guide: Line-Following AI Unit

<!-- CLASS-SPECIFIC: this whole guide is written for one teacher's class and setup. See CLASS-SPECIFIC.md. -->

Everything below is what I can verify from the code itself. I have **not** run any of this on a real SPIKE hub or in VS Code — treat the hardware/deployment sections as "here's what the code assumes," not as tested instructions. You said you're planning to walk the whole thing yourself first, which is exactly the right way to catch anything I got wrong.

<!-- CLASS-SPECIFIC: VS Code and the Python extension, student laptops. See CLASS-SPECIFIC.md. -->

## 1. Software each student laptop needs

- **Python 3** (any recent 3.x; this was built/tested against 3.14). Check with `python3 --version` in a terminal.
- **pygame**: `pip install pygame` (or `pip3 install pygame`, depending on their setup).
- **VS Code** with the Microsoft **Python extension** installed (`ms-python.python`) — this is what gives them the green "Run Python File" ▷ button students are told to use in the student guide. Without it they'd need to run everything via the integrated terminal instead (`python menu.py`), which also works fine.
- A **pygame window benign warning** shows on some machines about AVX2 support — this is harmless, just a performance note, not an error. Worth mentioning once so students don't panic.

Quick per-laptop smoke test before class: open this folder in VS Code, run `menu.py`, choose 1, confirm a window opens showing cars driving a track. If it opens and closes instantly or throws an import error, pygame isn't installed correctly on that machine.

## Handing it out: the student package

Run `python make_student_package.py` in the project folder. It writes `dist/LineFollowerAI-student.zip`: one folder (`LineFollowerAI`) with the program, the student guide, the explainers, a `README.md` quick start, `requirements.txt`, a `check_setup.py` self-test, and a ready-made `.vscode` folder so the Run button (or F5) launches `menu.py`.

What it leaves out on purpose: this teacher guide, `CLASS-SPECIFIC.md`, your own `.vscode` settings, and your `best_weights.json` / `progress.json` (those are your training results). `spike_line_follower.py` is packaged with whatever weights it holds now; students replace them with their own.

Each student unzips it somewhere they can save (Documents is fine; not inside the zip itself or a read-only folder), opens the folder in VS Code, and follows `README.md`: install Python and the VS Code Python extension, then `pip install -r requirements.txt`, then `check_setup.py`, then run `menu.py`. Rebuild the zip whenever you change the code or documents. Either run the command again, or leave `python make_student_package.py --watch` running in a spare terminal: it rebuilds the zip a moment after any packaged file is saved (Ctrl+C to stop). Every build carries a short **build id** (shown in `BUILD-INFO.txt` inside the zip, and printed by `check_setup.py`). The id only changes when file contents change, so a student can tell you which version they have and you can compare it with your latest build.

## 2. Project files each student needs

Give every student their own copy of this whole folder. The important files:

| File | Purpose |
|---|---|
| `menu.py` | Phase 1 entry point — the file students run. Menu: 1) train weights, 2) time trial, 3) start over, 4) rules vs weights, 5) glossary, 6) copy to Spike robot code. Shows whether trained weights exist, how much training produced them, the best lap times on each track, and whether `spike_line_follower.py` has the saved weights |
| `line_follower_ai.py` | Simulation scenario 1, **training**: 40 brains evolve over generations, each tested at 1×–3× speed (called from the menu; also runs on its own) |
| `time_trial.py` | Simulation scenario 2, **time trial**: one car runs one lap with `best_weights.json` and reports its lap time; a slider sets the speed from 0.5× to 3×, and T switches between Track A (the training track) and Track B (a held-out track no brain trains on) (called from the menu; also runs on its own) |
| `progress.py` | Helper that reads/writes `progress.json` (training sessions, generations, best lap time) and copies weights into the robot file — students don't touch it |
| `spike_line_follower_baseline.py` | Stage 2 — the hand-coded two-sensor robot, used for the first race |
| `spike_line_follower.py` | Stage 3 — the AI-driven robot; its `WEIGHTS` are overwritten when a student chooses "Copy to Spike Robot Code" in the menu (training alone doesn't touch it) |
| `weights-explained.md` | Student-facing explainer of what a "weight" is, referenced in Stage 3 |
| `student-guide.md` | The step-by-step student instructions |
| `best_weights.json` | Auto-generated after training; not something students need to touch directly |
| `progress.json` | Auto-generated; the menu's record of training and best lap time at each speed. Deleted by "Start over" |

**Important:** each student needs their *own* folder (their own working directory). Training writes to `spike_line_follower.py`, `best_weights.json` and `progress.json` in place — if multiple students shared one folder over a network drive, they'd overwrite each other's results.

<!-- CLASS-SPECIFIC: Pybricks firmware and the port wiring (A, E, F, B). See CLASS-SPECIFIC.md. -->

## 3. SPIKE Prime hub setup — please double-check this section

The `spike_*.py` files both start with:
```python
from pybricks.hubs import PrimeHub
from pybricks.pupdevices import Motor, ColorSensor
```
This only works if the hub is running **Pybricks firmware**, not the stock LEGO Education SPIKE App firmware. If your hubs already run Pybricks (it sounds like they do, since you mentioned already using the two color sensors for edge-sensing), you're set. If not: Pybricks firmware is installed via a browser-based installer, and code is normally written/run through the Pybricks web IDE (not VS Code) connected to the hub over USB or Bluetooth. Since you already have a working pipeline for getting code onto your hubs, I'd defer to whatever process you're already using — just confirm it can take a plain `.py` file like the ones here and run it as-is.

**Wiring assumption baked into the code** (both spike files): left motor → Port A, right motor → Port E, left edge sensor → Port F, right edge sensor → Port B. If your robots are built differently, either rewire to match, or have students edit the `Port.X` values at the top of the file — either is a fine teaching moment.

<!-- CLASS-SPECIFIC: tape-edged track, linoleum floor, 10-inch lane, sensor spacing in studs. See CLASS-SPECIFIC.md. -->

## 4. Physical track considerations

**Track construction:** two strips of black tape mark the track's edges, with the floor between them (e.g. linoleum) as the drivable lane — confirmed with the teacher, and the code now matches this. A sensor reading *light* means it's safely over the floor; reading *dark* means it's drifted onto a piece of edge tape and needs to steer away. This is the opposite polarity from a classic single-line-follower (where the robot chases a dark line), so if you've taught SPIKE line following before with "dark = good" logic, flag that difference for students.

The simulation trains against a 50px-wide lane with two edges, and the two simulated sensors sit roughly 87% of the way from center to each edge (i.e., just inside the tape) — the simulation's internal rendering happens to use a solid dark band to represent "the safe lane" (an implementation detail), but the real robot code translates real sensor readings into that same abstract "safe vs. edge" signal, so the physical tape/floor color scheme doesn't need to visually match the simulation for the trained weights to transfer correctly.

- Make the gap between the two tape strips wide enough that each sensor, mounted near the front, sits over the floor near its respective tape line when the robot is centered — close to the edge, not dead center — so it can detect drift before actually reaching the tape.
- **Calibrate `REFLECTION_THRESHOLD` (currently 30) on your actual classroom floor and tape color** before any student races. Check that the floor reads clearly *above* 30 and the tape clearly *below* it — this is the single most common reason a robot won't move or will spin immediately.

### Sensor placement for a 10-inch-wide track

Since students are designing their own robots, give them a concrete target rather than "somewhere near the edge." Using the same lateral-offset ratio the simulation was tuned with (sensors at ~87% of the way from center to each edge):

- **Each sensor ~4.3 inches (≈14 LEGO studs) from the robot's centerline** — i.e. the two sensors sit about **8.6 inches (≈27-28 studs) apart**, leaving roughly **0.7 inches (~18mm) of margin** before either one actually reaches its tape strip.
- Two ways to mount that: a straight crossbar with a sensor at each end (~8.6in wide — needs a fairly wide chassis), or two ~5-inch arms splayed outward at 60° from straight-ahead ending in a sensor each (narrower footprint, and matches the simulation's geometry exactly, including a small forward look-ahead).
- This 87% ratio came from optimizing margins *in the simulation*, not a law of physics — it's a starting point. Real builds have more slop than a simulation (motor mismatches, mounting imprecision, uneven tape), so a twitchy/oscillating robot suggests pulling the sensors in slightly (more margin); a robot that corrects too late and drives off suggests pushing them out.

### Does the physical track need to match the simulated track's shape?

No — you don't need to trace the simulation's exact wiggle pattern. Two things matter far more than the literal shape:

1. **Lane width matches what the sensors are mounted for.** We tested this directly: a trained network completely fails (instant crash) on a narrower track of the *same shape*, but transfers reasonably to a *different shape* of the same width. Whatever width you build, keep the two sensors mounted at the same proportional distance from center (~87% of the way to each edge) used above.
2. **No turn tighter than the robot's real minimum turning radius**, with a comfortable safety margin. The simulated track was deliberately built so its tightest bend (~80px radius) is more than 2x the simulated car's minimum turning radius (~37px). The same principle applies physically: have students measure how tight their actual robot can turn at `BASE_SPEED`/`TURN_STRENGTH`, and don't build anything tighter than that with margin to spare. A too-tight physical bend is un-drivable by *any* controller, trained or hand-coded — no amount of AI fixes a physically impossible turn.

What doesn't matter: exact coordinates, the specific wave pattern, or the overall size of the loop. The network only ever reacts to "did my left/right sensor just lose the floor" — it has no notion of absolute position or the track's overall shape, which is why a *loosely* similar course (gentle, rounded bends, no hairpins or sudden reversals) transfers about as well as an exact replica, and is much easier to lay tape for. If a real robot struggles on a specific bend, that's a good moment to have students check whether that bend is simply too tight for the robot's actual turning radius, versus a training/tuning problem.

## 5. A generalization caveat worth telling students about (or not)

We tested this directly: a network trained on one track shape transfers *reasonably* to a differently-shaped track of the same width, but completely fails on a track of a different width, because the sensors' physical spacing only makes sense relative to the width they were tuned for. Practically: **whatever width you build your physical practice track at, keep it consistent** across the unit, or retraining/recalibration is needed. This could also be a great discussion topic (why doesn't the AI "just know" how to handle a different track?).

**Track B in the simulation.** The time trial has a second track, Track B, that is never used in training. It is a deliberate *test set*: it lets students see training data bias first-hand (a brain trained only on Track A can crash on a track it has never seen, or lose its high-speed margin). In a quick check, a brain that finished Track A at 2× finished Track B at 1× but not 1.5×. Results vary by brain, so have students compare their own. See "A track your car has never seen" in the student guide. A natural extension, if you want students to *fix* the bias: change training to score each brain on both tracks, the same way it already averages over several speeds.

## 6. Known rough edges / things I'd sanity-check first

- **Training is nondeterministic.** Every run of `line_follower_ai.py` starts from random weights, so results vary run to run — sometimes dramatically. Encourage a few retrains rather than expecting one run to nail it.
- **Training speed depends on the laptop.** The simulation runs at a fixed 60 FPS target but simulated (not real) generation time, so slower laptops will just take longer wall-clock time per generation, not fail outright. Training now simulates each brain at five speeds (1×–3×) every frame, though only the 1× cars are drawn; on a development machine that costs about 2.5 ms per frame against a 16 ms budget at 60 FPS, so it should be fine, but worth checking on your slowest student laptop. Worth timing on your own machine to plan class pacing.
- **Stage 1 (one-sensor) has no provided code file** — the student guide walks them through writing it themselves as a short exercise, reusing the same wiring pattern as Stage 2. If you'd rather hand them a working one-sensor file to start from (instead of writing it cold), let me know and I'll build one.
- **The motor-mixing math had a sign bug** in the original template that I found and fixed while building this (steering was inverted relative to what the simulation intended). Both `spike_line_follower.py` and `spike_line_follower_baseline.py` have the corrected version — just flagging it in case you're comparing against an older copy of any of these files.
- Nothing here has been run on real Pybricks hardware — the math and wiring assumptions are verified against the simulation, but the first real robot test is genuinely a first test.

<!-- CLASS-SPECIFIC: pacing for this class's periods. See CLASS-SPECIFIC.md. -->

## 7. Suggested pacing (a guess, not a strong recommendation)

- Stage 1 (one-sensor): a class period to build and tune.
- Stage 2 (two-sensor + race): a class period to build/tune, a period for the race itself.
- Stage 3 (AI training): training itself runs unattended for several minutes once set up, so this splits well into "set up and start training" then "come back, evaluate, deploy, race" — possibly two periods.
