"""Vector arrows for force, velocity and acceleration with a color legend."""
import math
import pygame


F_COLOR = (230, 70, 70)    # 合力 / net force
V_COLOR = (80, 160, 255)   # 速度 / velocity
A_COLOR = (90, 220, 120)   # 加速度 / acceleration
# 三个矢量单位不同，各用独立比例 px/单位 / different units, so each has its own scale
F_SCALE = 8.0    # px per N
V_SCALE = 18.0   # px per m/s
A_SCALE = 5.0    # px per m/s^2
MAX_PX = 150.0   # 屏幕内自动截断 / clamp arrow length on screen


def draw_arrow(screen, camera, origin, vector, color, scale, max_px=MAX_PX) -> None:
    """Draw an arrow from origin; length = |vector|*scale, clamped to max_px."""
    mag = vector.length()
    if mag == 0.0:
        return
    ox, oy = camera.world_to_screen(origin)
    d = vector / mag
    length_px = min(mag * scale, max_px)
    # 屏幕 y 向下，方向分量翻转 y / screen y is downward, so flip the y component
    dx, dy = d.x, -d.y
    tip = (ox + dx * length_px, oy + dy * length_px)
    pygame.draw.line(screen, color, (ox, oy), tip, 2)
    _arrowhead(screen, color, (ox, oy), tip, 8.0)


def _arrowhead(screen, color, base, tip, size) -> None:
    """Draw a filled triangular arrowhead at the tip."""
    dx, dy = tip[0] - base[0], tip[1] - base[1]
    length = math.hypot(dx, dy)
    if length == 0.0:
        return
    ux, uy = dx / length, dy / length
    px, py = -uy, ux
    h1 = (tip[0] - ux * size + px * size * 0.5, tip[1] - uy * size + py * size * 0.5)
    h2 = (tip[0] - ux * size - px * size * 0.5, tip[1] - uy * size - py * size * 0.5)
    pygame.draw.polygon(screen, color, [tip, h1, h2])


def draw_body_vectors(screen, camera, body) -> None:
    """Draw net force (red), velocity (blue) and acceleration (green) arrows."""
    if body.is_static:
        return
    f = body.force_accumulator
    v = body.velocity
    a = f * body.inv_mass
    draw_arrow(screen, camera, body.position, f, F_COLOR, F_SCALE)
    draw_arrow(screen, camera, body.position, v, V_COLOR, V_SCALE)
    draw_arrow(screen, camera, body.position, a, A_COLOR, A_SCALE)


def draw_legend(screen, font, pos) -> None:
    """Draw the color legend for force / velocity / acceleration."""
    x, y = pos
    items = [("F 合力 Force", F_COLOR),
             ("v 速度 Velocity", V_COLOR),
             ("a 加速度 Accel", A_COLOR)]
    for i, (label, color) in enumerate(items):
        pygame.draw.line(screen, color, (x, y + i * 20 + 8), (x + 18, y + i * 20 + 8), 3)
        surf = font.render(label, True, (200, 200, 200))
        screen.blit(surf, (x + 24, y + i * 20))
