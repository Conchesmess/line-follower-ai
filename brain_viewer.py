"""
RULES vs WEIGHTS — an interactive side-by-side
===============================================
Left:   the hand-written rule YOU wrote for your robot in Stage 2: the block
        program with "if B is color black then move left" and "if F is color
        black then move right". Every block is a decision you made.
Right:  the trained neural network. There is no "if" anywhere in it, just
        18 numbers (weights) that multiply, add and squash the sensor values.
Bottom: for all four possible sensor readings, what each one decides.

Click the two sensor buttons (or press L / R) to change what the car "sees".
Click a hidden neuron to see what it calculates and how it votes
on the turn. Click a line in the network to select a weight, then press Up/Down to turn
that knob and watch the brain's answers change. Press Home to put it back.
Press W (or click the blue button at the top) to read "What are weights?".

The sensor/turn conventions match the simulation: a sensor reads 1 when it
sees the line (on the track) and 0 when it is off; turn > 0 steers right.
"""

import math

import pygame

import markdown_viewer
from hover_tips import HoverTips
from line_follower_ai import (
    SCREEN_W, SCREEN_H, BG_COLOR, BLACK, NUM_SENSORS, HIDDEN_NODES, NeuralNet,
)

GREY = (130, 130, 130)
LIGHT = (225, 225, 225)
GREEN = (0, 140, 60)
RED = (200, 0, 0)
POS = (40, 90, 200)       # positive weight / activation
LINK_COLOR = (0, 90, 200)
EXPLAINER = "weights-explained.md"
LINK_TEXT = "Read: What are weights?  (W)"
NEG = (210, 70, 50)       # negative weight / activation
HILITE = (255, 240, 170)
STRAIGHT_BAND = 0.15      # |turn| below this counts as "straight"

# CLASS-SPECIFIC: this block (RULE_LINES, rule_for, and the F/B labels and
# captions in the drawing code below) mirrors ONE class's Stage 2 block program.
# A generic version should replace it with the learner's own rule, or a neutral
# example. See CLASS-SPECIFIC.md for everything that needs the same treatment.
# The student's own Stage 2 rule: the forever loop of their block program
# (images/stage2-decide-turn.png), shown line by line. RULE_LINES[i] is
# highlighted when i is in the set returned by rule_for(). Keep these lines
# matching that program.
# In the blocks, "sees black" means the sensor is on the TAPE, i.e. OFF the
# lane. Sensor B is treated as the right-hand sensor and F as the left-hand one,
# which is the only way the rule agrees with the simulation's steering.
RULE_LINES = [   # CLASS-SPECIFIC
    "forever",
    "  start moving forward",
    "  if B is color black then",
    "    move left (-85) for 85 degrees",
    "  if F is color black then",
    "    move right (100) for 60 degrees",
    "  if B or F is color red then",
    "    stop all",
]

# Network drawing geometry
IN_X, HID_X, OUT_X = 450, 660, 840
IN_Y = [220, 310]
HID_Y = [143 + i * 52 for i in range(HIDDEN_NODES)]
OUT_Y = [265]
NODE_R = 17


def rule_for(left_on, right_on):
    """Returns (turn, highlighted line numbers) for the rule the student wrote.
    left_on / right_on = the sensor is on the line (so NOT seeing black tape).
    F is the left sensor and B the right one."""
    b_black, f_black = not right_on, not left_on
    if b_black and f_black:
        return 0.0, {0, 1, 2, 3, 4, 5}      # lost: both blocks fire and cancel out
    if b_black:
        return -1.0, {0, 1, 2, 3}
    if f_black:
        return +1.0, {0, 1, 4, 5}
    return 0.0, {0, 1}


def describe(turn):
    if abs(turn) < STRAIGHT_BAND:
        return "straight"
    return "RIGHT" if turn > 0 else "LEFT"


def forward_detail(brain, sensors):
    """Like NeuralNet.forward, but also returns the hidden activations."""
    hidden = [math.tanh(sum(w * s for w, s in zip(hw, sensors))) for hw in brain.w1]
    turn = math.tanh(sum(w * h for w, h in zip(brain.w2, hidden)))
    return hidden, [turn]


def edge_list(n_in, n_hidden, n_out):
    """Every weight as (flat index, (x1, y1), (x2, y2), label)."""
    edges = []
    for h in range(n_hidden):
        for i in range(n_in):
            side = "left" if i == 0 else "right"
            edges.append((h * n_in + i, (IN_X, IN_Y[i]), (HID_X, HID_Y[h]),
                          f"{side} sensor -> hidden {h + 1}"))
    base = n_in * n_hidden
    for o in range(n_out):
        for h in range(n_hidden):
            edges.append((base + o * n_hidden + h, (HID_X, HID_Y[h]), (OUT_X, OUT_Y[o]),
                          f"hidden {h + 1} -> turn"))
    return edges


def distance_to_segment(p, a, b):
    ax, ay = a
    bx, by = b
    dx, dy = bx - ax, by - ay
    length_sq = dx * dx + dy * dy
    t = 0 if length_sq == 0 else max(0, min(1, ((p[0] - ax) * dx + (p[1] - ay) * dy) / length_sq))
    return math.hypot(p[0] - (ax + t * dx), p[1] - (ay + t * dy))


def blend(color, amount):
    """White toward `color` by amount 0..1."""
    amount = max(0.0, min(1.0, amount))
    return tuple(int(255 + (c - 255) * amount) for c in color)


def run_brain_viewer(screen, weights):
    """Returns True if the window was closed, False for Esc (back to menu).
    weights=None uses a random (untrained) brain."""
    pygame.display.set_caption("Line Follower AI — rules vs weights")
    clock = pygame.time.Clock()
    title_font = pygame.font.SysFont("consolas,menlo,dejavusansmono,couriernew,monospace", 26, bold=True)
    font = pygame.font.SysFont("consolas,menlo,dejavusansmono,couriernew,monospace", 16)
    code_font = pygame.font.SysFont("consolas,menlo,dejavusansmono,couriernew,monospace", 12)
    tiny = pygame.font.SysFont("consolas,menlo,dejavusansmono,couriernew,monospace", 12)

    untrained = weights is None
    original = list(NeuralNet().weights if untrained else weights)
    flat = list(original)
    brain = NeuralNet(list(flat))
    edges = edge_list(NUM_SENSORS, HIDDEN_NODES, 1)
    sensors = [1, 1]            # [left_on, right_on]
    selected = None             # index into `flat`
    sel_neuron = None           # which hidden neuron the inspector shows
    tips = HoverTips()          # glossary hover tips and links on this screen
    left_btn = pygame.Rect(20, 46, 230, 32)
    right_btn = pygame.Rect(260, 46, 230, 32)

    def pick_edge(pos):
        best, best_d = None, 7
        for idx, a, b, _ in edges:
            d = distance_to_segment(pos, a, b)
            if d < best_d:
                best, best_d = idx, d
        return best

    def neuron_of_edge(idx):
        n_first = NUM_SENSORS * HIDDEN_NODES
        return idx // NUM_SENSORS if idx < n_first else idx - n_first

    def pick_neuron(pos):
        for h, y in enumerate(HID_Y):
            if math.hypot(pos[0] - HID_X, pos[1] - y) <= NODE_R + 3:
                return h
        return None

    link_rect = pygame.Rect(510, 46, 340, 32)

    def open_explainer():
        closed = markdown_viewer.run_markdown_viewer(screen, markdown_viewer.resolve_markdown(EXPLAINER)
                                                     or EXPLAINER)
        pygame.display.set_caption("Line Follower AI — rules vs weights")
        return closed

    window_closed = False
    running = True
    while running:
        clock.tick(30)
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running, window_closed = False, True
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    running = False
                elif event.key == pygame.K_w:
                    if open_explainer():
                        running, window_closed = False, True
                elif event.key == pygame.K_l:
                    sensors[0] ^= 1
                elif event.key == pygame.K_r:
                    sensors[1] ^= 1
                elif event.key == pygame.K_HOME:
                    flat = list(original)
                    brain = NeuralNet(list(flat))
                elif event.key in (pygame.K_UP, pygame.K_DOWN) and selected is not None:
                    flat[selected] = round(flat[selected] + (0.1 if event.key == pygame.K_UP else -0.1), 2)
                    brain = NeuralNet(list(flat))
            elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                closed = tips.click(screen, event.pos)         # a glossary term was clicked?
                if closed is not None:
                    if closed:
                        running, window_closed = False, True
                elif left_btn.collidepoint(event.pos):
                    sensors[0] ^= 1
                elif right_btn.collidepoint(event.pos):
                    sensors[1] ^= 1
                elif link_rect.collidepoint(event.pos):
                    if open_explainer():
                        running, window_closed = False, True
                elif event.pos[0] > 340 and event.pos[1] < 470:
                    h = pick_neuron(event.pos)
                    if h is not None:
                        sel_neuron, selected = h, None
                    else:
                        selected = pick_edge(event.pos)
                        if selected is not None:
                            sel_neuron = neuron_of_edge(selected)

        hidden, outputs = forward_detail(brain, sensors)
        rule_turn, rule_lines = rule_for(*sensors)

        screen.fill(BG_COLOR)
        tips.begin()
        screen.blit(title_font.render("Rules vs Weights", True, BLACK), (20, 12))
        if untrained:
            tips.add(screen.blit(font.render("UNTRAINED: random weights", True, RED), (590, 20)), "Untrained")

        # ---- sensor buttons ---------------------------------------------
        for rect, name, on in ((left_btn, "Left (F)", sensors[0]), (right_btn, "Right (B)", sensors[1])):
            pygame.draw.rect(screen, (190, 235, 200) if on else (245, 205, 200), rect, border_radius=6)
            pygame.draw.rect(screen, GREY, rect, 1, border_radius=6)
            screen.blit(font.render(f"{name}: {'ON line' if on else 'OFF'}", True, BLACK), (rect.x + 10, rect.y + 7))

        # ---- explainer link (top right, button style) --------------------------
        hover = link_rect.collidepoint(pygame.mouse.get_pos())
        pygame.draw.rect(screen, (190, 215, 250) if hover else (215, 230, 250), link_rect, border_radius=6)
        pygame.draw.rect(screen, LINK_COLOR, link_rect, 2, border_radius=6)
        label = font.render(LINK_TEXT, True, LINK_COLOR)
        screen.blit(label, (link_rect.x + (link_rect.w - label.get_width()) // 2, link_rect.y + 7))

        # ---- rule panel (left)   CLASS-SPECIFIC: titles/captions name the class's Stage 2 program --------------------------------------------
        panel = pygame.Rect(20, 112, 345, 215)
        pygame.draw.rect(screen, (255, 255, 255), panel, border_radius=6)
        pygame.draw.rect(screen, GREY, panel, 1, border_radius=6)
        tips.add(screen.blit(font.render("RULES: your Stage 2 program", True, BLACK), (panel.x, panel.y - 24)),
                 "Rule (hand-written)")
        for i, line in enumerate(RULE_LINES):
            y = panel.y + 10 + i * 24
            if i in rule_lines:
                pygame.draw.rect(screen, HILITE, (panel.x + 4, y - 2, panel.w - 8, 22))
            screen.blit(code_font.render(line, True, BLACK), (panel.x + 8, y))
        result = font.render(f"Rule decides: {describe(rule_turn)}", True, BLACK)
        screen.blit(result, (panel.x, panel.bottom + 8))
        screen.blit(tiny.render("The block program you wrote for your robot.", True, GREY), (panel.x, panel.bottom + 32))
        screen.blit(tiny.render("'Black' = tape = sensor OFF the line.", True, GREY), (panel.x, panel.bottom + 46))

        # ---- hidden-neuron inspector (bottom left) ---------------------------------
        insp = pygame.Rect(20, 392, 322, 100)
        pygame.draw.rect(screen, (255, 255, 255), insp, border_radius=6)
        pygame.draw.rect(screen, GREY, insp, 1, border_radius=6)
        contribs = [hidden[h] * brain.w2[h] for h in range(HIDDEN_NODES)]
        total = sum(contribs)
        turn_val = outputs[0]
        if sel_neuron is None:
            rows = [
                (code_font, "Click a hidden neuron (middle circles)", BLACK),
                (tiny, "to see what it calculates.", BLACK),
                (tiny, "Each has its own 2 weights, so the same", GREY),
                (tiny, "sensor readings give different values.", GREY),
                (tiny, f"All 6 sum {total:+.2f}; tanh -> turn {turn_val:+.2f}", BLACK),
            ]
        else:
            h = sel_neuron
            wl, wr = brain.w1[h]
            wo = brain.w2[h]
            pre = wl * sensors[0] + wr * sensors[1]
            if abs(wl) > 1.5 * abs(wr):
                listens = "mostly LEFT sensor"
            elif abs(wr) > 1.5 * abs(wl):
                listens = "mostly RIGHT sensor"
            else:
                listens = "both sensors equally"
            sends = "RIGHT" if contribs[h] > 0 else "LEFT"
            rows = [
                (code_font, f"Hidden neuron {h + 1}: value {hidden[h]:+.2f}", BLACK),
                (tiny, f"listens to: {listens}", BLACK),
                (tiny, f"({wl:+.2f}x{sensors[0]})+({wr:+.2f}x{sensors[1]})={pre:+.2f}, tanh {hidden[h]:+.2f}", BLACK),
                (tiny, f"vote = {hidden[h]:+.2f} x {wo:+.2f} = {contribs[h]:+.2f} -> {sends}", BLACK),
                (tiny, f"All 6 votes sum {total:+.2f}; tanh -> turn {turn_val:+.2f}", BLACK),
            ]
        ry = insp.y + 7
        for f, text, color in rows:
            screen.blit(f.render(text, True, color), (insp.x + 8, ry))
            ry += 20 if f is code_font else 14

        # ---- network panel (right) -----------------------------------------
        tips.add(screen.blit(font.render("WEIGHTS: evolution found 18 numbers", True, BLACK), (350, 88)), "Weight")
        related = set()
        if sel_neuron is not None:
            related = {sel_neuron * NUM_SENSORS + i for i in range(NUM_SENSORS)} | \
                      {NUM_SENSORS * HIDDEN_NODES + sel_neuron}
        for idx, a, b, _ in edges:
            w = flat[idx]
            color = POS if w >= 0 else NEG
            width = 1 + int(4 * min(abs(w) / 2.0, 1.0))
            if idx in related and idx != selected:
                pygame.draw.line(screen, (240, 190, 0), a, b, width + 6)
            if idx == selected:
                pygame.draw.line(screen, BLACK, a, b, width + 4)
            pygame.draw.line(screen, color, a, b, width)

        for i, y in enumerate(IN_Y):
            pygame.draw.circle(screen, (120, 200, 140) if sensors[i] else (235, 190, 185), (IN_X, y), NODE_R)
            pygame.draw.circle(screen, GREY, (IN_X, y), NODE_R, 1)
            screen.blit(font.render(str(sensors[i]), True, BLACK), (IN_X - 5, y - 8))
            screen.blit(tiny.render("left" if i == 0 else "right", True, GREY), (IN_X - 50, y - 6))
            tips.add((IN_X - NODE_R, y - NODE_R, 2 * NODE_R, 2 * NODE_R), "Input", click=False)
        for h, y in enumerate(HID_Y):
            a = hidden[h]
            pygame.draw.circle(screen, blend(POS if a >= 0 else NEG, abs(a)), (HID_X, y), NODE_R)
            pygame.draw.circle(screen, GREY, (HID_X, y), NODE_R, 1)
            if h == sel_neuron:
                pygame.draw.circle(screen, BLACK, (HID_X, y), NODE_R + 3, 3)
            label = tiny.render(f"{a:+.2f}", True, BLACK)
            screen.blit(label, (HID_X - label.get_width() // 2, y - 6))
            tips.add((HID_X - NODE_R, y - NODE_R, 2 * NODE_R, 2 * NODE_R), "Hidden neuron / hidden node", click=False)
        for o, y in enumerate(OUT_Y):
            v = outputs[o]
            pygame.draw.circle(screen, blend(POS if v >= 0 else NEG, abs(v)), (OUT_X, y), NODE_R)
            pygame.draw.circle(screen, GREY, (OUT_X, y), NODE_R, 1)
            label = tiny.render(f"{v:+.2f}", True, BLACK)
            screen.blit(label, (OUT_X - label.get_width() // 2, y - 6))
            tips.add(screen.blit(tiny.render("turn", True, GREY), (OUT_X - 18, y + 22)), "Output")
            tips.add((OUT_X - NODE_R, y - NODE_R, 2 * NODE_R, 2 * NODE_R), "Output", click=False)
        tips.add(screen.blit(tiny.render("sensors", True, GREY), (IN_X - 22, IN_Y[0] - 40)), "Sensor")
        tips.add(screen.blit(tiny.render("6 hidden neurons", True, GREY), (HID_X - 48, HID_Y[0] - 32)),
                 "Hidden neuron / hidden node")
        screen.blit(tiny.render("blue = +   red = -   thicker = bigger", True, GREY), (350, 470))

        turn = outputs[0]
        tips.add(screen.blit(font.render(f"Brain decides: {describe(turn)}  (turn {turn:+.2f})", True, BLACK), (450, 428)),
                 "Neural network")
        if selected is None:
            info = "Click a line in the network to select a weight."
        else:
            info = f"Selected: {next(e[3] for e in edges if e[0] == selected)} = {flat[selected]:+.2f}   (Up/Down = change)"
        screen.blit(tiny.render(info, True, BLACK), (350, 450))

        # ---- comparison table (bottom) ---------------------------------------
        top = 495
        cols = [30, 150, 280, 450, 680]
        for x, text in zip(cols, ("Left (F)", "Right (B)", "Rule says", "Brain says", "Same direction?")):
            rect = screen.blit(font.render(text, True, BLACK), (x, top))
            tips.add(rect, {"Rule says": "Rule (hand-written)", "Brain says": "Neural network"}.get(text))
        pygame.draw.line(screen, GREY, (20, top + 22), (SCREEN_W - 20, top + 22), 1)
        for r, (l, rt) in enumerate(((1, 1), (0, 1), (1, 0), (0, 0))):
            y = top + 30 + r * 28
            if [l, rt] == sensors:
                pygame.draw.rect(screen, HILITE, (20, y - 3, SCREEN_W - 40, 26))
            r_turn, _ = rule_for(l, rt)
            b_turn = forward_detail(brain, [l, rt])[1][0]
            lost = (l, rt) == (0, 0)
            same = describe(r_turn) == describe(b_turn)
            screen.blit(font.render("on line" if l else "OFF", True, BLACK), (cols[0], y))
            screen.blit(font.render("on line" if rt else "OFF", True, BLACK), (cols[1], y))
            screen.blit(font.render("lost: crashed" if lost else describe(r_turn), True, BLACK), (cols[2], y))
            screen.blit(font.render(f"{describe(b_turn)}  ({b_turn:+.2f})", True, BLACK), (cols[3], y))
            if not lost:
                screen.blit(font.render("yes" if same else "no", True, GREEN if same else RED), (cols[4], y))
            else:
                screen.blit(font.render("(car has crashed)", True, GREY), (cols[4], y))

        note = "A rule is decisions you write. Weights blend the sensors: change one number and several answers shift."
        screen.blit(tiny.render(note, True, GREY), (20, SCREEN_H - 62))
        screen.blit(tiny.render("L / R = toggle sensors    click a line + Up/Down = change a weight    Home = reset    W = explainer    Esc = back",
                                True, GREY), (20, SCREEN_H - 40))
        tips.draw(screen)
        pygame.display.flip()

    return window_closed
