# -*- coding: utf-8 -*-
"""
开心农场 v2.0 — tkinter 图形界面版（养殖场增强版）
"""
import tkinter as tk
from tkinter import ttk, messagebox
import json
import datetime
import time
import random
import threading
import os
import sys
import io

# ============ 从 farm_game_v2 导入所有逻辑（包含 barn 模块） ============
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from farm_game_v2 import (
    FACTORY_LIST, TALENTS_LIST, TALENT_GROUPS,
    ACHIEVEMENTS_LIST, SEASONS, MAX_LANDS, WAREHOUSE_CAPACITY,
    REFRESH_INTERVAL, AUTO_SAVE_INTERVAL, SEASON_DURATION,
    BARN_ANIMALS_LIST, FEED_RECIPES, MAX_BARNS, INITIAL_BARNS,
    load_crops, new_save, try_level_up, get_season, season_crop_bonus,
    calc_growth_time, calc_yield_multiplier, get_double_chance,
    get_talent_value, get_talent_level, inventory_usage, inventory_space,
    land_upgrade_cost, check_factories_ready, try_trigger_event, get_merchant_discount,
    now_dt, now_str, parse_dt, write_save, calc_offline,
    check_achievements, check_baby_mature,
    # Barn functions
    load_save_v2, write_save_v2, calc_barn_offline,
    get_barn_animal, get_age_stage, can_barn_produce, check_feed_available,
    process_barn_production, collect_all_barns,
    barn_upgrade_cost, barn_upgrade_effects, barn_yield_multiplier, double_barn_chance,
    start_feed_production, collect_feed, check_feed_factory_ready,
    do_breed, can_breed, consume_feed,
    feed_barn_animals,
    FEED_FRUIT_NAMES,
)
from farm import SAVE_FILE


# ============ 字体 ============
def get_fonts():
    families = ["Microsoft YaHei", "SimHei", "PingFang SC", "Noto Sans CJK SC", "TkDefaultFont"]
    return {
        "normal": (families, 11),
        "small": (families, 9),
        "bold": (families, 12, "bold"),
        "title": (families, 13, "bold"),
        "button": (families, 11),
        "land": (families, 10),
        "barn": (families, 10),
    }

F = get_fonts()


# ============ 颜色 ============
COLORS = {
    "bg": "#f0f0f0",
    "land_empty": "#e8d5b7",
    "land_growing": "#fff3cd",
    "land_ready": "#d4edda",
    "land_hover": "#cce5ff",
    "btn_bg": "#e0e0e0",
    "btn_active": "#d0d0d0",
    "gold": "#b8860b",
    "exp": "#6f42c1",
    "diamond": "#00bcd4",
    "mature": "#28a745",
    "barn_empty": "#f0e6d3",
    "barn_ready": "#d4edda",
    "barn_busy": "#fff3cd",
    "barn_feed": "#cce5ff",
}


# ============ 农作物图标绘制 ============
# tkinter Canvas 绘制函数，接受 (canvas, cx, cy, s) 参数
# cx,cy 为中心坐标，s 为缩放因子（基于 32x32 坐标系）

def _draw_wheat(c, cx, cy, s=1.0):
    c.create_line(cx, cy+12*s, cx, cy-8*s, fill="#5a8a3c", width=max(1, int(2*s)))
    c.create_line(cx, cy+4*s, cx-8*s, cy+8*s, fill="#6aaa3c", width=max(1, int(1.5*s)))
    c.create_line(cx, cy+2*s, cx+8*s, cy+6*s, fill="#6aaa3c", width=max(1, int(1.5*s)))
    for i, ox in enumerate([-4, 0, 4]):
        oy = -8 - i*5
        c.create_oval(cx+ox*s-3*s, cy+oy*s-3*s, cx+ox*s+3*s, cy+oy*s+2*s, fill="#d4a017", outline="#b8860b", width=1)
        c.create_line(cx+ox*s, cy+oy*s-3*s, cx+ox*s, cy+oy*s-8*s, fill="#d4a017", width=1)

def _draw_corn(c, cx, cy, s=1.0):
    c.create_line(cx, cy+12*s, cx, cy-10*s, fill="#4a7a2c", width=max(1, int(2*s)))
    c.create_line(cx, cy-2*s, cx-10*s, cy-6*s, fill="#5a8a3c", width=max(1, int(2*s)))
    c.create_line(cx, cy+2*s, cx+10*s, cy-2*s, fill="#5a8a3c", width=max(1, int(2*s)))
    c.create_oval(cx+3*s, cy-8*s, cx+10*s, cy+4*s, fill="#f0c040", outline="#c89520", width=1)
    for i in range(3):
        c.create_line(cx+6*s+i*2*s, cy-8*s, cx+4*s+i*3*s, cy-14*s, fill="#8B4513", width=1)

def _draw_rice(c, cx, cy, s=1.0):
    c.create_line(cx, cy+12*s, cx, cy-4*s, fill="#5a8a3c", width=max(1, int(2*s)))
    c.create_line(cx, cy+2*s, cx-8*s, cy+6*s, fill="#6aaa3c", width=max(1, int(1.5*s)))
    for dx, dy in [(-4, -4), (0, -6), (4, -4)]:
        ex, ey = cx+dx*s, cy+dy*s-2*s
        c.create_line(cx, cy-4*s, ex, ey, fill="#c8a020", width=1)
        c.create_oval(ex-3*s, ey-2*s, ex+3*s, ey+3*s, fill="#d4a017", outline="#b8860b", width=1)

def _draw_rose(c, cx, cy, s=1.0):
    c.create_line(cx, cy+12*s, cx, cy-2*s, fill="#2a6a1c", width=max(1, int(2*s)))
    c.create_line(cx, cy+6*s, cx+4*s, cy+4*s, fill="#2a6a1c", width=1)
    c.create_line(cx, cy+2*s, cx-4*s, cy, fill="#2a6a1c", width=1)
    c.create_oval(cx-8*s, cy+4*s, cx-3*s, cy+9*s, fill="#3a8a2c", outline="#2a6a1c", width=1)
    for i, r in enumerate([8, 6, 4]):
        c.create_oval(cx-r*s, cy-r*s-4*s, cx+r*s, cy+r*s-4*s, fill=["#e03030","#d02020","#c01010"][i], outline="", width=0)

def _draw_carrot(c, cx, cy, s=1.0):
    c.create_polygon(cx, cy+12*s, cx-8*s, cy-2*s, cx+8*s, cy-2*s, fill="#e87020", outline="#c05a10", width=1)
    c.create_line(cx, cy+12*s, cx, cy-2*s, fill="#d06010", width=1)
    for dx in [-5, 0, 5]:
        c.create_line(cx+dx*s, cy-2*s, cx+dx*s, cy-10*s, fill="#3a8a2c", width=max(1, int(2*s)))

def _draw_pumpkin(c, cx, cy, s=1.0):
    c.create_oval(cx-12*s, cy-10*s, cx+12*s, cy+10*s, fill="#e67300", outline="#c45a00", width=1)
    for dx in [-6, 0, 6]:
        c.create_arc(cx+dx*s-8*s, cy-10*s, cx+dx*s+8*s, cy+10*s, start=0, extent=180, fill="#d46500", outline="", width=0)
    c.create_rectangle(cx-3*s, cy-12*s, cx+3*s, cy-9*s, fill="#5a8a3c", outline="#3a6a1c", width=1)
    c.create_line(cx+3*s, cy-11*s, cx+10*s, cy-15*s, cx+12*s, cy-10*s, fill="#5a8a3c", width=max(1, int(1.5*s)), smooth=True)

def _draw_golden_pumpkin(c, cx, cy, s=1.0):
    """金色南瓜图标（彩蛋）"""
    # 主体 - 金色多层
    c.create_oval(cx-12*s, cy-10*s, cx+12*s, cy+10*s, fill="#ffd700", outline="#b8860b", width=2)
    for dx in [-6, 0, 6]:
        c.create_arc(cx+dx*s-8*s, cy-10*s, cx+dx*s+8*s, cy+10*s, start=0, extent=180, fill="#ffc125", outline="", width=0)
    # 高光
    c.create_oval(cx-6*s, cy-7*s, cx-2*s, cy-2*s, fill="#fff8dc", outline="", width=0)
    # 金色蒂柄
    c.create_rectangle(cx-3*s, cy-12*s, cx+3*s, cy-9*s, fill="#8B6914", outline="#6b4e0a", width=1)
    c.create_line(cx+3*s, cy-11*s, cx+10*s, cy-15*s, cx+12*s, cy-10*s, fill="#8B6914", width=max(1, int(2*s)), smooth=True)
    # 闪光星星
    for ex, ey in [(cx+6*s, cy-6*s), (cx+9*s, cy-3*s), (cx-3*s, cy+5*s), (cx-7*s, cy-4*s), (cx+4*s, cy+6*s)]:
        c.create_text(ex, ey, text="✦", fill="#fff8dc", font=("Microsoft YaHei", max(7, int(6*s))))

CROP_DRAW_FUNCS = {
    "小麦": _draw_wheat, "玉米": _draw_corn, "水稻": _draw_rice,
    "玫瑰": _draw_rose, "胡萝卜": _draw_carrot, "南瓜": _draw_pumpkin,
    "金色南瓜": _draw_golden_pumpkin,
}


# ============ 动物图标绘制 ============

def _draw_chicken(c, cx, cy, s=1.0):
    c.create_oval(cx-8*s, cy-6*s, cx+8*s, cy+8*s, fill="#f0e060", outline="#d0b040", width=1)
    c.create_oval(cx+4*s, cy-10*s, cx+12*s, cy-2*s, fill="#f0e060", outline="#d0b040", width=1)
    c.create_polygon(cx+12*s, cy-6*s, cx+16*s, cy-5*s, cx+12*s, cy-4*s, fill="#e8a020", outline="", width=0)
    c.create_arc(cx+6*s, cy-12*s, cx+11*s, cy-8*s, start=0, extent=180, fill="#e03030", outline="", width=0)
    c.create_oval(cx+8*s, cy-7*s, cx+10*s, cy-5*s, fill="#333", outline="", width=0)
    c.create_arc(cx-4*s, cy-2*s, cx+4*s, cy+4*s, start=0, extent=-180, fill="#e0c840", outline="", width=0)

def _draw_duck(c, cx, cy, s=1.0):
    c.create_oval(cx-10*s, cy-4*s, cx+8*s, cy+8*s, fill="#c8b878", outline="#a89858", width=1)
    c.create_oval(cx+2*s, cy-8*s, cx+10*s, cy, fill="#6a8a3c", outline="#5a7a2c", width=1)
    c.create_polygon(cx+10*s, cy-4*s, cx+16*s, cy-3*s, cx+16*s, cy-1*s, cx+10*s, cy-2*s, fill="#e8a020", outline="", width=0)
    c.create_oval(cx+7*s, cy-5*s, cx+9*s, cy-3*s, fill="#333", outline="", width=0)
    c.create_arc(cx-4*s, cy, cx+4*s, cy+5*s, start=0, extent=-180, fill="#b8a868", outline="", width=0)

def _draw_rabbit(c, cx, cy, s=1.0):
    c.create_oval(cx-8*s, cy-2*s, cx+8*s, cy+8*s, fill="#e0d8d0", outline="#c0b8b0", width=1)
    c.create_oval(cx-6*s, cy-8*s, cx+6*s, cy+2*s, fill="#e0d8d0", outline="#c0b8b0", width=1)
    for dx in [-3, 3]:
        c.create_oval(cx+dx*s-3*s, cy-18*s, cx+dx*s+3*s, cy-8*s, fill="#e0d8d0", outline="#c0b8b0", width=1)
        c.create_oval(cx+dx*s-1.5*s, cy-16*s, cx+dx*s+1.5*s, cy-9*s, fill="#f0c0c0", outline="", width=0)
    c.create_oval(cx-3*s, cy-5*s, cx-1*s, cy-3*s, fill="#e03030", outline="", width=0)
    c.create_oval(cx+1*s, cy-5*s, cx+3*s, cy-3*s, fill="#e03030", outline="", width=0)
    c.create_oval(cx-1*s, cy-2*s, cx+1*s, cy, fill="#f0a0a0", outline="", width=0)

def _draw_goose(c, cx, cy, s=1.0):
    c.create_oval(cx-10*s, cy-2*s, cx+8*s, cy+8*s, fill="#f0f0f0", outline="#d0d0d0", width=1)
    c.create_line(cx+2*s, cy-2*s, cx+6*s, cy-12*s, fill="#f0f0f0", width=max(2, int(4*s)))
    c.create_line(cx+2*s, cy-2*s, cx+6*s, cy-12*s, fill="#d0d0d0", width=1)
    c.create_oval(cx+4*s, cy-14*s, cx+10*s, cy-8*s, fill="#f0f0f0", outline="#d0d0d0", width=1)
    c.create_polygon(cx+10*s, cy-12*s, cx+16*s, cy-11*s, cx+10*s, cy-10*s, fill="#e8a020", outline="", width=0)
    c.create_oval(cx+7*s, cy-12*s, cx+9*s, cy-10*s, fill="#333", outline="", width=0)
    c.create_arc(cx-4*s, cy+1*s, cx+4*s, cy+6*s, start=0, extent=-180, fill="#e8e8e8", outline="", width=0)

def _draw_sheep(c, cx, cy, s=1.0):
    body = [cx-10*s, cy-4*s, cx-8*s, cy-10*s, cx-4*s, cy-12*s, cx, cy-13*s,
            cx+4*s, cy-12*s, cx+8*s, cy-10*s, cx+10*s, cy-4*s, cx+10*s, cy+2*s,
            cx+8*s, cy+6*s, cx+4*s, cy+8*s, cx, cy+9*s, cx-4*s, cy+8*s,
            cx-8*s, cy+6*s, cx-10*s, cy+2*s]
    c.create_polygon(body, fill="#f0f0f0", outline="#d0d0d0", width=1)
    c.create_oval(cx-6*s, cy-8*s, cx+2*s, cy, fill="#e8e0d0", outline="#d0c8b8", width=1)
    c.create_oval(cx-3*s, cy-5*s, cx-1*s, cy-3*s, fill="#333", outline="", width=0)
    c.create_oval(cx-1*s, cy-5*s, cx+1*s, cy-3*s, fill="#333", outline="", width=0)
    c.create_oval(cx-8*s, cy-6*s, cx-5*s, cy-3*s, fill="#e0d8c8", outline="", width=0)
    c.create_oval(cx+2*s, cy-6*s, cx+5*s, cy-3*s, fill="#e0d8c8", outline="", width=0)
    for dx in [-6, -2, 2, 6]:
        c.create_line(cx+dx*s, cy+8*s, cx+dx*s, cy+13*s, fill="#333", width=max(1, int(2*s)))

def _draw_pig(c, cx, cy, s=1.0):
    c.create_oval(cx-10*s, cy-4*s, cx+10*s, cy+8*s, fill="#f0b0b0", outline="#d09090", width=1)
    c.create_oval(cx-8*s, cy-8*s, cx+2*s, cy+2*s, fill="#f0b0b0", outline="#d09090", width=1)
    c.create_oval(cx-6*s, cy-3*s, cx-2*s, cy, fill="#e89090", outline="#d08080", width=1)
    c.create_oval(cx-5*s, cy-2*s, cx-4*s, cy-1*s, fill="#c06060", outline="", width=0)
    c.create_oval(cx-3*s, cy-2*s, cx-2*s, cy-1*s, fill="#c06060", outline="", width=0)
    c.create_oval(cx-4*s, cy-5*s, cx-2*s, cy-3*s, fill="#333", outline="", width=0)
    c.create_polygon(cx+1*s, cy-8*s, cx+4*s, cy-12*s, cx+5*s, cy-7*s, fill="#f0b0b0", outline="#d09090", width=1)
    c.create_line(cx+10*s, cy+2*s, cx+14*s, cy-2*s, cx+12*s, cy-6*s, fill="#f0b0b0", width=max(1, int(2*s)), smooth=True)

def _draw_cow(c, cx, cy, s=1.0):
    c.create_oval(cx-10*s, cy-4*s, cx+10*s, cy+8*s, fill="#f0f0f0", outline="#d0d0d0", width=1)
    c.create_oval(cx-6*s, cy-2*s, cx-2*s, cy+3*s, fill="#333", outline="", width=0)
    c.create_oval(cx+2*s, cy+1*s, cx+6*s, cy+5*s, fill="#333", outline="", width=0)
    c.create_oval(cx-8*s, cy-8*s, cx-2*s, cy, fill="#f0f0f0", outline="#d0d0d0", width=1)
    c.create_line(cx-7*s, cy-8*s, cx-9*s, cy-14*s, fill="#8B7355", width=max(1, int(2*s)))
    c.create_line(cx-3*s, cy-8*s, cx-1*s, cy-14*s, fill="#8B7355", width=max(1, int(2*s)))
    c.create_oval(cx-6*s, cy-5*s, cx-4*s, cy-3*s, fill="#333", outline="", width=0)
    c.create_oval(cx-5*s, cy-2*s, cx-3*s, cy, fill="#e0c0c0", outline="", width=0)
    for dx in [-6, -2, 2, 6]:
        c.create_line(cx+dx*s, cy+8*s, cx+dx*s, cy+13*s, fill="#333", width=max(1, int(2*s)))

def _draw_alpaca(c, cx, cy, s=1.0):
    c.create_oval(cx-8*s, cy-2*s, cx+8*s, cy+8*s, fill="#d0b080", outline="#b09060", width=1)
    c.create_oval(cx-4*s, cy-10*s, cx+4*s, cy-2*s, fill="#d0b080", outline="#b09060", width=1)
    c.create_oval(cx-4*s, cy-14*s, cx+4*s, cy-8*s, fill="#d0b080", outline="#b09060", width=1)
    c.create_arc(cx-4*s, cy-16*s, cx+4*s, cy-12*s, start=0, extent=180, fill="#e0c890", outline="", width=0)
    c.create_oval(cx-2*s, cy-12*s, cx, cy-10*s, fill="#333", outline="", width=0)
    c.create_oval(cx+1*s, cy-12*s, cx+3*s, cy-10*s, fill="#333", outline="", width=0)
    c.create_oval(cx, cy-9*s, cx+2*s, cy-8*s, fill="#c0a070", outline="", width=0)
    c.create_oval(cx-5*s, cy-16*s, cx-3*s, cy-13*s, fill="#d0b080", outline="", width=0)
    c.create_oval(cx+3*s, cy-16*s, cx+5*s, cy-13*s, fill="#d0b080", outline="", width=0)

def _draw_horse(c, cx, cy, s=1.0):
    c.create_oval(cx-10*s, cy-4*s, cx+10*s, cy+8*s, fill="#a08050", outline="#807040", width=1)
    c.create_polygon(cx+4*s, cy-4*s, cx+8*s, cy-14*s, cx+12*s, cy-14*s, cx+10*s, cy-4*s,
                     fill="#a08050", outline="#807040", width=1)
    c.create_oval(cx+6*s, cy-16*s, cx+14*s, cy-8*s, fill="#a08050", outline="#807040", width=1)
    c.create_oval(cx+10*s, cy-14*s, cx+12*s, cy-12*s, fill="#333", outline="", width=0)
    c.create_line(cx+6*s, cy-14*s, cx+2*s, cy-10*s, cx+4*s, cy-4*s, fill="#604020", width=max(1, int(2*s)), smooth=True)
    c.create_line(cx-10*s, cy+2*s, cx-16*s, cy-2*s, fill="#604020", width=max(1, int(2*s)))
    for dx in [-6, -2, 2, 6]:
        c.create_line(cx+dx*s, cy+8*s, cx+dx*s, cy+13*s, fill="#604020", width=max(1, int(2*s)))

def _draw_deer(c, cx, cy, s=1.0):
    c.create_oval(cx-10*s, cy-2*s, cx+8*s, cy+8*s, fill="#c8a060", outline="#b08840", width=1)
    c.create_line(cx+2*s, cy-2*s, cx+4*s, cy-10*s, fill="#c8a060", width=max(2, int(4*s)))
    c.create_oval(cx, cy-12*s, cx+7*s, cy-6*s, fill="#c8a060", outline="#b08840", width=1)
    c.create_line(cx+3*s, cy-12*s, cx+1*s, cy-18*s, fill="#8B7355", width=max(1, int(2*s)))
    c.create_line(cx+1*s, cy-16*s, cx-3*s, cy-18*s, fill="#8B7355", width=max(1, int(1.5*s)))
    c.create_line(cx+3*s, cy-12*s, cx+6*s, cy-18*s, fill="#8B7355", width=max(1, int(2*s)))
    c.create_line(cx+5*s, cy-16*s, cx+9*s, cy-18*s, fill="#8B7355", width=max(1, int(1.5*s)))
    c.create_oval(cx+4*s, cy-10*s, cx+6*s, cy-8*s, fill="#333", outline="", width=0)
    c.create_oval(cx+2*s, cy-7*s, cx+4*s, cy-6*s, fill="#333", outline="", width=0)
    c.create_oval(cx-10*s, cy-2*s, cx-7*s, cy+1*s, fill="#f0f0f0", outline="", width=0)
    for dx in [-6, -2, 2, 6]:
        c.create_line(cx+dx*s, cy+8*s, cx+dx*s, cy+13*s, fill="#8B7355", width=max(1, int(2*s)))

ANIMAL_DRAW_FUNCS = {
    "鸡": _draw_chicken, "鸭": _draw_duck, "兔": _draw_rabbit, "鹅": _draw_goose,
    "羊": _draw_sheep, "猪": _draw_pig, "牛": _draw_cow,
    "羊驼": _draw_alpaca, "马": _draw_horse, "鹿": _draw_deer,
}


# ============ GUI ============
class FarmGUIv2:
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("开心农场 v2.0 — 养殖场增强版")
        self.root.geometry("1000x760")
        self.root.minsize(950, 720)
        self.root.configure(bg=COLORS["bg"])

        # 游戏数据（使用 v2 加载以包含养殖场数据）
        self.crops = load_crops()
        self.data = load_save_v2()

        # 离线收益（含养殖场）
        self._calc_offline_v2()

        # 变量
        self.land_canvas = None
        self.barn_canvas = None
        self.event_queue = []
        self._save_pending = False
        self.current_tab = "land"  # "land" or "barn"

        # 创建界面
        self._create_top_bar()
        self._create_tab_bar()
        self._create_main_area()
        self._create_event_log()

        # 检查成就
        self._log("💡 欢迎回到开心农场 v2.0（养殖场增强版）！")
        new_achs = check_achievements(self.data)
        if new_achs:
            self._log(f"🏆 达成 {new_achs} 个新成就！")

        # 自动保存 + 自动刷新
        self._schedule_auto_save()
        self._schedule_refresh()

        # 关闭事件
        self.root.protocol("WM_DELETE_WINDOW", self._on_close)

    # ==================== 离线计算 ====================

    def _calc_offline_v2(self):
        """增强离线收益（含养殖场）"""
        # 作物离线计算
        calc_offline(self.data, self.crops)
        # 养殖场离线计算
        items, exp = calc_barn_offline(self.data)
        if items > 0:
            self._log(f"📦 离线养殖场产出 {items} 件，{exp}✨")

    # ==================== 界面构建 ====================

    def _create_top_bar(self):
        """顶部状态栏"""
        self.top_frame = tk.Frame(self.root, bg=COLORS["bg"], height=85)
        self.top_frame.pack(side="top", fill="x", padx=10, pady=(8, 2))
        self.top_frame.pack_propagate(False)

        self.status_labels = {}
        row1 = tk.Frame(self.top_frame, bg=COLORS["bg"])
        row1.pack(fill="x", pady=(6, 3))
        row2 = tk.Frame(self.top_frame, bg=COLORS["bg"])
        row2.pack(fill="x", pady=(0, 4))

        info1 = [
            ("gold", "💰 0"),
            ("diamond", "💎 0"),
            ("level", "Lv.1"),
            ("exp", "✨ 0/100"),
        ]
        for key, text in info1:
            lbl = tk.Label(row1, text=text, font=F["bold"], bg=COLORS["bg"])
            lbl.pack(side="left", padx=(0, 25))
            self.status_labels[key] = lbl

        info2 = [
            ("season", "🌸 春季"),
            ("land_usage", "🌱 0/6"),
            ("barn_usage", "🐔 0/6"),
            ("barn_pending", "📦 待收:0"),
            ("factories", "🏭 0"),
            ("save_time", "💾 --"),
        ]
        for key, text in info2:
            lbl = tk.Label(row2, text=text, font=F["normal"], bg=COLORS["bg"])
            lbl.pack(side="left", padx=(0, 25))
            self.status_labels[key] = lbl

    def _create_tab_bar(self):
        """标签切换栏"""
        tab_frame = tk.Frame(self.root, bg=COLORS["bg"])
        tab_frame.pack(side="top", fill="x", padx=10, pady=(0, 2))

        self.tab_btns = {}
        for tab_id, text in [("land", "🌱 土地"), ("barn", "🐔 养殖场")]:
            btn = tk.Button(tab_frame, text=text, font=F["bold"],
                           command=lambda t=tab_id: self._switch_tab(t),
                           relief="raised", bd=2, padx=15, pady=2)
            btn.pack(side="left", padx=2)
            self.tab_btns[tab_id] = btn

        # 额外操作按钮（右对齐）
        spacer = tk.Frame(tab_frame, bg=COLORS["bg"])
        spacer.pack(side="left", fill="x", expand=True)

        for key, text, cmd in [
            ("shop", "🏪 商店", self._on_shop),
            ("save", "💾 保存", self._on_save),
            ("help", "📖 帮助", self._on_help),
        ]:
            btn = tk.Button(tab_frame, text=text, font=F["button"],
                           command=cmd, bg=COLORS["btn_bg"],
                           activebackground=COLORS["btn_active"],
                           relief="raised", bd=1)
            btn.pack(side="right", padx=2)

    def _switch_tab(self, tab_id):
        """切换土地/养殖场标签"""
        self.current_tab = tab_id
        for tid, btn in self.tab_btns.items():
            btn.config(relief="sunken" if tid == tab_id else "raised",
                      bg="#d0e8ff" if tid == tab_id else COLORS["btn_bg"])
        self._show_tab_content(tab_id)

    def _create_main_area(self):
        """中间主区域"""
        self.main_frame = tk.Frame(self.root, bg=COLORS["bg"])
        self.main_frame.pack(fill="both", expand=True, padx=10, pady=5)

        # 土地框架（默认显示）
        self.land_container = tk.Frame(self.main_frame, bg=COLORS["bg"])
        self.land_container.pack(fill="both", expand=True)

        # 养殖场框架（隐藏）
        self.barn_container = tk.Frame(self.main_frame, bg=COLORS["bg"])
        self.barn_container.pack_forget()

        self._build_land_ui()
        self._build_barn_ui()

        # 默认显示土地
        self._switch_tab("land")

    # ==================== 土地界面 ====================

    def _build_land_ui(self):
        """构建土地界面"""
        # 左侧土地网格
        grid_container = tk.Frame(self.land_container, bg=COLORS["bg"])
        grid_container.pack(side="left", fill="both", expand=True)

        tk.Label(grid_container, text="🌱 土地状况", font=F["title"],
                 bg=COLORS["bg"], anchor="w").pack(fill="x")

        self.land_frame = tk.Frame(grid_container, bg=COLORS["bg"])
        self.land_frame.pack(fill="both", expand=True, pady=2)

        # 右侧操作栏（可滚动）
        self.action_frame = tk.Frame(self.land_container, bg="#f5f5f5",
                                     width=230, relief="groove", bd=1)
        self.action_frame.pack(side="right", fill="y", padx=(10, 0))
        self.action_frame.pack_propagate(False)

        tk.Label(self.action_frame, text="📋 操作菜单", font=F["title"],
                 bg="#f5f5f5").pack(pady=(8, 3))

        action_canvas = tk.Canvas(self.action_frame, bg="#f5f5f5",
                                  highlightthickness=0)
        action_scrollbar = tk.Scrollbar(self.action_frame, orient="vertical",
                                        command=action_canvas.yview)
        self.action_inner = tk.Frame(action_canvas, bg="#f5f5f5")

        def _on_canvas_configure(e):
            action_canvas.itemconfig(inner_id, width=e.width)
            action_canvas.configure(scrollregion=action_canvas.bbox("all"))

        self.action_inner.bind("<Configure>", lambda e: action_canvas.configure(scrollregion=action_canvas.bbox("all")))
        action_canvas.bind("<Configure>", _on_canvas_configure)
        inner_id = action_canvas.create_window((0, 0), window=self.action_inner, anchor="nw")
        action_canvas.configure(yscrollcommand=action_scrollbar.set)

        action_canvas.pack(side="left", fill="both", expand=True)
        action_scrollbar.pack(side="right", fill="y")

        actions = [
            ("1", "🌱 种植", self._on_plant),
            ("3", "🌾 收获", self._on_harvest),
            ("8", "🔓 解锁土地", self._on_unlock_land),
            ("5", "🏭 加工", self._on_factories),
            ("6", "📦 仓库", self._on_warehouse),
            ("9", "⭐ 天赋", self._on_talents),
            ("0", "🏆 成就", self._on_achievements),
        ]

        self.action_btns = {}
        for key, text, cmd in actions:
            btn = tk.Button(self.action_inner, text=text, font=F["button"],
                            command=cmd, bg=COLORS["btn_bg"],
                            activebackground=COLORS["btn_active"],
                            relief="raised", bd=1, height=1)
            btn.pack(fill="x", padx=8, pady=3)
            self.action_btns[key] = btn

        self._build_land_grid()

    def _build_land_grid(self):
        """创建单 Canvas 土地网格"""
        for w in self.land_frame.winfo_children():
            w.destroy()
        self.land_canvas = tk.Canvas(self.land_frame, highlightthickness=0, bg=COLORS["bg"])
        self.land_canvas.pack(fill="both", expand=True)
        self.land_canvas.bind("<Button-1>", self._on_land_click)
        self.land_canvas.bind("<Configure>", lambda e: self._update_land_grid())
        self._update_land_grid()

    # ==================== 养殖场界面 ====================

    def _build_barn_ui(self):
        """构建养殖场界面（左侧栏位网格 + 右侧操作栏，与土地布局对称）"""
        # 顶部状态
        self.barn_status_frame = tk.Frame(self.barn_container, bg=COLORS["bg"])
        self.barn_status_frame.pack(fill="x", pady=(0, 5))

        self.barn_status_labels = {}
        for key, text in [
            ("usage", "🐔 栏位: 0/6"),
            ("pending", "📦 待收: 0"),
            ("feed", "🍽️ 饲料: 0"),
        ]:
            lbl = tk.Label(self.barn_status_frame, text=text,
                          font=F["normal"], bg=COLORS["bg"])
            lbl.pack(side="left", padx=(0, 25))
            self.barn_status_labels[key] = lbl

        # 中间主区域：左侧网格 + 右侧操作栏
        barn_main = tk.Frame(self.barn_container, bg=COLORS["bg"])
        barn_main.pack(fill="both", expand=True)

        # 左侧栏位网格
        self.barn_grid_frame = tk.Frame(barn_main, bg=COLORS["bg"])
        self.barn_grid_frame.pack(side="left", fill="both", expand=True)
        self._build_barn_grid()

        # 右侧操作栏（可滚动，与土地侧边栏同宽）
        self.barn_action_frame = tk.Frame(barn_main, bg="#f5f5f5",
                                          width=230, relief="groove", bd=1)
        self.barn_action_frame.pack(side="right", fill="y", padx=(10, 0))
        self.barn_action_frame.pack_propagate(False)

        tk.Label(self.barn_action_frame, text="🐔 养殖操作", font=F["title"],
                 bg="#f5f5f5").pack(pady=(8, 3))

        action_canvas = tk.Canvas(self.barn_action_frame, bg="#f5f5f5",
                                  highlightthickness=0)
        action_scrollbar = tk.Scrollbar(self.barn_action_frame, orient="vertical",
                                        command=action_canvas.yview)
        self.barn_action_inner = tk.Frame(action_canvas, bg="#f5f5f5")

        def _on_canvas_configure(e):
            action_canvas.itemconfig(inner_id, width=e.width)
            action_canvas.configure(scrollregion=action_canvas.bbox("all"))

        self.barn_action_inner.bind("<Configure>", lambda e: action_canvas.configure(scrollregion=action_canvas.bbox("all")))
        action_canvas.bind("<Configure>", _on_canvas_configure)
        inner_id = action_canvas.create_window((0, 0), window=self.barn_action_inner, anchor="nw")
        action_canvas.configure(yscrollcommand=action_scrollbar.set)

        action_canvas.pack(side="left", fill="both", expand=True)
        action_scrollbar.pack(side="right", fill="y")

        barn_actions = [
            ("buy", "🐣 购买动物", self._on_buy_barn_animal),
            ("feed", "🍽️ 投喂", self._on_feed_animals),
            ("collect", "📦 收集产出", self._on_collect_barn),
            ("feed_factory", "🏭 饲料加工", self._on_feed_factory),
            ("breed", "🧬 繁殖", self._on_breed),
            ("warehouse", "📦 仓库", self._on_warehouse),
            ("unlock", "🔓 解锁栏位", self._on_unlock_barn),
        ]
        self.barn_action_btns = {}
        for key, text, cmd in barn_actions:
            btn = tk.Button(self.barn_action_inner, text=text, font=F["button"],
                           command=cmd, bg=COLORS["btn_bg"],
                           activebackground=COLORS["btn_active"],
                           relief="raised", bd=1, height=1)
            btn.pack(fill="x", padx=8, pady=3)
            self.barn_action_btns[key] = btn

        # 底部饲料库存
        self.feed_info_frame = tk.Frame(self.barn_container, bg="#fafafa",
                                        relief="groove", bd=1, height=30)
        self.feed_info_frame.pack(fill="x", pady=(5, 0))
        self.feed_info_frame.pack_propagate(False)
        self.feed_info_label = tk.Label(self.feed_info_frame, text="🍽️ 饲料库存: 空",
                                        font=F["small"], bg="#fafafa", anchor="w")
        self.feed_info_label.pack(fill="x", padx=10, pady=2)

    def _build_barn_grid(self):
        """创建单 Canvas 养殖栏位网格"""
        for w in self.barn_grid_frame.winfo_children():
            w.destroy()
        self.barn_canvas = tk.Canvas(self.barn_grid_frame, highlightthickness=0, bg=COLORS["bg"])
        self.barn_canvas.pack(fill="both", expand=True)
        self.barn_canvas.bind("<Button-1>", self._on_barn_click)
        self.barn_canvas.bind("<Configure>", lambda e: self._update_barn_grid())
        self._update_barn_grid()

    # ==================== 事件日志 ====================

    def _create_event_log(self):
        """底部事件日志"""
        log_frame = tk.Frame(self.root, bg=COLORS["bg"], height=100)
        log_frame.pack(side="bottom", fill="x", padx=10, pady=(0, 8))
        log_frame.pack_propagate(False)

        tk.Label(log_frame, text="📋 事件日志", font=F["bold"],
                 bg=COLORS["bg"], anchor="w").pack(fill="x")

        text_frame = tk.Frame(log_frame, relief="sunken", bd=1)
        text_frame.pack(fill="both", expand=True)

        self.log_text = tk.Text(text_frame, font=F["normal"], height=4,
                                wrap="word", state="disabled",
                                bg="#fafafa", fg="#333")
        self.log_text.pack(side="left", fill="both", expand=True)

        scrollbar = tk.Scrollbar(text_frame, command=self.log_text.yview)
        scrollbar.pack(side="right", fill="y")
        self.log_text.config(yscrollcommand=scrollbar.set)

    # ==================== 标签切换 ====================

    def _show_tab_content(self, tab_id):
        """显示指定标签内容"""
        if tab_id == "land":
            self.land_container.pack(fill="both", expand=True)
            self.barn_container.pack_forget()
        else:
            self.land_container.pack_forget()
            self.barn_container.pack(fill="both", expand=True)
            self._update_barn_grid()

    # ==================== 界面更新 ====================

    def _schedule_refresh(self):
        """5 秒自动刷新（含金色南瓜检测）"""
        self._check_golden_pumpkin_transformation()
        self._update_ui()
        self.root.after(5000, self._schedule_refresh)

    def _schedule_auto_save(self):
        """5 分钟自动保存"""
        write_save_v2(self.data)
        self.root.after(AUTO_SAVE_INTERVAL * 1000, self._schedule_auto_save)

    def _update_ui(self):
        """刷新所有界面元素"""
        d = self.data
        try:
            # 状态栏
            need = d["level"] * 100
            self.status_labels["gold"].config(text=f"💰 {d['gold']:,}")
            self.status_labels["diamond"].config(text=f"💎 {d.get('diamond', 0)}")
            self.status_labels["level"].config(text=f"Lv.{d['level']}")
            self.status_labels["exp"].config(text=f"✨ {d['exp']}/{need}")

            season, _ = get_season(d)
            planted = sum(1 for l in d["lands"][:d["unlocked_lands"]] if l["crop"])
            factories_ready = sum(1 for f in FACTORY_LIST if d["factories"][f["factory"]].get("ready"))

            # 养殖场统计
            unlocked_barns = d.get("unlocked_barns", INITIAL_BARNS)
            occupied = sum(1 for b in d.get("barns", [])[:unlocked_barns] if b["animal"] is not None)
            pending = sum(b.get("pending_product", 0) for b in d.get("barns", [])[:unlocked_barns])
            feed_total = sum(d.get("feed_inventory", {}).values())

            self.status_labels["season"].config(text=f"🌸 {season}季")
            self.status_labels["land_usage"].config(text=f"🌱 {planted}/{d['unlocked_lands']}")
            self.status_labels["barn_usage"].config(text=f"🐔 {occupied}/{unlocked_barns}")
            self.status_labels["barn_pending"].config(text=f"📦 待收:{pending}")
            self.status_labels["factories"].config(text=f"🏭 {factories_ready}")
            self.status_labels["save_time"].config(text=f"💾 {d['last_save_time'][5:16]}")

            # 土地网格
            self._update_land_grid()

            # 养殖场网格
            self._update_barn_grid()
            self._update_barn_status()

            # 检查工厂完成
            check_factories_ready(d)

            # 检查饲料厂完成
            check_feed_factory_ready(d)

            # 检查幼崽成熟
            check_baby_mature(d)

            # 养殖场生产
            process_barn_production(d)

            # 天赋：自动收集动物产品
            if get_talent_level(d["talent_tree"], "auto_collect") > 0:
                total, collected = collect_all_barns(d)
                if total > 0:
                    self._log(f"🤖 自动收集 {total} 件动物产品")

            # 随机事件 + 日志
            old_events = d.get("total_events", 0)
            old_stdout = sys.stdout
            sys.stdout = buf = io.StringIO()
            try:
                try_trigger_event(d, self.crops)
            finally:
                sys.stdout = old_stdout
            captured = buf.getvalue().strip()
            if captured:
                for line in captured.split("\n"):
                    line = line.strip()
                    if line:
                        self._log(line)

            # 成就检查
            check_achievements(d)

        except Exception as e:
            self._log(f"⚠️ 刷新异常: {e}")

    def _update_land_grid(self):
        """在 Canvas 上绘制土地网格（含农作物图标）"""
        if not hasattr(self, 'land_canvas') or not self.land_canvas:
            return
        self.land_canvas.delete("all")
        d = self.data
        now = now_dt()
        season, _ = get_season(d)
        cw = self.land_canvas.winfo_width() - 2
        ch = self.land_canvas.winfo_height() - 2
        if cw < 50 or ch < 50:
            return
        cols, rows = 10, 5
        cell_w, cell_h = cw / cols, ch / rows

        for r in range(rows):
            for c in range(cols):
                lid = r * cols + c + 1
                x0, y0 = c * cell_w, r * cell_h
                x1, y1 = x0 + cell_w, y0 + cell_h
                cx, cy_ = (x0 + x1) / 2, (y0 + y1) / 2

                font_s = max(7, min(cell_w, cell_h) / 6)
                ft = ("Microsoft YaHei", int(font_s))
                ft2 = ("Microsoft YaHei", max(7, int(font_s) - 2))

                if lid > d["unlocked_lands"]:
                    self.land_canvas.create_rectangle(x0, y0, x1, y1, fill="#ddd", outline="#ccc", width=1)
                    self.land_canvas.create_text(cx, cy_, text=f"#{lid}\n🔒", font=ft, fill="#999", justify="center")
                    continue

                land = d["lands"][lid - 1]

                if not land["crop"]:
                    lv_show = land.get("upgrade_level", 1)
                    self.land_canvas.create_rectangle(x0, y0, x1, y1, fill=COLORS["land_empty"], outline="#c0b090", width=1)
                    self.land_canvas.create_text(cx, cy_, text=f"#{lid}\n⬜\nLv.{lv_show}", font=ft, fill="#666", justify="center")
                else:
                    pt = parse_dt(land["plant_time"])
                    growth = calc_growth_time(land["crop"], land["upgrade_level"], d["talent_tree"])
                    # 金色南瓜需要双倍生长时间
                    if land.get("golden_pumpkin"):
                        growth *= 2
                    remain = growth - (now - pt).total_seconds() / 60.0
                    name = land["crop"]
                    is_golden = land.get("golden_pumpkin", False)

                    if remain <= 0:
                        bg_c, border = COLORS["land_ready"], "#90c090"
                    else:
                        bg_c, border = COLORS["land_growing"], "#d0c080"
                    self.land_canvas.create_rectangle(x0, y0, x1, y1, fill=bg_c, outline=border, width=1)

                    # 土地编号 + 等级
                    lv_show = land.get("upgrade_level", 1)
                    self.land_canvas.create_text(cx, y0 + 4, text=f"#{lid} Lv.{lv_show}", font=ft2, fill="#333", anchor="n")

                    # 作物图标（金色南瓜用特殊图标）
                    size = min(cell_w, cell_h) * 0.55
                    s = size / 32
                    draw_name = "金色南瓜" if is_golden else name
                    draw_func = CROP_DRAW_FUNCS.get(draw_name)
                    if draw_func:
                        draw_func(self.land_canvas, cx, cy_ - 1, s)

                    # 状态文字
                    if remain <= 0:
                        icon = "🌟" if is_golden else "✅"
                        self.land_canvas.create_text(cx, y1 - 4, text=icon, font=ft2, fill="#b8860b" if is_golden else "#28a745", anchor="s")
                    else:
                        m, sec = int(remain), int((remain - int(remain)) * 60)
                        self.land_canvas.create_text(cx, y1 - 3, text=f"{m}:{sec:02d}", font=ft2, fill="#333", anchor="s")

    def _update_barn_grid(self):
        """在 Canvas 上绘制养殖栏位网格（含动物图标）"""
        if not hasattr(self, 'barn_canvas') or not self.barn_canvas:
            return
        self.barn_canvas.delete("all")
        d = self.data
        now = now_dt()
        unlocked_barns = d.get("unlocked_barns", INITIAL_BARNS)
        cw = self.barn_canvas.winfo_width() - 2
        ch = self.barn_canvas.winfo_height() - 2
        if cw < 50 or ch < 50:
            return
        cols, rows = 10, 5
        cell_w, cell_h = cw / cols, ch / rows

        for r in range(rows):
            for c in range(cols):
                bid = r * cols + c + 1
                x0, y0 = c * cell_w, r * cell_h
                x1, y1 = x0 + cell_w, y0 + cell_h
                cx, cy_ = (x0 + x1) / 2, (y0 + y1) / 2

                font_s = max(7, min(cell_w, cell_h) / 6)
                ft = ("Microsoft YaHei", int(font_s))
                ft2 = ("Microsoft YaHei", max(7, int(font_s) - 2))

                if bid > unlocked_barns:
                    self.barn_canvas.create_rectangle(x0, y0, x1, y1, fill="#ddd", outline="#ccc", width=1)
                    self.barn_canvas.create_text(cx, cy_, text=f"#{bid}\n🔒", font=ft, fill="#999", justify="center")
                    continue

                barn = d["barns"][bid - 1]
                lv = barn.get("level", 1)

                if barn["animal"] is None:
                    self.barn_canvas.create_rectangle(x0, y0, x1, y1, fill=COLORS["barn_empty"], outline="#c0b090", width=1)
                    self.barn_canvas.create_text(cx, cy_, text=f"#{bid}\n⬜空闲\nLv.{lv}", font=ft2, fill="#666", justify="center")
                else:
                    a = get_barn_animal(barn["animal_type"])
                    stage = get_age_stage(barn)
                    pending = barn.get("pending_product", 0)
                    stage_emoji = {"juvenile": "🐣", "adult": "🐔", "elder": "👴"}.get(stage, "🐔")

                    # 背景色
                    if pending > 0:
                        bg_c, border = COLORS["barn_ready"], "#90c090"
                    elif can_barn_produce(barn, d):
                        feed_ok = check_feed_available(d, barn["animal_type"])
                        bg_c, border = (COLORS["barn_busy"], "#c0b060") if feed_ok else ("#f8d7da", "#e0a0a0")
                    else:
                        bg_c, border = COLORS["barn_busy"], "#c0b060"
                    self.barn_canvas.create_rectangle(x0, y0, x1, y1, fill=bg_c, outline=border, width=1)

                    # 编号 + 等级
                    self.barn_canvas.create_text(cx, y0 + 4, text=f"#{bid} Lv.{lv}", font=ft2, fill="#333", anchor="n")

                    # 动物图标
                    size = min(cell_w, cell_h) * 0.55
                    s = size / 32
                    draw_func = ANIMAL_DRAW_FUNCS.get(barn["animal_type"])
                    if draw_func:
                        draw_func(self.barn_canvas, cx, cy_ - 1, s)

                    # 状态文字
                    if pending > 0:
                        self.barn_canvas.create_text(cx, y1 - 4, text=f"✅{pending}个", font=ft2, fill="#28a745", anchor="s")
                    elif can_barn_produce(barn, d):
                        feed_ok = check_feed_available(d, barn["animal_type"])
                        if feed_ok:
                            self.barn_canvas.create_text(cx, y1 - 4, text="🔄生产", font=ft2, fill="#333", anchor="s")
                        else:
                            self.barn_canvas.create_text(cx, y1 - 4, text="❌缺料", font=ft2, fill="#c0392b", anchor="s")
                    else:
                        fed = barn.get("fed_time")
                        if fed is None:
                            self.barn_canvas.create_text(cx, y1 - 4, text="未投喂", font=ft2, fill="#c0392b", anchor="s")
                        else:
                            fed_dt = parse_dt(fed)
                            elapsed_since_feed = (now - fed_dt).total_seconds() / 60.0
                            last = barn.get("last_produce_time")

                            if last is None:
                                remain = 10.0 - elapsed_since_feed
                            else:
                                speed_bonus = get_talent_value(d["talent_tree"], "animal_speed")
                                barn_speed = 0.0
                                for lv2 in range(2, barn.get("level", 1) + 1):
                                    eff = barn_upgrade_effects(lv2)
                                    if "speed" in eff:
                                        barn_speed += eff["speed"]
                                if barn.get("level", 1) >= 10:
                                    barn_speed += 0.10
                                total_speed = speed_bonus + barn_speed
                                cycle = a["cycle"] * max(0.1, 1.0 - total_speed)
                                last_dt = parse_dt(last)
                                remain = cycle - (now - last_dt).total_seconds() / 60.0

                            if remain <= 0:
                                self.barn_canvas.create_text(cx, y1 - 4, text=f"{stage_emoji}即将产出", font=ft2, fill="#333", anchor="s")
                            else:
                                m, sec = int(remain), int((remain - int(remain)) * 60)
                                self.barn_canvas.create_text(cx, y1 - 4, text=f"{m}:{sec:02d}", font=ft2, fill="#333", anchor="s")

    def _update_barn_status(self):
        """更新养殖场状态信息"""
        d = self.data
        unlocked_barns = d.get("unlocked_barns", INITIAL_BARNS)
        occupied = sum(1 for b in d.get("barns", [])[:unlocked_barns] if b["animal"] is not None)
        pending = sum(b.get("pending_product", 0) for b in d.get("barns", [])[:unlocked_barns])
        feed_inv = d.get("feed_inventory", {})
        feed_total = sum(feed_inv.values())

        self.barn_status_labels["usage"].config(text=f"🐔 栏位: {occupied}/{unlocked_barns}")
        self.barn_status_labels["pending"].config(text=f"📦 待收: {pending}")
        self.barn_status_labels["feed"].config(text=f"🍽️ 饲料: {feed_total}")

        # 饲料详情
        parts = [f"{k}:{v}" for k, v in feed_inv.items() if v > 0]
        self.feed_info_label.config(text=f"🍽️ 饲料库存: {' | '.join(parts) if parts else '空'}")

    # ==================== 日志 ====================

    def _log(self, msg):
        """向事件日志追加消息"""
        try:
            self.log_text.config(state="normal")
            ts = datetime.datetime.now().strftime("%H:%M:%S")
            self.log_text.insert("end", f"[{ts}] {msg}\n")
            self.log_text.see("end")
            lines = int(self.log_text.index("end-1c").split(".")[0])
            if lines > 200:
                self.log_text.delete("1.0", f"{lines - 100}.0")
            self.log_text.config(state="disabled")
        except Exception:
            pass

    # ==================== 土地操作 ====================

    def _check_golden_pumpkin_transformation(self):
        """南瓜首次成熟时1%概率变金色南瓜，一生仅一次"""
        d = self.data
        now = now_dt()
        triggered = False
        for land in d["lands"][:d["unlocked_lands"]]:
            if land.get("crop") != "南瓜":
                continue
            # 已判定过（变金或不变），不再处理
            if land.get("_maturity_roll_done"):
                continue
            if land.get("golden_pumpkin"):
                land["_maturity_roll_done"] = True
                continue
            if not land.get("plant_time"):
                continue
            pt = parse_dt(land["plant_time"])
            growth = calc_growth_time("南瓜", land["upgrade_level"], d["talent_tree"])
            if (now - pt).total_seconds() / 60.0 < growth:
                continue  # 还没成熟
            # 首次成熟，一生一次的1%判定
            land["_maturity_roll_done"] = True
            if random.random() < 0.01:
                land["golden_pumpkin"] = True
                land["plant_time"] = now_str()  # 重置生长计时器，再长一个周期
                self._log("🌟 彩蛋！一块南瓜田变成了金色南瓜！再等一个生长周期即可收获！")
                triggered = True
        return triggered

    def _on_land_click(self, event):
        """点击 Canvas 土地网格（含升级、收获、种植），升级不关闭弹窗"""
        cw = self.land_canvas.winfo_width()
        ch = self.land_canvas.winfo_height()
        col = int(event.x / cw * 10)
        row = int(event.y / ch * 5)
        lid = row * 10 + col + 1
        if lid > len(self.data["lands"]) or lid > self.data["unlocked_lands"]:
            return
        land = self.data["lands"][lid - 1]
        d = self.data
        is_golden = land.get("golden_pumpkin", False)

        dialog = tk.Toplevel(self.root)
        dialog.title(f"土地 #{lid}")
        dialog.geometry("300x260")
        dialog.transient(self.root)
        dialog.grab_set()
        dialog.configure(bg=COLORS["bg"])

        info_text = tk.StringVar()
        info_label = tk.Label(dialog, textvariable=info_text, font=F["normal"],
                              bg=COLORS["bg"], justify="left")
        info_label.pack(pady=(12, 2), padx=12)

        btn_frame = tk.Frame(dialog, bg=COLORS["bg"])
        btn_frame.pack(pady=(5, 12))

        def refresh_info():
            lv = land.get("upgrade_level", 1)
            crop_name = "金色南瓜🌟" if is_golden else (land["crop"] or "空闲")
            cost = land_upgrade_cost(lv) if lv < 10 else None
            lines = [f"土地 #{lid}  Lv.{lv}", f"作物: {crop_name}"]
            if cost:
                ok = "✅" if d["gold"] >= cost else "❌"
                lines.append(f"升级: {cost}💰 {ok}")
            else:
                lines.append("已满级 ✅")
            if land["crop"]:
                pt = parse_dt(land["plant_time"])
                growth = calc_growth_time(land["crop"], land["upgrade_level"], d["talent_tree"])
                if is_golden:
                    growth *= 2
                remain = growth - (now_dt() - pt).total_seconds() / 60.0
                if remain > 0:
                    m, sec = int(remain), int((remain - int(remain)) * 60)
                    lines.append(f"剩余: {m}分{sec}秒")
            info_text.set("\n".join(lines))
            return lv

        def do_upgrade():
            lv = land.get("upgrade_level", 1)
            if lv >= 10:
                messagebox.showinfo("提示", "已满级！")
                return
            cost = land_upgrade_cost(lv)
            if not cost or d["gold"] < cost:
                messagebox.showwarning("金币不足", f"需要 {cost}💰")
                return
            d["gold"] -= cost
            land["upgrade_level"] += 1
            self._log(f"⬆️ 土地 #{lid} 升级到 Lv.{land['upgrade_level']}")
            new_lv = refresh_info()
            if new_lv >= 10:
                upgrade_btn.config(text="已满级", state="disabled")
            self._update_ui()

        first_lv = refresh_info()

        if land["crop"]:
            pt = parse_dt(land["plant_time"])
            growth = calc_growth_time(land["crop"], land["upgrade_level"], d["talent_tree"])
            if is_golden:
                growth *= 2
            remain = growth - (now_dt() - pt).total_seconds() / 60.0
            if remain <= 0:
                icon = "🌟" if is_golden else "🌾"
                tk.Button(btn_frame, text=f"{icon} 收获", font=F["button"],
                          command=lambda: [self._harvest_single(lid), dialog.destroy()],
                          bg="#d4edda", width=12).pack(pady=2)
        else:
            tk.Button(btn_frame, text="🌱 种植", font=F["button"],
                      command=lambda: [self._show_plant_dialog(lid), dialog.destroy()],
                      bg=COLORS["btn_bg"], width=12).pack(pady=2)

        upgrade_btn = tk.Button(btn_frame, text="⬆️ 升级", font=F["button"],
                                command=do_upgrade, bg=COLORS["btn_bg"], width=12)
        if first_lv >= 10:
            upgrade_btn.config(text="已满级", state="disabled")
        upgrade_btn.pack(pady=2)

        tk.Button(btn_frame, text="❌ 关闭", font=F["button"],
                  command=dialog.destroy, bg=COLORS["btn_bg"], width=12).pack(pady=2)

    def _harvest_single(self, lid):
        """收获单块土地（含金色南瓜彩蛋）"""
        land = self.data["lands"][lid - 1]
        if not land["crop"]:
            return
        is_golden = land.get("golden_pumpkin", False)
        crop_name = "金色南瓜" if is_golden else land["crop"]

        if is_golden:
            # 金色南瓜：10倍售价，固定1个，不享受季节加成/双倍
            c = self.crops.get("南瓜")
            if not c:
                return
            qty = 1
            self.data["inventory"]["crops"]["金色南瓜"] = self.data["inventory"]["crops"].get("金色南瓜", 0) + 1
            self.data["exp"] += c["exp"] * 2
            self.data["total_harvests"] += 1
            try_level_up(self.data)
            self._log("🌟 收获金色南瓜！价值 10 倍！")
        else:
            c = self.crops.get(land["crop"])
            if not c:
                return
            season, _ = get_season(self.data)
            ym = calc_yield_multiplier(land["upgrade_level"], self.data["talent_tree"],
                                       land["crop"], season)
            qty = max(1, int(ym))
            dc = get_double_chance(land["upgrade_level"], self.data["talent_tree"])
            if random.random() < dc:
                qty *= 2

            inv = self.data["inventory"]["crops"]
            inv[land["crop"]] = inv.get(land["crop"], 0) + qty
            self.data["exp"] += c["exp"]
            self.data["total_harvests"] += 1
            try_level_up(self.data)
            self._log(f"🌾 收获第 {lid} 号土地 {land['crop']}×{qty}，获得 {c['exp']}✨")

        land["crop"] = None
        land["plant_time"] = None
        land["golden_pumpkin"] = False
        self._update_ui()

    def _show_plant_dialog(self, lid=None):
        """种植对话框"""
        d = self.data
        avail = [(n, c) for n, c in self.crops.items() if d["level"] >= c["level"]]
        if not avail:
            messagebox.showinfo("提示", f"等级 {d['level']} 无法种植任何作物")
            return

        dialog = tk.Toplevel(self.root)
        dialog.title("🌱 种植")
        dialog.geometry("450x450")
        dialog.resizable(False, False)
        dialog.transient(self.root)
        dialog.grab_set()

        tk.Label(dialog, text=f"选择作物  金币: {d['gold']:,}  等级: {d['level']}",
                 font=F["bold"]).pack(pady=(10, 5))

        frame = tk.Frame(dialog)
        frame.pack(fill="both", expand=True, padx=10, pady=5)

        canvas = tk.Canvas(frame, highlightthickness=0)
        scrollbar = tk.Scrollbar(frame, orient="vertical", command=canvas.yview)
        scroll_frame = tk.Frame(canvas)

        scroll_frame.bind("<Configure>", lambda e: canvas.configure(scrollregion=canvas.bbox("all")))
        canvas.create_window((0, 0), window=scroll_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)

        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")

        # 购买种子按钮
        buy_btn = tk.Button(dialog, text="🛒 购买种子", font=F["button"],
                            command=lambda: self._show_buy_seeds_dialog(dialog),
                            bg=COLORS["btn_bg"])
        buy_btn.pack(pady=(0, 10))

        inv = d["inventory"]["seeds"]

        def do_plant_crop(name):
            if inv.get(name, 0) <= 0:
                messagebox.showwarning("种子不足", f"{name} 种子不足，请先购买")
                return
            lands_to_plant = []
            if lid is not None:
                lands_to_plant = [lid]
            else:
                free = [l["id"] for l in d["lands"][:d["unlocked_lands"]] if not l["crop"]]
                if not free:
                    messagebox.showinfo("提示", "没有空闲土地")
                    return
                if len(free) == 1:
                    lands_to_plant = [free[0]]
                elif inv.get(name, 0) >= len(free):
                    if messagebox.askyesno("批量种植", f"空闲 {len(free)} 块土地，全部种上 {name} 吗？"):
                        lands_to_plant = free
                    else:
                        lands_to_plant = [free[0]]
                else:
                    lands_to_plant = [free[0]]
                    self._log(f"⚠️ 种子不足（{inv.get(name,0)}），只种 1 块")

            planted = 0
            for plot_id in lands_to_plant:
                if inv.get(name, 0) <= 0:
                    break
                plot = d["lands"][plot_id - 1]
                if plot["crop"]:
                    continue
                inv[name] -= 1
                plot["crop"] = name
                plot["plant_time"] = now_str()
                plot["golden_pumpkin"] = False
                plot["_maturity_roll_done"] = False
                planted += 1

            dialog.destroy()
            if planted > 0:
                self._log(f"✅ 在 {planted} 块土地上种下 {name}")
                self._update_ui()

        for i, (n, c) in enumerate(avail, 1):
            has = inv.get(n, 0)
            season, _ = get_season(d)
            bonus = season_crop_bonus(n, season)
            bstr = f" x{bonus:.1f}" if bonus != 1.0 else ""
            status = "✅" if has > 0 else "❌"
            text = f"{i}. {n}  Lv.{c['level']}  ⏱{c['growth_minutes']}min  💰{c['sell_price']}  📦{has}{bstr}  {status}"
            btn = tk.Button(scroll_frame, text=text, font=F["small"],
                            anchor="w", padx=5,
                            command=lambda x=n: do_plant_crop(x),
                            bg="#fff", relief="groove", bd=1)
            btn.pack(fill="x", padx=5, pady=2)

        dialog.wait_window()

    def _show_buy_seeds_dialog(self, parent):
        """购买种子对话框"""
        d = self.data
        avail = [(n, c) for n, c in self.crops.items() if d["level"] >= c["level"]]
        if not avail:
            messagebox.showinfo("提示", "没有可购买的种子")
            return

        dialog = tk.Toplevel(parent)
        dialog.title("🛒 购买种子")
        dialog.geometry("400x400")
        dialog.transient(parent)
        dialog.grab_set()

        tk.Label(dialog, text=f"金币: {d['gold']:,}", font=F["bold"]).pack(pady=10)

        frame = tk.Frame(dialog)
        frame.pack(fill="both", expand=True, padx=10)

        canvas = tk.Canvas(frame, highlightthickness=0)
        scrollbar = tk.Scrollbar(frame, orient="vertical", command=canvas.yview)
        scroll_frame = tk.Frame(canvas)
        scroll_frame.bind("<Configure>", lambda e: canvas.configure(scrollregion=canvas.bbox("all")))
        canvas.create_window((0, 0), window=scroll_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)
        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")

        def buy(name, price):
            qty = self._quantity_dialog(f"购买 {name}", parent=dialog)
            if not qty:
                return
            cost = price * qty
            if d["gold"] < cost:
                messagebox.showwarning("金币不足", f"需要 {cost}💰，当前 {d['gold']}💰")
                return
            d["gold"] -= cost
            inv = d["inventory"]["seeds"]
            inv[name] = inv.get(name, 0) + qty
            self._log(f"🛒 购买 {name}种子×{qty}，花费 {cost}💰")
            dialog.destroy()

        for i, (n, c) in enumerate(avail, 1):
            discount = get_talent_value(d["talent_tree"], "seed_discount")
            price = int(c["seed_price"] * (1.0 - discount))
            can = d["gold"] >= price
            text = f"{i}. {n}  {price}💰 (原{c['seed_price']})  {'✅' if can else '❌'}"
            btn = tk.Button(scroll_frame, text=text, font=F["small"],
                            anchor="w", padx=5,
                            command=lambda x=n, p=price: buy(x, p),
                            bg="#fff", relief="groove", bd=1,
                            state="normal" if can else "disabled")
            btn.pack(fill="x", padx=5, pady=2)

    def _quantity_dialog(self, title, min_v=1, max_v=999, parent=None):
        """带 +/- 按钮的数量选择对话框"""
        win = tk.Toplevel(parent or self.root)
        win.title(title)
        win.geometry("340x130")
        win.resizable(False, False)
        win.transient(parent or self.root)
        win.grab_set()

        result = [None]
        tk.Label(win, text="选择数量:", font=F["bold"]).pack(pady=(12, 5))

        frame = tk.Frame(win)
        frame.pack()

        qty_var = tk.IntVar(value=1)

        def sub():
            v = qty_var.get()
            if v > min_v:
                qty_var.set(v - 1)

        def add():
            v = qty_var.get()
            if v < max_v:
                qty_var.set(v + 1)

        def sub5():
            v = qty_var.get()
            qty_var.set(max(min_v, v - 5))

        def add5():
            v = qty_var.get()
            qty_var.set(min(max_v, v + 5))

        tk.Button(frame, text="-5", font=F["button"], width=3,
                  command=sub5, bg="#f0f0f0").pack(side="left", padx=2)
        tk.Button(frame, text="-", font=F["button"], width=3,
                  command=sub, bg="#f0f0f0").pack(side="left", padx=2)
        tk.Label(frame, textvariable=qty_var, font=("TkDefaultFont", 16, "bold"),
                 width=5, anchor="center").pack(side="left", padx=8)
        tk.Button(frame, text="+", font=F["button"], width=3,
                  command=add, bg="#f0f0f0").pack(side="left", padx=2)
        tk.Button(frame, text="+5", font=F["button"], width=3,
                  command=add5, bg="#f0f0f0").pack(side="left", padx=2)

        btn_frame = tk.Frame(win)
        btn_frame.pack(pady=(10, 0))

        def confirm():
            result[0] = qty_var.get()
            win.destroy()

        tk.Button(btn_frame, text="✅ 确定", font=F["button"],
                  command=confirm, bg="#d4edda", width=8).pack(side="left", padx=5)
        tk.Button(btn_frame, text="❌ 取消", font=F["button"],
                  command=win.destroy, bg="#f8d7da", width=8).pack(side="left", padx=5)

        def on_key(e):
            if e.keysym in ("Left", "Down"):
                sub()
            elif e.keysym in ("Right", "Up"):
                add()
            elif e.keysym == "Return":
                confirm()
            elif e.keysym == "Escape":
                win.destroy()

        win.bind("<Key>", on_key)
        win.wait_window()
        return result[0]

    # ==================== 操作按钮（土地） ====================

    def _on_plant(self):
        self._show_plant_dialog()

    def _on_harvest(self):
        d = self.data
        now = now_dt()
        season, _ = get_season(d)
        count = 0
        total_qty = 0
        total_exp = 0

        for land in d["lands"][:d["unlocked_lands"]]:
            if not land["crop"] or not land["plant_time"]:
                continue
            # 金色南瓜只能手动收获，一键收获跳过
            if land.get("golden_pumpkin"):
                continue
            c = self.crops.get(land["crop"])
            if not c:
                continue
            pt = parse_dt(land["plant_time"])
            growth = calc_growth_time(land["crop"], land["upgrade_level"], d["talent_tree"])
            if (now - pt).total_seconds() / 60.0 < growth:
                continue

            ym = calc_yield_multiplier(land["upgrade_level"], d["talent_tree"],
                                       land["crop"], season)
            qty = max(1, int(ym))
            dc = get_double_chance(land["upgrade_level"], d["talent_tree"])
            if random.random() < dc:
                qty *= 2
            if d.get("event_active", {}).get("golden_hour"):
                qty *= 2

            inv = d["inventory"]["crops"]
            inv[land["crop"]] = inv.get(land["crop"], 0) + qty
            total_qty += qty
            total_exp += c["exp"]
            count += 1
            land["crop"] = None
            land["plant_time"] = None

        if count == 0:
            self._log("🌾 没有可收获的作物")
        else:
            d["exp"] += int(total_exp)
            d["total_harvests"] += count
            try_level_up(d)
            self._log(f"🌾 收获 {count} 块地，获得 {total_qty} 件作物，{int(total_exp)}✨")
            if inventory_space(d) < 0:
                self._log("⚠️ 仓库空间不足！")
        self._update_ui()

    def _on_shop(self):
        """商店（种子 + 动物）"""
        d = self.data
        dialog = tk.Toplevel(self.root)
        dialog.title("🏪 商店")
        dialog.geometry("520x480")
        dialog.transient(self.root)
        dialog.grab_set()

        tk.Label(dialog, text=f"🏪 商店  金币: {d['gold']:,}  等级: {d['level']}",
                 font=F["bold"]).pack(pady=(10, 5))

        notebook = ttk.Notebook(dialog)
        notebook.pack(fill="both", expand=True, padx=10, pady=5)

        # ---- 种子标签页 ----
        seed_frame = tk.Frame(notebook, bg=COLORS["bg"])
        notebook.add(seed_frame, text="🌱 种子")

        merchant_disc = get_merchant_discount(d)
        if merchant_disc > 0:
            disc_frame = tk.Frame(seed_frame, bg="#fff3cd")
            disc_frame.pack(fill="x", padx=5, pady=3)
            tk.Label(disc_frame, text="🧑‍🌾 神秘商人光临！种子8折优惠中（5分钟）",
                     font=F["bold"], bg="#fff3cd", fg="#856404").pack(pady=2)

        seed_canvas = tk.Canvas(seed_frame, bg=COLORS["bg"], highlightthickness=0)
        seed_scroll = tk.Scrollbar(seed_frame, orient="vertical", command=seed_canvas.yview)
        seed_inner = tk.Frame(seed_canvas, bg=COLORS["bg"])
        seed_inner.bind("<Configure>", lambda e: seed_canvas.configure(scrollregion=seed_canvas.bbox("all")))
        seed_canvas.create_window((0, 0), window=seed_inner, anchor="nw")
        seed_canvas.configure(yscrollcommand=seed_scroll.set)
        seed_canvas.pack(side="left", fill="both", expand=True)
        seed_scroll.pack(side="right", fill="y")

        for i, (n, c) in enumerate(self.crops.items(), 1):
            unlocked = d["level"] >= c["level"]
            if unlocked:
                discount = get_talent_value(d["talent_tree"], "seed_discount") + merchant_disc
                price = int(c["seed_price"] * (1.0 - discount))
                can = d["gold"] >= price
                disc_tag = "🔥" if merchant_disc > 0 else ""
                text = f"{disc_tag}{i}. {n}  {price}💰(原{c['seed_price']})  Lv.{c['level']}  "
                text += f"生长{c['growth_minutes']}min  售{c['sell_price']}💰  {'✅' if can else '❌'}"

                def buy_seed(name=n, p=price):
                    qty = self._quantity_dialog(f"购买 {name}", parent=dialog)
                    if not qty:
                        return
                    cost = p * qty
                    if d["gold"] < cost:
                        messagebox.showwarning("金币不足", f"需要 {cost}💰")
                        return
                    d["gold"] -= cost
                    d["inventory"]["seeds"][name] = d["inventory"]["seeds"].get(name, 0) + qty
                    self._log(f"🛒 购买 {name}种子×{qty}，花费 {cost}💰")
                    dialog.destroy()
                    self._update_ui()

                btn = tk.Button(seed_inner, text=text, font=F["small"],
                                anchor="w", padx=5,
                                command=buy_seed if can else None,
                                bg="#fff" if can else "#eee",
                                state="normal" if can else "disabled",
                                relief="groove", bd=1)
            else:
                text = f"🔒 {i}. {n}  需Lv.{c['level']}  生长{c['growth_minutes']}min  售{c['sell_price']}💰"
                btn = tk.Button(seed_inner, text=text, font=F["small"],
                                anchor="w", padx=5, state="disabled",
                                bg="#f0f0f0", relief="groove", bd=1)
            btn.pack(fill="x", padx=5, pady=2)

        # ---- 动物标签页 ----
        animal_frame = tk.Frame(notebook, bg=COLORS["bg"])
        notebook.add(animal_frame, text="🐔 动物")

        animal_canvas = tk.Canvas(animal_frame, bg=COLORS["bg"], highlightthickness=0)
        animal_scroll = tk.Scrollbar(animal_frame, orient="vertical", command=animal_canvas.yview)
        animal_inner = tk.Frame(animal_canvas, bg=COLORS["bg"])
        animal_inner.bind("<Configure>", lambda e: animal_canvas.configure(scrollregion=animal_canvas.bbox("all")))
        animal_canvas.create_window((0, 0), window=animal_inner, anchor="nw")
        animal_canvas.configure(yscrollcommand=animal_scroll.set)
        animal_canvas.pack(side="left", fill="both", expand=True)
        animal_scroll.pack(side="right", fill="y")

        for i, a in enumerate(BARN_ANIMALS_LIST, 1):
            unlocked = d["level"] >= a["level"]
            discount = 1.0 - get_talent_value(d["talent_tree"], "animal_discount")
            price = int(a["price"] * discount)
            can = unlocked and d["gold"] >= price
            feed_desc = "+".join(f"{k}×{v}" for k, v in a["feed"].items())
            if not unlocked:
                text = f"🔒 {i}. {a['name']}  需Lv.{a['level']}  {a['price']}💰  →{a['product']}({a['sell_price']}💰)"
                btn = tk.Button(animal_inner, text=text, font=F["small"],
                                anchor="w", padx=5, state="disabled",
                                bg="#eee", relief="groove", bd=1)
            else:
                text = f"{i}. {a['name']}  {price}💰(原{a['price']})  →{a['product']}({a['sell_price']}💰)"
                text += f"  饲料:{feed_desc}  {'✅' if can else '❌'}"

                def buy_animal(name=a["name"]):
                    # 找空闲栏位
                    ub = d.get("unlocked_barns", INITIAL_BARNS)
                    free_idx = None
                    for bi, barn in enumerate(d["barns"][:ub]):
                        if barn["animal"] is None and barn.get("unlocked", False):
                            free_idx = bi
                            break
                    if free_idx is None:
                        messagebox.showwarning("无空栏位", "没有空闲的养殖栏位！")
                        return
                    ad = get_barn_animal(name)
                    if ad is None:
                        return
                    discount2 = 1.0 - get_talent_value(d["talent_tree"], "animal_discount")
                    cost = int(ad["price"] * discount2)
                    if d["gold"] < cost:
                        messagebox.showwarning("金币不足", f"需要 {cost}💰")
                        return
                    d["gold"] -= cost
                    barn = d["barns"][free_idx]
                    barn["animal"] = name
                    barn["animal_type"] = name
                    barn["purchase_time"] = now_str()
                    barn["age_stage"] = "juvenile"
                    barn["production_count"] = 0
                    barn["last_produce_time"] = None
                    barn["pending_product"] = 0
                    barn["breed_cooldown"] = None
                    self._log(f"✅ 在栏位 {free_idx+1} 放入 {name}，花费 {cost}💰")
                    dialog.destroy()
                    self._update_ui()

                btn = tk.Button(animal_inner, text=text, font=F["small"],
                                anchor="w", padx=5,
                                command=buy_animal if can else None,
                                bg="#fff" if can else "#f0f0f0",
                                state="normal" if can else "disabled",
                                relief="groove", bd=1)
            btn.pack(fill="x", padx=5, pady=2)

        dialog.wait_window()

    def _on_factories(self):
        """加工系统"""
        d = self.data
        dialog = tk.Toplevel(self.root)
        dialog.title("🏭 加工")
        dialog.geometry("550x450")
        dialog.transient(self.root)
        dialog.grab_set()

        tk.Label(dialog, text=f"🏭 工厂加工  金币: {d['gold']:,}",
                 font=F["bold"]).pack(pady=(10, 5))

        frame = tk.Frame(dialog)
        frame.pack(fill="both", expand=True, padx=10)

        canvas = tk.Canvas(frame, highlightthickness=0)
        scrollbar = tk.Scrollbar(frame, orient="vertical", command=canvas.yview)
        scroll_frame = tk.Frame(canvas)
        scroll_frame.bind("<Configure>", lambda e: canvas.configure(scrollregion=canvas.bbox("all")))
        canvas.create_window((0, 0), window=scroll_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)
        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")

        for f in FACTORY_LIST:
            fc = d["factories"][f["factory"]]
            unlocked = d["level"] >= f["level"]
            if not unlocked:
                text = f"🔒 {f['factory']}  →  {f['product']}  需Lv.{f['level']}"
                btn = tk.Button(scroll_frame, text=text, font=F["small"],
                                anchor="w", padx=5, state="disabled",
                                bg="#eee", relief="groove", bd=1)
                btn.pack(fill="x", padx=5, pady=2)
                continue

            inv = d["inventory"]
            save_lv = get_talent_value(d["talent_tree"], "save_materials")

            if fc.get("ready"):
                text = f"✅ {f['factory']}  →  {f['product']}  可收取!"
                btn = tk.Button(scroll_frame, text=text, font=F["small"],
                                anchor="w", padx=5,
                                bg="#d4edda", relief="groove", bd=1)

                def collect_factory(fc_=fc, f_=f):
                    qty = 1
                    dp = get_talent_value(d["talent_tree"], "double_process")
                    if random.random() < dp:
                        qty = 2
                    prod_inv = inv["products"]
                    prod_inv[f_["product"]] = prod_inv.get(f_["product"], 0) + qty
                    fc_["current_order"] = None
                    fc_["start_time"] = None
                    fc_["ready"] = False
                    d["total_processed"] = d.get("total_processed", 0) + 1
                    self._log(f"✅ 收取 {f_['product']}×{qty}")
                    dialog.destroy()
                    self._update_ui()

                btn.config(command=collect_factory)
                btn.pack(fill="x", padx=5, pady=2)
                continue

            if fc["current_order"]:
                st = parse_dt(fc["start_time"])
                pt = f["time"] * (1.0 - get_talent_value(d["talent_tree"], "process_speed"))
                remain = max(0, pt - (now_dt() - st).total_seconds() / 60.0)
                text = f"⏳ {f['factory']}  →  {f['product']}  剩余 {remain:.0f}min"
                btn = tk.Button(scroll_frame, text=text, font=F["small"],
                                anchor="w", padx=5,
                                bg="#fff3cd", relief="groove", bd=1, state="disabled")
                btn.pack(fill="x", padx=5, pady=2)
                continue

            ings = []
            can_make = True
            for ing_name, ing_qty in f["ingredients"].items():
                need = max(1, ing_qty - save_lv)
                have = inv["crops"].get(ing_name, 0) + inv["products"].get(ing_name, 0)
                ings.append(f"{ing_name}×{need}(有{have})")
                if have < need:
                    can_make = False

            ings_str = "+".join(ings)
            text = f"⬜ {f['factory']}  →  {f['product']}  [{ings_str}]  💰{f['sell_price']}  ⏱{f['time']}min"
            btn = tk.Button(scroll_frame, text=text, font=F["small"],
                            anchor="w", padx=5,
                            bg="#fff" if can_make else "#f0f0f0",
                            relief="groove", bd=1)

            def start_factory(f_=f, fc_=fc):
                save_lv2 = get_talent_value(d["talent_tree"], "save_materials")
                for ing_name, ing_qty in f_["ingredients"].items():
                    need = max(1, ing_qty - save_lv2)
                    c_have = inv["crops"].get(ing_name, 0)
                    if c_have >= need:
                        inv["crops"][ing_name] = c_have - need
                    else:
                        if c_have > 0:
                            inv["crops"][ing_name] = 0
                            need -= c_have
                        inv["products"][ing_name] = inv["products"].get(ing_name, 0) - need
                fc_["current_order"] = f_["product"]
                fc_["start_time"] = now_str()
                fc_["ready"] = False
                self._log(f"🏭 开始加工 {f_['product']}，{f_['time']}分钟后完成")
                dialog.destroy()
                self._update_ui()

            if can_make:
                btn.config(command=start_factory)
            else:
                btn.config(state="disabled")
            btn.pack(fill="x", padx=5, pady=2)

        dialog.wait_window()

    def _on_warehouse(self):
        """仓库（含种子半价回收）"""
        d = self.data
        dialog = tk.Toplevel(self.root)
        dialog.title("📦 仓库")
        dialog.geometry("500x400")
        dialog.transient(self.root)
        dialog.grab_set()

        usage = inventory_usage(d)
        tk.Label(dialog, text=f"📦 仓库 ({usage}/{WAREHOUSE_CAPACITY})  金币: {d['gold']:,}",
                 font=F["bold"]).pack(pady=(10, 5))

        frame = tk.Frame(dialog)
        frame.pack(fill="both", expand=True, padx=10)

        canvas = tk.Canvas(frame, highlightthickness=0)
        scrollbar = tk.Scrollbar(frame, orient="vertical", command=canvas.yview)
        scroll_frame = tk.Frame(canvas)
        scroll_frame.bind("<Configure>", lambda e: canvas.configure(scrollregion=canvas.bbox("all")))
        canvas.create_window((0, 0), window=scroll_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)
        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")

        def sell_all_crops():
            total_gold = 0
            total_qty = 0
            inv = d["inventory"]["crops"]
            for name, qty in list(inv.items()):
                if name == "金色南瓜":
                    price = int(12000 * (1.0 + get_talent_value(d["talent_tree"], "sell_bonus")))
                else:
                    c = self.crops.get(name, {})
                    price = int(c.get("sell_price", 0) * (1.0 + get_talent_value(d["talent_tree"], "sell_bonus")))
                if d.get("event_active", {}).get("harvest_festival"):
                    price *= 2
                total_gold += qty * price
                total_qty += qty
                del inv[name]
            if total_qty > 0:
                d["gold"] += total_gold
                d["total_earnings"] += total_gold
                self._log(f"💰 出售所有作物，共 {total_qty} 件，获得 {total_gold}💰")
            else:
                self._log("📦 没有作物可出售")
            dialog.destroy()
            self._update_ui()

        def _get_product_price(name):
            """从工厂或动物配置查询产品售价"""
            pf = next((x for x in FACTORY_LIST if x["product"] == name), None)
            if pf:
                return pf["sell_price"]
            an = next((a for a in BARN_ANIMALS_LIST if a["product"] == name), None)
            if an:
                return an["sell_price"]
            return 0

        def sell_all_products():
            total_gold = 0
            total_qty = 0
            inv = d["inventory"]["products"]
            for name, qty in list(inv.items()):
                base_price = _get_product_price(name)
                if base_price <= 0:
                    continue
                price = int(base_price * (1.0 + get_talent_value(d["talent_tree"], "sell_bonus")))
                if d.get("event_active", {}).get("harvest_festival"):
                    price *= 2
                total_gold += qty * price
                total_qty += qty
                del inv[name]
            if total_qty > 0:
                d["gold"] += total_gold
                d["total_earnings"] += total_gold
                self._log(f"💰 出售所有产品，共 {total_qty} 件，获得 {total_gold}💰")
            else:
                self._log("📦 没有产品可出售")
            dialog.destroy()
            self._update_ui()

        def sell_all_seeds():
            total_gold = 0
            total_qty = 0
            inv = d["inventory"]["seeds"]
            for name, qty in list(inv.items()):
                c = self.crops.get(name, {})
                price = int(c.get("seed_price", 0) * 0.5)
                total_gold += qty * price
                total_qty += qty
                del inv[name]
            if total_qty > 0:
                d["gold"] += total_gold
                d["total_earnings"] += total_gold
                self._log(f"💰 出售所有种子，共 {total_qty} 件，获得 {total_gold}💰")
            else:
                self._log("📦 没有种子可出售")
            dialog.destroy()
            self._update_ui()

        btn_frame = tk.Frame(dialog)
        btn_frame.pack(fill="x", padx=10, pady=5)
        tk.Button(btn_frame, text="🌾 出售所有作物", font=F["button"],
                  command=sell_all_crops, bg="#d4edda").pack(side="left", padx=5)
        tk.Button(btn_frame, text="📦 出售所有加工品", font=F["button"],
                  command=sell_all_products, bg="#cce5ff").pack(side="left", padx=5)
        tk.Button(btn_frame, text="🌱 出售所有种子", font=F["button"],
                  command=sell_all_seeds, bg="#fff3cd").pack(side="left", padx=5)

        # 种子列表（半价回收）
        if d["inventory"]["seeds"]:
            tk.Label(scroll_frame, text="── 种子库存（半价回收）──", font=F["bold"],
                     bg=COLORS["bg"]).pack(fill="x", pady=(5, 0))
            for name, qty in sorted(d["inventory"]["seeds"].items()):
                if qty <= 0:
                    continue
                c = self.crops.get(name, {})
                price = int(c.get("seed_price", 0) * 0.5)
                text = f"{name}  ×{qty}  →  {price}💰/个  =  {qty * price}💰"

                def sell_seed_slider(n=name, p=price):
                    self._sell_with_slider("出售种子", "seeds", n, p,
                                           d["inventory"]["seeds"].get(n, 0), dialog)

                btn = tk.Button(scroll_frame, text=text, font=F["small"],
                                anchor="w", padx=5, bg="#fff",
                                relief="groove", bd=1, command=sell_seed_slider)
                btn.pack(fill="x", padx=5, pady=2)

        # 作物列表
        if d["inventory"]["crops"]:
            tk.Label(scroll_frame, text="── 作物库存 ──", font=F["bold"],
                     bg=COLORS["bg"]).pack(fill="x", pady=(5, 0))
            for name, qty in sorted(d["inventory"]["crops"].items()):
                if qty <= 0:
                    continue
                if name == "金色南瓜":
                    price = int(12000 * (1.0 + get_talent_value(d["talent_tree"], "sell_bonus")))
                else:
                    c = self.crops.get(name, {})
                    price = int(c.get("sell_price", 0) * (1.0 + get_talent_value(d["talent_tree"], "sell_bonus")))
                if d.get("event_active", {}).get("harvest_festival"):
                    price *= 2
                text = f"{name}  ×{qty}  →  {price}💰/个  =  {qty * price}💰"

                def sell_crop_slider(n=name, p=price):
                    self._sell_with_slider("出售作物", "crops", n, p,
                                           d["inventory"]["crops"].get(n, 0), dialog)

                btn = tk.Button(scroll_frame, text=text, font=F["small"],
                                anchor="w", padx=5, bg="#fff",
                                relief="groove", bd=1, command=sell_crop_slider)
                btn.pack(fill="x", padx=5, pady=2)

        # 加工品/动物产品列表
        if d["inventory"]["products"]:
            tk.Label(scroll_frame, text="── 产品库存 ──", font=F["bold"],
                     bg=COLORS["bg"]).pack(fill="x", pady=(5, 0))
            for name, qty in sorted(d["inventory"]["products"].items()):
                if qty <= 0:
                    continue
                base_price = _get_product_price(name)
                if base_price <= 0:
                    continue
                price = int(base_price * (1.0 + get_talent_value(d["talent_tree"], "sell_bonus")))
                if d.get("event_active", {}).get("harvest_festival"):
                    price *= 2
                text = f"{name}  ×{qty}  →  {price}💰/个  =  {qty * price}💰"

                def sell_product_slider(n=name, p=price):
                    self._sell_with_slider("出售产品", "products", n, p,
                                           d["inventory"]["products"].get(n, 0), dialog)

                btn = tk.Button(scroll_frame, text=text, font=F["small"],
                                anchor="w", padx=5, bg="#fff",
                                relief="groove", bd=1, command=sell_product_slider)
                btn.pack(fill="x", padx=5, pady=2)

        dialog.wait_window()

    def _on_upgrade_land(self):
        """升级土地"""
        d = self.data
        dialog = tk.Toplevel(self.root)
        dialog.title("⬆️ 升级土地")
        dialog.geometry("550x400")
        dialog.transient(self.root)
        dialog.grab_set()

        tk.Label(dialog, text=f"⬆️ 土地升级  金币: {d['gold']:,}",
                 font=F["bold"]).pack(pady=(10, 5))

        frame = tk.Frame(dialog)
        frame.pack(fill="both", expand=True, padx=10)

        canvas = tk.Canvas(frame, highlightthickness=0)
        scrollbar = tk.Scrollbar(frame, orient="vertical", command=canvas.yview)
        scroll_frame = tk.Frame(canvas)
        scroll_frame.bind("<Configure>", lambda e: canvas.configure(scrollregion=canvas.bbox("all")))
        canvas.create_window((0, 0), window=scroll_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)
        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")

        for i, land in enumerate(d["lands"][:d["unlocked_lands"]], 1):
            lv = land["upgrade_level"]
            if lv >= 10:
                text = f"#{i}  [{'空' if not land['crop'] else land['crop']}]  Lv.{lv}  MAX"
                btn = tk.Button(scroll_frame, text=text, font=F["small"],
                                anchor="w", padx=5, state="disabled",
                                bg="#eee", relief="groove", bd=1)
                btn.pack(fill="x", padx=5, pady=2)
                continue
            cost = land_upgrade_cost(lv)
            can = d["gold"] >= cost
            text = f"#{i}  [{'空' if not land['crop'] else land['crop']}]  Lv.{lv}→{lv+1}  {cost}💰  {'✅' if can else '❌'}"

            def upgrade(n=i, c=cost):
                if d["gold"] < c:
                    messagebox.showwarning("金币不足", f"需要 {c}💰")
                    return
                d["gold"] -= c
                d["lands"][n - 1]["upgrade_level"] += 1
                self._log(f"⬆️ 土地 #{n} 升级到 Lv.{d['lands'][n-1]['upgrade_level']}")
                dialog.destroy()
                self._update_ui()

            btn = tk.Button(scroll_frame, text=text, font=F["small"],
                            anchor="w", padx=5, bg="#fff" if can else "#f0f0f0",
                            relief="groove", bd=1,
                            command=upgrade if can else None,
                            state="normal" if can else "disabled")
            btn.pack(fill="x", padx=5, pady=2)

        dialog.wait_window()

    def _on_unlock_land(self):
        d = self.data
        if d["unlocked_lands"] >= MAX_LANDS:
            messagebox.showinfo("提示", "所有土地已解锁！")
            return
        next_id = d["unlocked_lands"] + 1
        cost = 200 * next_id
        req_level = (next_id - 1) // 5 + 1
        if d["level"] < req_level:
            messagebox.showwarning("等级不足", f"需要等级 {req_level}")
            return
        if d["gold"] < cost:
            messagebox.showwarning("金币不足", f"需要 {cost}💰")
            return
        if messagebox.askyesno("解锁土地", f"解锁第 {next_id} 号土地？\n消耗 {cost}💰"):
            d["gold"] -= cost
            d["unlocked_lands"] = next_id
            self._log(f"🔓 解锁第 {next_id} 号土地")
            self._update_ui()

    def _on_talents(self):
        d = self.data
        dialog = tk.Toplevel(self.root)
        dialog.title("⭐ 天赋树")
        dialog.geometry("550x500")
        dialog.transient(self.root)
        dialog.grab_set()

        tk.Label(dialog, text=f"⭐ 天赋树  天赋点: {d['talent_points']}",
                 font=F["bold"]).pack(pady=(10, 5))

        frame = tk.Frame(dialog)
        frame.pack(fill="both", expand=True, padx=10)

        canvas = tk.Canvas(frame, highlightthickness=0)
        scrollbar = tk.Scrollbar(frame, orient="vertical", command=canvas.yview)
        scroll_frame = tk.Frame(canvas)
        scroll_frame.bind("<Configure>", lambda e: canvas.configure(scrollregion=canvas.bbox("all")))
        canvas.create_window((0, 0), window=scroll_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)
        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")

        for grp in TALENT_GROUPS:
            tk.Label(scroll_frame, text=f"── {grp} ──", font=F["bold"],
                     bg=COLORS["bg"]).pack(fill="x", pady=(8, 2))
            for t in TALENTS_LIST:
                if t[1] != grp:
                    continue
                _, _, name, max_lv, desc, _ = t
                level = d["talent_tree"].get(name, 0)
                if level >= max_lv:
                    bar = "■" * max_lv + " MAX"
                    btn = tk.Button(scroll_frame,
                                    text=f"{name}  {bar}  {desc}",
                                    font=F["small"], anchor="w", padx=5,
                                    state="disabled", bg="#d4edda",
                                    relief="groove", bd=1)
                else:
                    bar = "■" * level + "□" * (max_lv - level) + f" ({level}/{max_lv})"
                    can = d["talent_points"] > 0
                    btn = tk.Button(scroll_frame,
                                    text=f"{name}  {bar}  {desc}",
                                    font=F["small"], anchor="w", padx=5,
                                    bg="#fff" if can else "#f0f0f0",
                                    relief="groove", bd=1,
                                    state="normal" if can else "disabled")

                    def upgrade_talent(n=name):
                        if d["talent_points"] <= 0:
                            messagebox.showwarning("天赋点不足", "没有足够的天赋点")
                            return
                        d["talent_tree"][n] = d["talent_tree"].get(n, 0) + 1
                        d["talent_points"] -= 1
                        self._log(f"⭐ 学习 {n} Lv.{d['talent_tree'][n]}")
                        dialog.destroy()
                        self._update_ui()

                    btn.config(command=upgrade_talent)
                btn.pack(fill="x", padx=5, pady=2)

        dialog.wait_window()

    def _on_achievements(self):
        d = self.data
        dialog = tk.Toplevel(self.root)
        dialog.title("🏆 成就")
        dialog.geometry("500x450")
        dialog.transient(self.root)
        dialog.grab_set()

        tk.Label(dialog, text="🏆 成就", font=F["bold"]).pack(pady=(10, 5))

        frame = tk.Frame(dialog)
        frame.pack(fill="both", expand=True, padx=10)

        canvas = tk.Canvas(frame, highlightthickness=0)
        scrollbar = tk.Scrollbar(frame, orient="vertical", command=canvas.yview)
        scroll_frame = tk.Frame(canvas)
        scroll_frame.bind("<Configure>", lambda e: canvas.configure(scrollregion=canvas.bbox("all")))
        canvas.create_window((0, 0), window=scroll_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)
        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")

        completed = set(d.get("achievements", []))
        for name, cond_str, _, reward in ACHIEVEMENTS_LIST:
            done = name in completed
            if name == "完美主义者":
                done = all(a[0] in completed or a[0] == "完美主义者"
                          for a in ACHIEVEMENTS_LIST)
            icon = "✅" if done else "🔲"
            r = ", ".join(f"{v}{k}" for k, v in reward.items() if v)
            text = f"{icon} {name}  {cond_str}  [奖励: {r}]"
            btn = tk.Button(scroll_frame, text=text, font=F["small"],
                            anchor="w", padx=5, bg="#d4edda" if done else "#fff",
                            relief="groove", bd=1, state="disabled")
            btn.pack(fill="x", padx=5, pady=2)

        dialog.wait_window()

    def _on_save(self):
        write_save_v2(self.data)
        self._log("💾 游戏已保存")

    def _on_help(self):
        msg = (
            "🌾 开心农场 v2.0 — 养殖场增强版\n\n"
            "【土地操作】\n"
            "1. 种植：点击「种植」或空闲土地\n"
            "2. 收获：点击「收获」批量成熟作物\n"
            "3. 商店：购买种子和养殖动物\n"
            "4. 加工：用原料加工高价值产品\n"
            "5. 仓库：查看并出售作物/加工品/种子\n\n"
            "【养殖场操作】（点击「🐔 养殖场」标签）\n"
            "1. 购买：在空闲栏位购买动物\n"
            "2. 收集：收取动物产品到仓库\n"
            "3. 饲料：用作物加工饲料喂养动物\n"
            "4. 繁殖：两只同种成年可繁殖幼崽\n"
            "5. 升级：提升栏位等级加速生产\n"
            "6. 解锁：用金币解锁更多栏位\n\n"
            "【系统】\n"
            "- 季节每 2 小时轮换\n"
            "- 离线期间土地/养殖场/工厂继续生产\n"
            "- 动物需要消耗饲料才能产出\n"
            "- 动物经历 幼年→成年→老年 三个阶段\n"
            "- 自动保存每 5 分钟"
        )
        messagebox.showinfo("帮助", msg)

    # ==================== 养殖场操作 ====================

    def _on_barn_click(self, event):
        """点击 Canvas 养殖栏位（含升级、收集、出售），升级不关闭弹窗"""
        cw = self.barn_canvas.winfo_width()
        ch = self.barn_canvas.winfo_height()
        col = int(event.x / cw * 10)
        row = int(event.y / ch * 5)
        bid = row * 10 + col + 1
        d = self.data
        ub = d.get("unlocked_barns", INITIAL_BARNS)
        if bid > ub:
            return
        barn = d["barns"][bid - 1]

        # ---- 公共：空闲/有动物都显示自定义弹窗 ----
        dialog = tk.Toplevel(self.root)
        dialog.title(f"栏位 #{bid}")
        dialog.geometry("300x300")
        dialog.transient(self.root)
        dialog.grab_set()
        dialog.configure(bg=COLORS["bg"])

        info_text = tk.StringVar()
        info_label = tk.Label(dialog, textvariable=info_text, font=F["normal"],
                              bg=COLORS["bg"], justify="left")
        info_label.pack(pady=(12, 2), padx=12)

        btn_frame = tk.Frame(dialog, bg=COLORS["bg"])
        btn_frame.pack(pady=(5, 10))

        def refresh_barn_info():
            lv = barn.get("level", 1)
            if barn["animal"] is None:
                cost = barn_upgrade_cost(lv) if lv < 10 else None
                lines = [f"栏位 #{bid}  Lv.{lv}", "空闲"]
                if cost:
                    ok = "✅" if d["gold"] >= cost else "❌"
                    lines.append(f"升级: {cost}💰 {ok}")
                else:
                    lines.append("已满级 ✅")
            else:
                a = get_barn_animal(barn["animal_type"])
                stage = get_age_stage(barn)
                sn = {"juvenile": "幼年", "adult": "成年", "elder": "老年"}.get(stage, "成年")
                pn = a["product"] if a else "?"
                pp = a["sell_price"] if a else 0
                sp = self._calc_barn_animal_sell_price(barn)
                pd_ = barn.get("pending_product", 0)
                cost = barn_upgrade_cost(lv) if lv < 10 else None
                lines = [
                    f"栏位 #{bid}  Lv.{lv}",
                    f"动物: {barn['animal_type']} ({sn})",
                    f"产品: {pn}({pp}💰)  待收:{pd_}",
                    f"出售价: {sp}💰",
                ]
                if cost:
                    ok = "✅" if d["gold"] >= cost else "❌"
                    lines.append(f"升级: {cost}💰 {ok}")
                else:
                    lines.append("已满级 ✅")
            info_text.set("\n".join(lines))
            return lv

        first_lv = refresh_barn_info()

        # ---- 按钮区 ----
        if barn["animal"] is None:
            # 空闲：升级 + 购买 + 关闭
            def upgrade_empty():
                lv = barn.get("level", 1)
                if lv >= 10:
                    messagebox.showinfo("提示", "已满级！")
                    return
                cost = barn_upgrade_cost(lv)
                if not cost or d["gold"] < cost:
                    messagebox.showwarning("金币不足", f"需要 {cost}💰")
                    return
                d["gold"] -= cost
                barn["level"] = lv + 1
                self._log(f"⬆️ 栏位 #{bid} 升级到 Lv.{barn['level']}")
                new_lv = refresh_barn_info()
                if new_lv >= 10:
                    upgrade_btn.config(text="已满级", state="disabled")
                self._update_ui()

            tk.Button(btn_frame, text="🐣 购买动物", font=F["button"],
                      command=lambda: [self._on_buy_barn_animal(), dialog.destroy()],
                      bg=COLORS["btn_bg"], width=14).pack(pady=2)
        else:
            # 有动物：收集 + 出售 + 升级 + 关闭
            pd_ = barn.get("pending_product", 0)
            if pd_ > 0:
                tk.Button(btn_frame, text="📦 收集产品", font=F["button"],
                          command=lambda: [self._collect_single_barn(bid), refresh_barn_info(), self._update_ui()],
                          bg="#d4edda", width=14).pack(pady=2)

            tk.Button(btn_frame, text="💰 出售动物", font=F["button"],
                      command=lambda: [self._sell_barn_animal(bid), dialog.destroy()],
                      bg=COLORS["btn_bg"], width=14).pack(pady=2)

        upgrade_btn = tk.Button(btn_frame, text="⬆️ 升级", font=F["button"],
                                command=None, bg=COLORS["btn_bg"], width=14)

        if barn["animal"] is None:
            upgrade_btn.config(command=upgrade_empty)
        else:
            def upgrade_occupied():
                lv = barn.get("level", 1)
                if lv >= 10:
                    messagebox.showinfo("提示", "已满级！")
                    return
                cost = barn_upgrade_cost(lv)
                if not cost or d["gold"] < cost:
                    messagebox.showwarning("金币不足", f"需要 {cost}💰")
                    return
                d["gold"] -= cost
                barn["level"] = lv + 1
                self._log(f"⬆️ 栏位 #{bid} 升级到 Lv.{barn['level']}")
                new_lv = refresh_barn_info()
                if new_lv >= 10:
                    upgrade_btn.config(text="已满级", state="disabled")
                self._update_ui()

            upgrade_btn.config(command=upgrade_occupied)

        if first_lv >= 10:
            upgrade_btn.config(text="已满级", state="disabled")
        upgrade_btn.pack(pady=2)

        tk.Button(btn_frame, text="❌ 关闭", font=F["button"],
                  command=dialog.destroy, bg=COLORS["btn_bg"], width=14).pack(pady=2)

    def _calc_barn_animal_sell_price(self, barn):
        """计算出售动物的价格"""
        a = get_barn_animal(barn["animal_type"])
        if a is None:
            return 0
        base = a["price"]
        # 基础回收价：50%
        price = int(base * 0.5)
        # 栏位等级加成：每级+5%
        lv = barn.get("level", 1)
        price += int(base * (lv - 1) * 0.05)
        # 产出次数加成：每产出10次+2%
        prod_count = barn.get("production_count", 0)
        price += int(base * min(prod_count / 10 * 0.02, 0.2))
        # 天赋加成：动物折扣天赋也影响出售价
        discount_talent = get_talent_value(self.data["talent_tree"], "animal_discount")
        price = int(price * (1.0 + discount_talent))
        return max(price, int(base * 0.1))

    def _sell_barn_animal(self, bid):
        """出售栏位中的动物"""
        d = self.data
        barn = d["barns"][bid - 1]
        if barn["animal"] is None:
            return

        a = get_barn_animal(barn["animal_type"])
        sell_price = self._calc_barn_animal_sell_price(barn)

        if not messagebox.askyesno("确认出售",
            f"确定要出售栏位 #{bid} 的 {barn['animal_type']} 吗？\n"
            f"可获得 {sell_price}💰\n"
            f"（该操作不可撤销）"):
            return

        # 先收集待收产品
        pending = barn.get("pending_product", 0)
        if pending > 0:
            inv = d["inventory"]["products"]
            inv[a["product"]] = inv.get(a["product"], 0) + pending
            self._log(f"📦 出售前收集 {a['product']}×{pending}")
            barn["pending_product"] = 0

        # 清空栏位
        animal_name = barn["animal_type"]
        barn["animal"] = None
        barn["animal_type"] = None
        barn["purchase_time"] = None
        barn["age_stage"] = None
        barn["production_count"] = 0
        barn["last_produce_time"] = None
        barn["pending_product"] = 0
        barn["breed_cooldown"] = None
        barn["fed_time"] = None

        d["gold"] = d.get("gold", 0) + sell_price
        self._log(f"💰 出售 {animal_name}，获得 {sell_price}💰")
        self._update_ui()

    def _collect_single_barn(self, bid):
        """收集单个栏位产品"""
        d = self.data
        barn = d["barns"][bid - 1]
        pending = barn.get("pending_product", 0)
        if pending <= 0:
            return
        a = get_barn_animal(barn["animal_type"])
        if a is None:
            return

        inv = d["inventory"]["products"]
        inv[a["product"]] = inv.get(a["product"], 0) + pending
        self._log(f"📦 收集栏位 #{bid} {a['product']}×{pending}")
        barn["pending_product"] = 0
        self._update_ui()

    def _on_buy_barn_animal(self):
        """购买养殖动物对话框"""
        d = self.data
        ub = d.get("unlocked_barns", INITIAL_BARNS)

        # 找空闲栏位
        free_idx = None
        free_list = []
        for i in range(ub):
            if d["barns"][i]["animal"] is None and d["barns"][i].get("unlocked", False):
                free_idx = i
                free_list.append(i + 1)
        if not free_list:
            messagebox.showwarning("无空栏位", "所有栏位已占满，请先解锁或升级栏位")
            return

        dialog = tk.Toplevel(self.root)
        dialog.title("🐣 购买动物")
        dialog.geometry("480x450")
        dialog.transient(self.root)
        dialog.grab_set()

        tk.Label(dialog, text=f"🐣 购买动物  金币: {d['gold']:,}  空闲栏位: {', '.join(map(str, free_list))}",
                 font=F["bold"]).pack(pady=(10, 5))

        frame = tk.Frame(dialog)
        frame.pack(fill="both", expand=True, padx=10)

        canvas = tk.Canvas(frame, highlightthickness=0)
        scrollbar = tk.Scrollbar(frame, orient="vertical", command=canvas.yview)
        scroll_frame = tk.Frame(canvas)
        scroll_frame.bind("<Configure>", lambda e: canvas.configure(scrollregion=canvas.bbox("all")))
        canvas.create_window((0, 0), window=scroll_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)
        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")

        for i, a_data in enumerate(BARN_ANIMALS_LIST, 1):
            unlocked = d["level"] >= a_data["level"]
            discount = 1.0 - get_talent_value(d["talent_tree"], "animal_discount")
            price = int(a_data["price"] * discount)
            can = unlocked and d["gold"] >= price
            feed_desc = "+".join(f"{k}×{v}" for k, v in a_data["feed"].items())

            if not unlocked:
                text = f"🔒 {i}. {a_data['name']}  需Lv.{a_data['level']}  {a_data['price']}💰  →{a_data['product']}({a_data['sell_price']}💰)"
                btn = tk.Button(scroll_frame, text=text, font=F["small"],
                                anchor="w", padx=5, state="disabled",
                                bg="#eee", relief="groove", bd=1)
            else:
                text = f"{i}. {a_data['name']:<4} {price:>5}💰  →{a_data['product']}({a_data['sell_price']}💰)  饲料:{feed_desc}  {'✅' if can else '❌'}"

                def buy(name=a_data["name"], p=price):
                    fi = None
                    for bi in range(ub):
                        if d["barns"][bi]["animal"] is None and d["barns"][bi].get("unlocked", False):
                            fi = bi
                            break
                    if fi is None:
                        messagebox.showwarning("无空栏位", "没有空闲栏位！")
                        return
                    if d["gold"] < p:
                        messagebox.showwarning("金币不足", f"需要 {p}💰")
                        return
                    d["gold"] -= p
                    barn = d["barns"][fi]
                    barn["animal"] = name
                    barn["animal_type"] = name
                    barn["purchase_time"] = now_str()
                    barn["age_stage"] = "juvenile"
                    barn["production_count"] = 0
                    barn["last_produce_time"] = None
                    barn["pending_product"] = 0
                    barn["breed_cooldown"] = None
                    self._log(f"✅ 在栏位 {fi+1} 放入 {name}，花费 {p}💰")
                    dialog.destroy()
                    self._update_ui()

                btn = tk.Button(scroll_frame, text=text, font=F["small"],
                                anchor="w", padx=5,
                                command=buy if can else None,
                                bg="#fff" if can else "#f0f0f0",
                                state="normal" if can else "disabled",
                                relief="groove", bd=1)
            btn.pack(fill="x", padx=5, pady=2)

        dialog.wait_window()

    def _on_feed_animals(self):
        """投喂动物：先收取饲料厂成品，再调用一次性投喂"""
        d = self.data
        # 1. 自动收取饲料厂完成品
        ff = d.get("feed_factory", {})
        if ff.get("ready"):
            if collect_feed(d):
                self._log("🍽️ 自动收取饲料厂成品")
        # 2. 调用新的一次性投喂函数（消耗饲料 → 设置 fed_time）
        fed, no_feed, already = feed_barn_animals(d)
        # 3. 触发生产（已投喂的动物按周期产出）
        process_barn_production(d)
        self._update_barn_status()
        self._log(f"🍽️ 投喂完成：新增投喂 {len(fed)} 只，已投喂 {len(already)} 只，缺饲料 {len(no_feed)} 只，饲料库存 {sum(d.get('feed_inventory', {}).values())} 份")
        self._update_ui()

    def _on_collect_barn(self):
        """收集所有栏位产品"""
        d = self.data
        # 先生产
        process_barn_production(d)
        # 再收集
        total, collected = collect_all_barns(d)
        if total > 0:
            items_str = " | ".join(collected)
            self._log(f"📦 收集养殖场 {total} 件产品: {items_str}")
        else:
            self._log("📦 没有可收集的动物产品")
        self._update_ui()

    def _on_feed_factory(self):
        """饲料加工对话框"""
        d = self.data
        dialog = tk.Toplevel(self.root)
        dialog.title("🏭 饲料加工")
        dialog.geometry("500x450")
        dialog.transient(self.root)
        dialog.grab_set()

        ff = d.get("feed_factory", {})
        feed_inv = d.get("feed_inventory", {})

        tk.Label(dialog, text=f"🏭 饲料加工  金币: {d['gold']:,}",
                 font=F["bold"]).pack(pady=(10, 5))

        # 饲料库存
        feed_parts = [f"{k}: {v}份" for k, v in feed_inv.items() if v > 0]
        feed_text = " | ".join(feed_parts) if feed_parts else "空"
        tk.Label(dialog, text=f"📦 饲料库存: {feed_text}",
                 font=F["normal"]).pack(pady=(0, 10))

        frame = tk.Frame(dialog)
        frame.pack(fill="both", expand=True, padx=10)

        canvas = tk.Canvas(frame, highlightthickness=0)
        scrollbar = tk.Scrollbar(frame, orient="vertical", command=canvas.yview)
        scroll_frame = tk.Frame(canvas)
        scroll_frame.bind("<Configure>", lambda e: canvas.configure(scrollregion=canvas.bbox("all")))
        canvas.create_window((0, 0), window=scroll_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)
        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")

        if ff.get("ready"):
            text = f"✅ 饲料加工完成！{ff.get('current_order', '')} 可收取"
            btn = tk.Button(scroll_frame, text=text, font=F["bold"],
                           anchor="w", padx=5,
                           bg="#d4edda", relief="groove", bd=1)

            def do_collect():
                if collect_feed(d):
                    self._log(f"🍽️ 收取饲料")
                    dialog.destroy()
                    self._update_ui()

            btn.config(command=do_collect)
            btn.pack(fill="x", padx=5, pady=5)
        elif ff.get("current_order"):
            st = parse_dt(ff["start_time"])
            recipe = next((r for r in FEED_RECIPES if r["name"] == ff["current_order"]), None)
            if recipe:
                remain = max(0, recipe["time"] - (now_dt() - st).total_seconds() / 60.0)
                text = f"⏳ 加工中: {ff['current_order']}  剩余 {remain:.0f}min"
                btn = tk.Button(scroll_frame, text=text, font=F["bold"],
                               anchor="w", padx=5,
                               bg="#fff3cd", relief="groove", bd=1,
                               state="disabled")
                btn.pack(fill="x", padx=5, pady=5)
        else:
            for i, r in enumerate(FEED_RECIPES, 1):
                unlocked = d["level"] >= r["level"]
                ings = []
                for ing_name, ing_qty in r["ingredients"].items():
                    if ing_name == "任意水果":
                        have = sum(d["inventory"]["crops"].get(f, 0) for f in FEED_FRUIT_NAMES)
                        ings.append(f"水果×{ing_qty}(有{have})")
                    else:
                        have = d["inventory"]["crops"].get(ing_name, 0)
                        ings.append(f"{ing_name}×{ing_qty}(有{have})")
                ings_str = "+".join(ings)

                if not unlocked:
                    text = f"🔒 {i}. {r['name']}  [{ings_str}]  ⏱{r['time']}min → {r['yield']}份  需Lv.{r['level']}"
                    btn = tk.Button(scroll_frame, text=text, font=F["small"],
                                    anchor="w", padx=5, state="disabled",
                                    bg="#eee", relief="groove", bd=1)
                else:
                    text = f"{i}. {r['name']}  [{ings_str}]  ⏱{r['time']}min → {r['yield']}份"

                    def do_feed(idx=i - 1):
                        if start_feed_production(d, idx):
                            self._log(f"🏭 开始加工 {FEED_RECIPES[idx]['name']}")
                            dialog.destroy()
                            self._update_ui()

                    btn = tk.Button(scroll_frame, text=text, font=F["small"],
                                    anchor="w", padx=5,
                                    bg="#fff", relief="groove", bd=1,
                                    command=do_feed)
                btn.pack(fill="x", padx=5, pady=2)

        dialog.wait_window()

    def _on_breed(self):
        """繁殖对话框"""
        d = self.data
        ub = d.get("unlocked_barns", INITIAL_BARNS)

        # 列出可繁殖的成年动物
        adults = []
        for i in range(ub):
            barn = d["barns"][i]
            if barn["animal"] is not None and get_age_stage(barn) == "adult":
                cd = barn.get("breed_cooldown")
                if cd and now_str() < cd:
                    continue  # 冷却中
                adults.append((i, barn))

        if len(adults) < 2:
            messagebox.showinfo("繁殖", "需要至少2只不在冷却中的成年动物才能繁殖")
            return

        dialog = tk.Toplevel(self.root)
        dialog.title("🧬 繁殖")
        dialog.geometry("500x400")
        dialog.transient(self.root)
        dialog.grab_set()

        tk.Label(dialog, text=f"🧬 繁殖  需要: 1000💰  成功率: 70%",
                 font=F["bold"]).pack(pady=(10, 5))

        frame = tk.Frame(dialog)
        frame.pack(fill="both", expand=True, padx=10)

        tk.Label(dialog, text="选择两个亲本（同种成年动物）：",
                 font=F["normal"]).pack()

        list_frame = tk.Frame(dialog)
        list_frame.pack(fill="both", expand=True, padx=10, pady=5)

        canvas = tk.Canvas(list_frame, highlightthickness=0)
        scrollbar = tk.Scrollbar(list_frame, orient="vertical", command=canvas.yview)
        scroll_frame = tk.Frame(canvas)
        scroll_frame.bind("<Configure>", lambda e: canvas.configure(scrollregion=canvas.bbox("all")))
        canvas.create_window((0, 0), window=scroll_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)
        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")

        sel_frame = tk.Frame(dialog)
        sel_frame.pack(pady=10)

        var1 = tk.IntVar(value=-1)
        var2 = tk.IntVar(value=-1)

        for idx, (bi, barn) in enumerate(adults):
            text = f"栏位 {bi+1}: {barn['animal_type']}  Lv.{barn.get('level', 1)}"
            rb = tk.Radiobutton(scroll_frame, text=text, font=F["small"],
                               variable=var1, value=idx, bg="#fff")
            rb.pack(fill="x", padx=5, pady=2, anchor="w")
            rb2 = tk.Radiobutton(scroll_frame, text=text, font=F["small"],
                                variable=var2, value=idx, bg="#fff")
            rb2.pack(fill="x", padx=5, pady=2, anchor="w")

        def do_breed_action():
            i1 = var1.get()
            i2 = var2.get()
            if i1 < 0 or i2 < 0 or i1 == i2:
                messagebox.showwarning("选择无效", "请选择两个不同的亲本")
                return

            bi1, b1 = adults[i1]
            bi2, b2 = adults[i2]
            ok, msg = can_breed(b1, b2, d)
            if not ok:
                messagebox.showwarning("繁殖失败", msg)
                return

            result, detail = do_breed(d, bi1, bi2)
            self._log(detail)
            dialog.destroy()
            self._update_ui()

        tk.Button(dialog, text="🧬 开始繁殖", font=F["bold"],
                 command=do_breed_action,
                 bg="#d4edda", padx=20, pady=5).pack(pady=(0, 10))

        dialog.wait_window()

    def _on_upgrade_barn(self):
        """升级栏位对话框"""
        d = self.data
        ub = d.get("unlocked_barns", INITIAL_BARNS)
        dialog = tk.Toplevel(self.root)
        dialog.title("⬆️ 升级栏位")
        dialog.geometry("550x400")
        dialog.transient(self.root)
        dialog.grab_set()

        tk.Label(dialog, text=f"⬆️ 栏位升级  金币: {d['gold']:,}",
                 font=F["bold"]).pack(pady=(10, 5))

        frame = tk.Frame(dialog)
        frame.pack(fill="both", expand=True, padx=10)

        canvas = tk.Canvas(frame, highlightthickness=0)
        scrollbar = tk.Scrollbar(frame, orient="vertical", command=canvas.yview)
        scroll_frame = tk.Frame(canvas)
        scroll_frame.bind("<Configure>", lambda e: canvas.configure(scrollregion=canvas.bbox("all")))
        canvas.create_window((0, 0), window=scroll_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)
        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")

        for i in range(ub):
            barn = d["barns"][i]
            lv = barn.get("level", 1)
            anim = barn["animal"] or "空"
            if lv >= 10:
                text = f"#{i+1}  [{anim}]  Lv.{lv}  MAX"
                btn = tk.Button(scroll_frame, text=text, font=F["small"],
                                anchor="w", padx=5, state="disabled",
                                bg="#eee", relief="groove", bd=1)
            else:
                cost = barn_upgrade_cost(lv)
                can = cost and d["gold"] >= cost
                ef = barn_upgrade_effects(lv + 1)
                eff_str = ""
                if "speed" in ef:
                    eff_str = f"速度+{int(ef['speed']*100)}%"
                elif "yield" in ef:
                    eff_str = f"产量+{int(ef['yield']*100)}%"
                elif "double" in ef:
                    eff_str = f"双倍+{int(ef['double']*100)}%"
                elif "global" in ef:
                    eff_str = "全局+10%"
                text = f"#{i+1}  [{anim}]  Lv.{lv}→{lv+1}  {cost}💰  {'✅' if can else '❌'}  {eff_str}"

                def upgrade(n=i, c=cost):
                    if not c or d["gold"] < c:
                        return
                    d["gold"] -= c
                    d["barns"][n]["level"] += 1
                    self._log(f"⬆️ 栏位 #{n+1} 升级到 Lv.{d['barns'][n]['level']}")
                    dialog.destroy()
                    self._update_ui()

                btn = tk.Button(scroll_frame, text=text, font=F["small"],
                                anchor="w", padx=5, bg="#fff" if can else "#f0f0f0",
                                relief="groove", bd=1,
                                command=upgrade if can else None,
                                state="normal" if can else "disabled")
            btn.pack(fill="x", padx=5, pady=2)

        dialog.wait_window()

    def _on_unlock_barn(self):
        """解锁栏位"""
        d = self.data
        if d.get("unlocked_barns", INITIAL_BARNS) >= MAX_BARNS:
            messagebox.showinfo("提示", "所有栏位已解锁！")
            return
        next_id = d["unlocked_barns"] + 1
        cost = 200 * next_id
        req_level = (next_id - 1) // 5 + 1
        if d["level"] < req_level:
            messagebox.showwarning("等级不足", f"需要等级 {req_level}")
            return
        if d["gold"] < cost:
            messagebox.showwarning("金币不足", f"需要 {cost}💰")
            return
        if messagebox.askyesno("解锁栏位", f"解锁第 {next_id} 号栏位？\n消耗 {cost}💰"):
            d["gold"] -= cost
            d["unlocked_barns"] = next_id
            d["barns"][next_id - 1]["unlocked"] = True
            self._log(f"🔓 解锁第 {next_id} 号栏位")
            self._update_ui()

    # ==================== 仓库出售滑行栏 ====================

    def _sell_with_slider(self, title, inv_category, item_name, unit_price,
                          max_qty, warehouse_dialog):
        """带滑行栏的数量选择出售对话框"""
        win = tk.Toplevel(self.root)
        win.title(title)
        win.geometry("380x220")
        win.resizable(False, False)
        win.transient(self.root)
        win.grab_set()

        tk.Label(win, text=f"{item_name}  单价: {unit_price}💰  库存: {max_qty}",
                 font=F["bold"]).pack(pady=(10, 5))

        qty_var = tk.IntVar(value=max(1, min(max_qty, max_qty // 2 or 1)))

        def update_total(*_):
            total_label.config(text=f"总价: {unit_price * qty_var.get()}💰")
            total_label.update()

        scale = tk.Scale(win, from_=1, to=max(max_qty, 1), orient="horizontal",
                         variable=qty_var, length=300, font=F["small"],
                         command=update_total)
        scale.pack(pady=5)

        total_label = tk.Label(win, text=f"总价: {unit_price * qty_var.get()}💰",
                               font=F["bold"])
        total_label.pack()

        btn_frame = tk.Frame(win)
        btn_frame.pack(pady=(10, 0))

        def confirm():
            qty = qty_var.get()
            inv = self.data["inventory"][inv_category]
            actual = inv.get(item_name, 0)
            qty = min(qty, actual)
            if qty <= 0:
                win.destroy()
                return
            gold = qty * unit_price
            self.data["gold"] += gold
            self.data["total_earnings"] += gold
            inv[item_name] -= qty
            if inv[item_name] <= 0:
                del inv[item_name]
            self._log(f"💰 出售 {item_name}×{qty}，获得 {gold}💰")
            win.destroy()
            warehouse_dialog.destroy()
            self._update_ui()

        tk.Button(btn_frame, text="✅ 出售", font=F["button"],
                  command=confirm, bg="#d4edda", width=8).pack(side="left", padx=5)
        tk.Button(btn_frame, text="❌ 取消", font=F["button"],
                  command=win.destroy, bg="#f8d7da", width=8).pack(side="left", padx=5)

        win.wait_window()

    # ---------- 关闭 ----------
    def _on_close(self):
        write_save_v2(self.data)
        self.root.destroy()

    # ---------- 启动 ----------
    def run(self):
        self.root.mainloop()


# ============ 入口 ============
if __name__ == "__main__":
    app = FarmGUIv2()
    app.run()
