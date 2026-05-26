# -*- coding: utf-8 -*-
"""
开心农场 v3.0
基于 farm.py 添加完整的养殖场系统（与土地对称的50栏位、饲料、繁殖）
"""
import sys
import os
import json
import datetime
import time
import random
import threading
from math import floor, ceil

# ============ JSON 配置加载 ============
_DATA_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "data")

def _load_json(filename):
    with open(os.path.join(_DATA_DIR, filename), "r", encoding="utf-8") as f:
        return json.load(f)

def reload_config():
    """重新加载所有 JSON 配置（用于热更新）"""
    global BARN_ANIMALS_LIST, FACTORY_LIST, FEED_RECIPES, TALENTS_LIST, EVENTS, ACHIEVEMENTS_LIST
    BARN_ANIMALS_LIST = _load_json("animals.json")
    FACTORY_LIST = _load_json("factories.json")
    FEED_RECIPES = _load_json("feeds.json")
    _t_raw = _load_json("talents.json")
    TALENTS_LIST = [(t["id"], t["group"], t["name"], t["max_lv"], t["desc"], t["effect_per_lv"], t["title"]) for t in _t_raw]
    EVENTS = _load_json("events.json")
    # 成就元数据从 JSON 加载，check_fn 由注册表提供
    _ach_meta_dir = os.path.join(_DATA_DIR, "achievements.json")
    _ach_meta = _load_json("achievements.json") if os.path.exists(_ach_meta_dir) else []
    _rebuild_achievements(_ach_meta)


def init_game():
    """初始化游戏：加载配置，必须在所有注册完成后调用"""
    reload_config()

# ============ 从 farm.py 导入基础逻辑 ============
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from farm import (
    MAX_LANDS, REFRESH_INTERVAL, AUTO_SAVE_INTERVAL, SAVE_FILE,
    load_crops, new_save, try_level_up, write_save, calc_offline,
)

# ============ 养殖场常量 ============
MAX_BARNS = 50
INITIAL_BARNS = 6
SAVE_FILE_V2 = "save.json"  # 与基础版共用存档

# ============ 核心游戏常量（原在 farm.py 完整版中） ============
INITIAL_LANDS = 6
WAREHOUSE_BASE_CAPACITY = 100
WAREHOUSE_PER_LEVEL = 5  # 每5级+10
WAREHOUSE_DIAMOND_BASE = 100  # 钻石扩容基础价格
WAREHOUSE_DIAMOND_INCREMENT = 50  # 每次递增
SEASONS = ["春", "夏", "秋", "冬"]
SEASON_DURATION = 120  # 每季节持续时间（分钟）

# ---------- 天赋组（固定） ----------
TALENT_GROUPS = ["种植系", "经营系", "养殖系"]

# ---------- 成就注册系统 ----------
"""成就列表，格式：(name, cond_str, check_fn, reward_dict)
由 register_achievement() 和 _rebuild_achievements() 共同构建"""
ACHIEVEMENTS_LIST = []

def _ach_check_completionist(data):
    """完美主义者：完成所有其他成就"""
    completed = set(data.get("achievements", []))
    other_achs = [a for a in ACHIEVEMENTS_LIST if a[0] != "完美主义者"]
    return all(a[0] in completed for a in other_achs) if other_achs else False

def register_achievement(name, cond_str, check_fn, reward):
    """注册一个成就"""
    # 检查是否已存在，避免重复注册
    for i, a in enumerate(ACHIEVEMENTS_LIST):
        if a[0] == name:
            ACHIEVEMENTS_LIST[i] = (name, cond_str, check_fn, reward)
            return
    ACHIEVEMENTS_LIST.append((name, cond_str, check_fn, reward))

def _rebuild_achievements(meta_list):
    """根据 JSON 元数据重建成就列表（保留已注册的 check_fn）"""
    global ACHIEVEMENTS_LIST
    old = {a[0]: a[2] for a in ACHIEVEMENTS_LIST}  # name -> check_fn
    new_list = []
    for m in meta_list:
        name = m["name"]
        check_fn = old.get(name)  # 保留已有的 check_fn
        new_list.append((name, m["cond_str"], check_fn, m["reward"]))
    # 加上只在代码中注册的成就（如完美主义者）
    for name, check_fn in old.items():
        if name not in {m["name"] for m in meta_list}:
            existing = next((a for a in ACHIEVEMENTS_LIST if a[0] == name), None)
            if existing:
                new_list.append(existing)
    ACHIEVEMENTS_LIST = new_list

# ———— 注册默认成就 ————
register_achievement("初次收获", "收获 1 次作物",            lambda d: d.get("total_harvests", 0) >= 1, {"gold": 100})
register_achievement("丰收达人", "收获 100 次作物",           lambda d: d.get("total_harvests", 0) >= 100, {"gold": 1000, "diamond": 5})
register_achievement("种植大师", "收获 1000 次作物",          lambda d: d.get("total_harvests", 0) >= 1000, {"gold": 5000, "diamond": 20})
register_achievement("第一桶金", "累计赚取 10000 金币",       lambda d: d.get("total_earnings", 0) >= 10000, {"gold": 500})
register_achievement("百万富翁", "累计赚取 1000000 金币",     lambda d: d.get("total_earnings", 0) >= 1000000, {"gold": 10000, "diamond": 50})
register_achievement("养殖新手", "收集 10 次动物产品",        lambda d: d.get("barn_total_collects", 0) >= 10, {"gold": 200})
register_achievement("养殖大户", "收集 1000 次动物产品",      lambda d: d.get("barn_total_collects", 0) >= 1000, {"gold": 5000, "diamond": 10})
register_achievement("加工能手", "加工 50 次",               lambda d: d.get("total_processed", 0) >= 50, {"gold": 1000})
register_achievement("天赋异禀", "学习 10 点天赋",           lambda d: sum(d.get("talent_tree", {}).values()) >= 10, {"gold": 2000})
register_achievement("土地大亨", "解锁 20 块土地",           lambda d: d.get("unlocked_lands", 0) >= 20, {"gold": 3000})
register_achievement("完美主义者", "完成所有其他成就",        _ach_check_completionist, {"diamond": 100})

# ———— 事件注册系统 ————
"""事件效果处理器注册表"""
EVENT_HANDLERS = {}

def register_event_handler(event_name, handler_fn):
    """注册事件效果处理器 handler_fn(data, event, crops)"""
    EVENT_HANDLERS[event_name] = handler_fn

def get_event_handler(event_name):
    return EVENT_HANDLERS.get(event_name)

def _event_pest_attack(data, event, crops):
    lands = data.get("lands", []) + data.get("lands_page2", [])
    targets = [l for l in lands if l.get("crop") and not l.get("golden_pumpkin")]
    if targets:
        t = random.choice(targets)
        # 虫灾改为延长生长时间2小时
        t["_wind_delay"] = t.get("_wind_delay", 0) + 120
        print(f"  🐛 {t['crop']} 遭虫灾！生长时间延长2小时")

def _event_wind_damage(data, event, crops):
    lands = data.get("lands", []) + data.get("lands_page2", [])
    targets = [l for l in lands if l.get("crop") and not l.get("golden_pumpkin")]
    if targets:
        t = random.choice(targets)
        # 暴风延长生长时间2小时
        t["_wind_delay"] = t.get("_wind_delay", 0) + 120
        print(f"  💨 {t['crop']} 遭暴风！生长时间延长2小时")


def _event_alien_attack(data, event, crops):
    lands = data.get("lands", []) + data.get("lands_page2", [])
    targets = [l for l in lands if l.get("crop") and not l.get("golden_pumpkin")]
    if targets:
        damaged = random.sample(targets, min(random.randint(1, 3), len(targets)))
        for t in damaged:
            print(f"  👽 {t['crop']} 被外星人飞船损坏！")
            t["crop"] = None
            t["plant_time"] = None
    data["gold"] = data.get("gold", 0) + 1000
    print(f"  💰 外星人留下1000💰作为赔偿！")

def _event_meteor_shower(data, event, crops):
    data["diamond"] = data.get("diamond", 0) + 5

# 前3个正面事件没有额外效果（仅标记 duration）
# 神秘商人也没有额外效果（get_merchant_discount 检查 event_active）

# ———— 注册默认事件处理器 ————
register_event_handler("pest_attack", _event_pest_attack)
register_event_handler("wind_damage", _event_wind_damage)
register_event_handler("alien_attack", _event_alien_attack)
register_event_handler("meteor_shower", _event_meteor_shower)

# 初始化配置（也可通过 init_game() 重新调用以支持扩展注册）
reload_config()

# ============ 核心工具函数（原在 farm.py 完整版中） ============

def now_dt():
    return datetime.datetime.now()

def now_str():
    return datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")

def parse_dt(s):
    try:
        return datetime.datetime.strptime(s, "%Y-%m-%d %H:%M:%S")
    except (ValueError, TypeError):
        return now_dt()

def get_season(data):
    """根据游戏时间计算当前季节"""
    first = data.get("_first_save_time")
    if not first:
        data["_first_save_time"] = now_str()
        first = data["_first_save_time"]
    try:
        elapsed = (now_dt() - parse_dt(first)).total_seconds() / 60.0
    except (ValueError, TypeError):
        elapsed = 0
    cycles = int(elapsed / SEASON_DURATION)
    idx = cycles % len(SEASONS)
    return SEASONS[idx], cycles

# 季节性作物加成（丰收季节产量 x1.5）
_SEASON_BONUS_MAP = {
    "春": ["小麦", "水稻", "土豆", "四叶草"],
    "夏": ["玉米", "玫瑰", "番茄", "蓝莓", "棉花", "甘蔗"],
    "秋": ["南瓜", "胡萝卜", "葡萄", "可可豆", "咖啡豆"],
    "冬": ["草莓", "茶叶", "黄金小麦", "彩虹花"],
}

def season_crop_bonus(crop_name, season):
    if season in _SEASON_BONUS_MAP and crop_name in _SEASON_BONUS_MAP[season]:
        return 1.5
    return 1.0

def get_talent_value(talent_tree, name):
    level = talent_tree.get(name, 0)
    if level <= 0:
        return 0.0
    for t in TALENTS_LIST:
        if t[2] == name:
            return t[5] * level
    return 0.0

def get_talent_level(talent_tree, name):
    return talent_tree.get(name, 0)

def calc_growth_time(crop_name, land_level, talent_tree, land=None):
    """计算作物生长时间（分钟），含暴风延迟"""
    crops = load_crops()
    c = crops.get(crop_name, {})
    base = c.get("growth_minutes", 10)
    speed_bonus = get_talent_value(talent_tree, "grow_speed")
    land_bonus = (land_level - 1) * 0.05
    time = base * max(0.1, 1.0 - speed_bonus - land_bonus)
    if land and land.get("_wind_delay", 0) > 0:
        time += land["_wind_delay"]
    return time

def calc_yield_multiplier(land_level, talent_tree, crop_name, season):
    mult = 1.0 + (land_level - 1) * 0.1 + get_talent_value(talent_tree, "yield_bonus")
    bonus = season_crop_bonus(crop_name, season)
    if bonus > 1.0:
        mult *= bonus
    return mult

def calc_harvest_yield(land, base_yield, mult):
    """累积式产量计算，避免小数取整损失"""
    remainder = land.get("_yield_remainder", 0.0)
    raw = base_yield * mult + remainder
    harvested = max(1, int(floor(raw)))
    land["_yield_remainder"] = raw - harvested
    return harvested

def get_double_chance(land_level, talent_tree):
    chance = (land_level - 1) * 0.02 + get_talent_value(talent_tree, "double_harvest")
    return min(chance, 0.9)

def warehouse_capacity(data):
    """计算仓库容量：基础 + 每5级 +10 + 钻石扩容"""
    base = WAREHOUSE_BASE_CAPACITY
    level_bonus = (data.get("level", 1) // 5) * 10
    diamond_bonus = data.get("warehouse_expansions", 0) * 10
    return base + level_bonus + diamond_bonus

def inventory_usage(data):
    inv = data.get("inventory", {})
    return len(inv.get("crops", {})) + len(inv.get("products", {})) + len(inv.get("feeds", {}))

def inventory_space(data):
    return warehouse_capacity(data) - inventory_usage(data)

def warehouse_expansion_cost(data):
    """下次钻石扩容费用"""
    count = data.get("warehouse_expansions", 0)
    return WAREHOUSE_DIAMOND_BASE + count * WAREHOUSE_DIAMOND_INCREMENT

def land_upgrade_cost(level):
    costs = {1: 200, 2: 500, 3: 1000, 4: 2000, 5: 4000,
             6: 8000, 7: 8000, 8: 15000, 9: 30000}
    return costs.get(level, None)

def check_factories_ready(data):
    """检查所有工厂加工是否完成"""
    now = now_dt()
    for f in FACTORY_LIST:
        fc = data["factories"].get(f["factory"], {})
        if fc.get("ready") or not fc.get("current_order") or not fc.get("start_time"):
            continue
        st = parse_dt(fc["start_time"])
        speed = 1.0 - get_talent_value(data.get("talent_tree", {}), "process_speed")
        pt = f["time"] * max(0.1, speed)
        if (now - st).total_seconds() / 60.0 >= pt:
            fc["ready"] = True

def _remove_expired_events(data):
    """移除已过期的正面事件"""
    now = now_dt()
    active = data.get("event_active", {})
    expired = []
    for ev_name, start_str in list(active.items()):
        try:
            start = parse_dt(start_str)
            ev = next((e for e in EVENTS if e["name"] == ev_name), None)
            if ev and ev.get("duration", 0) > 0 and (now - start).total_seconds() / 60.0 >= ev["duration"]:
                expired.append(ev_name)
        except Exception:
            expired.append(ev_name)
    for ev in expired:
        del active[ev]
        print(f"  ⏰ {ev} 效果已结束")

def _apply_event_effect(data, event, crops):
    """应用事件效果（通过注册表分发）"""
    data.setdefault("event_active", {})
    if event["positive"]:
        data["event_active"][event["name"]] = now_str()
    # 无论正负面，有注册处理器就调用
    handler = get_event_handler(event["name"])
    if handler:
        handler(data, event, crops)

def try_trigger_event(data, crops):
    """尝试触发随机事件（约10%概率）
    负面事件（虫灾/暴风）每3小时最多触发一次，有60秒预警"""
    _remove_expired_events(data)

    # 检查是否有待处理的预警
    pending = data.get("_pending_warning")
    if pending:
        warn_time = parse_dt(pending["time"])
        if (now_dt() - warn_time).total_seconds() >= 60:
            # 预警超时，触发事件
            event = pending["event"]
            _apply_event_effect(data, event, crops)
            print(event.get("desc", ""))
            data["_pending_warning"] = None
        return

    if random.random() > 0.1:
        return
    active = data.get("event_active", {})
    event = random.choice(EVENTS)
    if event["name"] in active:
        return

    # 负面事件3小时冷却 + 60秒预警
    if not event["positive"]:
        last_disaster = data.get("_last_disaster_time")
        if last_disaster:
            elapsed = (now_dt() - parse_dt(last_disaster)).total_seconds() / 60.0
            if elapsed < 180:
                return
        data["_last_disaster_time"] = now_str()
        # 设置60秒预警
        data["_pending_warning"] = {"event": event, "time": now_str()}
        print(f"⚠️ 预警：{event['desc']} 将在60秒后发生！花费500💰可取消。")
        return

    _apply_event_effect(data, event, crops)
    print(event["desc"])

def cancel_event_warning(data):
    """花费500💰取消即将发生的负面事件"""
    pending = data.get("_pending_warning")
    if not pending:
        return False, "没有待处理的预警"
    if data.get("gold", 0) < 500:
        return False, "💰不足500"
    data["gold"] = data.get("gold", 0) - 500
    data["_pending_warning"] = None
    return True, "已花费500💰取消事件"

def get_merchant_discount(data):
    """返回神秘商人折扣率（0.2 = 8折），无折扣返回0"""
    active = data.get("event_active", {})
    if "merchant_visit" in active:
        return 0.2
    return 0.0

def check_achievements(data):
    """检查成就完成情况，返回新达成数量"""
    completed = set(data.get("achievements", []))
    new_count = 0
    for name, _, check_fn, reward in ACHIEVEMENTS_LIST:
        if name in completed:
            continue
        if check_fn(data):
            completed.add(name)
            new_count += 1
            for k, v in reward.items():
                if k == "gold":
                    data["gold"] = data.get("gold", 0) + v
                elif k == "exp":
                    data["exp"] = data.get("exp", 0) + v
                elif k == "diamond":
                    data["diamond"] = data.get("diamond", 0) + v * 2  # 成就钻石奖励翻倍
            print(f"🏆 达成成就：{name}！获得奖励！")
    if new_count > 0:
        data["achievements"] = list(completed)
    return new_count

# ============ 天赋重置与果实 ============

TALENT_RESET_DIAMOND = 50
TALENT_RESET_GOLD = 5000
TALENT_FRUIT_CHANCE = 0.005  # 0.5%
TALENT_FRUIT_MAX = 10

def reset_talents(data, pay_with_diamond=True):
    """重置所有天赋点，消耗50💎或5000💰"""
    cost_diamond = TALENT_RESET_DIAMOND
    cost_gold = TALENT_RESET_GOLD
    if pay_with_diamond:
        if data.get("diamond", 0) < cost_diamond:
            return False, f"💎不足，需要 {cost_diamond}💎"
        data["diamond"] = data.get("diamond", 0) - cost_diamond
    else:
        if data.get("gold", 0) < cost_gold:
            return False, f"💰不足，需要 {cost_gold}💰"
        data["gold"] = data.get("gold", 0) - cost_gold

    tree = data.get("talent_tree", {})
    total = sum(tree.values())
    data["talent_points"] = data.get("talent_points", 0) + total
    data["talent_tree"] = {}
    return True, f"已重置，返还 {total} 天赋点"

def check_talent_fruit_drop(data):
    """检查是否掉落天赋果实"""
    if random.random() < TALENT_FRUIT_CHANCE:
        used = data.get("talent_fruits_used", 0)
        if used < TALENT_FRUIT_MAX:
            inv = data.get("inventory", {})
            inv.setdefault("crops", {})
            inv["crops"]["天赋果实"] = inv["crops"].get("天赋果实", 0) + 1
            return True
    return False

def use_talent_fruit(data):
    """使用天赋果实获得1天赋点"""
    inv = data.get("inventory", {})
    crops = inv.get("crops", {})
    if crops.get("天赋果实", 0) <= 0:
        return False, "没有天赋果实"
    used = data.get("talent_fruits_used", 0)
    if used >= TALENT_FRUIT_MAX:
        return False, f"最多使用 {TALENT_FRUIT_MAX} 个天赋果实"
    crops["天赋果实"] = crops["天赋果实"] - 1
    data["talent_points"] = data.get("talent_points", 0) + 1
    data["talent_fruits_used"] = used + 1
    return True, f"获得 1 天赋点！(已用 {data['talent_fruits_used']}/{TALENT_FRUIT_MAX})"

def apply_exp_bonus(data):
    """应用 study_bonus 天赋加成到 exp"""
    bonus = get_talent_value(data.get("talent_tree", {}), "study_bonus")
    return 1.0 + bonus

# ============ 钻石商店 ============

DIAMOND_SHOP_ITEMS = [
    {"name": "天赋重置药水", "diamond": 50, "desc": "重置所有天赋点", "action": "reset_talent"},
    {"name": "仓库扩容券",   "diamond": 100, "desc": "仓库容量+10", "action": "warehouse_expand"},
    {"name": "幸运四叶草",   "diamond": 20, "desc": "下次收获双倍概率+50%", "action": "lucky_clover"},
    {"name": "加速化肥",     "diamond": 5, "desc": "一块土地缩短1小时", "action": "speed_fertilizer"},
    {"name": "动物速长剂",   "diamond": 10, "desc": "跳过动物幼年期", "action": "animal_growth"},
    {"name": "皮肤：彩虹土地","diamond": 200, "desc": "外观特效(无加成)", "action": "skin_rainbow"},
]

def diamond_shop_purchase(data, item_idx):
    """钻石商店购买，返回 (success, message)"""
    if item_idx < 0 or item_idx >= len(DIAMOND_SHOP_ITEMS):
        return False, "无效物品"
    item = DIAMOND_SHOP_ITEMS[item_idx]
    diamond = data.get("diamond", 0)
    if diamond < item["diamond"]:
        return False, f"💎不足，需要 {item['diamond']}💎"

    action = item["action"]
    if action == "reset_talent":
        ok, msg = reset_talents(data, pay_with_diamond=True)
        if ok:
            data["diamond"] = diamond - item["diamond"]
        return ok, msg
    elif action == "warehouse_expand":
        data["diamond"] = diamond - item["diamond"]
        data["warehouse_expansions"] = data.get("warehouse_expansions", 0) + 1
        return True, f"仓库容量+10！当前 {warehouse_capacity(data)}"
    elif action == "lucky_clover":
        data["diamond"] = diamond - item["diamond"]
        data["lucky_clover"] = True
        return True, "幸运四叶草已激活！下次收获双倍概率+50%"
    elif action == "speed_fertilizer":
        data["diamond"] = diamond - item["diamond"]
        data["speed_fertilizer"] = data.get("speed_fertilizer", 0) + 1
        return True, f"获得加速化肥×1！(共 {data['speed_fertilizer']})"
    elif action == "animal_growth":
        data["diamond"] = diamond - item["diamond"]
        data["animal_growth"] = data.get("animal_growth", 0) + 1
        return True, f"获得动物速长剂×1！(共 {data['animal_growth']})"
    elif action == "skin_rainbow":
        if data.get("skin_rainbow"):
            return False, "已拥有彩虹土地皮肤"
        data["diamond"] = diamond - item["diamond"]
        data["skin_rainbow"] = True
        return True, "获得皮肤：彩虹土地！"
    return False, "未知操作"

def get_diamond_shop_item(idx):
    if 0 <= idx < len(DIAMOND_SHOP_ITEMS):
        return DIAMOND_SHOP_ITEMS[idx]
    return None

# ============ 动物饲料消耗量 ============

ANIMAL_FEED_CONSUMPTION = {
    "鸡": 1, "鸭": 1, "兔": 1, "鹅": 1, "羊": 1, "羊驼": 1, "马": 1, "鹿": 1, "独角兽": 1,
    "猪": 2, "牛": 2, "蜜蜂": 2, "龙": 2,
}

def get_feed_consume(animal_type, data):
    """计算动物每周期实际饲料消耗（含节省原料天赋）"""
    base = ANIMAL_FEED_CONSUMPTION.get(animal_type, 1)
    save_bonus = get_talent_value(data.get("talent_tree", {}), "save_materials")
    actual = max(1, int(ceil(base - save_bonus)))
    return actual
FEED_FRUIT_NAMES = ["草莓", "蓝莓", "葡萄", "苹果"]

# BARN_ANIMALS_LIST、FEED_RECIPES 由 data/animals.json、data/feeds.json 加载


# ============ 存档扩展 ============

def new_barn_slots():
    """创建初始养殖栏位"""
    return [{
        "id": i + 1,
        "unlocked": i < INITIAL_BARNS,
        "level": 1,
        "animal": None,
        "animal_type": None,
        "purchase_time": None,
        "age_stage": None,
        "production_count": 0,
        "last_produce_time": None,
        "pending_product": 0,
        "breed_cooldown": None,
        "fed_time": None,
        "_yield_remainder": 0.0,
    } for i in range(MAX_BARNS)]


def migrate_barn(barn):
    """确保栏位包含所有最新字段"""
    barn.setdefault("level", 1)
    barn.setdefault("last_produce_time", None)
    barn.setdefault("pending_product", 0)
    barn.setdefault("breed_cooldown", None)
    barn.setdefault("age_stage", None)
    barn.setdefault("production_count", 0)
    barn.setdefault("fed_time", None)
    barn.setdefault("_yield_remainder", 0.0)
    return barn


def load_save_v2():
    """加载存档（兼容旧版）"""
    try:
        with open(SAVE_FILE_V2, "r", encoding="utf-8") as f:
            data = json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        data = new_save()
        data["version"] = "3.0"
        data["barns"] = new_barn_slots()
        data["unlocked_barns"] = INITIAL_BARNS
        data.setdefault("inventory", {})["feeds"] = {"基础饲料": 0, "精制饲料": 0, "高级饲料": 0, "特殊饲料": 0}
        data["agro_buildings"] = new_agro_building_slots()
        data["unlocked_agro_buildings"] = INITIAL_AGRO_BUILDINGS
        data["barn_total_collects"] = 0
        write_save_v2(data)
        return data

    # 迁移旧存档
    if "barns" not in data:
        data["barns"] = new_barn_slots()
    else:
        while len(data["barns"]) < MAX_BARNS:
            data["barns"].append({
                "id": len(data["barns"]) + 1,
                "unlocked": False,
                "level": 1,
                "animal": None,
                "animal_type": None,
                "purchase_time": None,
                "age_stage": None,
                "production_count": 0,
                "last_produce_time": None,
                "pending_product": 0,
                "breed_cooldown": None,
                "fed_time": None,
            })
    for barn in data["barns"]:
        migrate_barn(barn)
        # 兼容旧存档：已有 last_produce_time 则视为已投喂
        if barn.get("last_produce_time") and barn.get("fed_time") is None:
            barn["fed_time"] = barn["last_produce_time"]
        barn.setdefault("age_stage", None)
        barn.setdefault("production_count", 0)

    data.setdefault("unlocked_barns", INITIAL_BARNS)
    data.setdefault("inventory", {}).setdefault("feeds", {"基础饲料": 0, "精制饲料": 0, "高级饲料": 0, "特殊饲料": 0})
    data.setdefault("barn_total_collects", 0)

    # v2.1 新字段
    data.setdefault("seed_bag", {})
    data.setdefault("talent_fruits_used", 0)
    data.setdefault("warehouse_expansions", 0)
    data.setdefault("lucky_clover", False)
    data.setdefault("speed_fertilizer", 0)
    data.setdefault("animal_growth", 0)
    data.setdefault("skin_rainbow", False)
    if "_pending_warning" not in data:
        data["_pending_warning"] = None

    # 饲料迁移：feed_inventory → inventory["feeds"]
    old_feed_inv = data.pop("feed_inventory", None)
    if old_feed_inv:
        data.setdefault("inventory", {}).setdefault("feeds", {})
        for k, v in old_feed_inv.items():
            data["inventory"]["feeds"][k] = data["inventory"]["feeds"].get(k, 0) + v

    # 农业建筑迁移
    if "agro_buildings" not in data:
        data["agro_buildings"] = new_agro_building_slots()
        # 如果有旧饲料厂数据，迁移到第一个建筑位
        old_ff = data.pop("feed_factory", None)
        if old_ff and old_ff.get("current_order"):
            data["agro_buildings"][0]["building"] = "feed_mill"
            data["agro_buildings"][0]["level"] = old_ff.get("level", 1)
            if old_ff.get("ready"):
                data["agro_buildings"][0]["order"] = old_ff["current_order"]
                data["agro_buildings"][0]["done_batches"] = 1
                data["agro_buildings"][0]["total_batches"] = 1
                data["agro_buildings"][0]["ready"] = True
            elif old_ff.get("current_order") and old_ff.get("start_time"):
                data["agro_buildings"][0]["order"] = old_ff["current_order"]
                data["agro_buildings"][0]["start_time"] = old_ff["start_time"]
                data["agro_buildings"][0]["total_batches"] = 1
        if old_ff:
            data["agro_buildings"][0]["unlocked"] = True
    else:
        while len(data["agro_buildings"]) < MAX_AGRO_BUILDINGS:
            data["agro_buildings"].append({
                "id": len(data["agro_buildings"]) + 1,
                "unlocked": False, "building": None, "level": 1,
                "order": None, "start_time": None, "ready": False,
                "total_batches": 0, "done_batches": 0,
            })
        for slot in data["agro_buildings"]:
            slot.setdefault("building", None)
            slot.setdefault("level", 1)
            slot.setdefault("order", None)
            slot.setdefault("start_time", None)
            slot.setdefault("ready", False)
            slot.setdefault("total_batches", 0)
            slot.setdefault("done_batches", 0)
    data.setdefault("unlocked_agro_buildings", INITIAL_AGRO_BUILDINGS)

    # 种子迁移：inventory["seeds"] → seed_bag
    old_seeds = data.get("inventory", {}).get("seeds", {})
    if old_seeds:
        for s, qty in old_seeds.items():
            data["seed_bag"][s] = data["seed_bag"].get(s, 0) + qty
        data["inventory"]["seeds"] = {}

    # 兼容旧存档：补充核心游戏字段
    data.setdefault("unlocked_lands", INITIAL_LANDS)
    data.setdefault("diamond", 0)
    data.setdefault("total_harvests", 0)
    data.setdefault("total_earnings", 0)
    data.setdefault("total_processed", 0)
    data.setdefault("talent_points", 0)
    data.setdefault("locked", {"crops": [], "products": [], "seeds": []})
    data.setdefault("talent_tree", {})
    data.setdefault("achievements", [])
    data.setdefault("event_active", {})
    data.setdefault("inventory", {"crops": {}, "seeds": {}, "products": {}})
    inv = data["inventory"]
    inv.setdefault("crops", {})
    inv.setdefault("seeds", {})
    inv.setdefault("products", {})
    # 兼容 MAX_LANDS 变更：补齐土地数量
    while len(data["lands"]) < MAX_LANDS:
        data["lands"].append({"id": len(data["lands"]) + 1, "crop": None, "plant_time": None})
    # 土地补全 upgrade_level / golden_pumpkin
    for land in data["lands"]:
        land.setdefault("upgrade_level", 1)
        land.setdefault("golden_pumpkin", False)
        land.setdefault("_maturity_roll_done", False)
        land.setdefault("_yield_remainder", 0.0)
        land.setdefault("_pest_reduced_yield", None)
        land.setdefault("_wind_delay", 0)

    # 地块2（多页土地支持）
    data.setdefault("active_land_page", 0)
    data.setdefault("unlocked_lands_page2", INITIAL_LANDS)
    if "lands_page2" not in data:
        data["lands_page2"] = [
            {"id": i + 1, "crop": None, "plant_time": None,
             "upgrade_level": 1, "golden_pumpkin": False,
             "_maturity_roll_done": False, "_yield_remainder": 0.0,
             "_pest_reduced_yield": None, "_wind_delay": 0}
            for i in range(MAX_LANDS)
        ]
    else:
        while len(data["lands_page2"]) < MAX_LANDS:
            data["lands_page2"].append({"id": len(data["lands_page2"]) + 1, "crop": None, "plant_time": None})
        for land in data["lands_page2"]:
            land.setdefault("upgrade_level", 1)
            land.setdefault("golden_pumpkin", False)
            land.setdefault("_maturity_roll_done", False)
            land.setdefault("_yield_remainder", 0.0)
            land.setdefault("_pest_reduced_yield", None)
            land.setdefault("_wind_delay", 0)
    # 工厂数据
    if "factories" not in data:
        data["factories"] = {}
    for f in FACTORY_LIST:
        if f["factory"] not in data["factories"]:
            data["factories"][f["factory"]] = {
                "current_order": None, "start_time": None, "ready": False
            }

    data["version"] = "3.0"
    return data


def write_save_v2(data):
    """保存存档"""
    data["last_save_time"] = now_str()
    data["version"] = "3.0"
    with open(SAVE_FILE_V2, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


# ============ 养殖场核心逻辑 ============

def get_barn_animal(name):
    """查找养殖动物配置"""
    for a in BARN_ANIMALS_LIST:
        if a["name"] == name:
            return a
    return None


def barn_upgrade_cost(level):
    """栏位升级成本"""
    costs = {1: 500, 2: 1000, 3: 2500, 4: 5000, 5: 10000,
             6: 10000, 7: 20000, 8: 40000, 9: 80000}
    return costs.get(level, None)


def barn_upgrade_effects(level):
    """栏位升级效果"""
    effects = {
        2: {"speed": 0.10},
        3: {"yield": 0.10},
        4: {"speed": 0.15},
        5: {"yield": 0.15},
        6: {"speed": 0.20},
        7: {"yield": 0.20},
        8: {"double": 0.05},
        9: {"yield": 0.25},
        10: {"global": 0.10},
    }
    return effects.get(level, {})


def get_age_stage(barn):
    """判断动物生命阶段"""
    if barn["animal"] is None:
        return None
    count = barn.get("production_count", 0)
    purchase = barn.get("purchase_time")
    if purchase is None:
        return "adult"
    # 幼年期：购买后前2次产出减半
    if count < 2:
        return "juvenile"
    # 老年期：40次产出后
    if count >= 40:
        return "elder"
    return "adult"


def can_barn_produce(barn, data):
    """判断栏位是否可产出（需已投喂且等待10分钟后首次产出）"""
    if barn["animal"] is None:
        return False
    a = get_barn_animal(barn["animal_type"])
    if a is None:
        return False

    # 必须投喂过才能生产
    fed = barn.get("fed_time")
    if fed is None:
        return False

    now = now_dt()
    fed_dt = parse_dt(fed)
    elapsed_since_feed = (now - fed_dt).total_seconds() / 60.0

    # 首次产出必须等待 10 分钟
    last = barn.get("last_produce_time")
    if last is None:
        return elapsed_since_feed >= 10

    # 后续按正常周期
    speed_bonus = get_talent_value(data["talent_tree"], "animal_speed")
    barn_speed = 0.0
    for lv in range(2, barn.get("level", 1) + 1):
        eff = barn_upgrade_effects(lv)
        if "speed" in eff:
            barn_speed += eff["speed"]
    if barn.get("level", 1) >= 10:
        barn_speed += 0.10
    total_speed = speed_bonus + barn_speed
    cycle = a["cycle"] * max(0.1, 1.0 - total_speed)

    last_dt = parse_dt(last)
    return (now - last_dt).total_seconds() / 60.0 >= cycle


def _feed_inv(data):
    """获取饲料库存 dict"""
    return data.get("inventory", {}).get("feeds", {})

def check_feed_available(data, animal_name):
    """检查动物所需饲料是否充足"""
    a = get_barn_animal(animal_name)
    if a is None:
        return True
    feed_inv = _feed_inv(data)
    for feed_name, need_qty in a["feed"].items():
        if feed_inv.get(feed_name, 0) < need_qty:
            return False
    return True


def consume_feed(data, animal_name):
    """消耗动物所需饲料"""
    a = get_barn_animal(animal_name)
    if a is None:
        return
    feed_inv = _feed_inv(data)
    for feed_name, need_qty in a["feed"].items():
        feed_inv[feed_name] = max(0, feed_inv.get(feed_name, 0) - need_qty)


def barn_yield_multiplier(barn, data):
    """计算栏位产量倍率"""
    mult = 1.0
    # 栏位升级产量加成
    for lv in range(2, barn.get("level", 1) + 1):
        eff = barn_upgrade_effects(lv)
        if "yield" in eff:
            mult += eff["yield"]
    # 天赋加成
    mult += get_talent_value(data["talent_tree"], "animal_price")
    # 全局加成（栏位10级）
    if barn.get("level", 1) >= 10:
        mult += 0.10
    # 生命阶段
    stage = get_age_stage(barn)
    if stage == "juvenile":
        mult *= 0.5
    elif stage == "elder":
        mult *= 0.7
    return mult


def double_barn_chance(barn, data):
    """双倍产出概率"""
    chance = 0.0
    if barn.get("level", 1) >= 8:
        chance += 0.05
    chance += get_talent_value(data["talent_tree"], "double_animal")
    return chance


def get_animal_feed_name(animal_type):
    """获取动物所需饲料名称"""
    a = get_barn_animal(animal_type)
    if a is None:
        return None
    # 返回第一个饲料名（实际上每个动物只有一种饲料）
    for name in a["feed"]:
        return name
    return None

def process_barn_production(data):
    """处理所有养殖栏位生产（每次刷新或手动收集时调用）
    每产出周期自动消耗饲料，不足则跳过"""
    total_items = 0
    total_exp = 0

    for barn in data["barns"][:data.get("unlocked_barns", INITIAL_BARNS)]:
        if barn["animal"] is None:
            continue
        a = get_barn_animal(barn["animal_type"])
        if a is None:
            continue

        if not can_barn_produce(barn, data):
            continue

        # 每周期消耗饲料
        feed_name = get_animal_feed_name(barn["animal_type"])
        if feed_name:
            need = get_feed_consume(barn["animal_type"], data)
            feed_inv = _feed_inv(data)
            if feed_inv.get(feed_name, 0) < need:
                continue  # 饲料不足，跳过
            feed_inv[feed_name] = feed_inv[feed_name] - need

        # 计算产量（含累积余数）
        mult = barn_yield_multiplier(barn, data)
        base_qty = max(1, int(round(mult)))
        # 累积余数（与土地类似）
        remainder = barn.get("_yield_remainder", 0.0)
        raw = mult + remainder
        qty = max(1, int(floor(raw)))
        barn["_yield_remainder"] = raw - qty

        if random.random() < double_barn_chance(barn, data):
            qty *= 2

        barn["pending_product"] = barn.get("pending_product", 0) + qty
        barn["last_produce_time"] = now_str()
        barn["production_count"] = barn.get("production_count", 0) + 1
        barn["age_stage"] = get_age_stage(barn)

        total_items += qty
        total_exp += a["exp"]
        # 天赋果实掉落
        check_talent_fruit_drop(data)

    if total_items > 0:
        exp_bonus = apply_exp_bonus(data)
        data["exp"] += int(total_exp * exp_bonus)
        data["barn_total_collects"] = data.get("barn_total_collects", 0) + total_items
        try_level_up(data)
        print(f"\n🐔 养殖场产出 {total_items} 件产品，{int(total_exp * exp_bonus)}✨")


def feed_barn_animals(data):
    """投喂动物：消耗饲料，标记投喂时间。
    动物每产出周期自动消耗饲料，饲料不足时跳过产出。
    可对已投喂动物补料（消耗1份饲料更新投喂时间）。"""
    fed_list = []
    no_feed_list = []
    already_fed = []

    for barn in data["barns"][:data.get("unlocked_barns", INITIAL_BARNS)]:
        if barn["animal"] is None:
            continue

        a = get_barn_animal(barn["animal_type"])
        if a is None:
            continue

        # 检查是否已经投喂过（可以补料）
        if barn.get("fed_time") is not None:
            # 检查是否缺料
            feed_name = get_animal_feed_name(barn["animal_type"])
            if feed_name:
                need = get_feed_consume(barn["animal_type"], data)
                feed_inv = _feed_inv(data)
                if feed_inv.get(feed_name, 0) >= need:
                    already_fed.append(barn["animal_type"])
                    continue
            else:
                already_fed.append(barn["animal_type"])
                continue

        # 检查饲料是否足够
        feed_name = get_animal_feed_name(barn["animal_type"])
        if feed_name is None:
            continue
        need = get_feed_consume(barn["animal_type"], data)
        feed_inv = _feed_inv(data)
        if feed_inv.get(feed_name, 0) < need:
            no_feed_list.append(barn["animal_type"])
            continue

        feed_inv[feed_name] = feed_inv[feed_name] - need
        barn["fed_time"] = now_str()
        if barn.get("last_produce_time") is None:
            barn["last_produce_time"] = None  # 首次投喂，等待10分钟后首次产出
        fed_list.append(barn["animal_type"])

    return fed_list, no_feed_list, already_fed


def calc_barn_offline(data):
    """离线养殖收益计算（每周期消耗饲料，不足跳过）"""
    last = parse_dt(data["last_save_time"])
    now = now_dt()
    elapsed = (now - last).total_seconds() / 60.0
    if elapsed <= 1:
        return 0, 0

    total_items = 0
    total_exp = 0
    offline_bonus = 1.0 + get_talent_value(data["talent_tree"], "offline_bonus")
    exp_bonus = apply_exp_bonus(data)
    # 离线期间共享饲料库存
    feed_available = dict(_feed_inv(data))

    for barn in data["barns"][:data.get("unlocked_barns", INITIAL_BARNS)]:
        if barn["animal"] is None:
            continue
        a = get_barn_animal(barn["animal_type"])
        if a is None:
            continue

        if barn.get("fed_time") is None:
            continue

        last_produce = barn.get("last_produce_time")
        if last_produce is None:
            fed_dt = parse_dt(barn["fed_time"])
            if (now - fed_dt).total_seconds() / 60.0 < 10:
                continue
            barn["last_produce_time"] = barn["fed_time"]
            last_produce = barn["last_produce_time"]

        lc = parse_dt(barn["last_produce_time"])
        speed_bonus = get_talent_value(data["talent_tree"], "animal_speed")
        barn_speed = 0.0
        for lv in range(2, barn.get("level", 1) + 1):
            eff = barn_upgrade_effects(lv)
            if "speed" in eff:
                barn_speed += eff["speed"]
        if barn.get("level", 1) >= 10:
            barn_speed += 0.10
        total_speed = speed_bonus + barn_speed
        cycle = a["cycle"] * max(0.1, 1.0 - total_speed)

        if (now - lc).total_seconds() / 60.0 < cycle:
            continue

        n = int(elapsed / cycle)
        if n <= 0:
            continue
        n = min(n, 200)

        # 检查饲料能支撑多少次产出
        feed_name = get_animal_feed_name(barn["animal_type"])
        if feed_name:
            need_per = get_feed_consume(barn["animal_type"], data)
            max_by_feed = feed_available.get(feed_name, 0) // need_per
            n = min(n, max_by_feed)
            if n <= 0:
                continue
            feed_available[feed_name] = feed_available[feed_name] - n * need_per

        mult = barn_yield_multiplier(barn, data)
        base_qty = max(1, int(round(mult)))
        # 累积余数
        remainder = barn.get("_yield_remainder", 0.0)
        raw = mult + remainder
        qty = max(1, int(floor(raw)))
        # 离线多个周期的余数计算
        total_raw = mult * n + remainder
        total_qty = max(n, int(floor(total_raw)))
        barn["_yield_remainder"] = total_raw - total_qty
        qty = total_qty

        dc = double_barn_chance(barn, data)
        if random.random() < dc:
            qty *= 2

        barn["pending_product"] = barn.get("pending_product", 0) + qty
        barn["last_produce_time"] = (lc + datetime.timedelta(minutes=cycle * n)).strftime("%Y-%m-%d %H:%M:%S")
        barn["production_count"] = barn.get("production_count", 0) + n
        barn["age_stage"] = get_age_stage(barn)

        total_items += qty
        total_exp += int(a["exp"] * n * offline_bonus * exp_bonus)

    if total_items > 0:
        data["barn_total_collects"] = data.get("barn_total_collects", 0) + total_items
        # 扣除离线消耗的饲料
        for k, v in feed_available.items():
            _feed_inv(data)[k] = v

    return total_items, int(total_exp)


def collect_all_barns(data):
    """收集所有栏位待收产品"""
    total_items = 0
    total_gold = 0
    inv_products = data["inventory"]["products"]
    collected_items = []

    for barn in data["barns"][:data.get("unlocked_barns", INITIAL_BARNS)]:
        pending = barn.get("pending_product", 0)
        if pending <= 0:
            continue
        a = get_barn_animal(barn["animal_type"])
        if a is None:
            continue

        # 直接进仓库
        inv_products[a["product"]] = inv_products.get(a["product"], 0) + pending
        total_items += pending
        collected_items.append(f"{a['product']}×{pending}")
        barn["pending_product"] = 0

    return total_items, collected_items


def parse_dd(s):
    """安全的日期解析"""
    try:
        return datetime.datetime.strptime(s, "%Y-%m-%d %H:%M:%S")
    except (ValueError, TypeError):
        return now_dt()

# ============ 农业建筑系统 ============

MAX_AGRO_BUILDINGS = 50
INITIAL_AGRO_BUILDINGS = 2

# 饲料配方按等级排序（方便建筑等级映射）
FEED_RECIPES_BY_LEVEL = sorted(FEED_RECIPES, key=lambda r: r["level"])

# ============ 酿酒配方 ============
BREW_RECIPES = [
    {"name": "啤酒",   "ingredients": {"小麦": 3},                "time": 5,  "yield": 2, "sell_price": 200,  "level": 1},
    {"name": "果酒",   "ingredients": {"草莓": 3},                "time": 8,  "yield": 1, "sell_price": 600,  "level": 5},
    {"name": "葡萄酒", "ingredients": {"葡萄": 4},                "time": 15, "yield": 1, "sell_price": 2000, "level": 10},
    {"name": "威士忌", "ingredients": {"玉米": 4, "小麦": 2},     "time": 25, "yield": 1, "sell_price": 4000, "level": 15},
]
BREW_RECIPES_BY_LEVEL = sorted(BREW_RECIPES, key=lambda r: r["level"])

def get_recipe_list(building_type):
    """根据建筑类型返回配方列表"""
    if building_type == "brewery":
        return BREW_RECIPES
    return FEED_RECIPES

def get_recipes_by_level(building_type):
    """根据建筑类型返回按等级排序的配方列表"""
    if building_type == "brewery":
        return BREW_RECIPES_BY_LEVEL
    return FEED_RECIPES_BY_LEVEL

def new_agro_building_slots():
    """创建初始农业建筑位"""
    return [{
        "id": i + 1,
        "unlocked": i < INITIAL_AGRO_BUILDINGS,
        "building": None,
        "level": 1,
        "order": None,
        "start_time": None,
        "ready": False,
        "total_batches": 0,
        "done_batches": 0,
    } for i in range(MAX_AGRO_BUILDINGS)]

def agro_build_cost(building_type="feed_mill"):
    """建造费用（饲料加工厂50000，酿酒厂100000）"""
    return 100000 if building_type == "brewery" else 50000

def agro_upgrade_cost(level):
    """建筑升级费用（1→2: 50000, 2→3: 150000, 3→4: 400000）"""
    costs = {1: 50000, 2: 150000, 3: 400000}
    return costs.get(level, None)

def agro_unlock_cost(slot_id):
    """解锁建筑位费用"""
    base = 1000
    return base + (slot_id - INITIAL_AGRO_BUILDINGS) * 500

def get_available_recipes(building_level, building_type="feed_mill"):
    """根据建筑等级和类型获取可加工配方"""
    recipes_by_level = get_recipes_by_level(building_type)
    available = []
    for i, recipe in enumerate(recipes_by_level):
        if building_level >= i + 1:
            available.append(recipe)
    return available

def check_agro_ready(slot):
    """检查单个建筑位当前批次是否完成"""
    if not slot.get("order") or slot.get("ready"):
        return
    if not slot.get("start_time"):
        return
    st = parse_dd(slot["start_time"])
    all_recipes = get_recipe_list(slot.get("building", "feed_mill"))
    recipe = next((r for r in all_recipes if r["name"] == slot["order"]), None)
    if recipe is None:
        return
    pt = recipe["time"]
    if (now_dt() - st).total_seconds() / 60.0 >= pt:
        slot["ready"] = True
        slot["done_batches"] = slot.get("done_batches", 0) + 1

def process_all_agro_buildings(data):
    """遍历所有建筑，检查完成并自动推进批次"""
    for slot in data.get("agro_buildings", [])[:data.get("unlocked_agro_buildings", INITIAL_AGRO_BUILDINGS)]:
        if not slot.get("building") or not slot.get("order"):
            continue
        check_agro_ready(slot)
        # 当前批次完成且还有剩余批次 → 自动开始下一批
        if slot.get("ready") and slot.get("done_batches", 0) < slot.get("total_batches", 0):
            all_recipes = get_recipe_list(slot.get("building", "feed_mill"))
            recipe = next((r for r in all_recipes if r["name"] == slot["order"]), None)
            if recipe and _consume_recipe_ingredients(data, recipe):
                slot["start_time"] = now_str()
                slot["ready"] = False
            else:
                # 原料不足，暂停
                slot["order"] = None
                slot["ready"] = False

def _consume_recipe_ingredients(data, recipe):
    """消耗配方原料，返回是否成功"""
    inv = data["inventory"]["crops"]
    # 先检查
    for ing_name, ing_qty in recipe["ingredients"].items():
        if ing_name == "任意水果":
            have = sum(inv.get(f, 0) for f in FEED_FRUIT_NAMES)
            if have < ing_qty:
                return False
        else:
            if inv.get(ing_name, 0) < ing_qty:
                return False
    # 再消耗
    for ing_name, ing_qty in recipe["ingredients"].items():
        if ing_name == "任意水果":
            remaining = ing_qty
            for f in FEED_FRUIT_NAMES:
                if remaining <= 0:
                    break
                have = inv.get(f, 0)
                take = min(have, remaining)
                inv[f] = have - take
                remaining -= take
        else:
            inv[ing_name] = inv.get(ing_name, 0) - ing_qty
    return True

def start_agro_production(data, slot_idx, recipe_name, quantity):
    """在指定建筑位开始加工，quantity 为批次数"""
    if slot_idx < 0 or slot_idx >= len(data.get("agro_buildings", [])):
        return False, "无效的建筑位"

    slot = data["agro_buildings"][slot_idx]
    btype = slot.get("building")
    if not btype:
        return False, "该位置没有建筑"
    if slot.get("order") and not slot.get("ready"):
        return False, "正在加工中，请先收取或等待完成"

    all_recipes = get_recipe_list(btype)
    recipe = next((r for r in all_recipes if r["name"] == recipe_name), None)
    if recipe is None:
        return False, "无效的配方"

    available = get_available_recipes(slot.get("level", 1), btype)
    if recipe not in available:
        recipes_by_lv = get_recipes_by_level(btype)
        return False, f"建筑等级不足，需要升级到 Lv.{recipes_by_lv.index(recipe) + 1}"

    if quantity <= 0:
        return False, "数量必须大于0"

    # 消耗第一批原料
    if not _consume_recipe_ingredients(data, recipe):
        return False, "原料不足"

    slot["order"] = recipe_name
    slot["start_time"] = now_str()
    slot["ready"] = False
    slot["total_batches"] = quantity
    slot["done_batches"] = 0
    return True, f"开始加工 {recipe_name}×{quantity}批"

def collect_agro_product(data, slot_idx):
    """收取建筑位已完成的产品（饲料→feeds，酒→products）"""
    if slot_idx < 0 or slot_idx >= len(data.get("agro_buildings", [])):
        return 0, "无效的建筑位"

    slot = data["agro_buildings"][slot_idx]
    btype = slot.get("building")
    if not btype:
        return 0, "该位置没有建筑"

    done = slot.get("done_batches", 0)
    if done <= 0 and not slot.get("ready"):
        return 0, "没有可收取的产品"

    # 也收取当前刚完成的批次
    check_agro_ready(slot)
    done = slot.get("done_batches", 0)

    if done <= 0:
        return 0, "没有可收取的产品"

    all_recipes = get_recipe_list(btype)
    recipe = next((r for r in all_recipes if r["name"] == slot["order"]), None)
    if recipe is None:
        slot["order"] = None
        slot["total_batches"] = 0
        slot["done_batches"] = 0
        slot["ready"] = False
        return 0, "配方数据异常"

    total_yield = recipe["yield"] * done

    # 根据建筑类型放入不同库存
    if btype == "brewery":
        dest = data["inventory"].setdefault("products", {})
    else:
        dest = _feed_inv(data)
    dest[recipe["name"]] = dest.get(recipe["name"], 0) + total_yield

    total = slot.get("total_batches", 0)
    if done >= total:
        slot["order"] = None
        slot["total_batches"] = 0
        slot["done_batches"] = 0
        slot["ready"] = False
        slot["start_time"] = None

    return total_yield, f"{recipe['name']}×{total_yield}（{done}批）"

def build_agro_building(data, slot_idx, building_type="feed_mill"):
    """在空建筑位建造"""
    if slot_idx < 0 or slot_idx >= len(data.get("agro_buildings", [])):
        return False, "无效的建筑位"
    slot = data["agro_buildings"][slot_idx]
    if not slot.get("unlocked"):
        return False, "该建筑位未解锁"
    if slot.get("building"):
        return False, "该位置已有建筑"
    cost = agro_build_cost(building_type)
    if data.get("gold", 0) < cost:
        return False, f"金币不足，需要 {cost}💰"
    data["gold"] = data.get("gold", 0) - cost
    slot["building"] = building_type
    slot["level"] = 1
    type_name = "酿酒厂" if building_type == "brewery" else "饲料加工厂"
    return True, f"建造{type_name}成功！花费 {cost}💰"

def upgrade_agro_building(data, slot_idx):
    """升级建筑"""
    if slot_idx < 0 or slot_idx >= len(data.get("agro_buildings", [])):
        return False, "无效的建筑位"
    slot = data["agro_buildings"][slot_idx]
    if not slot.get("building"):
        return False, "该位置没有建筑"
    lv = slot.get("level", 1)
    if lv >= 4:
        return False, "已满级"
    cost = agro_upgrade_cost(lv)
    if cost is None:
        return False, "无法升级"
    if data.get("gold", 0) < cost:
        return False, f"金币不足，需要 {cost}💰"
    data["gold"] = data.get("gold", 0) - cost
    slot["level"] = lv + 1
    new_recipes = [r["name"] for r in get_available_recipes(lv + 1, slot.get("building", "feed_mill"))]
    return True, f"升级成功！Lv.{lv}→Lv.{lv+1}，可加工：{', '.join(new_recipes)}"

def get_agro_slot_status(slot):
    """获取建筑位状态文本"""
    if not slot.get("building"):
        return "空地"
    btype = slot["building"]
    lv = slot.get("level", 1)
    if btype == "feed_mill":
        name = "饲料加工厂"
    elif btype == "brewery":
        name = "酿酒厂"
    else:
        name = btype
    if slot.get("order"):
        done = slot.get("done_batches", 0)
        total = slot.get("total_batches", 0)
        if slot.get("ready"):
            return f"{name} Lv.{lv} ✅ 第{done}/{total}批完成"
        return f"{name} Lv.{lv} ⏳ {slot['order']} 第{done}/{total}批"
    return f"{name} Lv.{lv} ⬜ 空闲"

# 兼容旧代码的别名
def check_feed_factory_ready(data):
    process_all_agro_buildings(data)

def start_feed_production(data, recipe_idx):
    """兼容旧接口：使用第一个空闲建筑位"""
    if recipe_idx < 0 or recipe_idx >= len(FEED_RECIPES):
        return False
    recipe = FEED_RECIPES[recipe_idx]
    # 找第一个空闲的feed_mill
    for i, slot in enumerate(data.get("agro_buildings", [])[:data.get("unlocked_agro_buildings", INITIAL_AGRO_BUILDINGS)]):
        if slot.get("building") == "feed_mill" and not slot.get("order"):
            ok, _ = start_agro_production(data, i, recipe["name"], 1)
            return ok
    print("❌ 没有空闲的饲料加工厂")
    return False

def collect_feed(data):
    """兼容旧接口：收取所有建筑位"""
    total = 0
    for i, slot in enumerate(data.get("agro_buildings", [])[:data.get("unlocked_agro_buildings", INITIAL_AGRO_BUILDINGS)]):
        if slot.get("building") == "feed_mill":
            qty, _ = collect_agro_product(data, i)
            total += qty
    if total > 0:
        print(f"✅ 收取饲料共 {total} 份！")
        return True
    print("❌ 没有可收取的饲料")
    return False


# ============ 繁殖系统 ============

def can_breed(barn1, barn2, data):
    """检查两只动物是否能繁殖"""
    if barn1["animal"] is None or barn2["animal"] is None:
        return False, "栏位为空"
    if barn1["animal_type"] != barn2["animal_type"]:
        return False, "不同种类无法繁殖"
    if barn1["id"] == barn2["id"]:
        return False, "需选择两个不同栏位"

    # 检查冷却
    now = now_str()
    cd1 = barn1.get("breed_cooldown")
    cd2 = barn2.get("breed_cooldown")
    if cd1 and now < cd1:
        return False, f"栏位{barn1['id']}繁殖冷却中"
    if cd2 and now < cd2:
        return False, f"栏位{barn2['id']}繁殖冷却中"

    # 检查是否成年
    s1 = get_age_stage(barn1)
    s2 = get_age_stage(barn2)
    if s1 != "adult" or s2 != "adult":
        return False, "需要两只成年动物"

    # 检查是否有空闲栏位
    free = any(
        b["animal"] is None and b["unlocked"]
        for b in data["barns"][:data.get("unlocked_barns", INITIAL_BARNS)]
    )
    if not free:
        return False, "没有空闲栏位接收幼崽"

    if data["gold"] < 1000:
        return False, "繁殖需要 1000💰"

    return True, ""


def do_breed(data, barn1_idx, barn2_idx):
    """执行繁殖"""
    b1 = data["barns"][barn1_idx]
    b2 = data["barns"][barn2_idx]

    ok, msg = can_breed(b1, b2, data)
    if not ok:
        return False, msg

    data["gold"] -= 1000

    # 基础75%成功率 + 亲本栏位等级≥5时各+5%（上限90%）
    success_rate = 0.75
    if b1.get("level", 1) >= 5:
        success_rate += 0.05
    if b2.get("level", 1) >= 5:
        success_rate += 0.05
    success_rate = min(success_rate, 0.9)

    success = random.random() < success_rate
    if not success:
        # 失败退回500💰，冷却15分钟
        data["gold"] += 500
        cd = (now_dt() + datetime.timedelta(minutes=15)).strftime("%Y-%m-%d %H:%M:%S")
        b1["breed_cooldown"] = cd
        b2["breed_cooldown"] = cd
        return False, "繁殖失败！退回500💰，亲本冷却15分钟"

    # 找空闲栏位放幼崽
    free_idx = None
    for i, b in enumerate(data["barns"][:data.get("unlocked_barns", INITIAL_BARNS)]):
        if b["animal"] is None and b["unlocked"]:
            free_idx = i
            break

    if free_idx is None:
        return False, "没有空闲栏位！"

    # 繁殖成功
    new_barn = data["barns"][free_idx]
    new_barn["animal"] = b1["animal"] + "宝宝"
    new_barn["animal_type"] = b1["animal_type"]
    new_barn["purchase_time"] = now_str()
    new_barn["age_stage"] = "juvenile"
    new_barn["production_count"] = 0
    new_barn["last_produce_time"] = None
    new_barn["pending_product"] = 0

    # 幼崽2小时成熟后才开始生产
    new_barn["breed_cooldown"] = (now_dt() + datetime.timedelta(hours=2)).strftime("%Y-%m-%d %H:%M:%S")
    # 这个 cooldown 用作成熟时间，到期后改为 None 并且 age_stage 改为 juvenile
    # 实际上幼崽从breed_cooldown到期后开始算juvenile

    # 亲本冷却15分钟
    cd = (now_dt() + datetime.timedelta(minutes=15)).strftime("%Y-%m-%d %H:%M:%S")
    b1["breed_cooldown"] = cd
    b2["breed_cooldown"] = cd

    return True, f"🎉 繁殖成功！{b1['animal_type']}宝宝已安置在栏位 {free_idx + 1}"


def check_baby_mature(data):
    """检查幼崽是否成熟"""
    now = now_str()
    for barn in data["barns"][:data.get("unlocked_barns", INITIAL_BARNS)]:
        if barn["animal"] is None:
            continue
        cd = barn.get("breed_cooldown")
        if cd and barn.get("age_stage") == "juvenile" and barn.get("production_count", 0) == 0:
            # 这可能是刚出生的幼崽，检查是否过了成熟期
            if now >= cd:
                barn["breed_cooldown"] = None
                barn["age_stage"] = "juvenile"  # 仍然是juvenile（前2次产出减半）
                barn["last_produce_time"] = cd  # 从成熟开始算产出时间
                print(f"  🐣 栏位{barn['id']}的{barn['animal_type']}已成熟！")



# ============ 增强版离线计算 ============

def calc_offline_crops_v2(data):
    """增强版离线作物计算（含土地升级、天赋加速、暴风延时的实际生长时间）
    返回 (gold, exp, count)"""
    crops = load_crops()
    try:
        last = parse_dt(data["last_save_time"])
    except (ValueError, TypeError):
        return 0, 0, 0
    now = now_dt()
    elapsed = (now - last).total_seconds() / 60.0
    if elapsed <= 0:
        return 0, 0, 0

    gold, exp, count = 0, 0, 0
    talent_tree = data.get("talent_tree", {})
    season = get_season(data)[0]

    for land in data["lands"][:data.get("unlocked_lands", INITIAL_LANDS)]:
        if not land.get("crop") or not land.get("plant_time"):
            continue
        c = crops.get(land["crop"])
        if not c:
            continue
        try:
            pt = parse_dt(land["plant_time"])
        except (ValueError, TypeError):
            continue

        # 使用实际生长时间（含土地升级+天赋+暴风延时）
        actual_growth = calc_growth_time(land["crop"], land.get("upgrade_level", 1), talent_tree, land)
        if (now - pt).total_seconds() / 60.0 < actual_growth:
            continue

        # 计算离线期间完成的完整周期数
        n = min(int(elapsed / actual_growth), 100)
        if n <= 0:
            continue

        # 计算实际产量倍率（土地等级+丰收季节+天赋）
        mult = calc_yield_multiplier(land.get("upgrade_level", 1), talent_tree, land["crop"], season)

        # 逐周期累积产量（使用累积余数机制避免小数损失）
        total_qty = 0
        for _ in range(n):
            total_qty += calc_harvest_yield(land, 1.0, mult)

        gold += int(c["sell_price"] * total_qty)
        exp += c["exp"] * n
        count += n

        # 更新种植时间到最后一个完成的周期结束
        land["plant_time"] = (
            pt + datetime.timedelta(minutes=actual_growth * n)
        ).strftime("%Y-%m-%d %H:%M:%S")

    # 地块2 离线计算
    page2_lands = data.get("lands_page2", [])
    page2_unlocked = data.get("unlocked_lands_page2", INITIAL_LANDS)
    for land in page2_lands[:page2_unlocked]:
        if not land.get("crop") or not land.get("plant_time"):
            continue
        c = crops.get(land["crop"])
        if not c:
            continue
        try:
            pt = parse_dt(land["plant_time"])
        except (ValueError, TypeError):
            continue
        actual_growth = calc_growth_time(land["crop"], land.get("upgrade_level", 1), talent_tree, land)
        if (now - pt).total_seconds() / 60.0 < actual_growth:
            continue
        n = min(int(elapsed / actual_growth), 100)
        if n <= 0:
            continue
        mult = calc_yield_multiplier(land.get("upgrade_level", 1), talent_tree, land["crop"], season)
        total_qty = 0
        for _ in range(n):
            total_qty += calc_harvest_yield(land, 1.0, mult)
        gold += int(c["sell_price"] * total_qty)
        exp += c["exp"] * n
        count += n
        land["plant_time"] = (
            pt + datetime.timedelta(minutes=actual_growth * n)
        ).strftime("%Y-%m-%d %H:%M:%S")

    if count > 0:
        data["gold"] = data.get("gold", 0) + gold
        data["exp"] = data.get("exp", 0) + exp
        try_level_up(data)

    return gold, exp, count


def calc_offline_agro_v2(data):
    """离线农业建筑处理（处理离线期间完成的多批加工），返回 (total_produced, total_batches)"""
    now = now_dt()
    try:
        last = parse_dt(data["last_save_time"])
    except (ValueError, TypeError):
        return 0, 0
    elapsed = (now - last).total_seconds() / 60.0
    if elapsed <= 0:
        return 0, 0

    total_produced = 0
    total_batches = 0

    for slot in data.get("agro_buildings", [])[:data.get("unlocked_agro_buildings", INITIAL_AGRO_BUILDINGS)]:
        if not slot.get("building") or not slot.get("order"):
            continue
        if not slot.get("start_time"):
            continue

        all_recipes = get_recipe_list(slot.get("building", "feed_mill"))
        recipe = next((r for r in all_recipes if r["name"] == slot["order"]), None)
        if not recipe:
            continue

        done = slot.get("done_batches", 0)
        total = slot.get("total_batches", 0)
        if done >= total:
            continue

        batch_time = recipe["time"]

        # 从 start_time 到现在经过了多少分钟
        st = parse_dd(slot["start_time"])
        elapsed_from_start = (now - st).total_seconds() / 60.0

        # 理论上能完成的批次数
        possible = int(elapsed_from_start / batch_time)
        possible = possible - done  # 扣除已完成的
        if possible <= 0:
            continue
        possible = min(possible, total - done)

        # 逐批消耗原料进行加工
        processed = 0
        dest = data["inventory"].setdefault("products", {}) if slot["building"] == "brewery" else _feed_inv(data)

        for _ in range(possible):
            if _consume_recipe_ingredients(data, recipe):
                done += 1
                processed += 1
            else:
                break  # 原料不足，停止后续批次

        if processed == 0:
            continue

        # 产出计算
        produced = recipe["yield"] * processed
        dest[recipe["name"]] = dest.get(recipe["name"], 0) + produced
        slot["done_batches"] = done

        if done >= total:
            slot["order"] = None
            slot["total_batches"] = 0
            slot["done_batches"] = 0
            slot["ready"] = False
            slot["start_time"] = None
        else:
            # 更新 start_time 到最后一个完成批次的结束时间
            slot["start_time"] = (st + datetime.timedelta(minutes=batch_time * done)).strftime("%Y-%m-%d %H:%M:%S")
            slot["ready"] = False

        total_produced += produced
        total_batches += processed

    return total_produced, total_batches


def calc_offline_v2(data):
    """增强版离线收益（含养殖场+农业建筑+工厂），返回 (gold, exp, total_count)"""
    # 1. 工厂加工状态离线检测
    check_factories_ready(data)

    # 2. 作物离线计算（使用实际生长时间）
    gold, exp, count = calc_offline_crops_v2(data)

    # 3. 养殖场离线计算
    items, barn_exp = calc_barn_offline(data)

    # 4. 农业建筑离线计算（饲料/酿酒多批次加工）
    agro_produced, agro_batches = calc_offline_agro_v2(data)

    exp_bonus = apply_exp_bonus(data)
    exp = int(exp * exp_bonus)

    parts = []
    if count > 0:
        parts.append(f"作物收获 {count} 次，获得 {gold}💰 {exp}✨")
    if items > 0:
        parts.append(f"养殖场产出 {items} 件")
    if agro_batches > 0:
        parts.append(f"农业建筑完成 {agro_batches} 批，产出 {agro_produced} 件")
    if parts:
        print(f"\n📦 离线收益：{'，'.join(parts)}")
        if barn_exp > 0:
            print(f"   养殖场获得 {barn_exp}✨（含离线加成）")

    return gold, exp + barn_exp, count + items


# ============ 金色南瓜彩蛋 ============

def check_golden_pumpkin(data):
    """南瓜首次成熟时1%概率变金色南瓜，一生仅一次"""
    now = now_dt()
    for land in data["lands"][:data.get("unlocked_lands", 6)]:
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
        growth = calc_growth_time("南瓜", land.get("upgrade_level", 1), data.get("talent_tree", {}))
        if (now - pt).total_seconds() / 60.0 < growth:
            continue
        # 首次成熟，一生一次的2%判定
        land["_maturity_roll_done"] = True
        if random.random() < 0.02:
            land["golden_pumpkin"] = True
            land["plant_time"] = now_str()
            print("  🌟 彩蛋！一块南瓜田变成了金色南瓜！再等一个生长周期即可收获！")

    # 地块2 金色南瓜检测
    for land in data.get("lands_page2", [])[:data.get("unlocked_lands_page2", INITIAL_LANDS)]:
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
        growth = calc_growth_time("南瓜", land.get("upgrade_level", 1), data.get("talent_tree", {}))
        if (now - pt).total_seconds() / 60.0 < growth:
            continue
        land["_maturity_roll_done"] = True
        if random.random() < 0.02:
            land["golden_pumpkin"] = True
            land["plant_time"] = now_str()
            print("  🌟 彩蛋！一块南瓜田变成了金色南瓜！再等一个生长周期即可收获！")
