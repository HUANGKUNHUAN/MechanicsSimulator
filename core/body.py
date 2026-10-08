"""Axis-aligned rigid body with force accumulator and impulse response."""
from core.vector2 import Vec2


class Body:
    """Axis-aligned rigid body with force accumulator and impulse response."""

    def __init__(self, mass, position, velocity=None, width=1.0, height=1.0,
                 restitution=0.0, is_static=False):
        self.is_static = is_static
        # 静态体用无穷大质量表示，inv_mass 恒为 0，永不参与除法 / Static bodies use
        # infinite mass so inv_mass stays 0 and they never take part in division.
        self.mass = float("inf") if is_static else mass
        self.position = position
        self.velocity = velocity if velocity is not None else Vec2(0.0, 0.0)
        self.width = width
        self.height = height
        self.restitution = restitution
        self.force_accumulator = Vec2(0.0, 0.0)
        self.labeled_forces = {}  # 分力记账 label -> 力矢量 / per-label force stash
        self.trail = []  # 位置历史，后续轮次用于残影 / reserved for trails later

    @property
    def inv_mass(self) -> float:
        """Inverse mass; 0 for static or zero-mass bodies to avoid division by zero."""
        if self.is_static or self.mass == 0:
            return 0.0
        return 1.0 / self.mass

    @property
    def bottom(self) -> float:
        """Lowest y of the AABB (y-up math coordinates)."""
        return self.position.y - self.height / 2.0

    def clear_forces(self) -> None:
        """Reset the accumulated force and labeled-force stash to zero."""
        self.force_accumulator = Vec2(0.0, 0.0)
        self.labeled_forces.clear()

    def add_force(self, f: Vec2) -> None:
        """Accumulate a force (N) onto this body."""
        self.force_accumulator = self.force_accumulator + f

    def add_labeled_force(self, label: str, f: Vec2) -> None:
        """Accumulate a labeled force for per-force work accounting."""
        self.labeled_forces[label] = self.labeled_forces.get(label, Vec2(0.0, 0.0)) + f

    def apply_impulse(self, j: Vec2) -> None:
        """Change velocity by an impulse: v += j / m (no-op for static bodies)."""
        self.velocity = self.velocity + j * self.inv_mass
