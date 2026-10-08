"""Energy/work HUD: renders a compact text panel of energy and work values."""
import pygame


def draw_hud(screen, font, lines, pos=(10, 40)) -> None:
    """Draw a list of (text, color) lines from the top-left corner."""
    x, y = pos
    line_h = 22
    for text, color in lines:
        surf = font.render(text, True, color)
        screen.blit(surf, (x, y))
        y += line_h
