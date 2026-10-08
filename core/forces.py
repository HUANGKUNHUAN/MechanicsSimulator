"""Force models: functions body -> Vec2, plus the Spring two-endpoint force."""
from core.vector2 import Vec2
from core.body import Body


def gravity(body, g: float = 9.81) -> Vec2:
    """Constant downward gravity (0, -m*g)."""
    return Vec2(0.0, -body.mass * g)


def constant_force(body, f: Vec2) -> Vec2:
    """Constant external force (slider-driven horizontal push)."""
    return f


class Spring:
    """Hooke spring between two endpoints (a Body or a fixed Vec2 anchor)."""

    def __init__(self, a, b, rest_length, k, c=0.0):
        self.a = a
        self.b = b
        self.rest_length = rest_length
        self.k = k
        self.c = c

    @staticmethod
    def _pos(e):
        return e.position if isinstance(e, Body) else e

    @staticmethod
    def _vel(e):
        return e.velocity if isinstance(e, Body) else Vec2(0.0, 0.0)

    def apply(self) -> None:
        """Apply spring and damping forces to both endpoints."""
        pa, pb = self._pos(self.a), self._pos(self.b)
        va, vb = self._vel(self.a), self._vel(self.b)
        d = pb - pa
        dist = d.length()
        if dist == 0.0:
            return
        # a→b 单位方向 / unit direction from a to b
        n = d / dist
        # 沿弹簧轴的相对速度 / relative velocity along the spring axis
        rel_v = (vb - va).dot(n)
        # 力 = 胡克恢复力 + 阻尼 / force = Hooke + damping
        F = (self.k * (dist - self.rest_length) + self.c * rel_v) * n
        if isinstance(self.a, Body):
            self.a.add_force(F)
            self.a.add_labeled_force("spring", F)
        if isinstance(self.b, Body):
            self.b.add_force(-F)
            self.b.add_labeled_force("spring", -F)
