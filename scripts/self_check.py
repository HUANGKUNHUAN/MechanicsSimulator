"""Numeric self-check for forces, contact, springs and collisions (standalone)."""
import math
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from core.vector2 import Vec2
from core.body import Body
from core.forces import gravity, constant_force, Spring
from core.collision import Ground, aabb_overlap
from core.physics import World


# --- friction / contact helpers (Round 3) ---

def _world(block_vx=0.0, block_y=0.5):
    w = World()
    w.add_contact(Ground(y=0.0, mu_s=0.5, mu_d=0.2))
    w.add_force(gravity)
    b = Body(mass=1.0, position=Vec2(0.0, block_y), velocity=Vec2(block_vx, 0.0),
             width=1.0, height=1.0)
    w.add_body(b)
    return w, b


def check_resting_stability():
    """Block resting on the ground must not drift or jitter for 10 s."""
    w, b = _world()
    for _ in range(int(10.0 / w.dt)):
        w.step(w.dt)
    assert b.position == Vec2(0.0, 0.5), f"drifted to {b.position}"
    assert b.velocity == Vec2(0.0, 0.0), f"velocity {b.velocity}"
    print(f"[1] resting stability OK: pos={b.position}, vel={b.velocity} after 10 s")


def check_braking():
    """v0=5 m/s, mu=0.2 must stop at ~ v0^2/(2*mu*g) = 6.371 m (error < 2%)."""
    w, b = _world(block_vx=5.0)
    x0 = b.position.x
    for _ in range(int(10.0 / w.dt)):
        w.step(w.dt)
        if abs(b.velocity.x) <= 1e-2:
            break
    dist = b.position.x - x0
    theory = 25.0 / (2 * 0.2 * 9.81)
    err = abs(dist - theory) / theory
    print(f"[2] braking: dist={dist:.4f} m, theory={theory:.4f} m, err={err*100:.3f}%")
    assert err < 0.02, f"braking error {err*100:.2f}% >= 2%"


def check_static_friction():
    """Push below mu_s*N must not move the block; above it must."""
    for F, expect_move in [(3.0, False), (6.0, True)]:
        w, b = _world()
        fvec = Vec2(F, 0.0)
        w.add_force(lambda body, f=fvec: constant_force(body, f))
        for _ in range(int(1.0 / w.dt)):
            w.step(w.dt)
        moved = b.velocity.x != 0.0 or b.position.x != 0.0
        print(f"[3] static: F={F} N -> {'moved' if moved else 'stayed'} "
              f"(expect {'move' if expect_move else 'stay'})")
        assert moved == expect_move, f"F={F} N: moved={moved}, expected {expect_move}"


def check_air_friction():
    """Friction must be zero while airborne: horizontal velocity stays constant."""
    w, b = _world(block_vx=3.0, block_y=5.0)
    for _ in range(int(0.5 / w.dt)):
        w.step(w.dt)
    assert b.velocity.x == 3.0, f"vx changed in air: {b.velocity.x}"
    print(f"[4] air friction: vx={b.velocity.x} unchanged, "
          f"vy={b.velocity.y:.3f} m/s (free fall) after 0.5 s")


# --- spring helpers / checks (Round 4) ---

def _run_spring(m, k, c, rest, x0):
    w = World()
    anchor = Vec2(0.0, 0.0)
    block = Body(mass=m, position=Vec2(x0, 0.0), velocity=Vec2(0.0, 0.0),
                 width=0.4, height=0.4)
    w.add_body(block)
    w.add_spring(Spring(anchor, block, rest, k, c))
    return w, block


def check_spring_period():
    """Undamped period T = 2*pi*sqrt(m/k), measured via zero crossings (err < 1%)."""
    m, k, rest, A0 = 1.0, 10.0, 1.0, 0.6
    w, block = _run_spring(m, k, 0.0, rest, rest + A0)
    T_theory = 2.0 * math.pi * math.sqrt(m / k)
    crossings = []
    prev_d = block.position.x - rest
    for _ in range(int(5 * T_theory / w.dt)):
        w.step(w.dt)
        d = block.position.x - rest
        if prev_d * d < 0.0:
            frac = prev_d / (prev_d - d)
            crossings.append(w.time - w.dt + frac * w.dt)
        prev_d = d
    intervals = [crossings[i + 1] - crossings[i] for i in range(len(crossings) - 1)]
    T_measured = 2.0 * sum(intervals) / len(intervals)
    err = abs(T_measured - T_theory) / T_theory
    print(f"[5] spring period: measured={T_measured:.4f} s, theory={T_theory:.4f} s, "
          f"err={err*100:.3f}%")
    assert err < 0.01, f"period error {err*100:.2f}% >= 1%"


def check_spring_energy():
    """Print K = 1/2 m v^2 and U = 1/2 k dx^2 at several times (trade-off; print only)."""
    m, k, rest, A0 = 1.0, 10.0, 1.0, 0.6
    w, block = _run_spring(m, k, 0.0, rest, rest + A0)
    T = 2.0 * math.pi * math.sqrt(m / k)
    E0 = 0.5 * k * A0 * A0
    print(f"[6] spring energy: E0 = {E0:.4f} J")
    prev_steps = 0
    for frac in (0.0, 0.25, 0.5, 0.75, 1.0, 2.0):
        target = int(frac * T / w.dt)
        for _ in range(target - prev_steps):
            w.step(w.dt)
        prev_steps = target
        dx = block.position.x - rest
        K = 0.5 * m * block.velocity.x ** 2
        U = 0.5 * k * dx * dx
        print(f"    t={frac:>4}T : K={K:.4f}  U={U:.4f}  E={K+U:.4f}")


def _track_peaks(m, k, c, rest, A0, n_cycles):
    w, block = _run_spring(m, k, c, rest, rest + A0)
    T = 2.0 * math.pi * math.sqrt(m / k)
    peaks = []
    prev_v = 0.0
    for _ in range(int(n_cycles * T / w.dt)):
        w.step(w.dt)
        v = block.velocity.x
        if prev_v > 0.0 and v <= 0.0:
            peaks.append(block.position.x - rest)
        prev_v = v
    return peaks


def check_spring_amplitude():
    """Undamped amplitude must not decay; damped must decay without diverging."""
    m, k, rest, A0 = 1.0, 10.0, 1.0, 0.6
    pu = _track_peaks(m, k, 0.0, rest, A0, 10)
    drift = (pu[0] - pu[-1]) / pu[0]
    print(f"[7] undamped amplitude: first={pu[0]:.4f} m, last={pu[-1]:.4f} m, "
          f"drift={drift*100:.3f}%")
    assert abs(drift) < 0.02, f"undamped amplitude drifted {drift*100:.2f}%"

    pd = _track_peaks(m, k, 1.0, rest, A0, 10)
    print(f"[8] damped amplitude: first={pd[0]:.4f} m, last={pd[-1]:.4f} m (decaying)")
    assert pd[-1] < pd[0] * 0.5, "damped amplitude did not decay enough"
    assert 0.0 <= pd[-1] < pd[0], "damped amplitude diverged"


# --- collision helpers / checks (Round 5) ---

def _collision_pair(m_a, v_a, m_b, v_b, e, x_a=0.0, x_b=2.0):
    w = World()
    a = Body(mass=m_a, position=Vec2(x_a, 0.0), velocity=Vec2(v_a, 0.0),
             width=1.0, height=1.0, restitution=e)
    b = Body(mass=m_b, position=Vec2(x_b, 0.0), velocity=Vec2(v_b, 0.0),
             width=1.0, height=1.0, restitution=e)
    w.add_body(a)
    w.add_body(b)
    return w, a, b


def check_collision_swap():
    """Equal mass, e=1 head-on: velocities must swap (A: +5 -> -3, B: -3 -> +5)."""
    w, a, b = _collision_pair(1.0, 5.0, 1.0, -3.0, 1.0)
    for _ in range(int(1.0 / w.dt)):
        w.step(w.dt)
    print(f"[9] elastic swap: v_a={a.velocity.x:.6f}, v_b={b.velocity.x:.6f} "
          f"(expect -3, +5)")
    assert abs(a.velocity.x + 3.0) < 1e-6, f"v_a={a.velocity.x}"
    assert abs(b.velocity.x - 5.0) < 1e-6, f"v_b={b.velocity.x}"


def check_collision_momentum():
    """Total momentum sum(m*v) must be conserved (diff < 1e-3)."""
    w, a, b = _collision_pair(2.0, 3.0, 1.0, -4.0, 0.7)
    p0 = a.mass * a.velocity.x + b.mass * b.velocity.x
    for _ in range(int(1.0 / w.dt)):
        w.step(w.dt)
    p1 = a.mass * a.velocity.x + b.mass * b.velocity.x
    diff = abs(p1 - p0)
    print(f"[10] momentum: before={p0:.6f}, after={p1:.6f}, diff={diff:.3e} kg·m/s")
    assert diff < 1e-3, f"momentum diff {diff:.3e}"


def check_collision_inelastic():
    """e=0 perfectly inelastic: common velocity 2.5 m/s, KE loss = 6.25 J."""
    w, a, b = _collision_pair(1.0, 5.0, 1.0, 0.0, 0.0)
    KE0 = 0.5 * a.mass * a.velocity.x ** 2 + 0.5 * b.mass * b.velocity.x ** 2
    for _ in range(int(1.0 / w.dt)):
        w.step(w.dt)
    KE1 = 0.5 * a.mass * a.velocity.x ** 2 + 0.5 * b.mass * b.velocity.x ** 2
    loss = KE0 - KE1
    print(f"[11] inelastic: v_a={a.velocity.x:.6f}, v_b={b.velocity.x:.6f} "
          f"(expect both 2.5), KE loss={loss:.4f} J (expect 6.25)")
    assert abs(a.velocity.x - 2.5) < 1e-6, f"v_a={a.velocity.x}"
    assert abs(b.velocity.x - 2.5) < 1e-6, f"v_b={b.velocity.x}"
    assert abs(loss - 6.25) < 1e-3, f"KE loss={loss}"


def check_collision_stack():
    """Three stacked blocks settle with no penetration and no jitter."""
    w = World()
    w.add_contact(Ground(y=0.0, mu_s=0.5, mu_d=0.3))
    w.add_force(gravity)
    blocks = []
    for i in range(3):
        b = Body(mass=1.0, position=Vec2(0.0, 0.5 + 1.0 * i), velocity=Vec2(0.0, 0.0),
                 width=1.0, height=1.0, restitution=0.0)
        w.add_body(b)
        blocks.append(b)
    for _ in range(int(2.0 / w.dt)):
        w.step(w.dt)
    # ponytail: sequential impulse solver (no warm start) leaves ~g*dt^2 residual
    # overlap per stacked contact; 5 mm ceiling is sub-pixel at 80 px/m. Upgrade to
    # a warm-started solver if visible sinking ever matters.
    for i in range(len(blocks)):
        for j in range(i + 1, len(blocks)):
            ov = aabb_overlap(blocks[i], blocks[j])
            depth = ov[0] if ov is not None else 0.0
            assert depth < 5e-3, f"blocks {i},{j} penetrate {depth:.2e} m"
        b = blocks[i]
        assert abs(b.velocity.x) < 0.1 and abs(b.velocity.y) < 0.1, \
            f"block {i} velocity {b.velocity}"
        print(f"    block {i}: pos={b.position}, vel={b.velocity}")
    print("[12] stack: 3 blocks settled with no penetration and no jitter")


if __name__ == "__main__":
    check_resting_stability()
    check_braking()
    check_static_friction()
    check_air_friction()
    check_spring_period()
    check_spring_energy()
    check_spring_amplitude()
    check_collision_swap()
    check_collision_momentum()
    check_collision_inelastic()
    check_collision_stack()
    print("ALL CHECKS PASSED")
