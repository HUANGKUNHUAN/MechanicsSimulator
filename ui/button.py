"""Simple clickable button with a minimum 44 px hit area."""
import pygame


class Button:
    """A rectangular button that reports clicks (hit area >= 44 px)."""

    def __init__(self, x, y, w, h, label):
        self.x = x
        self.y = y
        self.w = max(w, 44)
        self.h = max(h, 44)
        self.label = label

    def hit(self, pos) -> bool:
        """True if the position falls inside the button."""
        return self.x <= pos[0] <= self.x + self.w and self.y <= pos[1] <= self.y + self.h

    def handle_event(self, event) -> bool:
        """Return True on a left-click inside the button."""
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            return self.hit(event.pos)
        return False

    def draw(self, screen, font) -> None:
        """Draw the button rectangle and its centered label."""
        rect = pygame.Rect(self.x, self.y, self.w, self.h)
        pygame.draw.rect(screen, (70, 70, 90), rect)
        pygame.draw.rect(screen, (150, 150, 170), rect, 2)
        surf = font.render(self.label, True, (230, 230, 230))
        tw, th = surf.get_size()
        screen.blit(surf, (self.x + (self.w - tw) // 2, self.y + (self.h - th) // 2))
