"""西瓜绘制测试 — 最终版 (v3 弧形条纹)"""
import tkinter as tk
import sys
sys.path.insert(0, ".")
from farm_tkinter_v2 import _draw_watermelon, _draw_pumpkin, _draw_sprout, _STAGE_SCALES

W, H = 600, 360
root = tk.Tk()
root.title("🍉 西瓜绘制 — 最终版")
root.geometry(f"{W}x{H}")
root.resizable(False, False)

c = tk.Canvas(root, width=W, height=H, bg="#f5f0e0")
c.pack(fill="both", expand=True)

c.create_text(W // 2, 20, text="🍉 西瓜（v3 弧形条纹） vs 🎃 南瓜", font=("Microsoft YaHei", 14, "bold"), fill="#333")

labels = ["幼苗", "生长期", "近成熟", "成熟"]
for i, label in enumerate(labels):
    c.create_text(140 + i * 100, 50, text=label, font=("Microsoft YaHei", 10), fill="#666")

# 第一行：西瓜
c.create_text(40, 120, text="🍉", font=("Microsoft YaHei", 16), fill="#1b6e1b")
for stage in range(4):
    cx = 140 + stage * 100
    scale = _STAGE_SCALES[stage]
    if stage == 0:
        _draw_sprout(c, cx, 120, s=1.2)
    else:
        _draw_watermelon(c, cx, 120, s=1.5 * scale)
    c.create_text(cx, 165, text=f"stage={stage}", font=("Microsoft YaHei", 8), fill="#aaa")

# 第二行：南瓜
c.create_text(40, 250, text="🎃", font=("Microsoft YaHei", 16), fill="#e67300")
for stage in range(4):
    cx = 140 + stage * 100
    scale = _STAGE_SCALES[stage]
    if stage == 0:
        _draw_sprout(c, cx, 250, s=1.2)
    else:
        _draw_pumpkin(c, cx, 250, s=1.5 * scale)
    c.create_text(cx, 295, text=f"stage={stage}", font=("Microsoft YaHei", 8), fill="#aaa")

c.create_text(W // 2, 335, text="西瓜 Lv.12 | 生长240min | 售价2,400💰 | 南瓜×2", font=("Microsoft YaHei", 10), fill="#888")

root.mainloop()
