# Class-specific pieces (to replace in a generic version)

This project grew out of one class's setup. These pieces assume that class's
Stage 2 robot program and way of teaching. Everything is marked in the files
with the word **CLASS-SPECIFIC** (a code comment, or an HTML comment in the
.md files, which the in-tool viewers hide).

A generic version should replace each item below with something any learner
or teacher could use, such as the learner's own rule or a neutral example.

## The Stage 2 "hand-written rule" (the first class-specific feature)

The Rules vs Weights page tells students: "this rule is the program *you*
wrote for your robot." It mirrors this class's **block program** (the LEGO
SPIKE app), where students built a forever loop with:
`if B is color black then move left (-85) for 85 degrees`,
`if F is color black then move right (100) for 60 degrees`,
`if B or F is color red then stop all`.

| Where | What is class-specific |
|---|---|
| `brain_viewer.py` | `RULE_LINES`, `rule_for()`, the "RULES: your Stage 2 program" title, the captions under the panel, and the "Left (F)" / "Right (B)" sensor labels. B is treated as the right sensor and F as the left one, the same for every robot, even though it varies by robot in the class. |
| `images/stage2-decide-turn.png` | Screenshot of that block program. |
| `glossary.md` | The "Rule (hand-written)" entry (names the Stage 2 program and sensor B). |
| `weights-explained.md` | The paragraph and screenshot in "Weights vs. Rules", and the table row "Rule (your Stage 2 program)". |
| `student-guide.md` | The "Remember what you just did" paragraph in Stage 2, and the Stage 3 mention of "your block program". |
| `menu.py` | Option 4's description ("the rule you wrote"). |

Notes for making it generic:
- The simulation's sensors read 1 when ON the line (the lane). In the class's
  blocks, "sees black" means the sensor is on the tape, i.e. OFF the lane. The
  page's caption explains this. A generic rule should pick one convention.
- Later, this class moves the same exercise to Python (`spike_line_follower_baseline.py`,
  `decide_turn()`). A version of the panel that showed that Python rule was
  built and removed. It is easy to bring back for a Python-first class.

## Other class-specific areas (marked)

| Where | What is class-specific |
|---|---|
| `student-guide.md` | The opening line (SPIKE Prime, classmate race), the three-stage structure, Stage 1 hardware, Stage 2 hardware and the 10-inch track, the VS Code instructions, "Put it on the robot", "Race again", and the hardware rows in Troubleshooting. |
| `teacher-setup-guide.md` | The whole guide (one teacher's class), plus sections 1 (VS Code, laptops), 3 (Pybricks, ports A, E, F and B), 4 (tape track, linoleum, 10-inch lane, stud measurements) and 7 (pacing). |
| `spike_line_follower.py`, `spike_line_follower_baseline.py` | Port assignments (motors A and E, sensors F and B), Pybricks/PrimeHub, `REFLECTION_THRESHOLD`, and the green start / red finish stripes. |
| `line_follower_ai.py` | `TRACK_LINE_WIDTH`, `SENSOR_SPREAD_DEG`, `SENSOR_LENGTH`: simulation geometry tuned to match the class's physical track and sensor placement. |

## Student package

| Where | What is class-specific |
|---|---|
| `README.md`, `make_student_package.py` | The quick start and the generated `.vscode` folder assume students use VS Code with the Python extension. |

## Port convention (decided)

The class's block program uses motors **A+E** and sensors **B** and **F**. The
Python files and both guides now use the same ports, so everything matches:

| Part | Port |
|---|---|
| Left motor | A |
| Right motor | E |
| Left sensor | F |
| Right sensor | B |

(B as the right sensor and F as the left is what the Rules vs Weights page
assumes.) Students may wire differently. They change the `Port` letters at the
top of the robot file to match, and the guide says so. A generic version could
make the ports one block of settings at the top of the file, or a menu choice.

The simulation's track and sensor geometry (above) is also a good candidate for
a configurable setting rather than fixed numbers.
