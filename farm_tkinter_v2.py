# -*- coding: utf-8 -*-
"""
开心农场 v3.0
"""
import tkinter as tk
from tkinter import ttk, messagebox
import json
import datetime
import time
import random
import threading
import sys
import io
import os

# ============ 从 farm_game_v2 导入所有逻辑（包含 barn 模块） ============
from farm_game_v2 import (
    FACTORY_LIST, TALENTS_LIST, TALENT_GROUPS,
    ACHIEVEMENTS_LIST, SEASONS, MAX_LANDS, WAREHOUSE_BASE_CAPACITY,
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
    calc_offline_crops_v2, calc_offline_agro_v2,
    get_barn_animal, get_age_stage, can_barn_produce, check_feed_available,
    process_barn_production, collect_all_barns,
    barn_upgrade_cost, barn_upgrade_effects, barn_yield_multiplier, double_barn_chance,
    start_feed_production, collect_feed, check_feed_factory_ready,
    do_breed, can_breed, consume_feed,
    feed_barn_animals,
    FEED_FRUIT_NAMES,
    init_game,
    # v2.1 新功能
    warehouse_capacity, warehouse_expansion_cost,
    calc_harvest_yield, cancel_event_warning,
    reset_talents, check_talent_fruit_drop, use_talent_fruit,
    diamond_shop_purchase, get_diamond_shop_item, DIAMOND_SHOP_ITEMS,
    get_animal_feed_name, get_feed_consume, ANIMAL_FEED_CONSUMPTION,
    apply_exp_bonus,
    # 农业建筑
    MAX_AGRO_BUILDINGS, INITIAL_AGRO_BUILDINGS, FEED_RECIPES_BY_LEVEL,
    agro_build_cost, agro_upgrade_cost, agro_unlock_cost,
    get_available_recipes, check_agro_ready, process_all_agro_buildings,
    _consume_recipe_ingredients, start_agro_production, collect_agro_product,
    build_agro_building, upgrade_agro_building, get_agro_slot_status,
    _feed_inv,
    # 酿酒
    BREW_RECIPES, BREW_RECIPES_BY_LEVEL, get_recipe_list, get_recipes_by_level,
    _SEASON_BONUS_MAP,
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
        "help": (families, 11),
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


# ============ 圆角矩形工具 ============
def _round_rect(canvas, x0, y0, x1, y1, r=8, **kwargs):
    """在 Canvas 上绘制圆角矩形（多边形 + smooth）"""
    r = min(r, (x1 - x0) / 2, (y1 - y0) / 2)
    pts = [x0+r, y0, x1-r, y0, x1, y0+r, x1, y1-r,
           x1-r, y1, x0+r, y1, x0, y1-r, x0, y0+r]
    return canvas.create_polygon(pts, smooth=True, splinesteps=12, **kwargs)


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

def _draw_potato(c, cx, cy, s=1.0):
    """土豆"""
    c.create_oval(cx-10*s, cy-8*s, cx+10*s, cy+8*s, fill="#c8a050", outline="#a08030", width=1)
    for dx, dy in [(-4, -2), (3, -3), (-1, 2), (4, 1)]:
        c.create_oval(cx+dx*s-2*s, cy+dy*s-2*s, cx+dx*s+2*s, cy+dy*s+2*s, fill="#b89040", outline="", width=0)

def _draw_tomato(c, cx, cy, s=1.0):
    """番茄"""
    c.create_oval(cx-10*s, cy-8*s, cx+10*s, cy+8*s, fill="#e03030", outline="#c01010", width=1)
    c.create_oval(cx-4*s, cy-9*s, cx+4*s, cy-5*s, fill="#3a8a2c", outline="#2a6a1c", width=1)
    c.create_arc(cx-8*s, cy-4*s, cx-3*s, cy+2*s, start=0, extent=180, fill="#d02020", outline="", width=0)
    c.create_oval(cx-8*s, cy-2*s, cx-5*s, cy+1*s, fill="#f0f0f0", outline="", width=0)

def _draw_strawberry(c, cx, cy, s=1.0):
    """草莓"""
    c.create_polygon(cx, cy+8*s, cx-10*s, cy-2*s, cx+10*s, cy-2*s, fill="#e04040", outline="#c02020", width=1)
    c.create_arc(cx-10*s, cy-6*s, cx+10*s, cy+2*s, start=0, extent=180, fill="#e04040", outline="#c02020", width=1)
    c.create_oval(cx-3*s, cy-8*s, cx+3*s, cy-4*s, fill="#3a8a2c", outline="#2a6a1c", width=1)
    for dx, dy in [(-4, 0), (0, 2), (4, 0), (-2, -2), (2, -2)]:
        c.create_oval(cx+dx*s-1*s, cy+dy*s-1*s, cx+dx*s+1*s, cy+dy*s+1*s, fill="#f0c040", outline="", width=0)

def _draw_blueberry(c, cx, cy, s=1.0):
    """蓝莓"""
    c.create_oval(cx-12*s, cy-9*s, cx+12*s, cy+9*s, fill="#4060d0", outline="#3040b0", width=1)
    c.create_oval(cx-7*s, cy-5*s, cx-3*s, cy-1*s, fill="#d0e0ff", outline="", width=0)
    c.create_oval(cx+2*s, cy-3*s, cx+5*s, cy-1*s, fill="#d0e0ff", outline="", width=0)
    c.create_oval(cx-1*s, cy-2*s, cx+2*s, cy+0*s, fill="#d0e0ff", outline="", width=0)
    c.create_polygon(cx-4*s, cy-11*s, cx, cy-14*s, cx+4*s, cy-11*s, fill="#5a3a1c", outline="#3a2a0c", width=1)

def _draw_coffee(c, cx, cy, s=1.0):
    """咖啡豆"""
    c.create_line(cx, cy+10*s, cx, cy-6*s, fill="#5a3a1c", width=max(1, int(2*s)))
    for dx, dy in [(-4, -2), (4, -2), (-3, 3), (3, 3)]:
        c.create_oval(cx+dx*s-4*s, cy+dy*s-3*s, cx+dx*s+4*s, cy+dy*s+3*s, fill="#6a4a2c", outline="#4a2a0c", width=1)
        c.create_line(cx+dx*s-2*s, cy+dy*s-3*s, cx+dx*s+2*s, cy+dy*s-6*s, fill="#6a4a2c", width=1)

def _draw_cotton(c, cx, cy, s=1.0):
    """棉花"""
    c.create_line(cx, cy+12*s, cx, cy-2*s, fill="#4a7a2c", width=max(1, int(2*s)))
    c.create_line(cx, cy+4*s, cx-6*s, cy+6*s, fill="#5a8a3c", width=1)
    c.create_line(cx, cy+2*s, cx+6*s, cy+4*s, fill="#5a8a3c", width=1)
    for dx, dy in [(0, -4), (-5, 0), (5, 0), (-3, 2), (3, 2)]:
        c.create_oval(cx+dx*s-6*s, cy+dy*s-4*s, cx+dx*s+6*s, cy+dy*s+4*s, fill="#f8f8f8", outline="#e0e0e0", width=1)

def _draw_sugarcane(c, cx, cy, s=1.0):
    """甘蔗"""
    c.create_line(cx, cy+12*s, cx, cy-12*s, fill="#7a3a1c", width=max(3, int(5*s)))
    for i in range(4):
        cy_seg = cy + 12*s - i*6*s
        c.create_line(cx-5*s, cy_seg, cx+5*s, cy_seg, fill="#5a2a0c", width=1)
    c.create_line(cx-2*s, cy-12*s, cx+6*s, cy-16*s, fill="#3a8a2c", width=max(1, int(2*s)))
    c.create_line(cx+2*s, cy-12*s, cx+8*s, cy-14*s, fill="#3a8a2c", width=max(1, int(2*s)))

def _draw_grape(c, cx, cy, s=1.0):
    """葡萄"""
    c.create_line(cx, cy+8*s, cx-2*s, cy-12*s, fill="#5a3a1c", width=max(1, int(2*s)))
    c.create_line(cx-2*s, cy-12*s, cx+6*s, cy-16*s, fill="#3a8a2c", width=1)
    colors = ["#6040a0", "#7050b0", "#503090"]
    for dx, dy in [(0, -2), (-5, 1), (5, 1), (-3, 4), (3, 4), (0, 6)]:
        c.create_oval(cx+dx*s-4*s, cy+dy*s-3*s, cx+dx*s+4*s, cy+dy*s+3*s, fill=colors[(dx+dy)%3], outline="#402080", width=1)

def _draw_cocoa(c, cx, cy, s=1.0):
    """可可豆"""
    c.create_line(cx, cy+10*s, cx, cy-8*s, fill="#5a3a1c", width=max(2, int(3*s)))
    c.create_oval(cx-7*s, cy-6*s, cx+7*s, cy+6*s, fill="#8B5a3c", outline="#6a3a1c", width=1)
    for dx in [-3, 0, 3]:
        c.create_line(cx+dx*s, cy-4*s, cx+dx*s, cy+4*s, fill="#6a3a1c", width=1)
    c.create_oval(cx-5*s, cy-2*s, cx-2*s, cy, fill="#c08040", outline="", width=0)

def _draw_tea(c, cx, cy, s=1.0):
    """茶叶"""
    c.create_line(cx, cy+12*s, cx, cy-2*s, fill="#4a6a2c", width=max(1, int(2*s)))
    for dx, dy in [(-5, -4), (5, -6), (-3, 2), (3, 0)]:
        c.create_polygon(
            cx+dx*s-5*s, cy+dy*s+3*s,
            cx+dx*s, cy+dy*s-5*s,
            cx+dx*s+5*s, cy+dy*s+3*s,
            fill="#5a8a3c", outline="#3a6a1c", width=1)
    c.create_oval(cx-2*s, cy-4*s, cx+2*s, cy+2*s, fill="#8a5a3c", outline="", width=0)

def _draw_clover(c, cx, cy, s=1.0):
    """四叶草"""
    c.create_line(cx, cy+10*s, cx, cy-2*s, fill="#3a6a1c", width=max(1, int(2*s)))
    for dx, dy in [(-4, -4), (4, -4), (-4, 2), (4, 2)]:
        c.create_oval(cx+dx*s-5*s, cy+dy*s-4*s, cx+dx*s+5*s, cy+dy*s+4*s, fill="#4a8a2c", outline="#3a6a1c", width=1)
    c.create_oval(cx-1*s, cy-1*s, cx+1*s, cy+1*s, fill="#6aaa3c", outline="", width=0)

def _draw_golden_wheat(c, cx, cy, s=1.0):
    """黄金小麦"""
    c.create_line(cx, cy+12*s, cx, cy-8*s, fill="#b8860b", width=max(1, int(2*s)))
    c.create_line(cx, cy+4*s, cx-8*s, cy+8*s, fill="#d4a017", width=max(1, int(1.5*s)))
    c.create_line(cx, cy+2*s, cx+8*s, cy+6*s, fill="#d4a017", width=max(1, int(1.5*s)))
    for i, ox in enumerate([-4, 0, 4]):
        oy = -8 - i*5
        c.create_oval(cx+ox*s-3*s, cy+oy*s-3*s, cx+ox*s+3*s, cy+oy*s+2*s, fill="#ffd700", outline="#b8860b", width=1)
        c.create_line(cx+ox*s, cy+oy*s-3*s, cx+ox*s, cy+oy*s-8*s, fill="#ffd700", width=1)

def _draw_rainbow_flower(c, cx, cy, s=1.0):
    """彩虹花"""
    c.create_line(cx, cy+10*s, cx, cy-2*s, fill="#3a6a1c", width=max(1, int(2*s)))
    c.create_line(cx-4*s, cy+4*s, cx-6*s, cy+2*s, fill="#3a6a1c", width=1)
    c.create_line(cx+4*s, cy+2*s, cx+6*s, cy, fill="#3a6a1c", width=1)
    rainbow = ["#ff0000", "#ff8800", "#ffff00", "#00cc00", "#0088ff", "#8800ff"]
    for i, (dx, dy) in enumerate([(0, -2), (-4, -4), (4, -4), (-2, -6), (2, -6), (0, -8)]):
        c.create_oval(cx+dx*s-4*s, cy+dy*s-3*s, cx+dx*s+4*s, cy+dy*s+3*s, fill=rainbow[i], outline="", width=0)

def _draw_watermelon(c, cx, cy, s=1.0):
    """西瓜 — 弧形条纹风格"""
    # 主体
    c.create_oval(cx-14*s, cy-11*s, cx+14*s, cy+11*s, fill="#1b6e1b", outline="#0f4f0f", width=1)
    # 用弧线做条纹
    c.create_arc(cx-14*s, cy-11*s, cx+14*s, cy+11*s, start=200, extent=40,
                 fill="#4db84d", outline="", width=0)
    c.create_arc(cx-14*s, cy-11*s, cx+14*s, cy+11*s, start=280, extent=30,
                 fill="#4db84d", outline="", width=0)
    c.create_arc(cx-14*s, cy-11*s, cx+14*s, cy+11*s, start=350, extent=30,
                 fill="#4db84d", outline="", width=0)
    # 高光
    c.create_oval(cx-6*s, cy-8*s, cx-2*s, cy-4*s, fill="#80d080", outline="", width=0)
    # 蒂柄
    c.create_line(cx, cy-11*s, cx+4*s, cy-17*s,
                  fill="#5a3a1c", width=max(2, int(2*s)), smooth=True, capstyle="round")

CROP_DRAW_FUNCS = {
    "小麦": _draw_wheat, "玉米": _draw_corn, "水稻": _draw_rice,
    "玫瑰": _draw_rose, "胡萝卜": _draw_carrot, "南瓜": _draw_pumpkin,
    "金色南瓜": _draw_golden_pumpkin,
    "土豆": _draw_potato, "番茄": _draw_tomato, "草莓": _draw_strawberry,
    "蓝莓": _draw_blueberry, "咖啡豆": _draw_coffee, "棉花": _draw_cotton,
    "甘蔗": _draw_sugarcane, "葡萄": _draw_grape, "可可豆": _draw_cocoa,
    "茶叶": _draw_tea, "四叶草": _draw_clover,
    "黄金小麦": _draw_golden_wheat, "彩虹花": _draw_rainbow_flower,
    "西瓜": _draw_watermelon,
}

# ============ 生长阶段支持 ============
# 生长阶段：0=幼苗, 1=生长期, 2=近成熟, 3=已成熟
_STAGE_SCALES = [0.50, 0.65, 0.85, 1.0]

def _calc_stage(remain, growth_total):
    if remain <= 0:
        return 3
    pct = 1.0 - remain / growth_total
    if pct < 0.33:
        return 0
    elif pct < 0.66:
        return 1
    else:
        return 2

def _draw_crop_staged(canvas, cx, cy, s, name, stage, tags=None):
    """按生长阶段绘制作物, stage=0-3，纯 canvas 绘图"""
    stage = min(max(stage, 0), 3)
    stage_scale = _STAGE_SCALES[stage]
    if stage == 0:
        _draw_sprout(canvas, cx, cy, s, tags=tags)
        return True
    draw_func = CROP_DRAW_FUNCS.get(name)
    if draw_func:
        if stage == 3:
            draw_func(canvas, cx, cy, s)
        else:
            draw_func(canvas, cx, cy, s * stage_scale)
        return True
    return False

def _draw_sprout(c, cx, cy, s=1.0, tags=None):
    """通用幼苗图标（所有作物的阶段 0）"""
    s2 = s * 0.6
    kw = {"tags": tags} if tags else {}
    c.create_arc(cx-6*s2, cy-2*s2, cx+6*s2, cy+6*s2, start=200, extent=140,
                 fill="#5a9a3c", outline="#3a7a1c", width=1, **kw)
    c.create_line(cx, cy+2*s2, cx, cy-6*s2, fill="#3a7a1c", width=max(1, int(2*s2)), **kw)
    c.create_oval(cx-4*s2, cy-8*s2, cx-1*s2, cy-5*s2, fill="#6aba4c", outline="", width=0, **kw)
    c.create_oval(cx+1*s2, cy-7*s2, cx+4*s2, cy-4*s2, fill="#6aba4c", outline="", width=0, **kw)


# ============ 季节性背景颜色 ============
SEASON_COLORS = {
    "春": "#c8ddb8",
    "夏": "#b8d4a4",
    "秋": "#e0cc98",
    "冬": "#d0d4d0",
}

def _draw_season_bg(canvas, cw, ch, season):
    """绘制季节性农场背景"""
    bg = SEASON_COLORS.get(season, "#d4e8c8")
    canvas.create_rectangle(0, 0, cw, ch, fill=bg, outline="")
    # 季节装饰（固定位置，用 season 做种子）
    import random as _r
    _r.seed(hash(season) % (2**31))
    decors = {"春": ["🌸", "🌼"], "夏": ["🌻", "☀️"], "秋": ["🍂", "🍁"], "冬": ["❄️", "⛄"]}
    emojis = decors.get(season, ["."])
    for _ in range(6):
        x = _r.randint(20, cw-20)
        y = _r.randint(20, ch-20)
        # 避开网格位置（放在网格间隙附近）
        e = _r.choice(emojis)
        canvas.create_text(x, y, text=e, font=("Microsoft YaHei", 8), fill="")


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

def _draw_bee(c, cx, cy, s=1.0):
    """蜜蜂"""
    c.create_oval(cx-9*s, cy-3*s, cx+9*s, cy+7*s, fill="#f0c040", outline="#d0a020", width=1)
    for dx in [-5, 0, 5]:
        c.create_line(cx+dx*s, cy-3*s, cx+dx*s, cy+7*s, fill="#333", width=max(1, int(2*s)))
    c.create_oval(cx-4*s, cy-9*s, cx+4*s, cy-3*s, fill="#f0e060", outline="#d0a020", width=1)
    c.create_oval(cx-1*s, cy-7*s, cx+2*s, cy-4*s, fill="#333", outline="", width=0)
    c.create_oval(cx-10*s, cy-8*s, cx-2*s, cy-2*s, fill="#e0e8ff", outline="#c0d0f0", width=1)
    c.create_oval(cx+2*s, cy-8*s, cx+10*s, cy-2*s, fill="#e0e8ff", outline="#c0d0f0", width=1)

def _draw_unicorn(c, cx, cy, s=1.0):
    """独角兽"""
    c.create_oval(cx-10*s, cy-4*s, cx+10*s, cy+8*s, fill="#f0f0f8", outline="#d0d0e0", width=1)
    c.create_polygon(cx+4*s, cy-4*s, cx+8*s, cy-14*s, cx+12*s, cy-14*s, cx+10*s, cy-4*s,
                     fill="#f0f0f8", outline="#d0d0e0", width=1)
    c.create_oval(cx+6*s, cy-16*s, cx+14*s, cy-8*s, fill="#f0f0f8", outline="#d0d0e0", width=1)
    c.create_polygon(cx+8*s, cy-16*s, cx+10*s, cy-26*s, cx+12*s, cy-16*s, fill="#ffd700", outline="#b8860b", width=1)
    c.create_oval(cx+10*s, cy-14*s, cx+12*s, cy-12*s, fill="#88ccff", outline="", width=0)
    c.create_line(cx+6*s, cy-14*s, cx+2*s, cy-10*s, cx+4*s, cy-4*s, fill="#e0e0e8", width=max(1, int(2*s)), smooth=True)
    c.create_line(cx-10*s, cy+2*s, cx-16*s, cy-2*s, fill="#e0e0e8", width=max(1, int(2*s)))
    c.create_oval(cx-12*s, cy-4*s, cx-8*s, cy, fill="#e0c0ff", outline="", width=0)
    for dx in [-6, -2, 2, 6]:
        c.create_line(cx+dx*s, cy+8*s, cx+dx*s, cy+13*s, fill="#e0e0e8", width=max(1, int(2*s)))

def _draw_dragon(c, cx, cy, s=1.0):
    """龙"""
    c.create_oval(cx-12*s, cy-6*s, cx+8*s, cy+8*s, fill="#30a030", outline="#208020", width=1)
    c.create_polygon(cx+6*s, cy-4*s, cx+14*s, cy-4*s, cx+12*s, cy+2*s, cx+8*s, cy,
                     fill="#30a030", outline="#208020", width=1)
    c.create_oval(cx+10*s, cy-6*s, cx+14*s, cy-2*s, fill="#30a030", outline="#208020", width=1)
    c.create_oval(cx+11*s, cy-5*s, cx+13*s, cy-3*s, fill="#ff0", outline="", width=0)
    for dx in [-8, -4, 0, 4]:
        c.create_polygon(cx+dx*s, cy-6*s, cx+dx*s+2*s, cy-12*s, cx+dx*s+4*s, cy-6*s, fill="#e04040", outline="#c02020", width=1)
    c.create_polygon(cx-6*s, cy-4*s, cx-16*s, cy-14*s, cx-10*s, cy-2*s, fill="#60c060", outline="#40a040", width=1)
    c.create_polygon(cx-10*s, cy-2*s, cx-18*s, cy-8*s, cx-12*s, cy, fill="#50b050", outline="#40a040", width=1)
    for dx in [-6, -2, 2, 6]:
        c.create_line(cx+dx*s, cy+8*s, cx+dx*s, cy+13*s, fill="#208020", width=max(1, int(2*s)))

ANIMAL_DRAW_FUNCS = {
    "鸡": _draw_chicken, "鸭": _draw_duck, "兔": _draw_rabbit, "鹅": _draw_goose,
    "羊": _draw_sheep, "猪": _draw_pig, "牛": _draw_cow,
    "羊驼": _draw_alpaca, "马": _draw_horse, "鹿": _draw_deer,
    "蜜蜂": _draw_bee, "独角兽": _draw_unicorn, "龙": _draw_dragon,
}


# ============ GUI ============
class FarmGUIv2:
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("开心农场 v3.0")
        self.root.geometry("1000x760")
        self.root.minsize(950, 720)
        self.root.configure(bg=COLORS["bg"])

        # 设置窗口图标和任务栏图标
        icon_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "南瓜农场.ico")
        if os.path.exists(icon_path):
            try:
                self.root.iconbitmap(default=icon_path)
            except Exception:
                pass
            self.root.after(100, self._set_taskbar_icon, icon_path)

        # 游戏数据（使用 v2 加载以包含养殖场数据）
        init_game()
        self.crops = load_crops()
        self.data = load_save_v2()

        # 离线收益（含养殖场）
        self._calc_offline_v2()

        # 变量
        self.land_canvas = None
        self.barn_canvas = None
        self.event_queue = []
        self._save_pending = False
        self._land_tip_window = None
        self._last_tip_lid = None
        self._last_tip_time = 0
        self._tip_after_id = None
        self.current_tab = "land"  # "land" or "barn"

        # F1 农场手册快捷键
        self.root.bind("<F1>", lambda e: self._show_help())

        # 创建界面
        self._create_top_bar()
        self._create_tab_bar()
        self._create_main_area()
        self._create_event_log()

        # 检查成就
        self._log("💡 欢迎回到开心农场 v3.0！")
        new_achs = check_achievements(self.data)
        if new_achs:
            self._log(f"🏆 达成 {new_achs} 个新成就！")

        # 自动保存 + 自动刷新
        self._schedule_auto_save()
        self._schedule_refresh()

        # 关闭事件
        self.root.protocol("WM_DELETE_WINDOW", self._on_close)

    def _set_taskbar_icon(self, icon_path):
        """延迟设置任务栏图标，确保窗口句柄已就绪"""
        try:
            import ctypes
            hwnd = self.root.winfo_id()
            if isinstance(hwnd, str):
                hwnd = int(hwnd, 16) if hwnd.startswith("0x") else int(hwnd)
            hwnd = int(hwnd)
            # LoadImage: IMAGE_ICON=1, LR_LOADFROMFILE=0x10
            hicon = ctypes.windll.user32.LoadImageW(None, icon_path, 1, 0, 0, 0x00000010)
            if hicon:
                # WM_SETICON: ICON_BIG=1, ICON_SMALL=0
                ctypes.windll.user32.SendMessageW(hwnd, 0x0080, 1, hicon)
                ctypes.windll.user32.SendMessageW(hwnd, 0x0080, 0, hicon)
        except Exception:
            pass

    # ==================== 多页地块辅助 ====================

    def _get_active_lands(self):
        """返回当前激活的地块页面的 lands 列表"""
        return self.data["lands_page2"] if self.data.get("active_land_page", 0) == 1 else self.data["lands"]

    def _get_active_unlocked(self):
        """返回当前激活的地块页面的已解锁数量"""
        return self.data.get("unlocked_lands_page2", 6) if self.data.get("active_land_page", 0) == 1 else self.data.get("unlocked_lands", 6)

    # ==================== 离线计算 ====================

    def _calc_offline_v2(self):
        """增强离线收益（含养殖场+农业建筑+工厂）"""
        # 1. 工厂加工状态离线检测
        check_factories_ready(self.data)

        # 2. 作物离线计算（含土地升级+天赋加速+暴风延时）
        gold, exp, count = calc_offline_crops_v2(self.data)

        # 3. 养殖场离线计算
        items, barn_exp = calc_barn_offline(self.data)

        # 4. 农业建筑离线计算（饲料/酿酒多批次加工）
        agro_produced, agro_batches = calc_offline_agro_v2(self.data)

        parts = []
        if count > 0:
            parts.append(f"作物收获 {count} 次，获得 {gold}💰")
        if items > 0:
            parts.append(f"养殖场产出 {items} 件")
        if agro_batches > 0:
            parts.append(f"农业建筑完成 {agro_batches} 批，产出 {agro_produced} 件")
        if parts:
            self._log(f"📦 离线收益：{'，'.join(parts)}")
            if barn_exp > 0:
                self._log(f"   养殖场获得 {barn_exp}✨（含离线加成）")

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
        for tab_id, text in [("land", "🌱 土地"), ("barn", "🐔 养殖场"), ("agro", "🏗️ 农业建筑")]:
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
            ("help", "📖 农场手册", self._show_help),
        ]:
            btn = tk.Button(tab_frame, text=text, font=F["button"],
                           command=cmd, bg=COLORS["btn_bg"],
                           activebackground=COLORS["btn_active"],
                           relief="raised", bd=1)
            btn.pack(side="right", padx=2)

    def _switch_tab(self, tab_id):
        """切换土地/养殖场/农业建筑标签"""
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

        # 农业建筑框架（隐藏）
        self.agro_container = tk.Frame(self.main_frame, bg=COLORS["bg"])
        self.agro_container.pack_forget()

        self._build_land_ui()
        self._build_barn_ui()
        self._build_agro_ui()

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

        # 地块1/地块2 切换按钮（土地状况下面的行）
        self._land_page_btns = {}
        page_btn_frame = tk.Frame(grid_container, bg=COLORS["bg"])
        page_btn_frame.pack(fill="x", pady=(0, 2))
        for pid, ptext in [(0, "地块1"), (1, "地块2")]:
            btn = tk.Button(page_btn_frame, text=ptext, font=F["button"],
                            command=lambda p=pid: self._switch_land_page(p),
                            relief="sunken" if pid == 0 else "raised",
                            bd=1, padx=8, pady=0,
                            bg="#d0e8ff" if pid == 0 else COLORS["btn_bg"])
            btn.pack(side="left", padx=1)
            self._land_page_btns[pid] = btn

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
            ("5", "🏪 商店", self._on_shop),
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
            ("breed", "🧬 繁殖", self._on_breed),
            ("warehouse", "📦 仓库", self._on_warehouse),
            ("talent", "⭐ 天赋", self._on_talents),
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

    # ==================== 农业建筑界面 ====================

    def _build_agro_ui(self):
        """构建农业建筑界面（左侧网格 + 右侧操作栏）"""
        # 顶部状态
        self.agro_status_frame = tk.Frame(self.agro_container, bg=COLORS["bg"])
        self.agro_status_frame.pack(fill="x", pady=(0, 5))

        self.agro_status_labels = {}
        for key, text in [
            ("usage", "🏗️ 建筑: 0/2"),
            ("processing", "⚙️ 加工中: 0"),
            ("ready", "✅ 待收取: 0"),
        ]:
            lbl = tk.Label(self.agro_status_frame, text=text,
                          font=F["normal"], bg=COLORS["bg"])
            lbl.pack(side="left", padx=(0, 25))
            self.agro_status_labels[key] = lbl

        # 中间主区域：左侧网格 + 右侧操作栏
        agro_main = tk.Frame(self.agro_container, bg=COLORS["bg"])
        agro_main.pack(fill="both", expand=True)

        # 左侧建筑网格
        self.agro_grid_frame = tk.Frame(agro_main, bg=COLORS["bg"])
        self.agro_grid_frame.pack(side="left", fill="both", expand=True)
        self._build_agro_grid()

        # 右侧操作栏（可滚动，与土地/养殖场侧边栏同宽）
        self.agro_action_frame = tk.Frame(agro_main, bg="#f5f5f5",
                                          width=230, relief="groove", bd=1)
        self.agro_action_frame.pack(side="right", fill="y", padx=(10, 0))
        self.agro_action_frame.pack_propagate(False)

        tk.Label(self.agro_action_frame, text="🏗️ 建筑操作", font=F["title"],
                 bg="#f5f5f5").pack(pady=(8, 3))

        action_canvas = tk.Canvas(self.agro_action_frame, bg="#f5f5f5",
                                  highlightthickness=0)
        action_scrollbar = tk.Scrollbar(self.agro_action_frame, orient="vertical",
                                        command=action_canvas.yview)
        self.agro_action_inner = tk.Frame(action_canvas, bg="#f5f5f5")

        def _on_canvas_configure(e):
            action_canvas.itemconfig(inner_id, width=e.width)
            action_canvas.configure(scrollregion=action_canvas.bbox("all"))

        self.agro_action_inner.bind("<Configure>", lambda e: action_canvas.configure(scrollregion=action_canvas.bbox("all")))
        action_canvas.bind("<Configure>", _on_canvas_configure)
        inner_id = action_canvas.create_window((0, 0), window=self.agro_action_inner, anchor="nw")
        action_canvas.configure(yscrollcommand=action_scrollbar.set)

        action_canvas.pack(side="left", fill="both", expand=True)
        action_scrollbar.pack(side="right", fill="y")

        agro_actions = [
            ("build", "🏗️ 建造工厂", self._on_build_agro),
            ("upgrade", "⬆️ 升级建筑", self._on_upgrade_agro),
            ("produce", "🔧 加工饲料", self._on_start_agro),
            ("collect", "📦 收取产品", self._on_collect_agro),
            ("unlock", "🔓 解锁地块", self._on_unlock_agro_slot),
            ("warehouse", "📦 仓库", self._on_warehouse),
            ("talent", "⭐ 天赋", self._on_talents),
        ]
        self.agro_action_btns = {}
        for key, text, cmd in agro_actions:
            btn = tk.Button(self.agro_action_inner, text=text, font=F["button"],
                           command=cmd, bg=COLORS["btn_bg"],
                           activebackground=COLORS["btn_active"],
                           relief="raised", bd=1, height=1)
            btn.pack(fill="x", padx=8, pady=3)
            self.agro_action_btns[key] = btn

        # 底部饲料库存
        self.agro_feed_info_frame = tk.Frame(self.agro_container, bg="#fafafa",
                                             height=28, relief="ridge", bd=1)
        self.agro_feed_info_frame.pack(side="bottom", fill="x", pady=(5, 0))
        self.agro_feed_info_frame.pack_propagate(False)
        self.agro_feed_info_label = tk.Label(self.agro_feed_info_frame, text="🍽️ 饲料库存: 空",
                                             font=F["small"], bg="#fafafa", anchor="w")
        self.agro_feed_info_label.pack(fill="x", padx=10, pady=2)

    def _build_agro_grid(self):
        """创建单 Canvas 农业建筑网格"""
        for w in self.agro_grid_frame.winfo_children():
            w.destroy()
        self.agro_canvas = tk.Canvas(self.agro_grid_frame, highlightthickness=0, bg=COLORS["bg"])
        self.agro_canvas.pack(fill="both", expand=True)
        self.agro_canvas.bind("<Button-1>", self._on_agro_click)
        self.agro_canvas.bind("<Configure>", lambda e: self._update_agro_grid())
        self._update_agro_grid()

    def _update_agro_grid(self):
        """在 Canvas 上绘制农业建筑网格"""
        if not hasattr(self, 'agro_canvas') or not self.agro_canvas:
            return
        self.agro_canvas.delete("all")
        d = self.data
        unlocked = d.get("unlocked_agro_buildings", INITIAL_AGRO_BUILDINGS)
        cw = self.agro_canvas.winfo_width() - 2
        ch = self.agro_canvas.winfo_height() - 2
        if cw < 50 or ch < 50:
            return
        cols, rows = 10, 5
        cell_w, cell_h = cw / cols, ch / rows

        for r in range(rows):
            for c in range(cols):
                sid = r * cols + c + 1
                x0, y0 = c * cell_w, r * cell_h
                x1, y1 = x0 + cell_w, y0 + cell_h
                cx, cy_ = (x0 + x1) / 2, (y0 + y1) / 2

                font_s = max(7, min(cell_w, cell_h) / 6)
                ft = ("Microsoft YaHei", int(font_s))
                ft2 = ("Microsoft YaHei", max(7, int(font_s) - 2))
                ft3 = ("Microsoft YaHei", max(6, int(font_s) - 4))

                if sid > unlocked:
                    self.agro_canvas.create_rectangle(x0, y0, x1, y1, fill="#ddd", outline="#ccc", width=1)
                    self.agro_canvas.create_text(cx, cy_, text=f"#{sid}\n🔒", font=ft, fill="#999", justify="center")
                    continue

                slots = d.get("agro_buildings", [])
                if sid > len(slots):
                    slot = {"building": None, "level": 1}
                else:
                    slot = slots[sid - 1]

                if not slot.get("building"):
                    bg_c, border = "#f0e6d3", "#c0b090"
                    self.agro_canvas.create_rectangle(x0, y0, x1, y1, fill=bg_c, outline=border, width=1)
                    # 编号靠上，空地靠下，拉开间距
                    self.agro_canvas.create_text(cx, cy_ - cell_h * 0.15, text=f"#{sid}", font=ft2, fill="#888", anchor="n")
                    self.agro_canvas.create_text(cx, cy_ + cell_h * 0.22, text="空地", font=ft2, fill="#999")
                else:
                    lv = slot.get("level", 1)
                    btype = slot.get("building", "feed_mill")
                    if btype == "feed_mill":
                        name = "加工厂"
                        idle_bg, idle_border = "#e8e8e8", "#c0c0c0"
                    else:
                        name = "酿酒厂"
                        idle_bg, idle_border = "#f5e6d3", "#d4a060"

                    if slot.get("order"):
                        done = slot.get("done_batches", 0)
                        total = slot.get("total_batches", 0)
                        order_name = slot["order"]
                        all_recipes = get_recipe_list(btype)
                        if slot.get("ready"):
                            bg_c, border = COLORS["land_ready"], "#90c090"
                            status_text = order_name
                            bottom_text = f"✅ {done}/{total}批"
                        else:
                            recipe = next((r for r in all_recipes if r["name"] == order_name), None)
                            if recipe and slot.get("start_time"):
                                st = parse_dt(slot["start_time"])
                                remain = recipe["time"] - (now_dt() - st).total_seconds() / 60.0
                                if remain > 0:
                                    m, sec = int(remain), int((remain - int(remain)) * 60)
                                    bottom_text = f"{m}:{sec:02d}"
                                else:
                                    bottom_text = f"{done}/{total}批"
                            else:
                                bottom_text = f"{done}/{total}批"
                            status_text = order_name
                            bg_c, border = COLORS["land_growing"], "#d0c080"
                    else:
                        bg_c, border = idle_bg, idle_border
                        status_text = "⬜ 空闲"
                        bottom_text = ""

                    self.agro_canvas.create_rectangle(x0, y0, x1, y1, fill=bg_c, outline=border, width=1)
                    # 顶部：建筑名
                    self.agro_canvas.create_text(cx, y0 + 4, text=name, font=ft3, fill="#333", anchor="n")
                    # 中间：加工物名称（或"空闲"）
                    self.agro_canvas.create_text(cx, cy_, text=status_text, font=ft2, fill="#333")
                    # 底部：时间（仿养殖场风格）
                    if bottom_text:
                        self.agro_canvas.create_text(cx, y1 - 4, text=bottom_text, font=ft2, fill="#333", anchor="s")

        # 更新状态栏
        self._update_agro_status()

    def _update_agro_status(self):
        """更新农业建筑状态信息"""
        d = self.data
        unlocked = d.get("unlocked_agro_buildings", INITIAL_AGRO_BUILDINGS)
        slots = d.get("agro_buildings", [])[:unlocked]
        built = sum(1 for s in slots if s.get("building"))
        processing = sum(1 for s in slots if s.get("order") and not s.get("ready"))
        ready = sum(1 for s in slots if s.get("ready"))

        if hasattr(self, 'agro_status_labels'):
            self.agro_status_labels["usage"].config(text=f"🏗️ 建筑: {built}/{unlocked}")
            self.agro_status_labels["processing"].config(text=f"⚙️ 加工中: {processing}")
            self.agro_status_labels["ready"].config(text=f"✅ 待收取: {ready}")

        feed_inv = d.get("inventory", {}).get("feeds", {})
        parts = [f"{k}:{v}" for k, v in feed_inv.items() if v > 0]
        if hasattr(self, 'agro_feed_info_label'):
            self.agro_feed_info_label.config(text=f"🍽️ 饲料库存: {' | '.join(parts) if parts else '空'}")

    def _on_agro_click(self, event):
        """点击农业建筑网格"""
        cw = self.agro_canvas.winfo_width()
        ch = self.agro_canvas.winfo_height()
        if cw < 50 or ch < 50:
            return
        col = int(event.x / cw * 10)
        row = int(event.y / ch * 5)
        sid = row * 10 + col + 1
        d = self.data
        unlocked = d.get("unlocked_agro_buildings", INITIAL_AGRO_BUILDINGS)

        if sid > unlocked:
            return  # 未解锁，忽略

        slots = d.get("agro_buildings", [])
        if sid > len(slots):
            return
        slot = slots[sid - 1]

        if not slot.get("building"):
            # 空地 → 弹出建造确认
            self._show_build_agro_dialog(sid)
        elif slot.get("ready"):
            # 有完成的产品 → 弹出收取确认
            self._show_collect_agro_dialog(sid)
        else:
            # 已建造 → 弹出详情对话框
            self._show_agro_detail_dialog(sid)

    # --------------------- 农业建筑弹窗 ---------------------

    def _show_build_agro_dialog(self, sid):
        """建造对话框（选择饲料加工厂或酿酒厂）"""
        d = self.data
        cost_feed = agro_build_cost("feed_mill")
        cost_brew = agro_build_cost("brewery")
        gold = d.get("gold", 0)

        win = tk.Toplevel(self.root)
        win.title(f"#{sid} 建造建筑")
        win.geometry("350x220")
        win.resizable(False, False)
        win.transient(self.root)
        win.grab_set()

        tk.Label(win, text=f"在 #{sid} 号地块建造：", font=F["title"]).pack(pady=(10, 10))

        btn_frame = tk.Frame(win)
        btn_frame.pack()

        can_feed = gold >= cost_feed
        can_brew = gold >= cost_brew
        tk.Button(btn_frame, text=f"🏭 饲料加工厂\n{cost_feed}💰",
                 font=F["button"], bg="#d4edda" if can_feed else "#f0f0f0",
                 command=lambda: self._do_build(sid, "feed_mill", win),
                 width=18, height=2).pack(side="left", padx=8)
        tk.Button(btn_frame, text=f"🍺 酿酒厂\n{cost_brew}💰",
                 font=F["button"], bg="#f5e6d3" if can_brew else "#f0f0f0",
                 command=lambda: self._do_build(sid, "brewery", win),
                 width=18, height=2).pack(side="left", padx=8)

        if not can_feed and not can_brew:
            tk.Label(win, text=f"❌ 金币不足（当前 {gold:,}）", font=F["normal"], fg="red").pack(pady=5)

        tk.Button(win, text="取消", font=F["button"],
                 command=win.destroy, bg="#f0f0f0", width=10).pack(pady=10)
        win.wait_window()

    def _do_build(self, sid, building_type, dialog):
        """执行建造"""
        d = self.data
        ok, msg = build_agro_building(d, sid - 1, building_type)
        if ok:
            self._log(f"🏗️ #{sid} {msg}")
            write_save_v2(d)
            dialog.destroy()
            self._update_ui()
        else:
            messagebox.showwarning("建造失败", msg)

    def _show_agro_detail_dialog(self, sid):
        """建筑详情对话框（升级/加工/收取）"""
        d = self.data
        slot = d["agro_buildings"][sid - 1]
        lv = slot.get("level", 1)
        btype = slot.get("building", "feed_mill")
        if btype == "brewery":
            building_name = "酿酒厂"
            emoji = "🍺"
            action_text = "🔧 开始酿造"
        else:
            building_name = "饲料加工厂"
            emoji = "🏭"
            action_text = "🔧 开始加工"

        recipes = get_available_recipes(lv, btype)
        recipe_names = ", ".join(r["name"] for r in recipes)

        win = tk.Toplevel(self.root)
        win.title(f"#{sid} {building_name} Lv.{lv}")
        win.geometry("420x320")
        win.resizable(False, False)
        win.transient(self.root)
        win.grab_set()

        tk.Label(win, text=f"{emoji} #{sid} {building_name}", font=F["title"]).pack(pady=(10, 3))
        tk.Label(win, text=f"等级：Lv.{lv}  可加工：{recipe_names}", font=F["normal"]).pack(pady=2)

        order = slot.get("order")
        if order:
            done = slot.get("done_batches", 0)
            total = slot.get("total_batches", 0)
            ready = slot.get("ready")
            status = f"✅ 已完成" if ready else f"⏳ 加工中"
            tk.Label(win, text=f"当前订单：{order} {done}/{total}批 {status}",
                    font=F["normal"], fg="#b8860b").pack(pady=3)

        btn_frame = tk.Frame(win)
        btn_frame.pack(pady=10)

        # 升级按钮
        if lv < 4:
            cost = agro_upgrade_cost(lv)
            if cost:
                can = "✅" if d.get("gold", 0) >= cost else "❌"
                tk.Button(btn_frame, text=f"⬆️ 升级到 Lv.{lv+1}（{cost}💰）{can}",
                         font=F["button"], command=lambda: self._do_upgrade_agro(sid, win),
                         bg="#fff3cd", width=28).pack(pady=3)

        # 加工按钮
        if not order or slot.get("ready"):
            tk.Button(btn_frame, text=action_text,
                     font=F["button"], command=lambda: self._show_start_agro_dialog(sid, win),
                     bg="#d4edda", width=28).pack(pady=3)

        # 收取按钮
        done = slot.get("done_batches", 0)
        if done > 0 or slot.get("ready"):
            tk.Button(btn_frame, text=f"📦 收取产品（{done}批已完成）",
                     font=F["button"], command=lambda: self._do_collect_agro(sid, win),
                     bg="#cce5ff", width=28).pack(pady=3)

        tk.Button(btn_frame, text="关闭", font=F["button"],
                 command=win.destroy, bg="#f0f0f0", width=28).pack(pady=10)

        win.wait_window()

    def _show_start_agro_dialog(self, sid, parent=None):
        """开始加工对话框（含数量滑块）"""
        d = self.data
        slot = d["agro_buildings"][sid - 1]
        lv = slot.get("level", 1)
        btype = slot.get("building", "feed_mill")
        if btype == "brewery":
            building_name = "酿酒厂"
            emoji = "🍺"
        else:
            building_name = "饲料加工厂"
            emoji = "🏭"
        recipes = get_available_recipes(lv, btype)

        if not recipes:
            messagebox.showwarning("加工", "没有可用的配方")
            return

        win = tk.Toplevel(parent or self.root)
        win.title(f"#{sid} 加工")
        win.geometry("450x380")
        win.resizable(False, False)
        win.transient(parent or self.root)
        win.grab_set()

        tk.Label(win, text=f"{emoji} #{sid} {building_name} Lv.{lv}", font=F["title"]).pack(pady=(8, 3))
        tk.Label(win, text="选择配方和数量：", font=F["bold"]).pack(pady=3)

        recipe_var = tk.StringVar(value=recipes[0]["name"])

        recipe_frame = tk.Frame(win)
        recipe_frame.pack(pady=5)
        for i, recipe in enumerate(recipes):
            inv = d["inventory"]["crops"]
            can = True
            ing_parts = []
            for ing_name, ing_qty in recipe["ingredients"].items():
                if ing_name == "任意水果":
                    have = sum(inv.get(f, 0) for f in FEED_FRUIT_NAMES)
                else:
                    have = inv.get(ing_name, 0)
                stock = f"(库存:{have})" if have > 0 else "(库存:0)"
                ing_parts.append(f"{ing_name}×{ing_qty}{stock}")
                if have < ing_qty:
                    can = False
            ing_text = ", ".join(ing_parts)
            prefix = "✅" if can else "❌"
            tk.Radiobutton(recipe_frame, text=f"{prefix} {recipe['name']} | {ing_text} | {recipe['time']}min/批 | 产{recipe['yield']}个",
                          variable=recipe_var, value=recipe["name"],
                          font=F["small"], anchor="w", justify="left",
                          command=lambda: update_max()).pack(anchor="w", pady=1)

        tk.Label(win, text="批次数量：", font=F["bold"]).pack(pady=(8, 2))
        qty_var = tk.IntVar(value=1)

        slider_frame = tk.Frame(win)
        slider_frame.pack()

        def update_max():
            recipe = next((r for r in recipes if r["name"] == recipe_var.get()), None)
            if recipe:
                max_batches = 999
                for ing_name, ing_qty in recipe["ingredients"].items():
                    if ing_name == "任意水果":
                        have = sum(inv.get(f, 0) for f in FEED_FRUIT_NAMES)
                    else:
                        have = inv.get(ing_name, 0)
                    max_batches = min(max_batches, have // ing_qty if ing_qty > 0 else 999)
                slider.config(to=max(max_batches, 1))
                qty_var.set(min(qty_var.get(), max_batches))

        def sub():
            v = qty_var.get()
            if v > 1:
                qty_var.set(v - 1)

        def add():
            v = qty_var.get()
            if v < int(slider.cget("to")):
                qty_var.set(v + 1)

        def sub5():
            v = qty_var.get()
            qty_var.set(max(1, v - 5))

        def add5():
            v = qty_var.get()
            qty_var.set(min(int(slider.cget("to")), v + 5))

        btn_row = tk.Frame(slider_frame)
        btn_row.pack()
        tk.Button(btn_row, text="-5", font=F["button"], width=3, command=sub5).pack(side="left", padx=2)
        tk.Button(btn_row, text="-", font=F["button"], width=3, command=sub).pack(side="left", padx=2)
        tk.Label(btn_row, textvariable=qty_var, font=("TkDefaultFont", 14, "bold"),
                width=5, anchor="center").pack(side="left", padx=8)
        tk.Button(btn_row, text="+", font=F["button"], width=3, command=add).pack(side="left", padx=2)
        tk.Button(btn_row, text="+5", font=F["button"], width=3, command=add5).pack(side="left", padx=2)

        slider = tk.Scale(win, from_=1, to=1, orient="horizontal",
                         variable=qty_var, length=350, font=F["small"])
        slider.pack(pady=5)

        yield_label = tk.Label(win, text="", font=F["bold"])
        yield_label.pack()

        def update_yield(*_):
            q = qty_var.get()
            recipe = next((r for r in recipes if r["name"] == recipe_var.get()), None)
            if recipe:
                total = recipe["yield"] * q
                total_time = recipe["time"] * q
                yield_label.config(text=f"预计产出：{recipe['name']}×{total}  总耗时：{total_time}分钟（{total_time/60:.1f}h）")

        qty_var.trace_add("write", update_yield)

        # 首次更新
        update_max()
        update_yield()

        def confirm():
            qty = qty_var.get()
            recipe_name = recipe_var.get()
            ok, msg = start_agro_production(d, sid - 1, recipe_name, qty)
            if ok:
                self._log(f"🔧 #{sid} {msg}")
                write_save_v2(d)
                win.destroy()
                if parent:
                    parent.destroy()
                self._update_ui()
            else:
                messagebox.showwarning("加工饲料", msg)

        tk.Button(win, text="✅ 开始加工", font=F["button"],
                 command=confirm, bg="#d4edda", width=15).pack(side="left", padx=(60, 10), pady=10)
        tk.Button(win, text="❌ 取消", font=F["button"],
                 command=win.destroy, bg="#f8d7da", width=15).pack(side="right", padx=(10, 60), pady=10)

        win.wait_window()

    def _show_collect_agro_dialog(self, sid):
        """收取产品对话框"""
        d = self.data
        slot = d["agro_buildings"][sid - 1]
        done = slot.get("done_batches", 0)
        btype = slot.get("building", "feed_mill")
        building_name = "酿酒厂" if btype == "brewery" else "饲料加工厂"

        # 先检查一下是否刚完成
        check_agro_ready(slot)
        done = slot.get("done_batches", 0)

        if done <= 0 and not slot.get("ready"):
            messagebox.showinfo("收取产品", "没有可收取的产品")
            return

        all_recipes = get_recipe_list(btype)
        recipe = next((r for r in all_recipes if r["name"] == slot["order"]), None)
        total_yield = recipe["yield"] * done if recipe else 0

        ok = messagebox.askyesno("收取产品",
            f"#{sid} {building_name} Lv.{slot.get('level', 1)}\n"
            f"已完成 {done} 批 {slot.get('order', '未知')}\n"
            f"预计获得：{slot.get('order', '未知')}×{total_yield}\n\n确定收取吗？")
        if ok:
            self._do_collect_agro(sid, None)

    def _do_collect_agro(self, sid, dialog=None):
        """执行收取"""
        d = self.data
        total, msg = collect_agro_product(d, sid - 1)
        if total > 0:
            self._log(f"📦 #{sid} 收取 {msg}")
            write_save_v2(d)
            if dialog:
                dialog.destroy()
            self._update_ui()
        else:
            messagebox.showwarning("收取产品", msg)

    def _do_upgrade_agro(self, sid, dialog=None):
        """执行升级"""
        d = self.data
        ok, msg = upgrade_agro_building(d, sid - 1)
        if ok:
            self._log(f"⬆️ #{sid} {msg}")
            write_save_v2(d)
            if dialog:
                dialog.destroy()
            self._update_ui()
        else:
            messagebox.showwarning("升级建筑", msg)

    # --------------------- 农业建筑操作按钮 ---------------------

    def _on_build_agro(self):
        """建造饲料加工厂"""
        d = self.data
        unlocked = d.get("unlocked_agro_buildings", INITIAL_AGRO_BUILDINGS)
        slots = d.get("agro_buildings", [])[:unlocked]
        # 找第一个空地
        for i, slot in enumerate(slots):
            if not slot.get("building"):
                self._show_build_agro_dialog(i + 1)
                return
        messagebox.showinfo("建造工厂", "所有已解锁地块都有建筑了，请先解锁新地块！")

    def _on_upgrade_agro(self):
        """升级建筑 - 需要先选择建筑"""
        d = self.data
        unlocked = d.get("unlocked_agro_buildings", INITIAL_AGRO_BUILDINGS)
        slots = d.get("agro_buildings", [])[:unlocked]
        built = [(i, s) for i, s in enumerate(slots) if s.get("building") and s.get("level", 1) < 4]
        if not built:
            messagebox.showinfo("升级建筑", "没有可升级的建筑（所有建筑已满级或无建筑）")
            return

        # 简单选择对话框
        win = tk.Toplevel(self.root)
        win.title("选择要升级的建筑")
        win.geometry("380x300")
        win.resizable(False, False)
        win.transient(self.root)
        win.grab_set()

        tk.Label(win, text="选择要升级的建筑：", font=F["bold"]).pack(pady=(8, 5))

        for idx, slot in built:
            lv = slot.get("level", 1)
            cost = agro_upgrade_cost(lv)
            can = "✅" if d.get("gold", 0) >= cost else "❌"
            sid = idx + 1
            btype = slot.get("building", "feed_mill")
            bname = "酿酒厂" if btype == "brewery" else "加工厂"
            tk.Button(win, text=f"#{sid} {bname} Lv.{lv} → Lv.{lv+1}（{cost}💰）{can}",
                     font=F["button"], command=lambda s=sid: self._do_upgrade_agro(s, win),
                     bg="#fff3cd", width=35, anchor="w").pack(pady=2)

        tk.Button(win, text="关闭", font=F["button"],
                 command=win.destroy, bg="#f0f0f0", width=15).pack(pady=10)
        win.wait_window()

    def _on_start_agro(self):
        """开始加工 - 需要先选择建筑"""
        d = self.data
        unlocked = d.get("unlocked_agro_buildings", INITIAL_AGRO_BUILDINGS)
        slots = d.get("agro_buildings", [])[:unlocked]
        available = [(i, s) for i, s in enumerate(slots) if s.get("building") and
                     (not s.get("order") or s.get("ready"))]
        if not available:
            messagebox.showinfo("加工饲料", "没有空闲的建筑")
            return

        if len(available) == 1:
            self._show_start_agro_dialog(available[0][0] + 1)
            return

        # 多个可选 → 选择对话框
        win = tk.Toplevel(self.root)
        win.title("选择加工建筑")
        win.geometry("400x280")
        win.resizable(False, False)
        win.transient(self.root)
        win.grab_set()

        tk.Label(win, text="选择要加工的建筑：", font=F["bold"]).pack(pady=(8, 5))

        for idx, slot in available:
            lv = slot.get("level", 1)
            btype = slot.get("building", "feed_mill")
            bname = "酿酒厂" if btype == "brewery" else "加工厂"
            recipes = get_available_recipes(lv, btype)
            recipe_names = ", ".join(r["name"] for r in recipes)
            sid = idx + 1
            tk.Button(win, text=f"#{sid} {bname} Lv.{lv} → 可加工：{recipe_names}",
                     font=F["button"], command=lambda s=sid: self._show_start_agro_dialog(s, win),
                     bg="#d4edda", width=40, anchor="w").pack(pady=2)

        tk.Button(win, text="关闭", font=F["button"],
                 command=win.destroy, bg="#f0f0f0", width=15).pack(pady=10)
        win.wait_window()

    def _on_collect_agro(self):
        """收取所有已完成的饲料"""
        d = self.data
        unlocked = d.get("unlocked_agro_buildings", INITIAL_AGRO_BUILDINGS)
        slots = d.get("agro_buildings", [])[:unlocked]
        ready_slots = [(i, s) for i, s in enumerate(slots) if s.get("ready") or s.get("done_batches", 0) > 0]

        if not ready_slots:
            messagebox.showinfo("收取产品", "没有可收取的产品")
            return

        total_all = 0
        msgs = []
        for idx, slot in ready_slots:
            total, msg = collect_agro_product(d, idx)
            if total > 0:
                total_all += total
                msgs.append(f"#{idx+1} {msg}")

        if total_all > 0:
            self._log(f"📦 收取产品：{', '.join(msgs)}")
            write_save_v2(d)
            self._update_ui()
        else:
            messagebox.showinfo("收取产品", "没有可收取的产品")

    def _on_unlock_agro_slot(self):
        """解锁农业建筑地块"""
        d = self.data
        unlocked = d.get("unlocked_agro_buildings", INITIAL_AGRO_BUILDINGS)
        if unlocked >= MAX_AGRO_BUILDINGS:
            messagebox.showinfo("解锁地块", "所有地块已解锁！")
            return

        cost = agro_unlock_cost(unlocked + 1)
        if d.get("gold", 0) < cost:
            messagebox.showwarning("解锁地块", f"金币不足！需要 {cost}💰\n当前金币：{d['gold']:,}")
            return

        ok = messagebox.askyesno("解锁地块",
            f"解锁第 {unlocked + 1} 号建筑地块\n费用：{cost}💰\n\n确定解锁吗？")
        if ok:
            d["gold"] = d.get("gold", 0) - cost
            d["unlocked_agro_buildings"] = unlocked + 1
            # 确保 slots 存在
            slots = d.get("agro_buildings", [])
            if unlocked < len(slots):
                slots[unlocked]["unlocked"] = True
            self._log(f"🔓 解锁农业建筑 #{unlocked + 1} 号地块，花费 {cost}💰")
            write_save_v2(d)
            self._update_ui()

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
        for c in (self.land_container, self.barn_container, self.agro_container):
            c.pack_forget()
        if tab_id == "land":
            self.land_container.pack(fill="both", expand=True)
        elif tab_id == "barn":
            self.barn_container.pack(fill="both", expand=True)
            self._update_barn_grid()
        else:
            self.agro_container.pack(fill="both", expand=True)
            self._update_agro_grid()

    def _switch_land_page(self, page):
        """切换地块1/地块2"""
        self.data["active_land_page"] = page
        for pid, btn in self._land_page_btns.items():
            active = pid == page
            btn.config(relief="sunken" if active else "raised",
                       bg="#d0e8ff" if active else COLORS["btn_bg"])
        self._update_land_grid()
        self._update_ui()

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
            active_lands = self._get_active_lands()
            active_unlocked = self._get_active_unlocked()
            planted = sum(1 for l in active_lands[:active_unlocked] if l["crop"])
            factories_ready = sum(1 for f in FACTORY_LIST if d["factories"][f["factory"]].get("ready"))

            # 养殖场统计
            unlocked_barns = d.get("unlocked_barns", INITIAL_BARNS)
            occupied = sum(1 for b in d.get("barns", [])[:unlocked_barns] if b["animal"] is not None)
            pending = sum(b.get("pending_product", 0) for b in d.get("barns", [])[:unlocked_barns])
            feed_total = sum(d.get("inventory", {}).get("feeds", {}).values())

            self.status_labels["season"].config(text=f"🌸 {season}季")
            self.status_labels["land_usage"].config(text=f"🌱 {planted}/{active_unlocked}")
            self.status_labels["barn_usage"].config(text=f"🐔 {occupied}/{unlocked_barns}")
            self.status_labels["barn_pending"].config(text=f"📦 待收:{pending}")
            self.status_labels["factories"].config(text=f"🏭 {factories_ready}")
            self.status_labels["save_time"].config(text=f"💾 {d['last_save_time'][5:16]}")

            # 土地网格
            self._update_land_grid()

            # 养殖场网格
            self._update_barn_grid()
            self._update_barn_status()

            # 农业建筑网格
            self._update_agro_grid()

            # 检查工厂完成
            check_factories_ready(d)

            # 检查饲料厂完成
            check_feed_factory_ready(d)

            # 检查幼崽成熟
            check_baby_mature(d)

            # 养殖场生产
            process_barn_production(d)

            # 检查事件预警
            pending = d.get("_pending_warning")
            if pending:
                self._show_event_warning(d, pending)

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
        """在 Canvas 上绘制土地网格（木框 + 生长阶段 + 季节性背景）"""
        if not hasattr(self, "land_canvas") or not self.land_canvas:
            return
        self.land_canvas.delete("all")
        if hasattr(self.land_canvas, "_img_refs"):
            self.land_canvas._img_refs.clear()
        d = self.data
        active_lands = self._get_active_lands()
        active_unlocked = self._get_active_unlocked()
        now = now_dt()
        season, _ = get_season(d)
        cw = self.land_canvas.winfo_width() - 2
        ch = self.land_canvas.winfo_height() - 2
        if cw < 50 or ch < 50:
            return
        cols, rows = 10, 5
        cell_w, cell_h = cw / cols, ch / rows

        # 绘制季节性背景
        _draw_season_bg(self.land_canvas, cw, ch, season)

        for r in range(rows):
            for c in range(cols):
                lid = r * cols + c + 1
                x0, y0 = c * cell_w, r * cell_h
                x1, y1 = x0 + cell_w, y0 + cell_h
                cx, cy_ = (x0 + x1) / 2, (y0 + y1) / 2
                tag = "land_" + str(lid)

                font_s = max(7, min(cell_w, cell_h) / 6)
                ft = ("Microsoft YaHei", int(font_s))
                ft2 = ("Microsoft YaHei", max(7, int(font_s) - 2))
                ft_small = ("Microsoft YaHei", max(6, int(font_s) - 4))
                corner_r = max(3, min(cell_w, cell_h) * 0.06)

                # ---- 锁定地块 ----
                if lid > active_unlocked:
                    _round_rect(self.land_canvas, x0, y0, x1, y1, corner_r,
                                fill="#ddd", outline="#bbb", width=1, tags=(tag,))
                    self.land_canvas.create_text(cx, cy_, text=f"#{lid}\n🔒",
                                                 font=ft, fill="#999", justify="center", tags=(tag,))
                    continue

                land = active_lands[lid - 1]
                lv_show = land.get("upgrade_level", 1)

                # 外框（浅色边框）
                _round_rect(self.land_canvas, x0, y0, x1, y1, corner_r,
                            fill="#d0d0d0", outline="", width=0, tags=(tag,))

                # ---- 空地 ----
                if not land["crop"]:
                    pad_soil = 3
                    soil_corner = max(2, corner_r - 2)
                    _round_rect(self.land_canvas, x0+pad_soil, y0+pad_soil, x1-pad_soil, y1-pad_soil, soil_corner,
                                fill=COLORS["barn_empty"], outline="", width=0, tags=(tag,))
                    icon_s = int(min(cell_w, cell_h) * 0.33)
                    self.land_canvas.create_text(cx, cy_ - 2, text="🌱",
                                                 font=("Microsoft YaHei", icon_s), tags=(tag,))
                else:
                    # ---- 有作物 ----
                    pt = parse_dt(land["plant_time"])
                    growth_total = calc_growth_time(land["crop"], land["upgrade_level"], d["talent_tree"])
                    if land.get("golden_pumpkin"):
                        growth_total *= 2
                    remain = growth_total - (now - pt).total_seconds() / 60.0
                    name = land["crop"]
                    is_golden = land.get("golden_pumpkin", False)
                    is_ready = remain <= 0
                    stage = _calc_stage(remain, growth_total)

                    # 内层背景色（按状态）
                    pad_soil = 3
                    soil_corner = max(2, corner_r - 2)
                    _round_rect(self.land_canvas, x0+pad_soil, y0+pad_soil, x1-pad_soil, y1-pad_soil, soil_corner,
                                fill=COLORS["land_ready"] if is_ready else COLORS["land_growing"],
                                outline="", width=0, tags=(tag,))

                    # 状态边框
                    if is_ready:
                        # 金色收获边框
                        _round_rect(self.land_canvas, x0-1, y0-1, x1+1, y1+1, corner_r+1,
                                    fill="", outline="#d4a030", width=3, tags=(tag,))
                    else:
                        # 绿色生长指示（土壤内缘）
                        _round_rect(self.land_canvas, x0+pad_soil-1, y0+pad_soil-1,
                                    x1-pad_soil+1, y1-pad_soil+1, soil_corner+1,
                                    fill="", outline="#5a8a3c", width=1, tags=(tag,))

                    # 作物图标（按生长阶段，1.5倍）
                    size = min(cell_w, cell_h) * 0.975
                    s = size / 32
                    draw_name = "金色南瓜" if is_golden else name
                    cy_crop = cy_ - (1 if stage >= 2 else 2)
                    if not _draw_crop_staged(self.land_canvas, cx, cy_crop, s, draw_name, stage, tags=(tag,)):
                        # 回退到原绘制函数
                        draw_func = CROP_DRAW_FUNCS.get(draw_name)
                        if draw_func:
                            s_stage = s * _STAGE_SCALES[stage]
                            draw_func(self.land_canvas, cx, cy_crop, s_stage if stage < 3 else s)

                    # 底部状态（仿养殖场风格）
                    if is_ready:
                        self.land_canvas.create_text(cx, y1 - 4, text="✨" if is_golden else "✓",
                                                     font=ft2,
                                                     fill="#d4a030" if is_golden else "#4a9e5f",
                                                     anchor="s", tags=(tag,))
                    else:
                        m, sec = int(remain), int((remain - int(remain)) * 60)
                        self.land_canvas.create_text(cx, y1 - 4, text=f"{m}:{sec:02d}",
                                                     font=ft2, fill="#333", anchor="s", tags=(tag,))

        # 工具提示事件绑定
        self.land_canvas.bind("<Motion>", self._on_land_hover)
        self.land_canvas.bind("<Leave>", self._hide_land_tip)

    # ============ 土地悬浮 Tooltip ============
    def _on_land_hover(self, event):
        """鼠标悬停时根据坐标计算地块编号"""
        if not hasattr(self, 'land_canvas') or not self.land_canvas:
            return
        cw = self.land_canvas.winfo_width() - 2
        ch = self.land_canvas.winfo_height() - 2
        if cw < 50 or ch < 50:
            self._hide_land_tip()
            return
        cols, rows = 10, 5
        c = int(event.x / (cw / cols))
        r = int(event.y / (ch / rows))
        if c < 0 or c >= cols or r < 0 or r >= rows:
            self._hide_land_tip()
            return
        lid = r * cols + c + 1
        if lid < 1 or lid > len(self._get_active_lands()):
            self._hide_land_tip()
            return
        # 锁定地块不显示
        if lid > self._get_active_unlocked():
            self._hide_land_tip()
            return
        # 取消未执行的延迟显示
        if hasattr(self, '_tip_after_id'):
            try:
                self.root.after_cancel(self._tip_after_id)
            except Exception:
                pass
        # 延迟 300ms 显示，避免工具窗触发 Leave 事件导致闪烁
        self._tip_after_id = self.root.after(300, self._show_land_tip, event.x_root, event.y_root, lid)

    def _show_land_tip(self, rx, ry, lid):
        """显示悬浮信息窗"""
        self._hide_land_tip()
        land = self._get_active_lands()[lid - 1]
        lines = [f" 第{lid}号地块 "]
        if land.get("crop"):
            name = land["crop"]
            lv = land.get("upgrade_level", 1)
            lines.append(f" 作物：{name}")
            lines.append(f" 等级：Lv.{lv}")
            pt = parse_dt(land["plant_time"])
            growth = calc_growth_time(name, lv, self.data.get("talent_tree", {}))
            if land.get("golden_pumpkin"):
                growth *= 2
            remain = growth - (now_dt() - pt).total_seconds() / 60.0
            if remain <= 0:
                lines.append(" ✅ 可收获！")
            else:
                m, s = int(remain), int((remain - int(remain)) * 60)
                lines.append(f" ⏱ {m}分{s}秒")
            # 产量加成
            multi = calc_yield_multiplier(name, lv, self.data["talent_tree"])
            if multi > 1:
                lines.append(f" ✖{multi:.1f}倍产量")
        else:
            lines.append(" 空地")
        win = tk.Toplevel(self.root)
        win.wm_overrideredirect(True)
        win.wm_geometry(f"+{rx+12}+{ry+8}")
        win.attributes("-topmost", True)
        frame = tk.Frame(win, bg="#2a2a2a", bd=0, highlightbackground="#5a3a1c", highlightthickness=1)
        frame.pack(fill="both", padx=1, pady=1)
        for line in lines:
            tk.Label(frame, text=line, bg="#2a2a2a", fg="#eee",
                     font=("Microsoft YaHei", 9), padx=8, pady=1, anchor="w").pack(fill="x")
        self._land_tip_window = win

    def _hide_land_tip(self, event=None):
        """隐藏悬浮信息窗"""
        # 取消未执行的延迟显示
        if hasattr(self, '_tip_after_id') and self._tip_after_id:
            try:
                self.root.after_cancel(self._tip_after_id)
            except Exception:
                pass
            self._tip_after_id = None
        w = getattr(self, '_land_tip_window', None)
        if w:
            try:
                w.destroy()
            except Exception:
                pass
            self._land_tip_window = None

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
        feed_inv = d.get("inventory", {}).get("feeds", {})
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
        """南瓜首次成熟时2%概率变金色南瓜，每轮种植一次判定"""
        d = self.data
        now = now_dt()
        triggered = False
        # 检查所有页面的南瓜，避免页面切换导致判定遗漏
        all_lands = [
            (d["lands"], d.get("unlocked_lands", 6)),
            (d.get("lands_page2", []), d.get("unlocked_lands_page2", 6)),
        ]
        for lands, unlocked in all_lands:
            for land in lands[:unlocked]:
                if land.get("crop") != "南瓜":
                    continue
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
                    continue
                land["_maturity_roll_done"] = True
                if random.random() < 0.03:
                    land["golden_pumpkin"] = True
                    land["plant_time"] = now_str()
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
        if lid > len(self._get_active_lands()) or lid > self._get_active_unlocked():
            return
        land = self._get_active_lands()[lid - 1]
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
        land = self._get_active_lands()[lid - 1]
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
        avail = [(n, c) for n, c in self.crops.items() if d["level"] >= c["level"] and not c.get("hidden")]
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

        inv = d.get("seed_bag", {})
        plant_lands = self._get_active_lands()
        plant_unlocked = self._get_active_unlocked()

        def do_plant_crop(name):
            if inv.get(name, 0) <= 0:
                messagebox.showwarning("种子不足", f"{name} 种子不足，请先购买")
                return
            lands_to_plant = []
            if lid is not None:
                lands_to_plant = [lid]
            else:
                free = [l["id"] for l in plant_lands[:plant_unlocked] if not l["crop"]]
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
                plot = plant_lands[plot_id - 1]
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
        avail = [(n, c) for n, c in self.crops.items() if d["level"] >= c["level"] and not c.get("hidden")]
        if not avail:
            messagebox.showinfo("提示", "没有可购买的种子")
            return

        dialog = tk.Toplevel(parent)
        dialog.title("🛒 购买种子")
        dialog.geometry("400x400")
        dialog.transient(parent)
        dialog.grab_set()

        gold_label = tk.Label(dialog, text=f"金币: {d['gold']:,}", font=F["bold"])
        gold_label.pack(pady=10)

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
            qty = self._quantity_dialog(f"购买 {name}", parent=dialog, unit_price=price, gold=d["gold"])
            if not qty:
                return
            cost = price * qty
            if d["gold"] < cost:
                messagebox.showwarning("金币不足", f"需要 {cost}💰，当前 {d['gold']}💰")
                return
            d["gold"] -= cost
            inv = d.get("seed_bag", {})
            inv[name] = inv.get(name, 0) + qty
            self._log(f"🛒 购买 {name}种子×{qty}，花费 {cost}💰")
            gold_label.config(text=f"金币: {d['gold']:,}")
            _rebuild_buttons()

        def _rebuild_buttons():
            for child in scroll_frame.winfo_children():
                child.destroy()
            for i, (n, c) in enumerate(avail, 1):
                discount = get_talent_value(d["talent_tree"], "seed_discount")
                price = int(c["seed_price"] * (1.0 - discount))
                can = d["gold"] >= price
                text = f"{i}. {n}  {price}💰  {'✅' if can else '❌'}"
                btn = tk.Button(scroll_frame, text=text, font=F["small"],
                                anchor="w", padx=5,
                                command=lambda x=n, p=price: buy(x, p),
                                bg="#fff", relief="groove", bd=1,
                                state="normal" if can else "disabled")
                btn.pack(fill="x", padx=5, pady=2)

        _rebuild_buttons()

    def _quantity_dialog(self, title, min_v=1, max_v=999, parent=None, unit_price=None, gold=None):
        """带 +/- 按钮的数量选择对话框，传入 unit_price+gold 会显示 Max 按钮"""
        win = tk.Toplevel(parent or self.root)
        win.title(title)
        win.geometry("400x160")
        win.resizable(False, False)
        win.transient(parent or self.root)
        win.grab_set()

        result = [None]
        tk.Label(win, text="选择数量:", font=F["bold"]).pack(pady=(8, 3))

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

        def set_max():
            if unit_price is not None and gold is not None and unit_price > 0:
                qty_var.set(max(min_v, min(max_v, gold // unit_price)))

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
        if unit_price is not None and gold is not None:
            max_qty = gold // unit_price if unit_price > 0 else max_v
            tk.Button(frame, text="Max", font=F["button"], width=3,
                      command=set_max, bg="#cce5ff", fg="#004085").pack(side="left", padx=2)

        btn_frame = tk.Frame(win)
        btn_frame.pack(pady=(6, 0))

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

        active_lands = self._get_active_lands()
        active_unlocked = self._get_active_unlocked()
        for land in active_lands[:active_unlocked]:
            # 金色南瓜必须跳过
            if land.get("golden_pumpkin"):
                continue
            if not land["crop"] or not land["plant_time"]:
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
            # 累积式产量（含 yield_remainder）
            qty = calc_harvest_yield(land, 1.0, ym)

            # 虫灾减产处理
            if land.get("_pest_reduced_yield"):
                qty = land["_pest_reduced_yield"]
                land["_pest_reduced_yield"] = None

            # 幸运四叶草 +50% 双倍概率
            dc = get_double_chance(land["upgrade_level"], d["talent_tree"])
            if d.get("lucky_clover"):
                dc += 0.5
                d["lucky_clover"] = False
            if random.random() < dc:
                qty *= 2
            if d.get("event_active", {}).get("golden_hour"):
                qty *= 2

            inv = d["inventory"]["crops"]
            inv[land["crop"]] = inv.get(land["crop"], 0) + qty
            total_qty += qty
            total_exp += c["exp"]
            count += 1
            # 天赋果实掉落检查
            if check_talent_fruit_drop(d):
                self._log("🍎 获得稀有掉落：天赋果实！")

            land["crop"] = None
            land["plant_time"] = None
            land["_wind_delay"] = 0

        if count == 0:
            self._log("🌾 没有可收获的作物")
        else:
            exp_bonus = apply_exp_bonus(d)
            d["exp"] += int(total_exp * exp_bonus)
            d["total_harvests"] += count
            try_level_up(d)
            self._log(f"🌾 收获 {count} 块地，获得 {total_qty} 件作物，{int(total_exp * exp_bonus)}✨")
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

        def _refresh_shop_gold():
            for w in dialog.winfo_children():
                if isinstance(w, tk.Label) and "🏪 商店" in w.cget("text"):
                    w.config(text=f"🏪 商店  金币: {d['gold']:,}  等级: {d['level']}")
                    break

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

        def _rebuild_seed_buttons():
            for w in seed_inner.winfo_children():
                w.destroy()
            for i, (n, c) in enumerate(self.crops.items(), 1):
                if c.get("hidden"):
                    continue
                unlocked = d["level"] >= c["level"]
                if unlocked:
                    discount = get_talent_value(d["talent_tree"], "seed_discount") + merchant_disc
                    price = int(c["seed_price"] * (1.0 - discount))
                    can = d["gold"] >= price
                    disc_tag = "🔥" if merchant_disc > 0 else ""
                    inv_count = d.get("seed_bag", {}).get(n, 0)
                    text = f"{disc_tag}{i}. {n}  {price}💰  库存:{inv_count}"

                    def buy_seed(name=n, p=price):
                        qty = self._quantity_dialog(f"购买 {name}", parent=dialog, unit_price=p, gold=d["gold"])
                        if not qty:
                            return
                        cost = p * qty
                        if d["gold"] < cost:
                            messagebox.showwarning("金币不足", f"需要 {cost}💰")
                            return
                        d["gold"] -= cost
                        d["seed_bag"][name] = d.get("seed_bag", {}).get(name, 0) + qty
                        self._log(f"🛒 购买 {name}种子×{qty}，花费 {cost}💰")
                        _refresh_shop_gold()
                        _rebuild_seed_buttons()

                    btn = tk.Button(seed_inner, text=text, font=F["small"],
                                    anchor="w", padx=5,
                                    command=buy_seed if can else None,
                                    bg="#fff" if can else "#eee",
                                    state="normal" if can else "disabled",
                                    relief="groove", bd=1)
                else:
                    text = f"🔒 {i}. {n}  需Lv.{c['level']}"
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

        def _rebuild_animal_buttons():
            for w in animal_inner.winfo_children():
                w.destroy()
            for i, a in enumerate(BARN_ANIMALS_LIST, 1):
                if a.get("hidden"):
                    continue
                unlocked = d["level"] >= a["level"]
                discount = 1.0 - get_talent_value(d["talent_tree"], "animal_discount")
                price = int(a["price"] * discount)
                can = unlocked and d["gold"] >= price
                if not unlocked:
                    text = f"🔒 {i}. {a['name']}  需Lv.{a['level']}  {a['price']}💰"
                    btn = tk.Button(animal_inner, text=text, font=F["small"],
                                    anchor="w", padx=5, state="disabled",
                                    bg="#eee", relief="groove", bd=1)
                else:
                    owned = sum(1 for b in d["barns"] if b.get("animal") == a["name"])
                    text = f"{i}. {a['name']}  {price}💰  拥有:{owned}"

                    def buy_animal(name=a["name"]):
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
                        _refresh_shop_gold()
                        _rebuild_animal_buttons()

                    btn = tk.Button(animal_inner, text=text, font=F["small"],
                                    anchor="w", padx=5,
                                    command=buy_animal if can else None,
                                    bg="#fff" if can else "#f0f0f0",
                                    state="normal" if can else "disabled",
                                    relief="groove", bd=1)
                btn.pack(fill="x", padx=5, pady=2)

        _rebuild_seed_buttons()
        _rebuild_animal_buttons()

        # ---- 饲料商店标签页 ----
        feed_frame = tk.Frame(notebook, bg=COLORS["bg"])
        notebook.add(feed_frame, text="🍽️ 饲料")

        # 饲料定价：直接购买比自行加工贵，但喂养后产出仍有利可图
        FEED_SHOP_PRICES = {
            "基础饲料": 8,
            "精制饲料": 35,
            "高级饲料": 300,
            "特殊饲料": 780,
        }

        feed_canvas = tk.Canvas(feed_frame, bg=COLORS["bg"], highlightthickness=0)
        feed_scroll = tk.Scrollbar(feed_frame, orient="vertical", command=feed_canvas.yview)
        feed_inner = tk.Frame(feed_canvas, bg=COLORS["bg"])
        feed_inner.bind("<Configure>", lambda e: feed_canvas.configure(scrollregion=feed_canvas.bbox("all")))
        feed_canvas.create_window((0, 0), window=feed_inner, anchor="nw")
        feed_canvas.configure(yscrollcommand=feed_scroll.set)
        feed_canvas.pack(side="left", fill="both", expand=True)
        feed_scroll.pack(side="right", fill="y")

        # 饲料说明
        feed_info_text = (
            "🍽️ 直接购买饲料比自行加工更贵，但省去种植加工时间\n"
            "💰 饲料价格参考：加工成本（种子价）< 商店价 < 动物产出价"
        )
        tk.Label(feed_inner, text=feed_info_text, font=F["small"],
                 bg="#fff3cd", fg="#856404", anchor="w", justify="left",
                 padx=5, pady=3).pack(fill="x", padx=5, pady=(5, 3))

        def _rebuild_feed_buttons():
            for w in feed_inner.winfo_children():
                if isinstance(w, tk.Frame) and hasattr(w, '_is_feed_btn_frame'):
                    w.destroy()
            for feed_name, price in FEED_SHOP_PRICES.items():
                can = d["gold"] >= price
                inv_count = d.get("inventory", {}).get("feeds", {}).get(feed_name, 0)
                text = f"{feed_name}  {price}💰/份  库存: {inv_count}"

                def buy_feed(name=feed_name, p=price):
                    qty = self._quantity_dialog(f"购买 {name}", parent=dialog, unit_price=p, gold=d["gold"])
                    if not qty:
                        return
                    cost = p * qty
                    if d["gold"] < cost:
                        messagebox.showwarning("金币不足", f"需要 {cost}💰")
                        return
                    d["gold"] -= cost
                    feed_inv = d.setdefault("inventory", {}).setdefault("feeds", {})
                    feed_inv[name] = feed_inv.get(name, 0) + qty
                    self._log(f"🛒 购买 {name}×{qty}，花费 {cost}💰")
                    _refresh_shop_gold()
                    _rebuild_feed_buttons()

                btn_frame = tk.Frame(feed_inner, bg=COLORS["bg"])
                btn_frame._is_feed_btn_frame = True
                btn_frame.pack(fill="x", padx=5, pady=2)

                btn = tk.Button(btn_frame, text=text, font=F["small"],
                                anchor="w", padx=5,
                                command=buy_feed if can else None,
                                bg="#fff" if can else "#eee",
                                state="normal" if can else "disabled",
                                relief="groove", bd=1)
                btn.pack(fill="x")

        _rebuild_feed_buttons()

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

    def _calc_warehouse_value(self, d):
        """计算仓库所有库存的总售价"""
        total = 0
        locked = d.setdefault("locked", {"crops": [], "products": [], "seeds": [], "feeds": []})
        # 种子
        for name, qty in d.get("seed_bag", {}).items():
            if qty > 0 and name not in locked["seeds"]:
                c = self.crops.get(name, {})
                total += qty * int(c.get("seed_price", 0) * 0.5)
        # 作物
        for name, qty in d["inventory"].get("crops", {}).items():
            if qty > 0 and name not in locked["crops"]:
                if name == "金色南瓜":
                    price = int(12000 * (1.0 + get_talent_value(d["talent_tree"], "sell_bonus")))
                else:
                    c = self.crops.get(name, {})
                    price = int(c.get("sell_price", 0) * (1.0 + get_talent_value(d["talent_tree"], "sell_bonus")))
                total += qty * price
        # 加工品/动物产品
        for name, qty in d["inventory"].get("products", {}).items():
            if qty > 0 and name not in locked["products"]:
                pf = next((x for x in FACTORY_LIST if x["product"] == name), None)
                if pf:
                    total += qty * pf["sell_price"]
                    continue
                an = next((a for a in BARN_ANIMALS_LIST if a["product"] == name), None)
                if an:
                    total += qty * an["sell_price"]
        # 饲料
        feed_prices = {"基础饲料": 15, "精制饲料": 30, "高级饲料": 60, "特殊饲料": 120}
        for name, qty in d["inventory"].get("feeds", {}).items():
            if qty > 0 and name not in locked.get("feeds", []):
                total += qty * feed_prices.get(name, 0)
        return total

    def _on_warehouse(self):
        """仓库（勾选·锁定·批量出售）"""
        d = self.data
        d.setdefault("locked", {"crops": [], "products": [], "seeds": [], "feeds": []})
        locked = d["locked"]

        dialog = tk.Toplevel(self.root)
        dialog.title("📦 仓库")
        dialog.geometry("720x520")
        dialog.transient(self.root)
        dialog.grab_set()

        # ── 状态变量 ──
        cb_vars = {}          # {(cat, name): BooleanVar}
        sel_info = {"qty": 0}  # 选中总件数

        def update_sel_label(lb):
            lb.config(text=f"☑ 已选 {sel_info['qty']} 件")

        # ── 顶栏 ──
        top = tk.Frame(dialog, bg=COLORS["bg"])
        top.pack(fill="x", padx=10, pady=(10, 2))
        usage = inventory_usage(d)
        total_v = self._calc_warehouse_value(d)
        tk.Label(top, text=f"📦 仓库 ({usage}/{warehouse_capacity(d)})", font=F["bold"],
                 bg=COLORS["bg"]).pack(side="left")
        tk.Label(top, text=f"  金币: {d['gold']:,}  ", font=F["bold"],
                 bg=COLORS["bg"]).pack(side="left")
        tk.Label(top, text=f"总价值: {total_v:,}💰", font=F["bold"],
                 bg=COLORS["bg"]).pack(side="left")

        # ── 操作栏 ──
        act = tk.Frame(dialog, bg=COLORS["bg"])
        act.pack(fill="x", padx=10, pady=5)

        sel_label = tk.Label(act, text="☑ 已选 0 件", font=F["small"], bg=COLORS["bg"])
        sel_label.pack(side="left", padx=2)

        def batch_sell():
            items = []
            for (cat, name), var in cb_vars.items():
                if cat == "seeds":
                    have = d.get("seed_bag", {}).get(name, 0)
                else:
                    have = d["inventory"][cat].get(name, 0)
                if var.get() and have > 0:
                    items.append((cat, name))
            if not items:
                return
            total_gold = 0
            total_qty = 0
            for cat, name in items:
                if cat == "seeds":
                    qty = d.get("seed_bag", {}).get(name, 0)
                else:
                    qty = d["inventory"][cat].get(name, 0)
                if qty <= 0:
                    continue
                price = _get_price(cat, name)
                total_gold += qty * price
                total_qty += qty
                if cat == "seeds":
                    del d["seed_bag"][name]
                else:
                    del d["inventory"][cat][name]
            d["gold"] += total_gold
            d["total_earnings"] += total_gold
            self._log(f"💰 批量出售 {total_qty} 件，获得 {total_gold}💰")
            write_save_v2(d)
            _rebuild_list()
            self._update_ui()

        tk.Button(act, text="✅ 出售选中", font=F["button"],
                  command=batch_sell, bg="#d4edda").pack(side="left", padx=2)

        def sell_all(cat, label):
            if cat == "seeds":
                inv = d.get("seed_bag", {})
            else:
                inv = d["inventory"][cat]
            locked_items = locked.get(cat, [])
            total_gold = 0
            total_qty = 0
            for name, qty in list(inv.items()):
                if name in locked_items or qty <= 0:
                    continue
                price = _get_price(cat, name)
                total_gold += qty * price
                total_qty += qty
                del inv[name]
            if total_qty > 0:
                d["gold"] += total_gold
                d["total_earnings"] += total_gold
                write_save_v2(d)
                self._log(f"💰 出售所有{label} {total_qty} 件，获得 {total_gold}💰")
            else:
                self._log(f"📦 没有{label}可出售")
            _rebuild_list()
            self._update_ui()

        tk.Button(act, text="🌾 出售所有作物", font=F["button"],
                  command=lambda: sell_all("crops", "作物"),
                  bg="#d4edda").pack(side="left", padx=2)
        tk.Button(act, text="📦 出售所有加工品", font=F["button"],
                  command=lambda: sell_all("products", "加工品"),
                  bg="#cce5ff").pack(side="left", padx=2)
        tk.Button(act, text="🍽️ 出售所有饲料", font=F["button"],
                  command=lambda: sell_all("feeds", "饲料"),
                  bg="#fff3cd").pack(side="left", padx=2)

        # ── 滚动列表 ──
        outer = tk.Frame(dialog)
        outer.pack(fill="both", expand=True, padx=10, pady=5)

        canvas = tk.Canvas(outer, highlightthickness=0, bg="#fafafa")
        scrollbar = tk.Scrollbar(outer, orient="vertical", command=canvas.yview)
        list_frame = tk.Frame(canvas, bg="#fafafa")
        list_frame.bind("<Configure>",
                        lambda e: canvas.configure(scrollregion=canvas.bbox("all")))
        canvas.create_window((0, 0), window=list_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)
        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")

        # 鼠标滚轮滚动
        def _on_mw(e):
            canvas.yview_scroll(int(-1 * (e.delta / 120)), "units")
        canvas.bind("<MouseWheel>", _on_mw)
        list_frame.bind("<MouseWheel>", _on_mw)

        def _get_price(cat, name):
            """获取单件售价"""
            if cat == "seeds":
                c = self.crops.get(name, {})
                return int(c.get("seed_price", 0) * 0.5)
            if name == "金色南瓜":
                return int(12000 * (1.0 + get_talent_value(d["talent_tree"], "sell_bonus")))
            c = self.crops.get(name, {})
            if c.get("sell_price"):
                p = int(c["sell_price"] * (1.0 + get_talent_value(d["talent_tree"], "sell_bonus")))
                if d.get("event_active", {}).get("harvest_festival"):
                    p *= 2
                return p
            pf = next((x for x in FACTORY_LIST if x["product"] == name), None)
            if pf:
                p = int(pf["sell_price"] * (1.0 + get_talent_value(d["talent_tree"], "sell_bonus")))
                if d.get("event_active", {}).get("harvest_festival"):
                    p *= 2
                return p
            an = next((a for a in BARN_ANIMALS_LIST if a["product"] == name), None)
            if an:
                p = int(an["sell_price"] * (1.0 + get_talent_value(d["talent_tree"], "sell_bonus")))
                if d.get("event_active", {}).get("harvest_festival"):
                    p *= 2
                return p
            brew = next((r for r in BREW_RECIPES if r["name"] == name), None)
            if brew:
                p = int(brew["sell_price"] * (1.0 + get_talent_value(d["talent_tree"], "sell_bonus")))
                if d.get("event_active", {}).get("harvest_festival"):
                    p *= 2
                return p
            feed_prices = {"基础饲料": 15, "精制饲料": 30, "高级饲料": 60, "特殊饲料": 120}
            if name in feed_prices:
                return feed_prices[name]
            return 0

        def make_item_row(cat, name, qty):
            """创建一行物品显示"""
            is_locked = name in locked.get(cat, [])
            bg = "#f0f0f0" if is_locked else "#fff"
            price = _get_price(cat, name)
            subtotal = qty * price

            row = tk.Frame(list_frame, bg=bg, relief="groove", bd=1)
            row.pack(fill="x", padx=2, pady=1)

            # 勾选框
            if not is_locked and qty > 0:
                var = tk.BooleanVar()
                cb_vars[(cat, name)] = var

                def on_check():
                    total = 0
                    for (c, n), v in cb_vars.items():
                        if v.get():
                            if c == "seeds":
                                total += d.get("seed_bag", {}).get(n, 0)
                            else:
                                total += d["inventory"][c].get(n, 0)
                    sel_info["qty"] = total
                    update_sel_label(sel_label)

                chk = tk.Checkbutton(row, variable=var, bg=bg,
                                     command=on_check)
                chk.pack(side="left", padx=(4, 0))
            else:
                tk.Label(row, text="  ", width=3, bg=bg).pack(side="left")

            # 名称
            fg = "#999" if is_locked else "#333"
            tk.Label(row, text=name, width=14, anchor="w", bg=bg,
                     font=F["small"], fg=fg).pack(side="left", padx=2)

            # 数量
            tk.Label(row, text=f"×{qty}", width=5, anchor="e", bg=bg,
                     font=F["small"], fg=fg).pack(side="left")

            # 单价
            tk.Label(row, text=f"{price}💰", width=7, anchor="e", bg=bg,
                     font=F["small"], fg=fg).pack(side="left")

            # 小计
            tk.Label(row, text=f"{subtotal:,}💰", width=10, anchor="e", bg=bg,
                     font=F["small"], fg=fg).pack(side="left")

            # 锁定按钮
            def toggle_lock(c=cat, n=name):
                lk = d.setdefault("locked", {"crops": [], "products": [], "seeds": []})
                lst = lk.setdefault(c, [])
                if n in lst:
                    lst.remove(n)
                else:
                    lst.append(n)
                _rebuild_list()

            lock_text = "🔒" if is_locked else "🔓"
            tk.Button(row, text=lock_text, font=F["small"], bg=bg, bd=0,
                      cursor="hand2", command=toggle_lock).pack(side="left", padx=2)

            # 出售按钮（锁定或数量为0时不显示）
            if qty > 0 and not is_locked:
                def sell_slider(c=cat, n=name, p=price):
                    if c == "seeds":
                        have = d.get("seed_bag", {}).get(n, 0)
                    else:
                        have = d["inventory"][c].get(n, 0)
                    self._sell_with_slider(
                        f"出售{n}", c, n, p, have, dialog, _rebuild_list)

                tk.Button(row, text="出售", font=F["small"], bg="#d4edda",
                          bd=1, command=sell_slider).pack(side="right", padx=2)

        def make_section(title, cat_key):
            """创建一个分类区块"""
            if cat_key == "seeds":
                inv = d.get("seed_bag", {})
            else:
                inv = d["inventory"].get(cat_key, {})
            items = [(n, q) for n, q in inv.items() if q > 0]
            if not items:
                return
            items.sort()
            # 分类标题
            lbl = f"── {title} ──"
            tk.Label(list_frame, text=lbl, font=F["bold"], bg="#fafafa",
                     fg="#555").pack(fill="x", pady=(8, 2), padx=4)
            # 每一行
            for name, qty in items:
                make_item_row(cat_key, name, qty)

        def _rebuild_list():
            """刷新整个列表"""
            for w in list_frame.winfo_children():
                w.destroy()
            cb_vars.clear()
            sel_info["qty"] = 0
            update_sel_label(sel_label)

            make_section("种子库存（半价回收）", "seeds")
            make_section("作物库存", "crops")
            make_section("产品库存", "products")
            make_section("饲料库存", "feeds")

            if not cb_vars and not d.get("seed_bag", {}) and all(
                not d["inventory"].get(cat, {})
                for cat in ("crops", "products", "feeds")
            ):
                tk.Label(list_frame, text="(仓库为空)", font=F["small"],
                         bg="#fafafa", fg="#999").pack(pady=20)

            # 刷新顶栏金币和总价值
            for w in top.winfo_children():
                txt = w.cget("text")
                if "金币" in txt:
                    w.config(text=f"  金币: {d['gold']:,}  ")
                elif "总价值" in txt:
                    w.config(text=f"总价值: {self._calc_warehouse_value(d):,}💰")

        _rebuild_list()
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

        upgrade_lands = self._get_active_lands()
        upgrade_unlocked = self._get_active_unlocked()
        for i, land in enumerate(upgrade_lands[:upgrade_unlocked], 1):
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
                upgrade_lands[n - 1]["upgrade_level"] += 1
                self._log(f"⬆️ 土地 #{n} 升级到 Lv.{upgrade_lands[n-1]['upgrade_level']}")
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
        if self._get_active_unlocked() >= MAX_LANDS:
            messagebox.showinfo("提示", "所有土地已解锁！")
            return
        next_id = self._get_active_unlocked() + 1
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
            if d.get("active_land_page", 0) == 1:
                d["unlocked_lands_page2"] = next_id
            else:
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

        title_label = tk.Label(dialog, font=F["bold"])
        title_label.pack(pady=(10, 5))

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

        def _rebuild():
            title_label.config(text=f"⭐ 天赋树  天赋点: {d['talent_points']}")
            for w in scroll_frame.winfo_children():
                w.destroy()
            for grp in TALENT_GROUPS:
                tk.Label(scroll_frame, text=f"── {grp} ──", font=F["bold"],
                         bg=COLORS["bg"]).pack(fill="x", pady=(8, 2))
                for t in TALENTS_LIST:
                    if t[1] != grp:
                        continue
                    _, _, name, max_lv, desc, _, title = t
                    level = d["talent_tree"].get(name, 0)
                    if level >= max_lv:
                        bar = "■" * max_lv + " MAX"
                        btn = tk.Button(scroll_frame,
                                        text=f"{title}  {bar}  {desc}",
                                        font=F["small"], anchor="w", padx=5,
                                        state="disabled", bg="#d4edda",
                                        relief="groove", bd=1)
                    else:
                        bar = "■" * level + "□" * (max_lv - level) + f" ({level}/{max_lv})"
                        can = d["talent_points"] > 0
                        btn = tk.Button(scroll_frame,
                                        text=f"{title}  {bar}  {desc}",
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
                            self._log(f"⭐ 学习 {title} Lv.{d['talent_tree'][n]}")
                            _rebuild()
                            self._update_ui()

                        btn.config(command=upgrade_talent)
                    btn.pack(fill="x", padx=5, pady=2)

        _rebuild()

        # 底部操作栏：重置 + 天赋果实
        bottom = tk.Frame(dialog, bg=COLORS["bg"])
        bottom.pack(fill="x", padx=10, pady=(5, 10))

        fruit_count = d.get("inventory", {}).get("crops", {}).get("天赋果实", 0)
        fruit_used = d.get("talent_fruits_used", 0)
        fruit_btn = tk.Button(bottom,
            text=f"🍎 天赋果实 ({fruit_count}个,已用{fruit_used}/10)",
            font=F["small"],
            state="normal" if fruit_count > 0 else "disabled",
            command=lambda: self._on_use_talent_fruit(d, dialog))
        fruit_btn.pack(side="left", padx=5)

        reset_btn_diamond = tk.Button(bottom,
            text=f"🔄 重置天赋 (50💎)",
            font=F["small"],
            command=lambda: self._on_reset_talents(d, True, dialog, _rebuild))
        reset_btn_diamond.pack(side="right", padx=5)

        reset_btn_gold = tk.Button(bottom,
            text=f"🔄 重置天赋 (5000💰)",
            font=F["small"],
            command=lambda: self._on_reset_talents(d, False, dialog, _rebuild))
        reset_btn_gold.pack(side="right", padx=5)

        _rebuild()
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
            "🌾 开心农场 v3.0\n\n"
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
        messagebox.showinfo("农场手册", msg)

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
                feed_str = ", ".join(f"{k}×{v}" for k, v in a.get("feed", {}).items()) if a else "?"
                lines = [
                    f"栏位 #{bid}  Lv.{lv}",
                    f"动物: {barn['animal_type']} ({sn})",
                    f"饲料: {feed_str}",
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

        visible_animals = [a for a in BARN_ANIMALS_LIST if not a.get("hidden")]
        for i, a_data in enumerate(visible_animals, 1):
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
        self._log(f"🍽️ 投喂完成：新增投喂 {len(fed)} 只，已投喂 {len(already)} 只，缺饲料 {len(no_feed)} 只，饲料库存 {sum(d.get('inventory', {}).get('feeds', {}).values())} 份")
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
        feed_inv = d.get("inventory", {}).get("feeds", {})

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
                          max_qty, parent_dialog=None, refresh_cb=None):
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
            if inv_category == "seeds":
                inv = self.data.get("seed_bag", {})
            else:
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
            write_save_v2(self.data)
            win.destroy()
            if callable(refresh_cb):
                refresh_cb()
            else:
                parent_dialog.destroy()
            self._update_ui()

        tk.Button(btn_frame, text="✅ 出售", font=F["button"],
                  command=confirm, bg="#d4edda", width=8).pack(side="left", padx=5)
        tk.Button(btn_frame, text="❌ 取消", font=F["button"],
                  command=win.destroy, bg="#f8d7da", width=8).pack(side="left", padx=5)

        win.wait_window()

    # ---------- 天赋重置 / 果实 ----------
    def _on_reset_talents(self, d, pay_diamond, dialog, rebuild):
        ok, msg = reset_talents(d, pay_diamond)
        if ok:
            messagebox.showinfo("天赋重置", msg)
            self._log(f"🔄 {msg}")
            rebuild()
            self._update_ui()
        else:
            messagebox.showwarning("天赋重置", msg)

    def _on_use_talent_fruit(self, d, dialog):
        ok, msg = use_talent_fruit(d)
        if ok:
            messagebox.showinfo("天赋果实", msg)
            self._log(msg)
            dialog.destroy()
        else:
            messagebox.showwarning("天赋果实", msg)

    # ---------- 事件预警 ----------
    def _show_event_warning(self, d, pending):
        event = pending.get("event", {})
        if not event:
            return
        # 只弹一次，用标志位防止重复弹窗
        if getattr(self, "_warning_shown", False):
            return
        self._warning_shown = True
        result = messagebox.askyesno(
            "⚠️ 灾害预警",
            f"{event.get('desc', '灾害即将发生')}\n\n是否花费 500💰 取消此事件？\n选择「是」= 花费500💰取消\n选择「否」= 忽略，事件正常发生"
        )
        if result:
            ok, msg = cancel_event_warning(d)
            if ok:
                self._log(f"🛡️ {msg}")
            else:
                self._log(f"⚠️ {msg}")
        else:
            # 忽略预警，立即触发事件
            d["_pending_warning"] = None
            self._log(f"⚠️ 忽略预警，事件即将发生...")
        self._warning_shown = False

    # ---------- 农场手册 ----------
    def _show_help(self):
        dialog = tk.Toplevel(self.root)
        dialog.title("📖 农场手册")
        dialog.geometry("620x600")
        dialog.transient(self.root)
        dialog.grab_set()

        tk.Label(dialog, text="📖 开心农场 v3.0 农场手册", font=F["title"]).pack(pady=(10, 5))

        frame = tk.Frame(dialog)
        frame.pack(fill="both", expand=True, padx=10, pady=5)

        text_widget = tk.Text(frame, font=F["help"],
                 bg=COLORS["bg"], fg="black", wrap="word",
                 spacing1=4, spacing3=4,
                 relief="flat", highlightthickness=0)
        scrollbar = tk.Scrollbar(frame, orient="vertical", command=text_widget.yview)
        text_widget.configure(yscrollcommand=scrollbar.set)
        text_widget.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")

        crops_self = self.crops
        crop_lines = []
        for n, c in sorted(crops_self.items(), key=lambda x: x[1].get("level", 99)):
            if c.get("hidden"):
                continue
            season_bonus = ""
            for s, clist in _SEASON_BONUS_MAP.items():
                if n in clist:
                    season_bonus = f" [{s}季×1.5]"
            crop_lines.append(f"  {n:<6} Lv.{c['level']:<2} 种子{c['seed_price']:>5}💰 售{c['sell_price']:>5}💰 生长{c['growth_minutes']}min{season_bonus}")
        crop_str = "\n".join(crop_lines)

        animal_lines = []
        for a in BARN_ANIMALS_LIST:
            if a.get("hidden"):
                continue
            feed_str = "+".join(f"{k}{v}" for k, v in a["feed"].items())
            animal_lines.append(f"  {a['name']:<4} Lv.{a['level']:<2} {a['price']:>5}💰 →{a['product']:<4}售{a['sell_price']}💰 周期{a['cycle']}min 饲料:{feed_str}")
        animal_str = "\n".join(animal_lines)

        help_text = f"""
🌟 季节系统
- 4个季节循环：春→夏→秋→冬，每季120分钟
- 当季作物产量×1.5

🌱 种植与土地
- 初始6块地，最多50块
- 每块土地可升级（Lv.1~10），每级增产10%
- 升级费用随等级递增
- 累积产量：小数部分不会损失，累积到下次收获

🌾 作物一览
{crop_str}

🐔 养殖系统
- 初始6个栏位，最多50个
- 动物生命周期：幼年(前2次产出减半)→成年→老年(40次后减产30%)
- 栏位升级：每级获得速度/产量/双倍等加成
- 繁殖：选两只同种成年动物，基础75%成功率，亲本栏位≥5级各+5%

🐓 动物一览
{animal_str}

🍽️ 饲料系统
- 首次投喂后动物开始产出，每产出周期自动消耗饲料
- 饲料不足时动物跳过产出，显示"缺料"
- 可随时补料
- 饲料消耗量受「节省原料」天赋影响
- 饲料配方在饲料厂加工

⭐ 天赋系统
- 3系：种植系、经营系、养殖系
- 升级获得天赋点
- 天赋果实：收获时0.5%概率掉落，最多用10个
- 重置天赋：50💎 或 5000💰

💎 钻石获取
- 成就奖励（已翻倍）
- 流星雨事件 +5💎
- 购买获得

🏆 成就系统
- 完成特定目标获得奖励
- 钻石奖励已翻倍

📦 仓库
- 基础容量100，每5级+10
- 种子独立存放，不占仓库空间
- 可花费钻石扩容（100💎起，每次+50💎）
- 支持锁定物品和批量出售

⚠️ 随机事件
- 正面：丰收节、黄金时段、风调雨顺、神秘商人、流星雨
- 负面：虫灾(减产50%)、暴风(延长生长2h)，有60秒预警可500💰取消
- 外星人：毁1-3块作物但赔偿1000💰

💾 离线收益
- 作物：已成熟自动收获一次
- 动物：按周期累积产出（每周期消耗饲料，不足跳过）
- 享受离线收益天赋加成

快捷键
- F1: 打开农场手册
"""
        text_widget.insert("1.0", help_text)
        text_widget.config(state="disabled")

        tk.Button(dialog, text="关闭", font=F["button"],
                  command=dialog.destroy, width=10).pack(pady=(5, 10))

    # ---------- 关闭 ----------
    def _on_close(self):
        write_save_v2(self.data)
        self.root.destroy()

    # ---------- 启动 ----------
    def run(self):
        self.root.mainloop()


# ============ 入口 ============
if __name__ == "__main__":
    try:
        import ctypes
        ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID("PumpkinFarm")
    except:
        pass
    app = FarmGUIv2()
    app.run()
