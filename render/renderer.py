"""World rendering primitives: grid, ground, bodies and springs (screen space)."""
import math
import pygame


def draw_grid(screen, camera, font) -> None:
    """Draw a 1 m grid with axis tick labels."""
    ppm = camera.ppm
    x_min = -camera.origin_x / ppm
    x_max = (camera.sw - camera.origin_x) / ppm
    y_max = camera.origin_y / ppm
    for x in range(int(math.floor(x_min)), int(math.ceil(x_max)) + 1):
        sx, _ = camera.to_screen(x, 0.0)
        pygame.draw.line(screen, (55, 55, 55), (sx, 0), (sx, camera.origin_y), 1)
        if x != 0:
            lbl = font.render(str(x), True, (140, 140, 140))
            screen.blit(lbl, (sx + 3, camera.origin_y + 4))
    for y in range(0, int(math.ceil(y_max)) + 1):
        _, sy = camera.to_screen(0.0, y)
        pygame.draw.line(screen, (55, 55, 55), (0, sy), (camera.sw, sy), 1)
        if y != 0:
            lbl = font.render(str(y), True, (140, 140, 140))
            screen.blit(lbl, (camera.origin_x + 4, sy - 12))


def draw_ground(screen, camera, y: float = 0.0) -> None:
    """Draw a thick ground line spanning the visible width."""
    x_min = -camera.origin_x / camera.ppm
    x_max = (camera.sw - camera.origin_x) / camera.ppm
    gx0, gy0 = camera.to_screen(x_min, y)
    gx1, gy1 = camera.to_screen(x_max, y)
    pygame.draw.line(screen, (120, 120, 120), (gx0, gy0), (gx1, gy1), 4)


def draw_body(screen, camera, body) -> None:
    """Draw a body as an AABB rectangle; static bodies use a distinct color."""
    x0, y0 = camera.to_screen(body.position.x - body.width / 2.0,
                              body.position.y + body.height / 2.0)
    x1, y1 = camera.to_screen(body.position.x + body.width / 2.0,
                              body.position.y - body.height / 2.0)
    color = (90, 90, 120) if body.is_static else (200, 120, 60)
    pygame.draw.rect(screen, color, pygame.Rect(x0, y0, x1 - x0, y1 - y0))


def draw_spring(screen, camera, spring, color=(220, 220, 220), coils=8) -> None:
    """Draw a spring as a zigzag line between its two endpoints."""
    # 端点可能是 Body 或固定 Vec2，用鸭子类型取位置 / endpoint may be a Body or a
    # fixed Vec2; duck-type to get its position.
    pa = getattr(spring.a, 'position', spring.a)
    pb = getattr(spring.b, 'position', spring.b)
    x0, y0 = camera.world_to_screen(pa)
    x1, y1 = camera.world_to_screen(pb)
    # 固定锚点（非 Body）画个小圆标记 / draw a dot for a fixed (non-Body) anchor
    if not hasattr(spring.a, 'position'):
        pygame.draw.circle(screen, (150, 150, 150), (x0, y0), 8)
    dx, dy = x1 - x0, y1 - y0
    length = math.hypot(dx, dy)
    if length == 0.0:
        return
    nx, ny = -dy / length, dx / length
    amp = 6.0
    pts = []
    for i in range(coils * 2 + 1):
        t = i / (coils * 2)
        off = amp if i % 2 == 0 else -amp
        pts.append((x0 + dx * t + nx * off, y0 + dy * t + ny * off))
    pygame.draw.lines(screen, color, False, pts, 2)
