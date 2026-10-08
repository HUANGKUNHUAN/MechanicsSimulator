"""Self-drawn draggable horizontal slider (no pygame_gui dependency)."""
import pygame

HITBOX = 44  # 命中区边长（像素）/ hit area edge in pixels


class Slider:
    """Self-drawn horizontal slider with mouse-drag interaction."""

    def __init__(self, x, y, w, label, min_val, max_val, value, fmt=".2f"):
        self.x = x
        self.y = y
        self.w = w
        self.label = label
        self.min = min_val
        self.max = max_val
        self.fmt = fmt
        self.knob_r = 8
        self.dragging = False
        self._value = value

    @property
    def value(self) -> float:
        """Current slider value."""
        return self._value

    def _frac(self) -> float:
        return (self._value - self.min) / (self.max - self.min)

    def _set_frac(self, frac: float) -> None:
        frac = max(0.0, min(1.0, frac))
        self._value = self.min + frac * (self.max - self.min)

    def _knob_x(self) -> int:
        return self.x + int(self._frac() * self.w)

    def handle_event(self, event) -> bool:
        """Handle a pygame event; returns True if the value changed."""
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            # 44×44 px 命中区，比可视滑块头更大，便于点中 / hit area larger than the knob
            if (abs(event.pos[0] - self._knob_x()) <= HITBOX // 2
                    and abs(event.pos[1] - self.y) <= HITBOX // 2):
                self.dragging = True
        elif event.type == pygame.MOUSEBUTTONUP and event.button == 1:
            self.dragging = False
        elif event.type == pygame.MOUSEMOTION and self.dragging:
            self._set_frac((event.pos[0] - self.x) / self.w)
            return True
        return False

    def draw(self, screen, font) -> None:
        """Draw the track, knob, label and current value."""
        pygame.draw.line(screen, (90, 90, 90),
                         (self.x, self.y), (self.x + self.w, self.y), 3)
        pygame.draw.circle(screen, (220, 220, 220), (self._knob_x(), self.y), self.knob_r)
        txt = f"{self.label}  {self._value:{self.fmt}}"
        surf = font.render(txt, True, (255, 255, 255))
        screen.blit(surf, (self.x, self.y - 28))
