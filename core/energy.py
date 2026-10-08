"""Energy and work accounting: kinetic, potential, and cumulative work (SI units)."""
from core.vector2 import Vec2


def kinetic_energy(body) -> float:
    """Kinetic energy K = 1/2 m v^2 (0 for static bodies)."""
    if body.is_static:
        return 0.0
    return 0.5 * body.mass * body.velocity.dot(body.velocity)


def spring_potential(spring) -> float:
    """Spring potential U_s = 1/2 k (dist - rest_length)^2."""
    a = spring.a.position if hasattr(spring.a, "position") else spring.a
    b = spring.b.position if hasattr(spring.b, "position") else spring.b
    dx = (b - a).length() - spring.rest_length
    return 0.5 * spring.k * dx * dx


def gravitational_potential(body, y0: float, g: float = 9.81) -> float:
    """Gravitational potential U_g = m g (y - y0)."""
    if body.is_static:
        return 0.0
    return body.mass * g * (body.position.y - y0)


def energy_report(world, y0: float = 0.0, g: float = 9.81) -> dict:
    """Aggregate K, U_s, U_g, E_mech and work totals for a world."""
    K = sum(kinetic_energy(b) for b in world.bodies)
    Us = sum(spring_potential(s) for s in world.springs)
    Ug = sum(gravitational_potential(b, y0, g) for b in world.bodies)
    tr = world.energy
    return {
        "K": K,
        "U_s": Us,
        "U_g": Ug,
        "E_mech": K + Us + Ug,
        "W_total": tr.total_work(),
        "impulse_loss": tr.impulse_loss,
        "k_initial": tr.k_initial,
        "work": dict(tr.work),
    }


class EnergyTracker:
    """Accumulates per-force work, impulse losses and the initial kinetic energy."""

    def __init__(self):
        self.work = {}           # 分力功 label -> 累计 F·dx (J) / per-force work
        self.impulse_loss = 0.0  # 碰撞/落地瞬时动能损失 (J) / instantaneous KE loss
        self.k_initial = None    # 重置时的初动能 K1 (J) / initial kinetic energy

    def record_work(self, label: str, force: Vec2, dx: Vec2) -> None:
        """Accumulate the work done by one labeled force over a displacement."""
        self.work[label] = self.work.get(label, 0.0) + force.dot(dx)

    def record_impulse_loss(self, delta_ke: float) -> None:
        """Accumulate an instantaneous kinetic-energy change (collision/landing)."""
        self.impulse_loss += delta_ke

    def total_work(self) -> float:
        """Sum of all labeled work (J)."""
        return sum(self.work.values())

    def reset(self, k0: float) -> None:
        """Clear work/loss and capture the initial kinetic energy K1."""
        self.work.clear()
        self.impulse_loss = 0.0
        self.k_initial = k0
