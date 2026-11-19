"""
MARKDOWN VIEWER
===============
Shows a .md file as a formatted, scrollable page inside the tool (headings,
paragraphs, bullets, numbered steps, code blocks, tables, bold/italic/`code`).
Also holds the small text helpers that glossary_viewer.py shares.

  Mouse wheel / Up / Down / PgUp / PgDn / Home / End   scroll
  Esc                                                  back
"""

import os
import re

import pygame

from line_follower_ai import SCREEN_W, SCREEN_H, BG_COLOR, BLACK

HERE = os.path.dirname(os.path.abspath(__file__))

GREY = (130, 130, 130)
HEAD_COLOR = (20, 60, 140)
CODE_COLOR = (150, 40, 40)
CODE_BG = (232, 232, 238)
LINK_COLOR = (0, 90, 200)
CARD_BG = (255, 255, 255)

MARGIN = 50
HEADER_H = 60
FOOTER_H = 30
BODY_W = SCREEN_W - 2 * MARGIN - 12          # leaves room for the scrollbar
LINE_H = 22
MAX_IMAGE_H = 460                           # tall screenshots are shrunk to fit the window


def make_fonts():
    f = lambda size, **kw: pygame.font.SysFont("consolas,menlo,dejavusansmono,couriernew,monospace", size, **kw)
    link = f(16)
    link.set_underline(True)
    return {
        "plain": f(16), "bold": f(16, bold=True), "italic": f(16, italic=True),
        "code": f(15), "link": link,
        "h1": f(30, bold=True), "h2": f(22, bold=True), "small": f(15),
    }


# ---- inline text ----------------------------------------------------------

# ---- glossary links ----------------------------------------------------------
# Words and phrases that link to a glossary entry, keyed by the entry's heading
# in glossary.md. A heading that isn't listed here gets aliases made from the
# heading itself (and its plural), so new glossary entries link automatically.
TERM_ALIASES = {
    "Bias (training data bias)": ["training data bias", "bias"],
    "Explore": ["explore", "exploring", "exploration"],
    "Exploit": ["exploit", "exploiting", "exploitation"],
    "Genetic algorithm (GA)": ["genetic algorithm", "ga"],
    "Hidden neuron / hidden node": ["hidden neuron", "hidden neurons", "hidden node", "hidden nodes"],
    "Progress bar (Lap)": ["progress bar"],
    "Rule (hand-written)": ["rule", "rules", "hand-written rule"],
    "Simulation (sim)": ["simulation", "sim"],
    "Track A / Track B": ["track a", "track b"],
    "Training": ["training", "trained"],
}
ELIGIBLE = ("plain", "bold", "italic")
_index_cache = None


def glossary_index():
    """Returns ({alias: heading}, longest alias in words), read from glossary.md."""
    global _index_cache
    if _index_cache is None:
        import glossary_viewer                     # imported here: it imports this module
        aliases = {}
        for heading, _ in glossary_viewer.load_entries()[1]:
            names = TERM_ALIASES.get(heading)
            if names is None:
                names = []
                for part in heading.split(" / "):
                    base = re.sub(r"\s*\(.*?\)", "", part).strip().lower()
                    names += [base, base + ("es" if base.endswith("s") else "s")]
            for name in names:
                aliases.setdefault(name.lower(), heading)
        _index_cache = (aliases, max((len(a.split()) for a in aliases), default=1))
    return _index_cache


def autolink(words, glossary, seen, skip):
    """Turns the first use of each glossary term in `words` into a link to its entry.
    `seen` collects the terms already linked on this page; `skip` is a term to leave alone."""
    aliases, longest = glossary
    out, i = list(words), 0
    while i < len(out):
        matched = 0
        for length in range(min(longest, len(out) - i), 0, -1):
            toks = out[i:i + length]
            if any(t[1] not in ELIGIBLE or t[2] is not None for t in toks):
                continue
            if any(re.search(r"[^\w-]$", t[0]) for t in toks[:-1]):      # no punctuation inside a phrase
                continue
            phrase = " ".join(re.sub(r"^[^\w]+|[^\w]+$", "", t[0]) for t in toks).lower()
            heading = aliases.get(phrase)
            if heading and heading != skip and heading not in seen:
                for k in range(length):
                    w, _, _, glue = out[i + k]
                    out[i + k] = (w, "link", "glossary:" + heading, glue)
                seen.add(heading)
                matched = length
                break
        i += matched or 1
    return out


def runs(text, glossary=None, seen=None, skip=None):
    """Splits markdown-ish text into [(word, style, target, glue)].
    style is plain / bold / italic / code / link; target is the link address or None;
    glue is True when no space follows the word (e.g. a link right before a full stop)."""
    out = []
    pattern = r"(\[[^\]]+\]\([^)]*\)|`[^`]+`|\*\*[^*]+\*\*|\*[^*]+\*)"
    parts = [p for p in re.split(pattern, text) if p]
    for n, part in enumerate(parts):
        target = None
        m = re.match(r"\[([^\]]+)\]\(([^)]*)\)$", part)
        if m:
            style, part, target = "link", m.group(1), m.group(2)
        elif part.startswith("`"):
            style, part = "code", part[1:-1]
        elif part.startswith("**"):
            style, part = "bold", part[2:-2]
        elif part.startswith("*"):
            style, part = "italic", part[1:-1].replace("`", "")
        else:
            style = "plain"
        words = part.split(" ")
        next_glues = n + 1 < len(parts) and not parts[n + 1][0].isspace() and not part.endswith(" ")
        for i, word in enumerate(words):
            if not word:
                continue
            last = i == len(words) - 1
            out.append((word, style, target, last and next_glues))
    if glossary is not None:
        out = autolink(out, glossary, seen if seen is not None else set(), skip)
    return out


def wrap(words, fonts, width):
    """Greedy word-wrap. Returns lines, each a list of (word, style, x, target)."""
    lines, line, x = [], [], 0
    space = fonts["plain"].size(" ")[0]
    for word, style, target, glue in words:
        w = fonts[style].size(word)[0]
        if line and x + w > width:
            lines.append(line)
            line, x = [], 0
        line.append((word, style, x, target))
        x += w + (0 if glue else space)
    if line:
        lines.append(line)
    return lines


def draw_lines(surface, fonts, lines, left, top, color=BLACK, hits=None):
    """Draws wrapped lines. Link rectangles are appended to `hits` as (rect, target).
    Returns the y below the last line."""
    for line in lines:
        for word, style, x, target in line:
            tail = ""
            if style == "link":
                m = re.match(r"^(.*?\w)([^\w]*)$", word)       # keep trailing punctuation out of the link
                if m:
                    word, tail = m.group(1), m.group(2)
            surf = fonts[style].render(word, True, LINK_COLOR if style == "link" else
                                       CODE_COLOR if style == "code" else color)
            px = left + x
            if tail:
                surface.blit(fonts["plain"].render(tail, True, color), (px + surf.get_width(), top + 1))
            if style == "code":
                pygame.draw.rect(surface, CODE_BG, (px - 2, top, surf.get_width() + 4, LINE_H - 2), border_radius=3)
            surface.blit(surf, (px, top + 1))
            if target and hits is not None:
                hits.append((pygame.Rect(px, top, surf.get_width(), LINE_H), target))
        top += LINE_H
    return top


# ---- block parsing ----------------------------------------------------------

def parse_blocks(text):
    """Returns a list of blocks: (kind, data). kinds: h1 h2 h3 p bullet num code table"""
    blocks, para, lines = [], [], text.split("\n")

    def flush():
        if para:
            blocks.append(("p", " ".join(s.strip() for s in para)))
            para.clear()

    i = 0
    while i < len(lines):
        line = lines[i]
        stripped = line.strip()
        if stripped.startswith("```"):
            flush()
            code = []
            i += 1
            while i < len(lines) and not lines[i].strip().startswith("```"):
                code.append(lines[i])
                i += 1
            blocks.append(("code", code))
        elif not stripped:
            flush()
        elif re.fullmatch(r"!\[[^\]]*\]\([^)]+\)", stripped):
            flush()
            alt, src = re.fullmatch(r"!\[([^\]]*)\]\(([^)]+)\)", stripped).groups()
            blocks.append(("image", (alt, src)))
        elif stripped.startswith("### "):
            flush(); blocks.append(("h3", stripped[4:]))
        elif stripped.startswith("## "):
            flush(); blocks.append(("h2", stripped[3:]))
        elif stripped.startswith("# "):
            flush(); blocks.append(("h1", stripped[2:]))
        elif stripped.startswith("|"):
            flush()
            rows = []
            while i < len(lines) and lines[i].strip().startswith("|"):
                cells = [c.strip() for c in lines[i].strip().strip("|").split("|")]
                if not all(re.fullmatch(r":?-{2,}:?", c) for c in cells if c):
                    rows.append(cells)
                i += 1
            blocks.append(("table", rows))
            continue
        elif re.match(r"[-*] ", stripped):
            flush(); blocks.append(("bullet", stripped[2:]))
        elif re.match(r"\d+\. ", stripped):
            flush()
            n, rest = stripped.split(". ", 1)
            blocks.append(("num", (n, rest)))
        else:
            para.append(stripped)
        i += 1
    flush()
    return blocks


# ---- layout: draw the whole page onto one tall surface -----------------------

_image_cache = {}


def load_image(src):
    """Loads an image that sits next to this program, scaled to fit the page.
    Returns None if the file isn't there (the page just leaves it out)."""
    if src not in _image_cache:
        img = None
        path = os.path.join(HERE, src)
        if "://" not in src and os.path.exists(path):
            try:
                img = pygame.image.load(path).convert_alpha()
                scale = min(1.0, BODY_W / img.get_width(), MAX_IMAGE_H / img.get_height())
                if scale < 1.0:
                    img = pygame.transform.smoothscale(
                        img, (round(img.get_width() * scale), round(img.get_height() * scale)))
            except pygame.error:
                img = None
        _image_cache[src] = img
    return _image_cache[src]


def render_page(text, fonts):
    """Returns (surface, link_hits, title). Link rects are in surface coordinates."""
    text = re.sub(r"<!--.*?-->", "", text, flags=re.S)     # authors' notes, not shown
    blocks = parse_blocks(text)
    title = next((d for k, d in blocks if k == "h1"), "Document")
    hits = []

    glossary = glossary_index()
    seen = set()

    def paragraph_lines(t, width):
        return wrap(runs(t, glossary, seen), fonts, width)

    # First pass measures height, second draws, using one function with a dry-run flag.
    def layout(surface):
        seen.clear()                                 # each pass links the first use of each term
        y = 0
        for kind, data in blocks:
            if kind == "h1":
                continue                                    # shown in the fixed header
            if kind in ("h2", "h3"):
                y += 14
                if surface:
                    surf = fonts["h2"].render(data, True, HEAD_COLOR)
                    surface.blit(surf, (0, y))
                    pygame.draw.line(surface, (200, 205, 220), (0, y + 30), (BODY_W, y + 30), 1)
                y += 40
            elif kind == "p":
                lines = paragraph_lines(data, BODY_W)
                if surface:
                    draw_lines(surface, fonts, lines, 0, y, hits=hits)
                y += len(lines) * LINE_H + 12
            elif kind in ("bullet", "num"):
                marker, body = ("•", data) if kind == "bullet" else (data[0] + ".", data[1])
                lines = paragraph_lines(body, BODY_W - 40)
                if surface:
                    surface.blit(fonts["bold"].render(marker, True, HEAD_COLOR), (14, y + 1))
                    draw_lines(surface, fonts, lines, 40, y, hits=hits)
                y += len(lines) * LINE_H + 6
            elif kind == "image":
                alt, src = data
                img = load_image(src)
                if img is None:
                    continue
                if surface:
                    surface.blit(img, (0, y))
                    pygame.draw.rect(surface, (200, 200, 200), (0, y, img.get_width(), img.get_height()), 1)
                y += img.get_height() + 4
                if alt:
                    cap = wrap(runs(f"*{alt}*"), fonts, BODY_W)
                    if surface:
                        draw_lines(surface, fonts, cap, 0, y, color=GREY)
                    y += len(cap) * LINE_H
                y += 12
            elif kind == "code":
                height = len(data) * LINE_H + 16
                if surface:
                    pygame.draw.rect(surface, CODE_BG, (0, y, BODY_W, height), border_radius=6)
                    for j, code_line in enumerate(data):
                        surface.blit(fonts["code"].render(code_line, True, CODE_COLOR), (14, y + 8 + j * LINE_H))
                y += height + 12
            elif kind == "table":
                y = layout_table(surface, data, y)
        return y

    def layout_table(surface, rows, y):
        cols = max(len(r) for r in rows)
        # first column narrower, the rest share what's left
        first = BODY_W // 5
        widths = [first] + [(BODY_W - first) // (cols - 1)] * (cols - 1) if cols > 1 else [BODY_W]
        for r, row in enumerate(rows):
            wrapped = []
            for c in range(cols):
                cell = row[c] if c < len(row) else ""
                if r == 0:
                    cell = f"**{cell.replace(chr(96), '')}**" if cell else ""
                wrapped.append(wrap(runs(cell, glossary, seen), fonts, widths[c] - 16))
            height = max(1, max(len(w) for w in wrapped)) * LINE_H + 10
            if surface:
                pygame.draw.rect(surface, (225, 232, 245) if r == 0 else CARD_BG, (0, y, BODY_W, height))
                x = 0
                for c in range(cols):
                    draw_lines(surface, fonts, wrapped[c], x + 8, y + 5, hits=hits)
                    x += widths[c]
                    if c:
                        pygame.draw.line(surface, (210, 210, 210), (x - widths[c], y), (x - widths[c], y + height))
                pygame.draw.line(surface, (210, 210, 210), (0, y + height), (BODY_W, y + height))
            y += height
        if surface:
            pygame.draw.rect(surface, (210, 210, 210), (0, y - sum_heights(rows, widths, cols) , BODY_W,
                                                        sum_heights(rows, widths, cols)), 1)
        return y + 14

    def sum_heights(rows, widths, cols):
        total = 0
        for r, row in enumerate(rows):
            n = 1
            for c in range(cols):
                cell = row[c] if c < len(row) else ""
                if r == 0 and cell:
                    cell = f"**{cell.replace(chr(96), '')}**"
                n = max(n, len(wrap(runs(cell), fonts, widths[c] - 16)))
            total += n * LINE_H + 10
        return total

    height = layout(None) + 20
    surface = pygame.Surface((BODY_W, height), pygame.SRCALPHA)
    layout(surface)
    return surface, hits, title


# ---- tooltips and the Back button ---------------------------------------------

BACK_RECT = pygame.Rect(SCREEN_W - MARGIN - 80, 14, 80, 30)
_definitions = None


def definition_of(heading):
    """The glossary's text for an entry, read from glossary.md (cached)."""
    global _definitions
    if _definitions is None:
        import glossary_viewer
        _definitions = dict(glossary_viewer.load_entries()[1])
    return _definitions.get(heading)


def draw_back_button(screen, fonts, label="< Back"):
    hover = BACK_RECT.collidepoint(pygame.mouse.get_pos())
    pygame.draw.rect(screen, (190, 215, 250) if hover else (215, 230, 250), BACK_RECT, border_radius=6)
    pygame.draw.rect(screen, LINK_COLOR, BACK_RECT, 2, border_radius=6)
    text = fonts["bold"].render(label, True, LINK_COLOR)
    screen.blit(text, text.get_rect(center=BACK_RECT.center))


def draw_tooltip(screen, fonts, heading, pos, hint=True):
    """A small box near `pos` with the glossary's first sentence for `heading`."""
    definition = definition_of(heading)
    if definition is None:
        return
    first = re.split(r"(?<=[.!?])\s+", definition)[0]
    width = 400
    lines = wrap(runs(first), fonts, width - 20)[:4]
    title = heading.split(" (")[0]
    height = 12 + 24 + len(lines) * LINE_H + (20 if hint else 0)
    rect = pygame.Rect(pos[0] + 14, pos[1] + 20, width, height)
    rect.right = min(rect.right, SCREEN_W - 8)
    if rect.bottom > SCREEN_H - 8:
        rect.bottom = pos[1] - 8
    pygame.draw.rect(screen, (255, 255, 235), rect, border_radius=8)
    pygame.draw.rect(screen, (150, 150, 120), rect, 1, border_radius=8)
    screen.blit(fonts["bold"].render(title, True, HEAD_COLOR), (rect.x + 10, rect.y + 8))
    draw_lines(screen, fonts, lines, rect.x + 10, rect.y + 32)
    if hint:
        screen.blit(fonts["small"].render("Click for the full entry", True, GREY), (rect.x + 10, rect.bottom - 20))


def set_hand_cursor(on):
    try:
        pygame.mouse.set_cursor(pygame.SYSTEM_CURSOR_HAND if on else pygame.SYSTEM_CURSOR_ARROW)
    except (pygame.error, AttributeError):
        pass


# ---- the screen --------------------------------------------------------------

def resolve_markdown(target):
    """Returns an absolute path if `target` is a local .md file next to this program, else None."""
    if not target or "://" in target or not target.lower().endswith(".md"):
        return None
    path = os.path.join(HERE, target)
    return path if os.path.exists(path) else None


def run_markdown_viewer(screen, path):
    """Shows a markdown file. Returns True if the window was closed, False for Esc (back)."""
    fonts = make_fonts()
    try:
        with open(path, encoding="utf-8") as f:
            text = f.read()
    except OSError:
        text = "# Not found\n\nCouldn't read " + os.path.basename(path)
    page, hits, title = render_page(text, fonts)

    pygame.display.set_caption(f"Line Follower AI — {title}")
    clock = pygame.time.Clock()
    view_top, view_h = HEADER_H, SCREEN_H - HEADER_H - FOOTER_H
    max_scroll = max(0, page.get_height() - view_h)
    scroll = 0
    clamp = lambda v: max(0, min(max_scroll, v))

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
                elif event.key == pygame.K_UP:
                    scroll = clamp(scroll - 40)
                elif event.key == pygame.K_DOWN:
                    scroll = clamp(scroll + 40)
                elif event.key == pygame.K_PAGEUP:
                    scroll = clamp(scroll - view_h + 40)
                elif event.key == pygame.K_PAGEDOWN:
                    scroll = clamp(scroll + view_h - 40)
                elif event.key == pygame.K_HOME:
                    scroll = 0
                elif event.key == pygame.K_END:
                    scroll = max_scroll
            elif event.type == pygame.MOUSEWHEEL:
                scroll = clamp(scroll - event.y * 50)
            elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1 and BACK_RECT.collidepoint(event.pos):
                running = False
            elif event.type == pygame.KEYDOWN and event.key == pygame.K_BACKSPACE:
                running = False
            elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                for rect, target in hits:
                    shifted = rect.move(MARGIN, view_top - scroll)
                    if not (shifted.collidepoint(event.pos) and view_top <= event.pos[1] < view_top + view_h):
                        continue
                    if target.startswith("glossary:"):
                        import glossary_viewer
                        closed = glossary_viewer.run_glossary_viewer(screen, start_term=target[len("glossary:"):])
                    elif resolve_markdown(target):
                        closed = run_markdown_viewer(screen, resolve_markdown(target))
                    else:
                        continue
                    if closed:
                        running, window_closed = False, True
                    pygame.display.set_caption(f"Line Follower AI — {title}")
                    break

        screen.fill(BG_COLOR)
        screen.blit(page, (MARGIN, view_top), pygame.Rect(0, scroll, BODY_W, view_h))

        if max_scroll:
            track = pygame.Rect(SCREEN_W - MARGIN + 4, view_top, 8, view_h)
            pygame.draw.rect(screen, (225, 225, 225), track, border_radius=4)
            thumb_h = max(30, int(view_h * view_h / page.get_height()))
            thumb_y = track.y + int((view_h - thumb_h) * scroll / max_scroll)
            pygame.draw.rect(screen, GREY, (track.x, thumb_y, track.w, thumb_h), border_radius=4)

        pygame.draw.rect(screen, BG_COLOR, (0, 0, SCREEN_W, HEADER_H))
        head = fonts["h1"].render(title, True, BLACK)
        if head.get_width() > SCREEN_W - 2 * MARGIN - 85:             # long titles: use the smaller font
            head = fonts["h2"].render(title, True, BLACK)
        screen.blit(head, (MARGIN, 14))
        pygame.draw.rect(screen, BG_COLOR, (0, SCREEN_H - FOOTER_H, SCREEN_W, FOOTER_H))
        screen.blit(fonts["small"].render("Scroll: wheel / arrows / PgUp / PgDn      Blue words: hover or click      Esc / Back: return",
                                          True, GREY), (MARGIN, SCREEN_H - 24))
        draw_back_button(screen, fonts)
        mouse = pygame.mouse.get_pos()
        hovered = next((t for r, t in hits if r.move(MARGIN, view_top - scroll).collidepoint(mouse)
                        and view_top <= mouse[1] < view_top + view_h), None)
        set_hand_cursor(hovered is not None or BACK_RECT.collidepoint(mouse))
        if hovered and hovered.startswith("glossary:"):
            draw_tooltip(screen, fonts, hovered[len("glossary:"):], mouse)
        pygame.display.flip()

    set_hand_cursor(False)
    return window_closed
