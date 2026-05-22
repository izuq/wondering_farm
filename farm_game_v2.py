# -*- coding: utf-8 -*-
"""
开心农场 v2.0 — 动物养殖场模块增强版
基于 farm.py 添加完整的养殖场系统（与土地对称的50栏位、饲料、繁殖）
"""
import sys
import os
import json
import datetime
import time
import random
import threading
from math import floor

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
    TALENTS_LIST = [(t["id"], t["group"], t["name"], t["max_lv"], t["desc"], t["effect_per_lv"]) for t in _t_raw]
    EVENTS = _load_json("events.json")
    # 成就元数据从 JSON 加载，check_fn 由注册表提供
    _ach_meta_dir = os.path.join(_DATA_DIR, "achievements.json")
    _ach_meta = _load_json("achievements.json") if os.path.exists(_ach_meta_dir) else []
    _rebuild_achievements(_ach_meta)

# reload_config() 将在注册表初始化后调用

# ============ 从 farm.py 导入基础逻辑 ============
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from farm import (
    MAX_LANDS, REFRESH_INTERVAL, AUTO_SAVE_INTERVAL, SAVE_FILE,
    load_crops, new_save, try_level_up, write_save, calc_offline,
    do_plant, do_harvest, show_lands, show_help,
    header, menu, clear, read_int, pause, get_key,
)

# ============ 养殖场常量 ============
MAX_BARNS = 50
INITIAL_BARNS = 6
SAVE_FILE_V2 = "save.json"  # 与基础版共用存档

# ============ 核心游戏常量（原在 farm.py 完整版中） ============
INITIAL_LANDS = 6
WAREHOUSE_CAPACITY = 100
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
    lands = data.get("lands", [])
    targets = [l for l in lands if l.get("crop")]
    if targets:
        t = random.choice(targets)
        print(f"  💥 {t['crop']} 被虫灾摧毁！")
        t["crop"] = None
        t["plant_time"] = None

def _event_wind_damage(data, event, crops):
    lands = data.get("lands", [])
    targets = [l for l in lands if l.get("crop")]
    if targets:
        t = random.choice(targets)
        print(f"  💨 {t['crop']} 被暴风吹毁！")
        t["crop"] = None
        t["plant_time"] = None

def _event_alien_attack(data, event, crops):
    lands = data.get("lands", [])
    targets = [l for l in lands if l.get("crop")]
    if targets:
        damaged = random.sample(targets, min(random.randint(1, 3), len(targets)))
        for t in damaged:
            print(f"  👽 {t['crop']} 被外星人飞船损坏！")
            t["crop"] = None
            t["plant_time"] = None
    data["gold"] = data.get("gold", 0) + 1000
    print(f"  💰 外星人留下1000💰作为赔偿！")

# 前3个正面事件没有额外效果（仅标记 duration）
# 神秘商人也没有额外效果（get_merchant_discount 检查 event_active）

# ———— 注册默认事件处理器 ————
register_event_handler("pest_attack", _event_pest_attack)
register_event_handler("wind_damage", _event_wind_damage)
register_event_handler("alien_attack", _event_alien_attack)

# ============ 加载 JSON 配置（必须在注册表初始化后） ============
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
    "春": ["小麦", "水稻"],
    "夏": ["玉米", "玫瑰"],
    "秋": ["南瓜", "胡萝卜"],
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

def calc_growth_time(crop_name, land_level, talent_tree):
    """计算作物生长时间（分钟）"""
    crops = load_crops()
    c = crops.get(crop_name, {})
    base = c.get("growth_minutes", 10)
    speed_bonus = get_talent_value(talent_tree, "grow_speed")
    land_bonus = (land_level - 1) * 0.05
    return base * max(0.1, 1.0 - speed_bonus - land_bonus)

def calc_yield_multiplier(land_level, talent_tree, crop_name, season):
    mult = 1.0 + (land_level - 1) * 0.1 + get_talent_value(talent_tree, "yield_bonus")
    bonus = season_crop_bonus(crop_name, season)
    if bonus > 1.0:
        mult *= bonus
    return mult

def get_double_chance(land_level, talent_tree):
    chance = (land_level - 1) * 0.02 + get_talent_value(talent_tree, "double_harvest")
    return min(chance, 0.9)

def inventory_usage(data):
    inv = data.get("inventory", {})
    return len(inv.get("crops", {})) + len(inv.get("products", {})) + len(inv.get("seeds", {}))

def inventory_space(data):
    return WAREHOUSE_CAPACITY - inventory_usage(data)

def land_upgrade_cost(level):
    costs = {1: 200, 2: 500, 3: 1000, 4: 2000, 5: 4000,
             6: 8000, 7: 15000, 8: 30000, 9: 60000}
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
    else:
        handler = get_event_handler(event["name"])
        if handler:
            handler(data, event, crops)

def try_trigger_event(data, crops):
    """尝试触发随机事件（约10%概率）
    负面事件（虫灾/暴风）每3小时最多触发一次"""
    _remove_expired_events(data)
    if random.random() > 0.1:
        return
    # 不在事件中才触发
    active = data.get("event_active", {})
    event = random.choice(EVENTS)
    if event["name"] in active:
        return

    # 负面事件3小时冷却检查
    if not event["positive"]:
        last_disaster = data.get("_last_disaster_time")
        if last_disaster:
            elapsed = (now_dt() - parse_dt(last_disaster)).total_seconds() / 60.0
            if elapsed < 180:
                return  # 3小时内不再触发负面事件
        data["_last_disaster_time"] = now_str()

    _apply_event_effect(data, event, crops)
    print(event["desc"])

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
                    data["diamond"] = data.get("diamond", 0) + v
            print(f"🏆 达成成就：{name}！获得奖励！")
    if new_count > 0:
        data["achievements"] = list(completed)
    return new_count

# ============ 终端版功能函数（原在 farm.py 完整版中） ============

def do_sell(data, crops):
    """终端版出售菜单"""
    print("\n  💰 出售\n" + "=" * 50)
    inv = data.get("inventory", {})
    crops_inv = inv.get("crops", {})
    prod_inv = inv.get("products", {})
    if not crops_inv and not prod_inv:
        print("没有可出售的物品")
        pause()
        return
    total = 0
    for name, qty in list(crops_inv.items()):
        if name == "金色南瓜":
            price = int(12000 * (1.0 + get_talent_value(data.get("talent_tree", {}), "sell_bonus")))
        else:
            c = crops.get(name, {})
            price = int(c.get("sell_price", 0) * (1.0 + get_talent_value(data.get("talent_tree", {}), "sell_bonus")))
        gold = qty * price
        total += gold
        print(f"  {name}×{qty} → {gold}💰")
        del crops_inv[name]
    for name, qty in list(prod_inv.items()):
        pf = next((x for x in FACTORY_LIST if x["product"] == name), None)
        if pf:
            price = int(pf["sell_price"] * (1.0 + get_talent_value(data.get("talent_tree", {}), "sell_bonus")))
            gold = qty * price
            total += gold
            print(f"  {name}×{qty} → {gold}💰")
            del prod_inv[name]
    if total > 0:
        data["gold"] = data.get("gold", 0) + total
        data["total_earnings"] = data.get("total_earnings", 0) + total
        print(f"  共获得 {total}💰")
    pause()

def do_factories(data):
    """终端版加工菜单"""
    while True:
        clear()
        header(data)
        print(f"\n  🏭 工厂加工\n" + "=" * 50)
        for f in FACTORY_LIST:
            fc = data["factories"].get(f["factory"], {})
            unlocked = data["level"] >= f["level"]
            if not unlocked:
                print(f"  🔒 {f['factory']}  需Lv.{f['level']}")
                continue
            if fc.get("ready"):
                print(f"  ✅ {f['factory']} → {f['product']}  可收取！")
                continue
            if fc.get("current_order"):
                st = parse_dt(fc["start_time"])
                remain = max(0, f["time"] - (now_dt() - st).total_seconds() / 60.0)
                print(f"  ⏳ {f['factory']} → {f['product']}  剩余 {remain:.0f}min")
                continue
            ings = []
            for ing, qty in f["ingredients"].items():
                have = data["inventory"]["crops"].get(ing, 0)
                ings.append(f"{ing}×{qty}(有{have})")
            print(f"  ⬜ {f['factory']} → {f['product']}  {'+'.join(ings)}  ⏱{f['time']}min")
        ch = read_int("\n选择工厂? (1-{} 收取, 0返回): ".format(len(FACTORY_LIST)), 0, len(FACTORY_LIST))
        if ch == 0:
            break
        f = FACTORY_LIST[ch - 1]
        fc = data["factories"].get(f["factory"], {})
        if fc.get("ready"):
            fc["current_order"] = None
            fc["start_time"] = None
            fc["ready"] = False
            data["inventory"]["products"][f["product"]] = data["inventory"]["products"].get(f["product"], 0) + 1
            print(f"✅ 收取 {f['product']}")
            pause()
            continue
        if fc.get("current_order"):
            print("⏳ 加工中...")
            pause()
            continue
        # 检查原料
        ok = True
        for ing, qty in f["ingredients"].items():
            if data["inventory"]["crops"].get(ing, 0) < qty:
                print(f"❌ {ing}不足")
                ok = False
        if not ok:
            pause()
            continue
        for ing, qty in f["ingredients"].items():
            data["inventory"]["crops"][ing] -= qty
        fc["current_order"] = f["product"]
        fc["start_time"] = now_str()
        fc["ready"] = False
        print(f"✅ 开始加工 {f['product']}")
        pause()

def do_upgrade_land(data):
    """终端版土地升级"""
    print("\n  ⬆️ 土地升级\n" + "=" * 50)
    total = data.get("unlocked_lands", INITIAL_LANDS)
    for i, land in enumerate(data["lands"][:total], 1):
        lv = land.get("upgrade_level", 1)
        if lv >= 10:
            print(f"  #{i}  [{'空' if not land.get('crop') else land['crop']}]  Lv.{lv} MAX")
        else:
            cost = land_upgrade_cost(lv)
            flag = "✅" if cost and data["gold"] >= cost else "❌"
            print(f"  #{i}  [{'空' if not land.get('crop') else land['crop']}]  Lv.{lv}→{lv+1}  {cost}💰{flag}")
    ch = read_int(f"\n选择土地升级 (1-{total}, 0返回): ", 0, total)
    if ch == 0:
        return
    land = data["lands"][ch - 1]
    lv = land.get("upgrade_level", 1)
    if lv >= 10:
        print("已满级！")
        pause()
        return
    cost = land_upgrade_cost(lv)
    if not cost or data["gold"] < cost:
        print("金币不足！")
        pause()
        return
    data["gold"] -= cost
    land["upgrade_level"] = lv + 1
    print(f"✅ 土地 #{ch} 升级到 Lv.{lv + 1}")
    pause()

def do_talents(data):
    """终端版天赋"""
    while True:
        clear()
        header(data)
        print(f"\n  ⭐ 天赋树  天赋点: {data.get('talent_points', 0)}\n" + "=" * 50)
        for grp in TALENT_GROUPS:
            print(f"\n  ── {grp} ──")
            for t in TALENTS_LIST:
                if t[1] != grp:
                    continue
                _, name, max_lv, desc, _ = t
                level = data.get("talent_tree", {}).get(name, 0)
                bar = "■" * level + "□" * (max_lv - level)
                status = "MAX" if level >= max_lv else f"{level}/{max_lv}"
                print(f"    {name:<16} {bar} {status}  {desc}")
        ch = read_int("\n输入天赋名学习 (0返回): ", 0, 0)
        if ch == 0:
            break
        # 简化：直接用数字选择
        all_talents = [t for t in TALENTS_LIST]
        for i, t in enumerate(all_talents, 1):
            print(f"  {i}. {t[2]}")
        sel = read_int(f"\n选择 (1-{len(all_talents)}, 0返回): ", 0, len(all_talents))
        if sel == 0:
            break
        t = all_talents[sel - 1]
        _, name, max_lv, desc, _ = t
        level = data.get("talent_tree", {}).get(name, 0)
        if level >= max_lv:
            print(f"{name} 已满级！")
            pause()
            continue
        if data.get("talent_points", 0) <= 0:
            print("天赋点不足！")
            pause()
            continue
        data.setdefault("talent_tree", {})[name] = data["talent_tree"].get(name, 0) + 1
        data["talent_points"] -= 1
        print(f"✅ 学习 {name} Lv.{data['talent_tree'][name]}")
        pause()

def do_achievements(data):
    """终端版成就"""
    clear()
    header(data)
    print(f"\n  🏆 成就\n" + "=" * 50)
    completed = set(data.get("achievements", []))
    for name, cond_str, _, reward in ACHIEVEMENTS_LIST:
        done = name in completed
        if name == "完美主义者":
            done = all(a[0] in completed or a[0] == "完美主义者" for a in ACHIEVEMENTS_LIST)
        icon = "✅" if done else "🔲"
        r = ", ".join(f"{v}{k}" for k, v in reward.items() if v)
        print(f"  {icon} {name:<10} {cond_str:<20} [奖励: {r}]")
    pause()

def do_unlock_land(data):
    """终端版解锁土地"""
    if data.get("unlocked_lands", INITIAL_LANDS) >= MAX_LANDS:
        print("所有土地已解锁！")
        pause()
        return
    next_id = data["unlocked_lands"] + 1
    cost = 200 * next_id
    req_level = (next_id - 1) // 5 + 1
    print(f"\n  解锁土地 #{next_id}")
    print(f"  要求: Lv.{req_level}  {cost}💰")
    print(f"  当前: Lv.{data['level']}  {data['gold']:,}💰")
    if data["level"] >= req_level and data["gold"] >= cost:
        ch = read_int("解锁? (1=是, 0=返回): ", 0, 1)
        if ch == 1:
            data["gold"] -= cost
            data["unlocked_lands"] = next_id
            print(f"✅ 解锁第 {next_id} 号土地！")
            pause()
    else:
        print("❌ 条件不足")
        pause()

# ============ 饲料水果名（固定） ============
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
        data["feed_inventory"] = {"基础饲料": 0, "精制饲料": 0, "高级饲料": 0, "特殊饲料": 0}
        data["feed_factory"] = {"level": 1, "current_order": None, "start_time": None, "ready": False}
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
    data.setdefault("feed_inventory", {"基础饲料": 0, "精制饲料": 0, "高级饲料": 0, "特殊饲料": 0})
    if "feed_factory" not in data:
        data["feed_factory"] = {"level": 1, "current_order": None, "start_time": None, "ready": False}
    data["feed_factory"].setdefault("level", 1)
    data.setdefault("barn_total_collects", 0)

    # 兼容旧存档：补充核心游戏字段
    data.setdefault("unlocked_lands", INITIAL_LANDS)
    data.setdefault("diamond", 0)
    data.setdefault("total_harvests", 0)
    data.setdefault("total_earnings", 0)
    data.setdefault("total_processed", 0)
    data.setdefault("talent_points", 0)
    data.setdefault("talent_tree", {})
    data.setdefault("achievements", [])
    data.setdefault("event_active", {})
    data.setdefault("inventory", {"crops": {}, "seeds": {}, "products": {}})
    inv = data["inventory"]
    inv.setdefault("crops", {})
    inv.setdefault("seeds", {})
    inv.setdefault("products", {})
    # 土地补全 upgrade_level / golden_pumpkin
    for land in data.get("lands", []):
        land.setdefault("upgrade_level", 1)
        land.setdefault("golden_pumpkin", False)
        land.setdefault("_maturity_roll_done", False)
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
             6: 20000, 7: 40000, 8: 80000, 9: 150000}
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


def check_feed_available(data, animal_name):
    """检查动物所需饲料是否充足"""
    a = get_barn_animal(animal_name)
    if a is None:
        return True
    feed_inv = data.get("feed_inventory", {})
    for feed_name, need_qty in a["feed"].items():
        if feed_inv.get(feed_name, 0) < need_qty:
            return False
    return True


def consume_feed(data, animal_name):
    """消耗动物所需饲料"""
    a = get_barn_animal(animal_name)
    if a is None:
        return
    feed_inv = data.get("feed_inventory", {})
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


def process_barn_production(data):
    """处理所有养殖栏位生产（每次刷新或手动收集时调用）
    不再消耗饲料——饲料在投喂时一次性消耗"""
    now = now_dt()
    total_items = 0
    total_exp = 0

    for barn in data["barns"][:data.get("unlocked_barns", INITIAL_BARNS)]:
        if barn["animal"] is None:
            continue
        a = get_barn_animal(barn["animal_type"])
        if a is None:
            continue

        # 检查是否已投喂且可产出（不再重复消耗饲料）
        if not can_barn_produce(barn, data):
            continue

        # 计算产量
        mult = barn_yield_multiplier(barn, data)
        qty = max(1, int(round(mult)))

        # 双倍几率
        if random.random() < double_barn_chance(barn, data):
            qty *= 2

        # 产出进 pending
        barn["pending_product"] = barn.get("pending_product", 0) + qty
        barn["last_produce_time"] = now_str()
        barn["production_count"] = barn.get("production_count", 0) + 1
        barn["age_stage"] = get_age_stage(barn)

        total_items += qty
        total_exp += a["exp"]

    if total_items > 0:
        data["exp"] += total_exp
        data["barn_total_collects"] = data.get("barn_total_collects", 0) + total_items
        try_level_up(data)
        print(f"\n🐔 养殖场产出 {total_items} 件产品，{total_exp}✨")


def feed_barn_animals(data):
    """一次性投喂：消耗饲料，记录投喂时间。
    之后动物可持续产出（无需再消耗饲料）。"""
    fed_list = []
    no_feed_list = []
    already_fed = []

    for barn in data["barns"][:data.get("unlocked_barns", INITIAL_BARNS)]:
        if barn["animal"] is None:
            continue
        if barn.get("fed_time") is not None:
            already_fed.append(barn["animal_type"])
            continue

        a = get_barn_animal(barn["animal_type"])
        if a is None:
            continue

        if not check_feed_available(data, barn["animal_type"]):
            no_feed_list.append(barn["animal_type"])
            continue

        consume_feed(data, barn["animal_type"])
        barn["fed_time"] = now_str()
        fed_list.append(barn["animal_type"])

    return fed_list, no_feed_list, already_fed


def calc_barn_offline(data):
    """离线养殖收益计算"""
    last = parse_dt(data["last_save_time"])
    now = now_dt()
    elapsed = (now - last).total_seconds() / 60.0
    if elapsed <= 1:
        return 0, 0

    total_items = 0
    total_exp = 0
    offline_bonus = 1.0 + get_talent_value(data["talent_tree"], "offline_bonus")

    for barn in data["barns"][:data.get("unlocked_barns", INITIAL_BARNS)]:
        if barn["animal"] is None:
            continue
        a = get_barn_animal(barn["animal_type"])
        if a is None:
            continue

        # 未投喂的动物离线不产出
        if barn.get("fed_time") is None:
            continue

        last_produce = barn.get("last_produce_time")
        if last_produce is None:
            # 首次产出：需要从投喂开始等10分钟
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

        mult = barn_yield_multiplier(barn, data)
        qty = max(1, int(round(mult)))

        dc = double_barn_chance(barn, data)
        if random.random() < dc:
            qty *= 2

        barn["pending_product"] = barn.get("pending_product", 0) + qty * n
        barn["last_produce_time"] = (lc + datetime.timedelta(minutes=cycle * n)).strftime("%Y-%m-%d %H:%M:%S")
        barn["production_count"] = barn.get("production_count", 0) + n
        barn["age_stage"] = get_age_stage(barn)

        total_items += qty * n
        total_exp += int(a["exp"] * n * offline_bonus)

    if total_items > 0:
        data["barn_total_collects"] = data.get("barn_total_collects", 0) + total_items

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


# ============ 饲料加工 ============

def check_feed_factory_ready(data):
    """检查饲料厂是否完成"""
    ff = data.get("feed_factory", {})
    if ff.get("ready") or not ff.get("current_order") or not ff.get("start_time"):
        return
    st = parse_dd(ff["start_time"])
    recipe = next((r for r in FEED_RECIPES if r["name"] == ff["current_order"]), None)
    if recipe is None:
        return
    pt = recipe["time"]
    if (now_dt() - st).total_seconds() / 60.0 >= pt:
        ff["ready"] = True


def parse_dd(s):
    """安全的日期解析"""
    try:
        return datetime.datetime.strptime(s, "%Y-%m-%d %H:%M:%S")
    except (ValueError, TypeError):
        return now_dt()


def start_feed_production(data, recipe_idx):
    """开始加工饲料"""
    if recipe_idx < 0 or recipe_idx >= len(FEED_RECIPES):
        return False
    recipe = FEED_RECIPES[recipe_idx]
    ff = data.get("feed_factory", {})

    if ff.get("current_order") and not ff.get("ready"):
        print(f"⏳ 饲料厂正在生产中...")
        return False

    if data["level"] < recipe["level"]:
        print(f"❌ 需要等级 {recipe['level']}")
        return False

    # 检查原料
    inv = data["inventory"]["crops"]
    for ing_name, ing_qty in recipe["ingredients"].items():
        if ing_name == "任意水果":
            have = sum(inv.get(f, 0) for f in FEED_FRUIT_NAMES)
            if have < ing_qty:
                print(f"❌ 原料不足：需要任意水果×{ing_qty}，当前有 {have}")
                return False
        else:
            if inv.get(ing_name, 0) < ing_qty:
                print(f"❌ {ing_name}不足：需要{ing_qty}，当前有{inv.get(ing_name, 0)}")
                return False

    # 消耗原料
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

    # 开始加工
    ff["current_order"] = recipe["name"]
    ff["start_time"] = now_str()
    ff["ready"] = False
    print(f"✅ 开始加工 {recipe['name']}，{recipe['time']}分钟后完成，可产 {recipe['yield']} 份")
    return True


def collect_feed(data):
    """收取完成的饲料"""
    ff = data.get("feed_factory", {})
    if not ff.get("ready"):
        print("❌ 饲料厂没有可收取的饲料")
        return False

    recipe = next((r for r in FEED_RECIPES if r["name"] == ff["current_order"]), None)
    if recipe is None:
        ff["current_order"] = None
        ff["start_time"] = None
        ff["ready"] = False
        return False

    feed_qty = recipe["yield"]
    feed_inv = data.get("feed_inventory", {})
    feed_inv[recipe["name"]] = feed_inv.get(recipe["name"], 0) + feed_qty

    ff["current_order"] = None
    ff["start_time"] = None
    ff["ready"] = False
    print(f"✅ 收取 {recipe['name']}×{feed_qty}！")
    return True


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

    # 70% 成功率
    success = random.random() < 0.7
    if not success:
        # 冷却30分钟
        cd = (now_dt() + datetime.timedelta(minutes=30)).strftime("%Y-%m-%d %H:%M:%S")
        b1["breed_cooldown"] = cd
        b2["breed_cooldown"] = cd
        return False, "繁殖失败！1000💰已消耗，亲本冷却30分钟"

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

    # 亲本冷却30分钟
    cd = (now_dt() + datetime.timedelta(minutes=30)).strftime("%Y-%m-%d %H:%M:%S")
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


# ============ 养殖场UI ============

def show_barn_header(data):
    """养殖场状态栏"""
    total = data.get("unlocked_barns", INITIAL_BARNS)
    occupied = sum(1 for b in data["barns"][:total] if b["animal"] is not None)
    pending = sum(b.get("pending_product", 0) for b in data["barns"][:total])
    feed_total = sum(data.get("feed_inventory", {}).values())
    print(f"  🐔 栏位: {occupied}/{total}   待收: {pending}   饲料: {feed_total}份")


def show_barns(data):
    """显示养殖栏位网格"""
    total = data.get("unlocked_barns", INITIAL_BARNS)
    now = now_dt()

    for i, barn in enumerate(data["barns"][:total], 1):
        lv = barn.get("level", 1)
        if barn["animal"] is None:
            unlocked_flag = "✅" if barn.get("unlocked", False) else "🔒"
            print(f"  [{i:>2}] {unlocked_flag} 空闲  Lv.{lv}", end="")
        else:
            a = get_barn_animal(barn["animal_type"])
            stage = get_age_stage(barn)
            stage_icon = {"juvenile": "🐣", "adult": "🐔", "elder": "👴"}.get(stage, "🐔")
            pending = barn.get("pending_product", 0)

            if pending > 0:
                status = f"✅ 可收({pending})"
            elif can_barn_produce(barn, data):
                feed_ok = check_feed_available(data, barn["animal_type"])
                if feed_ok:
                    status = "🔄 生产中"
                else:
                    status = "❌ 缺饲料"
            else:
                last = barn.get("last_produce_time")
                if last:
                    a_data = get_barn_animal(barn["animal_type"])
                    speed_bonus = get_talent_value(data["talent_tree"], "animal_speed")
                    barn_speed = 0.0
                    for lv2 in range(2, barn.get("level", 1) + 1):
                        eff = barn_upgrade_effects(lv2)
                        if "speed" in eff:
                            barn_speed += eff["speed"]
                    if barn.get("level", 1) >= 10:
                        barn_speed += 0.10
                    cycle = a_data["cycle"] * max(0.1, 1.0 - speed_bonus - barn_speed)
                    elapsed = (now - parse_dt(last)).total_seconds() / 60.0
                    remain = max(0, cycle - elapsed)
                    status = f"⏳ {remain:.0f}min"
                else:
                    status = "⏳ 等待首次产出"

            prod_name = barn.get("animal_type", "")
            print(f"  [{i:>2}] {stage_icon} {prod_name:<4} {status:<12} Lv.{lv}", end="")

        # 每5个栏位换行
        if i % 5 == 0 or i == total:
            print()
        else:
            print("  ", end="")
    print()


def show_barn_animals_detail(data):
    """详细动物列表"""
    print(f"\n  📋 养殖场详情\n" + "=" * 58)
    print(f"  {'栏位':>4}  {'动物':<6}  {'阶段':<6}  {'产出':<6}  {'状态'}")
    print(f"  " + "-" * 52)
    total = data.get("unlocked_barns", INITIAL_BARNS)
    for i, barn in enumerate(data["barns"][:total], 1):
        if barn["animal"] is None:
            continue
        a = get_barn_animal(barn["animal_type"])
        stage = get_age_stage(barn)
        stage_name = {"juvenile": "幼年", "adult": "成年", "elder": "老年"}.get(stage, "成年")
        pending = barn.get("pending_product", 0)
        prod_count = barn.get("production_count", 0)
        prod_name = a["product"] if a else "?"
        if pending > 0:
            st = f"✅ {pending}个待收"
        elif can_barn_produce(barn, data):
            st = "🔄 可产出"
        else:
            st = "⏳ 冷却中"
        print(f"  {i:>4}  {barn['animal_type']:<6}  {stage_name:<6}  {prod_name:<6}  {st}")

    # 饲料库存
    feed_inv = data.get("feed_inventory", {})
    if any(feed_inv.values()):
        print(f"\n  📦 饲料库存：")
        parts = [f"{k}: {v}份" for k, v in feed_inv.items() if v > 0]
        print(f"    {' | '.join(parts)}")


def do_barn_main(data):
    """养殖场主菜单"""
    while True:
        clear()
        header(data)
        show_barn_header(data)
        print()
        show_barns(data)

        print(f"  [1]购买动物  [2]收集产出  [3]繁殖  [4]饲料加工")
        print(f"  [5]升级栏位  [6]详情  [7]解锁栏位  [0]返回")
        print()

        choice = read_int("选择: ", 0, 7)
        if choice is None or choice == 0:
            break
        elif choice == 1:
            do_buy_barn_animal(data)
        elif choice == 2:
            do_collect_barn_products(data)
        elif choice == 3:
            do_breed_menu(data)
        elif choice == 4:
            do_feed_menu(data)
        elif choice == 5:
            do_upgrade_barn_menu(data)
        elif choice == 6:
            clear()
            header(data)
            show_barn_animals_detail(data)
            pause()
        elif choice == 7:
            do_unlock_barn(data)


def do_unlock_barn(data):
    """解锁新栏位"""
    if data.get("unlocked_barns", INITIAL_BARNS) >= MAX_BARNS:
        print("所有栏位已解锁！")
        pause()
        return
    next_id = data["unlocked_barns"] + 1
    cost = 200 * next_id
    req_level = (next_id - 1) // 5 + 1
    print(f"\n  🔓 解锁栏位")
    print(f"  下一栏位：第 {next_id} 号")
    print(f"  要求：等级 {req_level}，金币 {cost}💰")
    print(f"  当前：等级 {data['level']}，金币 {data['gold']:,}")
    if data["level"] >= req_level and data["gold"] >= cost:
        ch = read_int("解锁? (1=是, 0=返回): ", 0, 1)
        if ch == 1:
            data["gold"] -= cost
            data["unlocked_barns"] = next_id
            print(f"✅ 解锁第 {next_id} 号栏位！")
            pause()
            return
    else:
        print("❌ 条件不足")
        pause()


def do_buy_barn_animal(data):
    """购买动物到栏位"""
    # 找空闲栏位
    free_idx = None
    for i, barn in enumerate(data["barns"][:data.get("unlocked_barns", INITIAL_BARNS)]):
        if barn["animal"] is None and barn.get("unlocked", False):
            free_idx = i
            break

    if free_idx is None:
        print("❌ 没有空闲栏位！")
        pause()
        return

    print(f"\n  🛒 购买动物（空栏位: {free_idx + 1}）\n" + "=" * 50)
    for i, a in enumerate(BARN_ANIMALS_LIST, 1):
        unlocked = data["level"] >= a["level"]
        discount = 1.0 - get_talent_value(data["talent_tree"], "animal_discount")
        price = int(a["price"] * discount)
        feed_desc = " + ".join(f"{k}×{v}" for k, v in a["feed"].items())
        flag = "✅" if unlocked and data["gold"] >= price else "❌"
        print(f"  {i}. {a['name']:<4} {price:>5}💰  Lv.{a['level']:<2} "
              f"→{a['product']}({a['sell_price']}💰)  🍽️{feed_desc}  {flag}")

    choice = read_int(f"\n选择 (1-{len(BARN_ANIMALS_LIST)}, 0返回): ", 0, len(BARN_ANIMALS_LIST))
    if choice is None or choice == 0:
        return

    a = BARN_ANIMALS_LIST[choice - 1]
    if data["level"] < a["level"]:
        print(f"❌ 需要等级 {a['level']}")
        pause()
        return

    discount = 1.0 - get_talent_value(data["talent_tree"], "animal_discount")
    price = int(a["price"] * discount)
    if data["gold"] < price:
        print(f"❌ 金币不足！需要 {price}💰")
        pause()
        return

    data["gold"] -= price
    barn = data["barns"][free_idx]
    barn["animal"] = a["name"]
    barn["animal_type"] = a["name"]
    barn["purchase_time"] = now_str()
    barn["age_stage"] = "juvenile"
    barn["production_count"] = 0
    barn["last_produce_time"] = None
    barn["pending_product"] = 0
    barn["breed_cooldown"] = None
    print(f"✅ 在栏位 {free_idx + 1} 放入 {a['name']}！花费 {price}💰")
    pause()


def do_collect_barn_products(data):
    """收集所有栏位待收产品"""
    # 先处理一轮生产
    process_barn_production(data)

    total_items, collected = collect_all_barns(data)
    if total_items > 0:
        print(f"\n📦 收集到 {total_items} 件产品：")
        for item in collected:
            print(f"    {item}")
        print(f"   已存入仓库！")
    else:
        print("\n📦 没有可收集的产品")
    pause()


def do_breed_menu(data):
    """繁殖菜单"""
    # 列出成年动物
    adults = []
    for i, barn in enumerate(data["barns"][:data.get("unlocked_barns", INITIAL_BARNS)]):
        if barn["animal"] is not None and get_age_stage(barn) == "adult":
            adults.append((i, barn))

    if len(adults) < 2:
        print("❌ 需要至少2只成年动物才能繁殖")
        pause()
        return

    print(f"\n  🧬 繁殖  (需要两个同种成年动物 + 1000💰)\n" + "=" * 50)
    print(f"  成年动物列表：")
    for idx, (i, b) in enumerate(adults, 1):
        cd = b.get("breed_cooldown")
        cd_info = ""
        if cd and now_str() < cd:
            remain = (parse_dt(cd) - now_dt()).total_seconds() / 60.0
            cd_info = f" ⏳冷却{remain:.0f}min"
        print(f"  {idx}. 栏位{b['id']:>2}  {b['animal_type']:<4}  Lv.{b.get('level', 1)}{cd_info}")

    sel1 = read_int(f"\n选择第1个亲本 (1-{len(adults)}, 0返回): ", 0, len(adults))
    if sel1 is None or sel1 == 0:
        return
    sel2 = read_int(f"选择第2个亲本 (1-{len(adults)}, 0返回): ", 0, len(adults))
    if sel2 is None or sel2 == 0:
        return

    i1, b1 = adults[sel1 - 1]
    i2, b2 = adults[sel2 - 1]
    ok, msg = can_breed(b1, b2, data)
    if ok:
        result, detail = do_breed(data, i1, i2)
        print(f"\n{detail}")
    else:
        print(f"\n❌ {msg}")
    pause()


def do_feed_menu(data):
    """饲料加工菜单"""
    while True:
        clear()
        header(data)
        ff = data.get("feed_factory", {})
        feed_inv = data.get("feed_inventory", {})

        print(f"\n  🏭 饲料加工厂\n" + "=" * 50)
        print(f"  饲料库存：")
        parts = [f"{k}: {v}份" for k, v in feed_inv.items()]
        print(f"    {' | '.join(parts) if parts else '空'}")
        print()

        if ff.get("ready"):
            print(f"  ✅ 饲料加工完成！")
            print(f"  [C] 收取")
        elif ff.get("current_order"):
            st = parse_dd(ff["start_time"])
            recipe = next((r for r in FEED_RECIPES if r["name"] == ff["current_order"]), None)
            if recipe:
                remain = max(0, recipe["time"] - (now_dt() - st).total_seconds() / 60.0)
                print(f"  ⏳ 加工中：{ff['current_order']}  剩余 {remain:.0f}min")
        else:
            print(f"  选择配方加工：")
            for i, r in enumerate(FEED_RECIPES, 1):
                unlocked = data["level"] >= r["level"]
                ings = []
                for ing_name, ing_qty in r["ingredients"].items():
                    ings.append(f"{ing_name}×{ing_qty}")
                flag = "✅" if unlocked else "🔒"
                print(f"  {i}. {r['name']:<6} {'+'.join(ings):<20} ⏱{r['time']}min → {r['yield']}份 {flag}")

        print(f"\n  [0] 返回")
        choice_raw = None
        try:
            raw = get_key(0.5)
            if raw and raw in (b"c", b"C"):
                if ff.get("ready"):
                    collect_feed(data)
                    pause()
                    continue
            else:
                # 尝试数字
                try:
                    s = raw.decode() if raw else ""
                    if s and s.isdigit():
                        choice_raw = int(s)
                except Exception:
                    pass
        except Exception:
            choice_raw = read_int(f"\n选择 (1-{len(FEED_RECIPES)}, 0返回): ", 0, len(FEED_RECIPES))

        if choice_raw == 0 or choice_raw is None:
            # 改用 read_int
            choice_raw = read_int(f"\n选择 (0-{len(FEED_RECIPES)}): ", 0, len(FEED_RECIPES))
            if choice_raw is None or choice_raw == 0:
                break

        if choice_raw and choice_raw > 0 and choice_raw <= len(FEED_RECIPES):
            start_feed_production(data, choice_raw - 1)
            pause()


def do_upgrade_barn_menu(data):
    """升级栏位菜单"""
    while True:
        clear()
        header(data)
        print(f"\n  ⬆️ 栏位升级\n" + "=" * 50)
        total = data.get("unlocked_barns", INITIAL_BARNS)
        for i in range(total):
            barn = data["barns"][i]
            lv = barn.get("level", 1)
            if lv >= 10:
                status = "MAX"
            else:
                cost = barn_upgrade_cost(lv)
                flag = "✅" if cost and data["gold"] >= cost else "❌"
                status = f"Lv.{lv}→{lv+1} {cost}💰{flag}" if cost else "MAX"
            anim = barn["animal"] or "空"
            print(f"  {i+1:>2}. [{anim:<4}] {status}")
        choice = read_int(f"\n选择栏位升级 (1-{total}, 0返回): ", 0, total)
        if choice is None or choice == 0:
            break
        barn = data["barns"][choice - 1]
        lv = barn.get("level", 1)
        if lv >= 10:
            print("已满级！")
            pause()
            continue
        cost = barn_upgrade_cost(lv)
        if cost is None:
            print("已满级！")
            pause()
            continue
        if data["gold"] < cost:
            print(f"金币不足！需要 {cost}💰")
            pause()
            continue
        data["gold"] -= cost
        barn["level"] = lv + 1
        print(f"✅ 栏位 {choice} 升级到 Lv.{lv + 1}！")
        pause()


# ============ 自动养殖（天赋解锁） ============

def auto_collect_barns(data):
    """自动收集（天赋解锁）"""
    if get_talent_level(data["talent_tree"], "auto_collect") <= 0:
        return
    process_barn_production(data)
    total_items, _ = collect_all_barns(data)
    if total_items > 0:
        inv = data["inventory"]["products"]
        print(f"  🤖 自动收集 {total_items} 件动物产品")


# ============ 增强版离线计算 ============

def calc_offline_v2(data):
    """增强版离线收益（含养殖场）"""
    # 先执行原有的离线计算
    crops_game = load_crops()
    old_report_items = []

    # 重定向 print 捕获原有输出
    from io import StringIO
    old_stdout = sys.stdout
    sys.stdout = StringIO()

    calc_offline(data, crops_game)

    output = sys.stdout.getvalue()
    sys.stdout = old_stdout
    if output.strip():
        old_report_items.append(output.strip())

    # 养殖场离线计算
    items, exp = calc_barn_offline(data)
    if items > 0:
        old_report_items.append(f"养殖场产出 {items} 件")

    if old_report_items:
        print(f"\n📦 离线收益：{'，'.join(old_report_items)}")
        if exp > 0:
            print(f"   获得 {exp}✨（含离线加成）")


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
        # 首次成熟，一生一次的1%判定
        land["_maturity_roll_done"] = True
        if random.random() < 0.01:
            land["golden_pumpkin"] = True
            land["plant_time"] = now_str()
            print("  🌟 彩蛋！一块南瓜田变成了金色南瓜！再等一个生长周期即可收获！")


# ============ 增强版主循环 ============

def main_v2():
    """养殖场增强版主循环"""
    crops_game = load_crops()
    data = load_save_v2()

    # 离线收益
    calc_offline_v2(data)
    check_achievements(data)
    print("\n💡 按任意键进入游戏...")
    pause()

    # 后台自动保存
    def auto_save_loop():
        while True:
            time.sleep(AUTO_SAVE_INTERVAL)
            write_save_v2(data)

    threading.Thread(target=auto_save_loop, daemon=True).start()

    _, data["_last_cycles"] = get_season(data)

    while True:
        clear()
        # 季节更新
        season, cycles = get_season(data)
        if cycles != data.get("_last_cycles", 0):
            data["_last_cycles"] = cycles
            data["season_cycles"] = data.get("season_cycles", 0) + 1
        # 工厂检查
        check_factories_ready(data)
        check_feed_factory_ready(data)
        check_baby_mature(data)

        header(data)
        show_barn_header(data)
        print()
        # 扩展主菜单
        print("  [1]种植    [2]收获    [3]土地    [4]养殖场")
        print("  [5]加工    [6]出售    [7]升级    [8]天赋")
        print("  [9]成就    [U]解锁   [A]自动收集 [S]保存")
        print("  [H]帮助   [X]退出")
        print()

        key = get_key(REFRESH_INTERVAL)

        if key is None:
            # 定时刷新：金色南瓜彩蛋、养殖场生产和自动收集
            check_golden_pumpkin(data)
            process_barn_production(data)
            auto_collect_barns(data)
            continue

        if key in (b"x", b"X"):
            write_save_v2(data)
            clear()
            print("🎮 游戏已保存，再见！")
            break

        elif key in (b"s", b"S"):
            clear()
            header(data)
            write_save_v2(data)
            print("\n✅ 游戏已保存！")
            pause()

        elif key in (b"u", b"U"):
            clear()
            header(data)
            print("  [1]解锁土地  [2]解锁栏位")
            ch = read_int("选择: ", 0, 2)
            if ch == 1:
                header(data)
                do_unlock_land(data)
            elif ch == 2:
                header(data)
                do_unlock_barn(data)

        elif key in (b"a", b"A"):
            clear()
            header(data)
            process_barn_production(data)
            total, collected = collect_all_barns(data)
            if total > 0:
                print(f"\n📦 手动收集 {total} 件动物产品")
                for item in collected:
                    print(f"    {item}")
            else:
                print("\n📦 没有可收集的产品")
            pause()

        elif key == b"1":
            clear()
            header(data)
            do_plant(data, crops_game)
            try_trigger_event(data, crops_game)
            check_achievements(data)

        elif key == b"2":
            clear()
            header(data)
            do_harvest(data, crops_game)
            try_trigger_event(data, crops_game)
            check_achievements(data)

        elif key == b"3":
            clear()
            header(data)
            show_lands(data, crops_game)

        elif key == b"4":  # 养殖场
            do_barn_main(data)

        elif key == b"5":
            clear()
            header(data)
            do_factories(data)
            try_trigger_event(data, crops_game)
            check_achievements(data)

        elif key == b"6":
            clear()
            header(data)
            do_sell(data, crops_game)

        elif key == b"7":
            clear()
            header(data)
            print("  [1]升级土地  [2]升级栏位")
            ch = read_int("选择: ", 0, 2)
            if ch == 1:
                header(data)
                do_upgrade_land(data)
            elif ch == 2:
                header(data)
                do_upgrade_barn_menu(data)

        elif key == b"8":
            clear()
            header(data)
            do_talents(data)

        elif key == b"9":
            clear()
            header(data)
            do_achievements(data)

        elif key in (b"h", b"H"):
            clear()
            header(data)
            show_help()
            print(f"  [A] 自动收集动物产品")
            print(f"  [4] 进入养殖场（购买、繁殖、饲料加工等）")
            pause()


if __name__ == "__main__":
    try:
        main_v2()
    except KeyboardInterrupt:
        print("\n\n👋 再见！")
        try:
            data = load_save_v2()
            write_save_v2(data)
        except Exception:
            pass
        sys.exit(0)
