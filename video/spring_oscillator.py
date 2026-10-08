"""弹簧振子 Manim 讲解视频 / spring oscillator (SHM) explainer video.

依赖 / depends on: manim (Community Edition >= 0.18; MathTex 需 LaTeX / needs LaTeX).
渲染 / render:
    python -m manim -ql -p video/spring_oscillator.py SpringOscillator   # 预览 480p15
    python -m manim -qh -p video/spring_oscillator.py SpringOscillator   # 高清 1080p60
"""
import numpy as np
from manim import *

# --- 物理参数 / physical parameters (SI) ---
M = 1.0                        # 质量 / mass (kg)
K_SPRING = 40.0                # 劲度系数 / spring stiffness (N/m)
A = 0.6                        # 振幅 / amplitude (m)
OMEGA = np.sqrt(K_SPRING / M)       # 角频率 / angular frequency (rad/s)
T_PERIOD = 2 * np.pi / OMEGA        # 周期 / period (s)
E_TOTAL = 0.5 * K_SPRING * A * A    # 总机械能 / total energy (J)

# --- 屏幕布局 / screen layout ---
SCALE = 3.0                    # 1 米 = 3 屏幕单位 / 1 m = 3 screen units
WALL_X = -4.0                  # 墙 x / wall x
X_EQ = 0.0                     # 平衡位置（方块中心）x / equilibrium block-center x
BLOCK_W = 1.0                  # 方块宽 / block width
BLOCK_H = 1.0                  # 方块高 / block height
COILS = 8                      # 弹簧圈数 / coil count
COIL_AMP = 0.35                # 线圈振幅 / coil amplitude
CJK_FONT = "Microsoft YaHei"   # 中文字体 / CJK font (Windows)


class SpringOscillator(Scene):
    """弹簧振子 / 简谐运动 spring oscillator (SHM): period and energy exchange."""

    def construct(self):
        self.phase = ValueTracker(0.0)   # 相位 ωt，驱动 x = A cos(ωt) / drives x
        self.show_title()                # 镜 0 / beat 0
        self.show_phenomenon()           # 镜 1 / beat 1
        self.show_forces()               # 镜 2 / beat 2
        self.show_energy()               # 镜 3 / beat 3
        self.show_conclusion()           # 镜 4 / beat 4

    # --- 工具 / helpers ---
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

    # --- 分镜 / beats ---
    def show_title(self):
        """镜 0：标题 / beat 0: title."""
        # 解说 / narration: 今天演示弹簧振子的简谐运动与能量转换。
        title = VGroup(
            self._cn("弹簧振子", 64),
            Text("Spring Oscillator — Simple Harmonic Motion", font_size=32),
        ).arrange(DOWN, buff=0.35)
        self.play(Write(title))
        self.wait(1.2)
        self.play(FadeOut(title))

    def show_phenomenon(self):
        """镜 1：现象 / beat 1: the block oscillates (two periods)."""
        self.setup_rig()
        self.wait(0.4)
        # 解说 / narration: 质量 m 的物块连在劲度系数 k 的弹簧上，拉开释放后
        # 在平衡位置两侧做简谐振动（动画放慢以看清，物理周期 T≈0.99 s）。
        self.play(self.phase.animate.set_value(4 * np.pi),
                  run_time=8.0, rate_func=linear)
        self.wait(0.4)

    def show_forces(self):
        """镜 2：受力与公式 / beat 2: restoring force and SHM equations."""
        # 相位停在 4π → x = A（最右），弹力指向平衡位置 / phase 4π -> x=A, force points left
        xb = X_EQ + self.x_now() * SCALE
        arrow = Arrow(start=[xb, 0.0, 0.0], end=[xb - 2.0, 0.0, 0.0],
                      color=RED, buff=0.0)
        flabel = MathTex(r"F = -k x", color=RED).next_to(arrow, DOWN, buff=0.2)
        self.play(GrowArrow(arrow), FadeIn(flabel))
        self.wait(0.8)
        # 解说 / narration: 弹簧弹力 F=-kx 始终指向平衡位置，是回复力。
        self.play(FadeOut(arrow), FadeOut(flabel))

        formulas = VGroup(
            MathTex(r"F = -k x"),
            MathTex(r"m a = -k x"),
            MathTex(r"\ddot{x} + \frac{k}{m} x = 0"),
            MathTex(r"x(t) = A \cos(\omega t)"),
            MathTex(r"\omega = \sqrt{\frac{k}{m}}"),
            MathTex(r"T = 2\pi \sqrt{\frac{m}{k}}"),
        ).arrange(DOWN, aligned_edge=LEFT, buff=0.35).to_edge(RIGHT, buff=0.4)
        # 解说 / narration: 由牛顿第二定律得简谐运动方程，解为余弦函数；
        # 角频率 ω=√(k/m)，周期 T=2π√(m/k)。
        for f in formulas:
            self.play(Write(f))
            self.wait(0.25)
        self.wait(0.8)
        self.play(FadeOut(formulas))

    def get_energy_hud(self):
        """Live K/U bars and numbers (they trade off; total stays constant)."""
        ph = self.phase.get_value()
        kval = 0.5 * K_SPRING * A * A * np.sin(ph) ** 2
        uval = 0.5 * K_SPRING * A * A * np.cos(ph) ** 2
        max_h, base_y = 2.0, -2.3
        k_h = max(max_h * kval / E_TOTAL, 0.04)
        u_h = max(max_h * uval / E_TOTAL, 0.04)
        k_bar = Rectangle(width=0.9, height=k_h).set_fill(GREEN, 0.7).set_stroke(GREEN, 2)
        k_bar.move_to([-3.5, base_y + k_h / 2.0, 0.0])
        u_bar = Rectangle(width=0.9, height=u_h).set_fill(ORANGE, 0.7).set_stroke(ORANGE, 2)
        u_bar.move_to([-2.2, base_y + u_h / 2.0, 0.0])
        k_lbl = MathTex("K").move_to([-3.5, base_y - 0.5, 0.0])
        u_lbl = MathTex("U").move_to([-2.2, base_y - 0.5, 0.0])
        k_num = DecimalNumber(kval, num_decimal_places=2).move_to([-3.5, base_y - 0.95, 0.0])
        u_num = DecimalNumber(uval, num_decimal_places=2).move_to([-2.2, base_y - 0.95, 0.0])
        return VGroup(k_bar, u_bar, k_lbl, u_lbl, k_num, u_num)

    def show_energy(self):
        """镜 3：能量交换与数值 / beat 3: energy exchange and numbers."""
        energy_formulas = VGroup(
            MathTex(r"K = \frac{1}{2} m v^2"),
            MathTex(r"U = \frac{1}{2} k x^2"),
            MathTex(r"E = K + U = \frac{1}{2} k A^2"),
            MathTex(r"= \frac{1}{2} \cdot 40 \cdot 0.6^2 = 7.2\ \mathrm{J}"),
        ).arrange(DOWN, aligned_edge=LEFT, buff=0.35).to_edge(RIGHT, buff=0.4)
        self.play(Write(energy_formulas))

        e_line = Line([-4.0, -0.3, 0.0], [-1.5, -0.3, 0.0], color=YELLOW)
        e_lbl = MathTex("E").next_to(e_line, LEFT, buff=0.1)
        self.energy_hud = always_redraw(self.get_energy_hud)
        self.add(self.energy_hud, e_line, e_lbl)
        # 解说 / narration: 动能与弹性势能此消彼长；总机械能 E=½kA²=7.2 J 保持不变。
        self.play(self.phase.animate.set_value(6 * np.pi),
                  run_time=4.0, rate_func=linear)
        self.wait(0.6)
        self.remove(self.energy_hud, e_line, e_lbl)
        self.play(FadeOut(energy_formulas))

    def show_conclusion(self):
        """镜 4：结论 / beat 4: conclusion."""
        self.remove(self.spring, self.block, self.x_num)
        self.play(FadeOut(self.wall, self.wall_label))
        # 解说 / narration: 结论：周期只取决于质量与刚度，机械能在动能与
        # 势能之间周期转换且守恒。
        conclusion = VGroup(
            MathTex(r"T = 2\pi \sqrt{\frac{m}{k}}"),
            self._cn("周期只取决于质量与刚度；机械能守恒", 34),
        ).arrange(DOWN, buff=0.45)
        self.play(Write(conclusion))
        self.wait(2.0)
