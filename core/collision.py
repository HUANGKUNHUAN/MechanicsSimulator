"""Ground plane contact plus AABB collision detection and impulse resolution."""
from core.vector2 import Vec2

_EPS = 1e-2       # 速度阈值，低于它视为静止（粘住）/ velocity below this counts as rest
_TOL = 1e-6       # 接触判定容差（米）/ contact detection tolerance in meters
_REST_EPS = 0.1   # 碰撞低速阈值：低于此按非弹性处理，防抖动 / below this treat as inelastic


def _sign(x: float) -> float:
    return 1.0 if x >= 0.0 else -1.0


class Ground:
    """Horizontal ground plane with normal support, Coulomb friction and landing fix."""

    def __init__(self, y: float, mu_s: float = 0.5, mu_d: float = 0.3,
                 g: float = 9.81, restitution: float = 0.0):
        self.y = y
        self.mu_s = mu_s
        self.mu_d = mu_d
        self.g = g
        self.restitution = restitution

    def in_contact(self, b) -> bool:
        """True if the body's bottom touches (or slightly penetrates) the ground."""
        return b.bottom <= self.y + _TOL

    def normal_force(self, b) -> float:
        """Support force magnitude N = m*g (exactly cancels gravity when resting)."""
        return b.mass * self.g

    def friction(self, b, external_x: float) -> Vec2:
        """Coulomb friction: static threshold when at rest, kinetic when sliding."""
        N = b.mass * self.g
        vx = b.velocity.x
        if abs(vx) < _EPS:
            # 静止：外力未超静摩擦上限 → 静摩擦恰好抵消 / at rest: below the static
            # limit, friction cancels the external push exactly.
            if abs(external_x) <= self.mu_s * N:
                return Vec2(-external_x, 0.0)
            # 突破静摩擦上限 → 进入动摩擦 / exceeds static limit: break free
            return Vec2(-_sign(external_x) * self.mu_d * N, 0.0)
        # 滑动：动摩擦与速度反向 / sliding: kinetic friction opposes velocity
        return Vec2(-_sign(vx) * self.mu_d * N, 0.0)

    def resolve(self, b) -> None:
        """Lift the body out of penetration and kill downward velocity on landing."""
        if b.bottom < self.y:
            b.position = Vec2(b.position.x, self.y + b.height / 2.0)
            if b.velocity.y < 0.0:
                b.velocity = Vec2(b.velocity.x, -b.velocity.y * self.restitution)


def aabb_overlap(a, b):
    """Return (penetration_depth, normal) if the two AABBs overlap, else None.

    Only axis-aligned boxes are supported (rotation is not considered).
    """
    a_l = a.position.x - a.width / 2.0
    a_r = a.position.x + a.width / 2.0
    a_b = a.position.y - a.height / 2.0
    a_t = a.position.y + a.height / 2.0
    b_l = b.position.x - b.width / 2.0
    b_r = b.position.x + b.width / 2.0
    b_b = b.position.y - b.height / 2.0
    b_t = b.position.y + b.height / 2.0
    ox = min(a_r, b_r) - max(a_l, b_l)
    oy = min(a_t, b_t) - max(a_b, b_b)
    if ox <= 0.0 or oy <= 0.0:
        return None
    # 最小穿透轴即碰撞法线 / the minimum penetration axis is the collision normal
    if ox < oy:
        n = Vec2(1.0, 0.0) if b.position.x > a.position.x else Vec2(-1.0, 0.0)
        return ox, n
    n = Vec2(0.0, 1.0) if b.position.y > a.position.y else Vec2(0.0, -1.0)
    return oy, n


def resolve_collision(a, b, depth, normal, e) -> None:
    """Apply collision impulse and positional separation.

    Formulas: v_rel = v_b - v_a;
              j = -(1+e)(v_rel·n) / (1/m_a + 1/m_b);
              v_a -= (j/m_a) n,  v_b += (j/m_b) n.
    """
    inv_a, inv_b = a.inv_mass, b.inv_mass
    total_inv = inv_a + inv_b
    if total_inv == 0.0:
        return
    # 相对速度沿法线分量 / relative velocity along the normal
    v_rel = b.velocity - a.velocity
    v_rel_n = v_rel.dot(normal)
    if v_rel_n < 0.0:
        # 低速接触按完全非弹性，避免静止时抖动 / slow contact -> inelastic to avoid jitter
        if abs(v_rel_n) < _REST_EPS:
            e = 0.0
        # 冲量大小 j = -(1+e)(v_rel·n) / (1/m_a + 1/m_b) / impulse magnitude
        j = -(1.0 + e) * v_rel_n / total_inv
        a.velocity -= normal * (j * inv_a)
        b.velocity += normal * (j * inv_b)
    # 位置修正：按逆质量比例分离，防止穿透 / positional separation by inverse mass
    a.position -= normal * (depth * inv_a / total_inv)
    b.position += normal * (depth * inv_b / total_inv)
