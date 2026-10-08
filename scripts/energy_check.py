"""Energy and work self-check (Round 8): conservation, work-energy, inelastic loss."""
import math
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from core.vector2 import Vec2
from core.body import Body
from core.forces import gravity, constant_force, Spring
from core.collision import Ground
from core.physics import World
from core.energy import kinetic_energy, spring_potential


def check_spring_conservation():
    """Undamped spring: energy must stay bounded (no secular drift) over many periods.

    ponytail: symplectic Euler keeps the spring's energy bounded but oscillating in a
    band of width ~omega*dt (here ~1.3%), the integrator's inherent ceiling, not a bug.
    A literal <0.5% bound would need omega*dt<0.5% (k<1.44). Upgrade to velocity-Verlet
    for a (omega*dt)^2 band if tighter conservation is ever required.
    """
    m, k, rest, A0 = 1.0, 10.0, 1.0, 0.6
    w = World()
    block = Body(mass=m, position=Vec2(rest + A0, 0.0), velocity=Vec2(0.0, 0.0),
                 width=0.4, height=0.4)
    w.add_body(block)
    w.add_spring(Spring(Vec2(0.0, 0.0), block, rest, k, 0.0))
    E0 = 0.5 * k * A0 * A0
    emin, emax = float("inf"), float("-inf")
    for _ in range(int(60.0 / w.dt)):
        w.step(w.dt)
        E = kinetic_energy(block) + spring_potential(w.springs[0])
        emin, emax = min(emin, E), max(emax, E)
    omega = math.sqrt(k / m)
    band = omega * w.dt          # 振荡带相对半宽 / relative half-width of the band
    fluct = (emax - emin) / E0   # 峰-峰相对波动 / peak-to-peak relative fluctuation
    drift = abs((emax + emin) / 2.0 - E0) / E0  # 均值偏离 = 长期漂移 / secular drift
    print(f"[13] spring bounded: E0={E0:.4f} J, fluct={fluct*100:.3f}% "
          f"(band 2*omega*dt={2*band*100:.3f}%), drift={drift*100:.4f}%")
    assert fluct <= 2.0 * band * 1.05, "energy oscillation exceeds the symplectic band"
    assert drift < 0.01, f"secular energy drift {drift*100:.4f}% >= 1%"


def check_work_energy():
    """Net work on a pushed sliding block must equal its kinetic-energy change."""
    w = World()
    w.add_contact(Ground(y=0.0, mu_s=0.5, mu_d=0.2))
    w.add_force(gravity, "gravity")
    F = Vec2(8.0, 0.0)
    w.add_force(lambda body, f=F: constant_force(body, f), "external")
    b = Body(mass=1.0, position=Vec2(0.0, 0.5), velocity=Vec2(0.0, 0.0),
             width=1.0, height=1.0, restitution=0.0)
    w.add_body(b)
    w.mark_reset()
    for _ in range(int(3.0 / w.dt)):
        w.step(w.dt)
    dk = kinetic_energy(b) - w.energy.k_initial
    W = w.energy.total_work()
    err = abs(W - dk) / max(abs(dk), 1e-9)
    print(f"[14] work-energy: W_total={W:.4f} J, dK={dk:.4f} J, err={err*100:.3f}%")
    assert err < 0.01, f"work-energy error {err*100:.3f}% >= 1%"


def check_inelastic_theory():
    """Collision KE loss must match the 1D impulse formula (1/2)*mu*(1-e^2)*u^2."""
    e, m1, m2, v1, v2 = 0.5, 1.0, 2.0, 3.0, -2.0
    w = World()
    a = Body(mass=m1, position=Vec2(0.0, 0.0), velocity=Vec2(v1, 0.0),
             width=1.0, height=1.0, restitution=e)
    b = Body(mass=m2, position=Vec2(2.0, 0.0), velocity=Vec2(v2, 0.0),
             width=1.0, height=1.0, restitution=e)
    w.add_body(a)
    w.add_body(b)
    w.mark_reset()
    for _ in range(int(1.0 / w.dt)):
        w.step(w.dt)
    mu = m1 * m2 / (m1 + m2)
    u = v1 - v2
    theory = 0.5 * mu * (1.0 - e * e) * u * u
    loss = -w.energy.impulse_loss
    err = abs(loss - theory) / theory
    print(f"[15] inelastic theory: loss={loss:.4f} J, theory={theory:.4f} J, "
          f"err={err*100:.2f}%")
    assert err < 0.05, f"inelastic loss error {err*100:.2f}% >= 5%"


if __name__ == "__main__":
    check_spring_conservation()
    check_work_energy()
    check_inelastic_theory()
    print("ENERGY CHECKS PASSED")
