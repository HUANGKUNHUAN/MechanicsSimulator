"""Fixed-timestep world: force accumulation, symplectic Euler, contact resolution."""
from core.vector2 import Vec2
from core.collision import aabb_overlap, resolve_collision
from core.energy import EnergyTracker, kinetic_energy


class World:
    """Container of bodies advanced at a fixed timestep with a frame accumulator."""

    def __init__(self, dt: float = 1.0 / 240.0, max_steps: int = 10,
                 collision_iterations: int = 4):
        self.dt = dt
        self.max_steps = max_steps
        self.collision_iterations = collision_iterations
        self.bodies = []
        self.forces = []     # 常规力 (label, callable) 列表 / regular forces (label, fn)
        self.springs = []    # 弹簧列表 / spring objects
        self.contacts = []   # 接触对象（如地面）/ contact objects (e.g. ground)
        self.time = 0.0
        self.accumulator = 0.0
        self.energy = EnergyTracker()  # 功/能量记账 / work and energy accounting

    def add_body(self, b) -> None:
        """Register a body."""
        self.bodies.append(b)

    def add_force(self, fn, label: str = "force") -> None:
        """Register a regular force callable with a work label (body -> Vec2)."""
        self.forces.append((label, fn))

    def add_spring(self, s) -> None:
        """Register a spring object."""
        self.springs.append(s)

    def add_contact(self, c) -> None:
        """Register a contact object."""
        self.contacts.append(c)

    def step(self, dt: float) -> None:
        """Advance one physics step: clear, accumulate, integrate, resolve."""
        # 1) 清空力累加器 / clear force accumulators
        for b in self.bodies:
            b.clear_forces()
        # 2) 常规力（带标签）/ regular forces (labeled for work accounting)
        for b in self.bodies:
            if b.is_static:
                continue
            for label, fn in self.forces:
                f = fn(b)
                b.add_force(f)
                b.add_labeled_force(label, f)
        # 2b) 弹簧力（两端点）/ spring forces (two-endpoint)
        for s in self.springs:
            s.apply()
        # 3) 接触力：法向支撑 + 摩擦 / contact forces: normal + friction
        for b in self.bodies:
            if b.is_static:
                continue
            for c in self.contacts:
                if c.in_contact(b):
                    nf = Vec2(0.0, c.normal_force(b))
                    fr = c.friction(b, b.force_accumulator.x)
                    b.add_force(nf)
                    b.add_force(fr)
                    b.add_labeled_force("normal", nf)
                    b.add_labeled_force("friction", fr)
        # 4) 半隐式欧拉积分 / symplectic Euler integration. 功用中点速度计算：
        #    W = F·(v_old+v_new)/2·dt，使 W_total 与 ΔK 一致到浮点精度 /
        #    work uses the midpoint velocity so W_total equals ΔK to machine precision.
        for b in self.bodies:
            if b.is_static:
                continue
            v_old = b.velocity
            a = b.force_accumulator * b.inv_mass
            b.velocity = b.velocity + a * dt   # 先速度 / velocity first
            dx = (v_old + b.velocity) * (0.5 * dt)  # 中点位移 / midpoint displacement
            for label, f in b.labeled_forces.items():
                self.energy.record_work(label, f, dx)
            b.position = b.position + b.velocity * dt  # 再用新速度更新位置 / then position
        # 5) 碰撞解算（迭代多次，记录动能损失）/ collision resolution (records KE loss)
        for _ in range(self.collision_iterations):
            self._resolve_collisions()
        # 6) 地面修正：穿透抬出 + 落地清速度 / ground resolve: lift out + kill landing vy
        for b in self.bodies:
            if b.is_static:
                continue
            for c in self.contacts:
                ke_before = kinetic_energy(b)
                c.resolve(b)
                ke_after = kinetic_energy(b)
                if ke_after != ke_before:
                    self.energy.record_impulse_loss(ke_after - ke_before)
        self.time += dt

    def _resolve_collisions(self) -> None:
        """Detect and resolve AABB overlaps between all body pairs."""
        bodies = self.bodies
        for i in range(len(bodies)):
            for j in range(i + 1, len(bodies)):
                a, b = bodies[i], bodies[j]
                if a.is_static and b.is_static:
                    continue
                overlap = aabb_overlap(a, b)
                if overlap is not None:
                    depth, normal = overlap
                    e = min(a.restitution, b.restitution)
                    ke_before = kinetic_energy(a) + kinetic_energy(b)
                    resolve_collision(a, b, depth, normal, e)
                    ke_after = kinetic_energy(a) + kinetic_energy(b)
                    if ke_after != ke_before:
                        self.energy.record_impulse_loss(ke_after - ke_before)

    def advance(self, frame_dt: float) -> int:
        """Run zero or more fixed-dt steps for one render frame; returns step count."""
        self.accumulator += frame_dt
        n = 0
        while self.accumulator >= self.dt and n < self.max_steps:
            self.step(self.dt)
            self.accumulator -= self.dt
            n += 1
        return n

    def mark_reset(self) -> None:
        """Capture the current total kinetic energy as the K1 reference for ΔK."""
        self.energy.reset(sum(kinetic_energy(b) for b in self.bodies))
