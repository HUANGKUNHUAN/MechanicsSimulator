"""Fading motion trail: a fixed-length queue of past body positions."""
from collections import deque
import pygame


class Trail:
    """Records body positions and draws a fading dot trail (oldest = faintest)."""

    def __init__(self, max_length: int = 150, color=(100, 200, 255)):
        self.max_length = max_length
        self.color = color
        self.enabled = True
        self.points = deque()

    def record(self, position) -> None:
        """Append the current position, dropping the oldest beyond max_length."""
        if not self.enabled:
            return
        self.points.append(position)
        while len(self.points) > self.max_length:
            self.points.popleft()

    def clear(self) -> None:
        """Empty the recorded history."""
        self.points.clear()

    def draw(self, screen, camera) -> None:
        """Draw the trail as dots whose alpha fades toward the oldest point."""
        if not self.enabled or len(self.points) < 2:
            return
        surf = pygame.Surface((screen.get_width(), screen.get_height()), pygame.SRCALPHA)
        n = len(self.points)
        for i, p in enumerate(self.points):
            # 越旧越透明 / older points are more transparent
            alpha = int(30 + 180 * (i + 1) / n)
            x, y = camera.world_to_screen(p)
            pygame.draw.circle(surf, (*self.color, alpha), (x, y), 4)
        screen.blit(surf, (0, 0))
