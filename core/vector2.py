"""Two-dimensional vector with component-wise arithmetic (pure Python)."""
from dataclasses import dataclass
from math import sqrt


@dataclass
class Vec2:
    """Two-component vector with component-wise arithmetic."""
    x: float
    y: float

    def __add__(self, o: "Vec2") -> "Vec2":
        return Vec2(self.x + o.x, self.y + o.y)

    def __sub__(self, o: "Vec2") -> "Vec2":
        return Vec2(self.x - o.x, self.y - o.y)

    def __mul__(self, s: float) -> "Vec2":
        return Vec2(self.x * s, self.y * s)

    __rmul__ = __mul__

    def __truediv__(self, s: float) -> "Vec2":
        return Vec2(self.x / s, self.y / s)

    def __neg__(self) -> "Vec2":
        return Vec2(-self.x, -self.y)

    def dot(self, o: "Vec2") -> float:
        """Dot product."""
        return self.x * o.x + self.y * o.y

    def length(self) -> float:
        """Euclidean length."""
        return sqrt(self.x * self.x + self.y * self.y)

    def normalized(self) -> "Vec2":
        """Unit vector; returns (0, 0) for the zero vector (no division by zero)."""
        l = self.length()
        if l == 0.0:
            return Vec2(0.0, 0.0)
        return self / l
