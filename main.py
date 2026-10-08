"""Application entry point: window, controls, playback, physics loop, rendering."""
import pygame
from render.camera import Camera
from render.renderer import draw_grid, draw_ground, draw_body, draw_spring
from render.arrows import draw_body_vectors, draw_legend
from render.trail import Trail
from scenes.scenarios import FrictionScene, SpringScene, CollisionScene
from ui.slider import Slider
from ui.button import Button
from ui.hud import draw_hud
from core.collision import Ground
from core.energy import energy_report

WIDTH, HEIGHT = 1000, 650
PPM = 80.0
MARGIN = 30       # 控制区左右边距 / control panel side margin
GAP_X = 15        # 控件水平间距 / horizontal gap
ROW_H = 52        # 控件行高 / control row height


def draw_world(screen, camera, font, scene, trails) -> None:
    """Draw grid, ground, bodies, springs, arrows, trails and legend."""
    draw_grid(screen, camera, font)
    for c in scene.world.contacts:
        if isinstance(c, Ground):
            draw_ground(screen, camera, c.y)
    for b in scene.world.bodies:
        draw_body(screen, camera, b)
        draw_body_vectors(screen, camera, b)
    for s in scene.world.springs:
        draw_spring(screen, camera, s)
    for t in trails.values():
        t.draw(screen, camera)
    draw_legend(screen, font, (screen.get_width() - 200, 10))


def flow(items, x0, y0, max_x, gap_x, row_h) -> None:
    """Assign x/y to controls, wrapping to a new row when exceeding max_x."""
    x, y = x0, y0
    for item in items:
        if x + item.w > max_x:
            x = x0
            y += row_h
        item.x = x
        item.y = y
        x += item.w + gap_x


def main() -> None:
    """Run the multi-scenario main loop."""
    pygame.init()
    screen = pygame.display.set_mode((WIDTH, HEIGHT), pygame.RESIZABLE)
    pygame.display.set_caption("力学仿真 Mechanics Simulator")
    clock = pygame.time.Clock()
    font = pygame.font.Font(None, 22)
    camera = Camera(PPM, (WIDTH, HEIGHT))

    friction = FrictionScene()
    friction_sliders = [
        Slider(0, 0, 300, "外力 F (N) / Force", 0, 20, 0, ".2f"),
        Slider(0, 0, 300, "动摩擦 μd / Kinetic μ", 0, 1, 0.2, ".3f"),
        Slider(0, 0, 300, "质量 m (kg) / Mass (重置)", 0.2, 5, 1, ".2f"),
        Slider(0, 0, 300, "初速度 v0 (m/s) / v0 (重置)", -5, 5, 0, ".2f"),
    ]

    spring = SpringScene()
    spring_sliders = [
        Slider(0, 0, 300, "刚度 k (N/m) / Stiffness", 1, 200, 40, ".1f"),
        Slider(0, 0, 300, "阻尼 c (N·s/m) / Damping", 0, 20, 0, ".2f"),
    ]

    collision = CollisionScene()
    collision_sliders = [
        Slider(0, 0, 300, "弹性系数 e / Restitution", 0, 1, 0.9, ".2f"),
    ]

    trail_enabled = Slider(0, 0, 180, "残影 Trail (开/关)", 0, 1, 1, ".0f")
    trail_length = Slider(0, 0, 180, "残影长度 Trail length", 10, 300, 150, ".0f")
    global_sliders = [trail_enabled, trail_length]

    modes = [
        ("摩擦 Friction", friction, friction_sliders),
        ("弹簧 Spring", spring, spring_sliders),
        ("碰撞 Collision", collision, collision_sliders),
    ]
    idx = 2  # 默认碰撞场景 / start on the collision scene
    buttons = [
        Button(0, 0, 110, 44, "播放 Play"),
        Button(0, 0, 110, 44, "暂停 Pause"),
        Button(0, 0, 110, 44, "重置 Reset"),
        Button(0, 0, 110, 44, "单步 Step"),
    ]
    trails = {}
    playing = True
    step_once = False
    running = True

    while running:
        dt = clock.tick(60) / 1000.0
        name, scene, sliders = modes[idx]
        all_sliders = sliders + global_sliders
        panel_top = camera.origin_y

        # --- 布局（每帧重算，缩放即生效）/ layout (recomputed each frame) ---
        flow(buttons, MARGIN, panel_top + 12, screen.get_width() - MARGIN, GAP_X, 60)
        flow(all_sliders, MARGIN, panel_top + 84, screen.get_width() - MARGIN, GAP_X, ROW_H)

        # --- 事件处理 / Event handling ---
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            elif event.type == pygame.VIDEORESIZE:
                camera.resize(event.size)
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    running = False
                elif event.key == pygame.K_1:
                    idx = 0
                elif event.key == pygame.K_2:
                    idx = 1
                elif event.key == pygame.K_3:
                    idx = 2
                elif event.key == pygame.K_SPACE:
                    playing = not playing
                elif event.key == pygame.K_r:
                    scene.reset()
                    trails.clear()

            if buttons[0].handle_event(event):
                playing = True
            if buttons[1].handle_event(event):
                playing = False
            if buttons[2].handle_event(event):
                scene.reset()
                trails.clear()
            if buttons[3].handle_event(event):
                step_once = True
            for s in all_sliders:
                s.handle_event(event)

        # --- 更新 / Update ---
        if idx == 0:
            friction.set_force(sliders[0].value)
            friction.set_mu_d(sliders[1].value)
            friction.set_mass(sliders[2].value)
            friction.set_v0(sliders[3].value)
        elif idx == 1:
            spring.set_k(sliders[0].value)
            spring.set_c(sliders[1].value)
        elif idx == 2:
            collision.set_e(sliders[0].value)

        if step_once:
            scene.world.step(scene.world.dt)  # 单步：只推进一个固定 dt / one fixed dt
            step_once = False
        elif playing:
            scene.step(dt)

        # --- 记录残影（仅动态体，自动剔除已不存在的体）/ record trails ---
        enabled = trail_enabled.value >= 0.5
        max_len = int(trail_length.value)
        active = {b for b in scene.world.bodies if not b.is_static}
        for k in list(trails):
            if k not in active:
                del trails[k]
        for b in active:
            t = trails.get(b)
            if t is None:
                t = trails[b] = Trail()
            t.enabled = enabled
            t.max_length = max_len
            t.record(b.position)

        # --- 渲染 / Render ---
        screen.fill((30, 30, 30))
        draw_world(screen, camera, font, scene, trails)

        # --- 能量与功 HUD / energy and work HUD ---
        rep = energy_report(scene.world)
        k0 = rep["k_initial"]
        dk = rep["K"] - (k0 if k0 is not None else rep["K"])
        white, amber, dim = (235, 235, 235), (255, 205, 110), (170, 170, 170)
        hud = [
            (f"动能 K / Kinetic: {rep['K']:.2f} J", white),
            (f"弹性势能 U_s / Elastic PE: {rep['U_s']:.2f} J", white),
            (f"重力势能 U_g / Grav. PE: {rep['U_g']:.2f} J", white),
            (f"机械能 E / Mechanical: {rep['E_mech']:.2f} J", amber),
            (f"合力功 W / Net work: {rep['W_total']:.2f} J", white),
            (f"ΔK = K - K1: {dk:+.2f} J", amber),
        ]
        for label, name in (("external", "外力 External"),
                            ("friction", "摩擦 Friction"),
                            ("spring", "弹簧 Spring"),
                            ("gravity", "重力 Gravity")):
            w = rep["work"].get(label, 0.0)
            hud.append((f"  W_{label} ({name}): {w:.2f} J", dim))
        draw_hud(screen, font, hud)

        hint = font.render(
            "1 摩擦 / 2 弹簧 / 3 碰撞    空格 播放/暂停    R 重置    ESC 退出",
            True, (180, 180, 180))
        screen.blit(hint, (10, 10))

        for s in all_sliders:
            s.draw(screen, font)
        for b in buttons:
            b.draw(screen, font)

        state = "播放中" if playing else "已暂停"
        pygame.display.set_caption(
            f"力学仿真 Mechanics Simulator [{name}]  FPS: {clock.get_fps():.0f}  [{state}]")
        pygame.display.flip()

    pygame.quit()


if __name__ == "__main__":
    main()
