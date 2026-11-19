# Line Follower AI: Quick Start

<!-- CLASS-SPECIFIC: assumes students use VS Code with the Python extension. See CLASS-SPECIFIC.md. -->

This folder is **your own copy** of the project. Training saves your results
into it, so keep everything together in this one folder.

## 1. Get ready (once)

1. Install **Python 3** from <https://www.python.org/downloads/>.
   On Windows, tick **"Add Python to PATH"** on the first installer screen.
2. Install **VS Code** from <https://code.visualstudio.com/>, then install the
   **Python** extension (VS Code will suggest it when you open this folder).
3. In VS Code, choose **File > Open Folder** and open this folder.
4. Open a terminal: **Terminal > New Terminal** (or press `` Ctrl+` ``).
5. Install the one extra library the project needs:

   | Your computer | Type this and press Enter |
   |---|---|
   | Windows | `py -m pip install -r requirements.txt` |
   | Mac / Linux | `python3 -m pip install -r requirements.txt` |

6. Check that everything is ready:

   | Your computer | Type this |
   |---|---|
   | Windows | `py check_setup.py` |
   | Mac / Linux | `python3 check_setup.py` |

   It should end with **"All good"**. If it doesn't, read what it says, or ask your teacher.

## 2. Run it

Open **`menu.py`** and press the **▷ Run Python File** button (top right of the
editor), or press **F5**. The menu window opens.

Then follow **`student-guide.md`**.

## 3. If something goes wrong

| What you see | What to do |
|---|---|
| `No module named pygame` | Do step 5 above again. |
| `python` is "not recognized" (Windows) | Use `py` instead of `python`, or reinstall Python and tick "Add Python to PATH". |
| A window opens and closes at once | Run `check_setup.py` and read its message. |
| A warning about "AVX2" | Harmless. Ignore it. |
| The window is bigger than your screen | Drag its edge to shrink it. It scales. |

## What's in this folder

| File | What it is |
|---|---|
| `menu.py` | **Start here.** The main menu. |
| `student-guide.md` | The step-by-step instructions. |
| `weights-explained.md`, `glossary.md` | Explainers. You can also open them from inside the program. |
| `spike_line_follower*.py` | The code that goes on your SPIKE robot. |
| `best_weights.json`, `progress.json` | Created when you train. They are your results. |
| everything else | The program itself. You don't need to edit it. |

## License

This project is licensed under the **Creative Commons Attribution-NonCommercial 4.0 International** license ([CC BY-NC 4.0](https://creativecommons.org/licenses/by-nc/4.0/)). The full text is in the `LICENSE` file.

You are free to copy, share and adapt it for **non-commercial** purposes, as long as you give **credit** (the author's name, a link to the license, and a note of any changes you made). You may not use it to make money.

Copyright (c) 2026 Conchesmess (<https://github.com/Conchesmess>).

Not affiliated with LEGO, SPIKE or Pybricks. Those names belong to their owners.
