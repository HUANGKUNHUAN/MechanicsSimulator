"""Scene assembly: friction, spring and collision scenarios."""
from core.vector2 import Vec2
from core.body import Body
from core.physics import World
from core.forces import gravity, constant_force, Spring
from core.collision import Ground


class FrictionScene:
    """Ground + block scene; horizontal force, friction, mass and v0 are bound."""

    def __init__(self, dt: float = 1.0 / 240.0, v0: float = 0.0):
        self.world = World(dt)
        self.ground = Ground(y=0.0, mu_s=0.5, mu_d=0.2)
        self.world.add_contact(self.ground)
        self.world.add_force(gravity, "gravity")
        self.F = Vec2(0.0, 0.0)   # 水平外力 / horizontal external force
        self.mass = 1.0
        self.v0 = v0              # 初速度 / initial velocity
        self.block = self._make_block()
        self.world.add_body(self.block)
        self.world.add_force(self._external_force, "external")
        self.world.mark_reset()

    def _make_block(self) -> Body:
        return Body(mass=self.mass, position=Vec2(0.0, 0.5), velocity=Vec2(self.v0, 0.0),
                    width=1.0, height=1.0, restitution=0.0)

    def _external_force(self, body) -> Vec2:
        return constant_force(body, self.F)

    def _rebuild(self) -> None:
        """Replace the block (reset position/velocity, keep current params)."""
        self.world.bodies.remove(self.block)
        self.block = self._make_block()
        self.world.add_body(self.block)

    def set_force(self, f: float) -> None:
        """Set the horizontal external force magnitude (N)."""
        self.F = Vec2(f, 0.0)

    def set_mu_d(self, mu: float) -> None:
        """Set the kinetic friction coefficient."""
        self.ground.mu_d = mu

    def set_mass(self, m: float) -> None:
        """Change mass (rebuilds the block; resets position/velocity)."""
        if m == self.mass:
            return
        self.mass = m
        self._rebuild()

    def set_v0(self, v0: float) -> None:
        """Change initial velocity (rebuilds the block; resets position/velocity)."""
        if v0 == self.v0:
            return
        self.v0 = v0
        self._rebuild()

    def reset(self) -> None:
        """Restore the initial state and clear the world clock."""
        self._rebuild()
        self.world.time = 0.0
        self.world.accumulator = 0.0
        self.world.mark_reset()

    def step(self, frame_dt: float) -> None:
        """Advance the world by one render frame's worth of fixed steps."""
        self.world.advance(frame_dt)


class SpringScene:
    """Block on a horizontal spring attached to a fixed anchor (SHM demo)."""

    def __init__(self, dt: float = 1.0 / 240.0, rest_length: float = 1.0,
                 initial_disp: float = 0.6):
        self.world = World(dt)
        self.rest_length = rest_length
        self.initial_disp = initial_disp
        self.anchor = Vec2(0.0, 1.0)   # 固定锚点 / fixed anchor
        self.block = Body(mass=1.0,
                          position=Vec2(rest_length + initial_disp, 1.0),
                          velocity=Vec2(0.0, 0.0), width=0.4, height=0.4)
        self.world.add_body(self.block)
        self.spring = Spring(self.anchor, self.block, rest_length, k=40.0, c=0.0)
        self.world.add_spring(self.spring)
        self.world.mark_reset()

    def set_k(self, k: float) -> None:
        """Set the spring stiffness (N/m)."""
        self.spring.k = k

    def set_c(self, c: float) -> None:
        """Set the spring damping (N·s/m)."""
        self.spring.c = c

    def reset(self) -> None:
        """Restore the block to its initial position/velocity and clear the clock."""
        self.world.bodies.remove(self.block)
        self.block = Body(mass=1.0,
                          position=Vec2(self.rest_length + self.initial_disp, 1.0),
                          velocity=Vec2(0.0, 0.0), width=0.4, height=0.4)
        self.world.add_body(self.block)
        self.spring.b = self.block  # 重连弹簧到新块 / reattach spring to the new block
        self.world.time = 0.0
        self.world.accumulator = 0.0
        self.world.mark_reset()

    def step(self, frame_dt: float) -> None:
        """Advance the world by one render frame's worth of fixed steps."""
        self.world.advance(frame_dt)


class CollisionScene:
    """Blocks bouncing off walls and each other under gravity (frictionless)."""

    def __init__(self, dt: float = 1.0 / 240.0, restitution: float = 0.9):
        self.world = World(dt)
        self.world.add_contact(Ground(y=0.0, mu_s=0.0, mu_d=0.0))
        self.world.add_force(gravity, "gravity")
        self.restitution = restitution
        self.walls = []
        self.blocks = []
        # 左右墙体（静态，弹性系数 1.0 使块的 e 生效）/ walls (static, e=1.0 so the
        # block's own restitution applies when bouncing off them)
        for wx in (-4.0, 4.0):
            w = Body(mass=1.0, position=Vec2(wx, 1.0), width=0.2, height=2.0,
                     is_static=True, restitution=1.0)
            self.world.add_body(w)
            self.walls.append(w)
        self._make_blocks()
        self.world.mark_reset()

    def _make_blocks(self) -> None:
        """Create the dynamic blocks at their initial positions/velocities."""
        for pos, vel, m in [
            (Vec2(-1.0, 3.0), Vec2(1.0, 0.0), 1.0),
            (Vec2(1.5, 1.0), Vec2(-0.5, 0.0), 2.0),
        ]:
            b = Body(mass=m, position=pos, velocity=vel,
                     width=1.0, height=1.0, restitution=self.restitution)
            self.world.add_body(b)
            self.blocks.append(b)

    def set_e(self, e: float) -> None:
        """Set the restitution of the dynamic blocks (live)."""
        self.restitution = e
        for b in self.blocks:
            b.restitution = e

    def reset(self) -> None:
        """Restore the dynamic blocks to their initial state and clear the clock."""
        for b in self.blocks:
            self.world.bodies.remove(b)
        self.blocks = []
        self._make_blocks()
        self.world.time = 0.0
        self.world.accumulator = 0.0
        self.world.mark_reset()

    def step(self, frame_dt: float) -> None:
        """Advance the world by one render frame's worth of fixed steps."""
        self.world.advance(frame_dt)
