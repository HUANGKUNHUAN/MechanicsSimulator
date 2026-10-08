"""弹簧振子 Manim 预览（前半：标题 + 振动现象）/ spring oscillator preview (first half: title + oscillation).

只渲染前两个分镜，供快速预览效果 / renders only the first two beats for a quick look.
渲染 / render:
    python -m manim -ql -p video/spring_preview.py SpringPreview
"""
import numpy as np
from manim import *

M = 1.0
K_SPRING = 40.0
A = 0.6
OMEGA = np.sqrt(K_SPRING / M)

SCALE = 3.0
WALL_X = -4.0
X_EQ = 0.0
BLOCK_W = 1.0
BLOCK_H = 1.0
COILS = 8
COIL_AMP = 0.35
CJK_FONT = "Microsoft YaHei"


class SpringPreview(Scene):
    """弹簧振子前半段：标题与简谐振动现象 / first half: title and SHM phenomenon."""

    def construct(self):
        self.phase = ValueTracker(0.0)   # 相位 ωt，驱动 x = A cos(ωt) / drives x
        self.show_title()
        self.show_phenomenon()

    def _cn(self, text, size=34):
        """Return a Text mobject using a CJK-capable font."""
        return Text(text, font=CJK_FONT, font_size=size)

    def x_now(self):
        """Current physical displacement x = A cos(phase), in meters."""
        return A * np.cos(self.phase.get_value())

    def _coil(self, x0, x1, y, coils, amp):
        """Build a zigzag spring polyline from x0 to x1 at height y."""
        n = coils * 2
        dx = (x1 - x0) / n
        pts = [np.array([x0, y, 0.0])]
        for i in range(1, n):
            yy = amp if i % 2 == 1 else -amp
            pts.append(np.array([x0 + i * dx, yy, 0.0]))
        pts.append(np.array([x1, y, 0.0]))
        return VMobject().set_points_as_corners(pts).set_stroke(color=WHITE, width=3)

    def get_spring(self):
        """Spring polyline whose right end follows the block."""
        xb = X_EQ + self.x_now() * SCALE
        return self._coil(WALL_X, xb - BLOCK_W / 2.0, 0.0, COILS, COIL_AMP)

    def get_block(self):
        """Block (with mass label m) at the current displacement."""
        xb = X_EQ + self.x_now() * SCALE
        rect = Rectangle(width=BLOCK_W, height=BLOCK_H).set_fill(BLUE, 0.6)
        rect.set_stroke(BLUE, 2)
        return VGroup(rect, MathTex("m")).move_to([xb, 0.0, 0.0])

    def get_x_readout(self):
        """Live displacement value (m) above the block."""
        xb = X_EQ + self.x_now() * SCALE
        num = DecimalNumber(self.x_now(), num_decimal_places=2)
        unit = MathTex(r"\mathrm{m}").next_to(num, RIGHT, buff=0.1)
        return VGroup(num, unit).move_to([xb, BLOCK_H / 2 + 0.5, 0.0])

    def setup_rig(self):
        """Create the wall, spring, block and x readout; add them to the scene."""
        self.wall = Line(UP * 1.3, DOWN * 1.3, color=GREY_A).shift(RIGHT * WALL_X)
        self.wall_label = self._cn("固定端 / fixed", 26).next_to(self.wall, UP, buff=0.2)
        self.spring = always_redraw(self.get_spring)
        self.block = always_redraw(self.get_block)
        self.x_num = always_redraw(self.get_x_readout)
        self.play(Create(self.wall), FadeIn(self.wall_label))
        self.add(self.spring, self.block, self.x_num)

    def show_title(self):
        """镜 0：标题 / beat 0: title."""
        title = VGroup(
            self._cn("弹簧振子", 64),
            Text("Spring Oscillator — Simple Harmonic Motion", font_size=32),
        ).arrange(DOWN, buff=0.35)
        self.play(Write(title))
        self.wait(1.0)
        self.play(FadeOut(title))

    def show_phenomenon(self):
        """镜 1：现象（两个周期）/ beat 1: oscillation (two periods)."""
        self.setup_rig()
        self.wait(0.4)
        self.play(self.phase.animate.set_value(4 * np.pi),
                  run_time=8.0, rate_func=linear)
        self.wait(0.6)
