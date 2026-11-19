"""
GLOSSARY VIEWER
===============
Shows glossary.md inside the tool. The words are read from the file every time,
so editing glossary.md changes what you see here.

  Mouse wheel / Up / Down / PgUp / PgDn / Home / End   scroll
  A-Z                                                  jump to a word
  Blue words                                           click to open that word's entry
  Backspace                                            back to where you were
  Esc                                                  back to the menu
"""

import os
import re

import pygame

from line_follower_ai import SCREEN_W, SCREEN_H, BG_COLOR, BLACK
from markdown_viewer import (runs, wrap, draw_lines, make_fonts, resolve_markdown, run_markdown_viewer,
                             glossary_index, BACK_RECT, draw_back_button, draw_tooltip, set_hand_cursor)

GLOSSARY_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "glossary.md")

GREY = (130, 130, 130)
TERM_COLOR = (20, 60, 140)
CODE_COLOR = (150, 40, 40)
CODE_BG = (232, 232, 238)
CARD_BG = (255, 255, 255)

MARGIN = 50
HEADER_H = 70
FOOTER_H = 30
CARD_PAD = 12
CARD_GAP = 10


def load_entries(path=GLOSSARY_PATH):
    """Returns (intro, entries). entries is a list of (term, definition) with markdown left in."""
    try:
        with open(path, encoding="utf-8") as f:
            text = f.read()
    except OSError:
        return None, []
    text = re.sub(r"<!--.*?-->", "", text, flags=re.S)     # authors' notes, not shown
    intro, entries = "", []
    for block in re.split(r"\n\s*\n", text):
        block = " ".join(block.split())
        m = re.match(r"\*\*(.+?)\*\*\s*[—-]\s*(.*)", block)
        if m:
            entries.append((m.group(1), m.group(2)))
        elif block and not block.startswith("#"):
            intro = block
    return intro, entries


def run_glossary_viewer(screen, start_term=None):
    """Returns True if the window was closed, False for Esc (back to menu).
    start_term: the heading of an entry to scroll to when the page opens."""
    pygame.display.set_caption("Line Follower AI — glossary")
    clock = pygame.time.Clock()
    title_font = pygame.font.SysFont("consolas,menlo,dejavusansmono,couriernew,monospace", 32, bold=True)
    term_font = pygame.font.SysFont("consolas,menlo,dejavusansmono,couriernew,monospace", 20, bold=True)
    small = pygame.font.SysFont("consolas,menlo,dejavusansmono,couriernew,monospace", 15)
    fonts = make_fonts()
    line_h = 22

    intro, entries = load_entries()
    index = glossary_index()
    text_w = SCREEN_W - 2 * MARGIN - 2 * CARD_PAD - 12     # room for the scrollbar

    # Lay out every card once: (term, wrapped_lines, top, height)
    cards, y = [], 0
    for term, definition in entries:
        lines = wrap(runs(definition, index, set(), skip=term), fonts, text_w)
        height = CARD_PAD * 2 + 26 + len(lines) * line_h
        cards.append((term, lines, y, height))
        y += height + CARD_GAP
    content_h = y
    view_top, view_h = HEADER_H, SCREEN_H - HEADER_H - FOOTER_H
    max_scroll = max(0, content_h - view_h)
    scroll = 0
    history = []                       # earlier scroll positions, for Backspace

    def clamp(v):
        return max(0, min(max_scroll, v))

    def jump_to_letter(ch):
        for term, _, top, _ in cards:
            if term.upper().startswith(ch):
                return top
        return None

    def top_of(term):
        return next((top for t, _, top, _ in cards if t == term), None)

    if start_term is not None and top_of(start_term) is not None:
        scroll = clamp(top_of(start_term))

    window_closed = False
    running = True
    last_hits = []
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
                elif event.key == pygame.K_BACKSPACE:
                    if history:
                        scroll = history.pop()
                    else:
                        running = False
                elif pygame.K_a <= event.key <= pygame.K_z:
                    target = jump_to_letter(chr(event.key).upper())
                    if target is not None:
                        scroll = clamp(target)
            elif event.type == pygame.MOUSEWHEEL:
                scroll = clamp(scroll - event.y * 50)
            elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1 and BACK_RECT.collidepoint(event.pos):
                if history:
                    scroll = history.pop()       # back to the previous word
                else:
                    running = False              # back to where you came from
            elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                for rect, target in last_hits:
                    if not (rect.collidepoint(event.pos) and view_top <= event.pos[1] < view_top + view_h):
                        continue
                    if target.startswith("glossary:"):
                        dest = top_of(target[len("glossary:"):])
                        if dest is not None:
                            history.append(scroll)
                            scroll = clamp(dest)
                    elif resolve_markdown(target):
                        if run_markdown_viewer(screen, resolve_markdown(target)):
                            running, window_closed = False, True
                        pygame.display.set_caption("Line Follower AI — glossary")
                    break

        screen.fill(BG_COLOR)
        hits = []

        # ---- cards (clipped to the scrolling area) --------------------------
        screen.set_clip(pygame.Rect(0, view_top, SCREEN_W, view_h))
        if not entries:
            screen.blit(fonts["plain"].render("Couldn't read glossary.md (is it next to menu.py?)",
                                              True, (200, 0, 0)), (MARGIN, view_top + 20))
        for term, lines, top, height in cards:
            cy = view_top + top - scroll
            if cy > view_top + view_h or cy + height < view_top:
                continue
            card = pygame.Rect(MARGIN, cy, SCREEN_W - 2 * MARGIN - 12, height)
            pygame.draw.rect(screen, CARD_BG, card, border_radius=8)
            pygame.draw.rect(screen, (210, 210, 210), card, 1, border_radius=8)
            screen.blit(term_font.render(term, True, TERM_COLOR), (card.x + CARD_PAD, card.y + CARD_PAD))
            ty = card.y + CARD_PAD + 26
            draw_lines(screen, fonts, lines, card.x + CARD_PAD, ty, hits=hits)
        screen.set_clip(None)

        # ---- scrollbar -------------------------------------------------------
        if max_scroll:
            track = pygame.Rect(SCREEN_W - MARGIN + 4, view_top, 8, view_h)
            pygame.draw.rect(screen, (225, 225, 225), track, border_radius=4)
            thumb_h = max(30, int(view_h * view_h / content_h))
            thumb_y = track.y + int((view_h - thumb_h) * scroll / max_scroll)
            pygame.draw.rect(screen, GREY, (track.x, thumb_y, track.w, thumb_h), border_radius=4)

        # ---- header / footer drawn over the scrolling area ---------------------
        pygame.draw.rect(screen, BG_COLOR, (0, 0, SCREEN_W, HEADER_H))
        screen.blit(title_font.render("Glossary", True, BLACK), (MARGIN, 14))
        if intro:
            short = intro.split(". ")[0].rstrip(".") + "."
            screen.blit(small.render(short, True, GREY), (MARGIN, 50))
        pygame.draw.rect(screen, BG_COLOR, (0, SCREEN_H - FOOTER_H, SCREEN_W, FOOTER_H))
        screen.blit(small.render("Scroll: wheel/arrows      A-Z: jump      Blue words: hover or click      Back / Esc: return",
                                 True, GREY), (MARGIN, SCREEN_H - 24))
        draw_back_button(screen, fonts)
        mouse = pygame.mouse.get_pos()
        hovered = next((t for r, t in hits if r.collidepoint(mouse) and view_top <= mouse[1] < view_top + view_h), None)
        set_hand_cursor(hovered is not None or BACK_RECT.collidepoint(mouse))
        if hovered and hovered.startswith("glossary:"):
            draw_tooltip(screen, fonts, hovered[len("glossary:"):], mouse)
        last_hits = hits
        pygame.display.flip()

    set_hand_cursor(False)
    return window_closed
