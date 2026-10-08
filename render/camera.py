"""World-to-screen coordinate transform (meters, y-up -> pixels, y-down)."""
from core.vector2 import Vec2


class Camera:
    """Maps physics world coordinates (m, y-up) to screen pixels (y-down)."""

    def __init__(self, ppm: float, screen_size, origin_y=None):
        self.ppm = ppm
        self.sw, self.sh = screen_size
        self.origin_x = self.sw // 2
        # 世界原点 y=0 放到屏幕下部，给滑块留空间 / put world y=0 near the bottom,
        # leaving room for the sliders.
        self.origin_y = self.sh - 220 if origin_y is None else origin_y

    @property
    def pixels_per_meter(self) -> float:
        """Pixels-per-meter scale (world length -> pixel length)."""
        return self.ppm

    def to_screen(self, x: float, y: float):
        """Convert a world point to an integer screen pixel position."""
        sx = int(round(self.origin_x + x * self.ppm))
        sy = int(round(self.origin_y - y * self.ppm))  # y 翻转 / y flip
        return sx, sy

    def world_to_screen(self, p: Vec2):
        """Convert a world Vec2 point to an integer screen pixel position."""
        return self.to_screen(p.x, p.y)

    def resize(self, screen_size) -> None:
        """Update screen size and recompute the origin on window resize."""
        self.sw, self.sh = screen_size
        self.origin_x = self.sw // 2
        self.origin_y = self.sh - 220
