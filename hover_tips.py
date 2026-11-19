"""
GLOSSARY HOVER TIPS FOR THE APP SCREENS
=======================================
Lets a screen mark pieces of its text (or a shape) as "this is a glossary
term". Hovering over one shows a small box with the first sentence of that
term's glossary entry; clicking it opens the glossary at the entry.

How a screen uses it:

    tips = HoverTips()
    ...each frame...
    tips.begin()                                    # forget last frame's hot spots
    tips.add(screen.blit(text_surface, pos), "Fitness")        # clickable text
    tips.add(circle_rect, "Neuron", click=False)               # tooltip only
    tips.segments(screen, font, [("Gen 3", "Generation"), ("alive 5/40", "Population")], (10, 10))
    tips.draw(screen)                               # underlines, tooltip, cursor
    pygame.display.flip()
    ...in the event loop...
    closed = tips.click(screen, event.pos)          # None = not on a term
    if closed is not None: ...                      # closed True = the window was closed

Terms are the headings in glossary.md, e.g. "Hidden neuron / hidden node".
"""

import pygame

from markdown_viewer import make_fonts, draw_tooltip, set_hand_cursor, definition_of, LINK_COLOR


class HoverTips:
    def __init__(self):
        self.spots = []          # (rect, term, clickable)
        self._fonts = None

    # ---- recording ---------------------------------------------------------
    def begin(self):
        self.spots = []

    def add(self, rect, term, click=True):
        """Marks `rect` as a glossary term. click=False gives a tooltip only,
        for things that already do something when clicked."""
        if term is not None and rect is not None:
            self.spots.append((pygame.Rect(rect), term, click))

    def segments(self, screen, font, parts, pos, color=(20, 20, 20), sep="  |  "):
        """Draws pieces of one line side by side. parts = [(text, term or None)].
        Returns the x just past the last piece."""
        x, y = pos
        for i, (text, term) in enumerate(parts):
            if i:
                x += screen.blit(font.render(sep, True, color), (x, y)).width
            rect = screen.blit(font.render(text, True, color), (x, y))
            self.add(rect, term)
            x += rect.width
        return x

    # ---- using it ----------------------------------------------------------
    def spot_at(self, pos):
        for rect, term, click in reversed(self.spots):     # later drawn = on top
            if rect.collidepoint(pos):
                return term, click
        return None

    def click(self, screen, pos):
        """Opens the glossary if `pos` is on a clickable term. Returns None if it
        wasn't, else True if the window was closed while the glossary was open."""
        hit = self.spot_at(pos)
        if hit is None or not hit[1] or definition_of(hit[0]) is None:
            return None
        import glossary_viewer                       # imported here: it imports this package's viewers
        caption = pygame.display.get_caption()[0]
        closed = glossary_viewer.run_glossary_viewer(screen, start_term=hit[0])
        pygame.display.set_caption(caption)
        return bool(closed)

    def draw(self, screen):
        """Dotted underline under clickable text, plus the tooltip and hand cursor."""
        for rect, term, click in self.spots:
            if click and rect.height <= 40:
                for x in range(rect.left, rect.right, 5):
                    pygame.draw.line(screen, LINK_COLOR, (x, rect.bottom), (min(x + 2, rect.right), rect.bottom))
        mouse = pygame.mouse.get_pos()
        hit = self.spot_at(mouse)
        set_hand_cursor(bool(hit and hit[1]))
        if hit and definition_of(hit[0]) is not None:
            if self._fonts is None:
                self._fonts = make_fonts()
            draw_tooltip(screen, self._fonts, hit[0], mouse, hint=hit[1])
