# -*- coding: utf-8 -*-
"""开心农场 v3.0 — PySide6 + QML 桥接层"""
import sys
import os
import datetime

from PySide6.QtCore import (
    QAbstractListModel, QModelIndex, QObject, Property,
    Signal, QTimer, QUrl, Slot,
)
from PySide6.QtGui import QGuiApplication
from PySide6.QtQml import QQmlApplicationEngine

import random

from farm_game_v2 import (
    load_save_v2, write_save_v2, load_crops, calc_offline_v2,
    calc_growth_time, get_season, check_golden_pumpkin,
    check_baby_mature, try_trigger_event, process_barn_production,
    check_factories_ready, process_all_agro_buildings,
    get_barn_animal, can_barn_produce, get_age_stage,
    check_feed_available, get_animal_feed_name,
    barn_upgrade_effects, barn_yield_multiplier,
    get_agro_slot_status, get_recipe_list, check_agro_ready,
    calc_yield_multiplier, calc_harvest_yield, get_double_chance,
    season_crop_bonus, check_talent_fruit_drop, apply_exp_bonus,
    land_upgrade_cost, try_level_up, now_str,
    INITIAL_LANDS, INITIAL_BARNS, INITIAL_AGRO_BUILDINGS,
    MAX_LANDS, MAX_BARNS, MAX_AGRO_BUILDINGS,
)

# ============ Emoji 映射 ============
CROP_EMOJI = {
    "小麦": "🌾", "玉米": "🌽", "水稻": "🌾", "玫瑰": "🌹",
    "胡萝卜": "🥕", "南瓜": "🎃", "土豆": "🥔", "番茄": "🍅",
    "草莓": "🍓", "蓝莓": "🫐", "咖啡豆": "🫘", "棉花": "☁️",
    "甘蔗": "🎋", "葡萄": "🍇", "可可豆": "🫘", "茶叶": "🍃",
    "四叶草": "🍀", "黄金小麦": "🌟", "彩虹花": "🌈",
}

ANIMAL_EMOJI = {
    "鸡": "🐔", "鸭": "🦆", "兔": "🐰", "鹅": "🦢",
    "羊": "🐑", "猪": "🐷", "牛": "🐮", "蜜蜂": "🐝",
    "羊驼": "🦙", "马": "🐴", "鹿": "🦌", "独角兽": "🦄", "龙": "🐉",
}

SEASON_EMOJI = {"春": "🌸", "夏": "☀️", "秋": "🍂", "冬": "❄️"}

ANIMAL_PRODUCT_EMOJI = {
    "鸡蛋": "🥚", "鸭蛋": "🥚", "兔毛": "🧶", "鹅蛋": "🥚",
    "羊毛": "🧶", "猪肉": "🥩", "牛肉": "🥩", "蜂蜜": "🍯",
    "羊驼毛": "🧶", "马奶": "🥛", "鹿茸": "🦌", "独角兽角": "🦄", "龙鳞": "🐉",
}

BUILDING_EMOJI = {"feed_mill": "🏭", "brewery": "🍺"}


def _parse_dt(s):
    try:
        return datetime.datetime.strptime(s, "%Y-%m-%d %H:%M:%S")
    except (ValueError, TypeError):
        return datetime.datetime.now()


def _fmt_time_left(minutes):
    if minutes <= 0:
        return ""
    if minutes < 1:
        return "<1m"
    h = int(minutes // 60)
    m = int(minutes % 60)
    if h >= 24:
        d = h // 24
        h = h % 24
        return f"{d}d{h}h"
    if h > 0:
        return f"{h}h{m:02d}m" if m > 0 else f"{h}h"
    return f"{m}m"


def _fmt_time_full(minutes):
    """超过1小时显示 h:m, 否则显示 m:##"""
    if minutes <= 0:
        return ""
    if minutes < 1:
        return "0:00"
    total_seconds = int(minutes * 60)
    h = total_seconds // 3600
    m = (total_seconds % 3600) // 60
    s = total_seconds % 60
    if h > 0:
        return f"{h}:{m:02d}:{s:02d}"
    return f"{m}:{s:02d}"


# ============ 玩家状态模型 ============
class PlayerModel(QObject):
    changed = Signal()

    def __init__(self, data, parent=None):
        super().__init__(parent)
        self._data = data

    def refresh(self):
        self.changed.emit()

    @Property(int, notify=changed)
    def gold(self):
        return self._data.get("gold", 0)

    @Property(int, notify=changed)
    def level(self):
        return self._data.get("level", 1)

    @Property(int, notify=changed)
    def exp(self):
        return self._data.get("exp", 0)

    @Property(int, notify=changed)
    def expNeed(self):
        return 80 + self._data.get("level", 1) * 40

    @Property(int, notify=changed)
    def diamond(self):
        return self._data.get("diamond", 0)

    @Property(int, notify=changed)
    def talentPoints(self):
        return self._data.get("talent_points", 0)

    @Property(int, notify=changed)
    def plantedCount(self):
        unlocked = self._data.get("unlocked_lands", INITIAL_LANDS)
        return sum(1 for l in self._data.get("lands", [])[:unlocked] if l.get("crop"))

    @Property(int, notify=changed)
    def maxLands(self):
        return self._data.get("unlocked_lands", INITIAL_LANDS)

    @Property(int, notify=changed)
    def barnCount(self):
        unlocked = self._data.get("unlocked_barns", INITIAL_BARNS)
        return sum(1 for b in self._data.get("barns", [])[:unlocked] if b.get("animal"))

    @Property(int, notify=changed)
    def maxBarns(self):
        return self._data.get("unlocked_barns", INITIAL_BARNS)

    @Property(int, notify=changed)
    def barnPending(self):
        unlocked = self._data.get("unlocked_barns", INITIAL_BARNS)
        return sum(b.get("pending_product", 0) for b in self._data.get("barns", [])[:unlocked])

    @Property(int, notify=changed)
    def agroReadyCount(self):
        unlocked = self._data.get("unlocked_agro_buildings", INITIAL_AGRO_BUILDINGS)
        return sum(1 for s in self._data.get("agro_buildings", [])[:unlocked] if s.get("ready"))

    @Property(int, notify=changed)
    def agroProcessingCount(self):
        unlocked = self._data.get("unlocked_agro_buildings", INITIAL_AGRO_BUILDINGS)
        return sum(1 for s in self._data.get("agro_buildings", [])[:unlocked] if s.get("order") and not s.get("ready"))

    @Property(int, notify=changed)
    def agroCount(self):
        unlocked = self._data.get("unlocked_agro_buildings", INITIAL_AGRO_BUILDINGS)
        return sum(1 for s in self._data.get("agro_buildings", [])[:unlocked] if s.get("building"))

    @Property(str, notify=changed)
    def season(self):
        s, _ = get_season(self._data)
        return s

    @Property(str, notify=changed)
    def seasonEmoji(self):
        return SEASON_EMOJI.get(self.season, "🌱")


# ============ 地块列表模型 ============
class FarmPlotModel(QAbstractListModel):
    def __init__(self, data, crops, parent=None):
        super().__init__(parent)
        self._data = data
        self._crops = crops
        self._pics_dir = os.path.join(
            os.path.dirname(os.path.abspath(__file__)), "pictures"
        )
        self._has_image = {}
        for name in crops:
            self._has_image[name] = os.path.exists(
                os.path.join(self._pics_dir, f"{name}.png")
            )

    def rowCount(self, parent=QModelIndex()):
        return self._data.get("unlocked_lands", INITIAL_LANDS)

    def data(self, index, role):
        if not index.isValid():
            return None
        lands = self._data["lands"]
        unlocked = self._data.get("unlocked_lands", INITIAL_LANDS)
        row = index.row()
        if row >= len(lands) or row >= unlocked:
            return None

        land = lands[row]
        crop_name = land.get("crop")

        if role == 0:  return land["id"]
        if role == 1:  return crop_name or ""
        if role == 4:  return False
        if role == 5:  return land.get("upgrade_level", 1)
        if role == 9:  return land.get("golden_pumpkin", False)

        if not crop_name:
            if role == 2: return 0
            if role == 3: return False
            if role == 6: return ""
            if role == 7: return False
            if role == 8: return ""
            return None

        plant_time = land.get("plant_time")
        if not plant_time:
            if role == 2: return 0
            if role == 3: return False
            if role == 6: return ""
            if role == 7: return self._has_image.get(crop_name, False)
            if role == 8: return CROP_EMOJI.get(crop_name, "🌱")
            return None

        talent_tree = self._data.get("talent_tree", {})
        growth = calc_growth_time(crop_name, land.get("upgrade_level", 1), talent_tree, land)
        pt = _parse_dt(plant_time)
        elapsed = (datetime.datetime.now() - pt).total_seconds() / 60.0
        progress = min(elapsed / growth, 2.0) if growth > 0 else 2.0

        if progress < 0.25:      stage = 0
        elif progress < 0.50:    stage = 1
        elif progress < 0.90:    stage = 2
        else:                    stage = 3

        ready = progress >= 1.0

        if role == 2: return stage
        if role == 3: return ready
        if role == 6:
            remaining = growth - elapsed
            return _fmt_time_left(remaining) if remaining > 0 and not ready else ""
        if role == 7: return self._has_image.get(crop_name, False)
        if role == 8: return CROP_EMOJI.get(crop_name, "🌱")
        return None

    def roleNames(self):
        return {
            0: b"lid", 1: b"crop", 2: b"stage",
            3: b"ready", 4: b"locked", 5: b"level",
            6: b"timeLeft", 7: b"hasImage", 8: b"emoji",
            9: b"goldenPumpkin",
        }

    def refresh(self):
        n = self.rowCount()
        if n > 0:
            self.dataChanged.emit(self.index(0), self.index(n - 1), [])

    @Property(int, notify=lambda: None)
    def plotCount(self):
        return self.rowCount()


# ============ 养殖场列表模型 ============
class BarnModel(QAbstractListModel):
    def __init__(self, data, parent=None):
        super().__init__(parent)
        self._data = data

    def rowCount(self, parent=QModelIndex()):
        return self._data.get("unlocked_barns", INITIAL_BARNS)

    def data(self, index, role):
        if not index.isValid():
            return None
        barns = self._data.get("barns", [])
        unlocked = self._data.get("unlocked_barns", INITIAL_BARNS)
        row = index.row()
        if row >= len(barns) or row >= unlocked:
            return None

        barn = barns[row]

        if role == 0:  return barn["id"]                # bid
        if role == 1:  return barn.get("animal") or ""   # animal
        if role == 2:  return barn.get("animal_type") or ""  # animalType
        if role == 3:  return barn.get("level", 1)       # level
        if role == 4:  return barn.get("pending_product", 0)  # pending
        if role == 8:  return False  # locked (all shown barns are unlocked)

        animal_type = barn.get("animal_type")
        if not animal_type:
            if role == 5: return ""         # timeLeft
            if role == 6: return "empty"    # status
            if role == 7: return ""         # emoji
            return None

        anim = get_barn_animal(animal_type)
        if not anim:
            if role == 5: return ""
            if role == 6: return "empty"
            if role == 7: return ""
            return None

        # emoji
        if role == 7:
            base = ANIMAL_EMOJI.get(animal_type, "🐾")
            stage = get_age_stage(barn)
            if stage == "juvenile": return "🐣"
            if stage == "elder":   return "👴" + base
            return base

        # status + timeLeft
        pending = barn.get("pending_product", 0)
        fed = barn.get("fed_time")

        if pending > 0:
            if role == 6: return "ready"
            if role == 5: return ""
            return None

        if not fed:
            if role == 6: return "not_fed"
            if role == 5: return ""
            return None

        # check if feed available
        has_feed = check_feed_available(self._data, animal_type)
        if not has_feed:
            if role == 6: return "no_feed"
            if role == 5: return ""
            return None

        # compute time until next production
        if role == 5 or role == 6:
            now = datetime.datetime.now()
            last = barn.get("last_produce_time")
            if last is None:
                # first production: 10 min from fed_time
                fed_dt = _parse_dt(fed)
                elapsed = (now - fed_dt).total_seconds() / 60.0
                remaining = 10.0 - elapsed
            else:
                last_dt = _parse_dt(last)
                cycle = anim["cycle"]
                # speed bonus
                speed = 0.0
                for lv in range(2, barn.get("level", 1) + 1):
                    eff = barn_upgrade_effects(lv)
                    if "speed" in eff:
                        speed += eff["speed"]
                if barn.get("level", 1) >= 10:
                    speed += 0.10
                from farm_game_v2 import get_talent_value
                speed += get_talent_value(self._data.get("talent_tree", {}), "animal_speed")
                cycle = cycle * max(0.1, 1.0 - speed)
                elapsed = (now - last_dt).total_seconds() / 60.0
                remaining = cycle - elapsed

            if role == 5: return _fmt_time_left(remaining) if remaining > 0 else ""
            if role == 6: return "producing" if remaining > 0 else "ready"

        return None

    def roleNames(self):
        return {
            0: b"bid", 1: b"animal", 2: b"animalType",
            3: b"level", 4: b"pending", 5: b"timeLeft",
            6: b"status", 7: b"emoji", 8: b"locked",
        }

    def refresh(self):
        n = self.rowCount()
        if n > 0:
            self.dataChanged.emit(self.index(0), self.index(n - 1), [])


# ============ 农业建筑列表模型 ============
class AgroBuildingModel(QAbstractListModel):
    def __init__(self, data, parent=None):
        super().__init__(parent)
        self._data = data

    def rowCount(self, parent=QModelIndex()):
        return self._data.get("unlocked_agro_buildings", INITIAL_AGRO_BUILDINGS)

    def data(self, index, role):
        if not index.isValid():
            return None
        slots = self._data.get("agro_buildings", [])
        unlocked = self._data.get("unlocked_agro_buildings", INITIAL_AGRO_BUILDINGS)
        row = index.row()
        if row >= len(slots) or row >= unlocked:
            return None

        slot = slots[row]
        btype = slot.get("building")
        bname = ""
        if btype == "feed_mill": bname = "饲料加工厂"
        elif btype == "brewery": bname = "酿酒厂"

        if role == 0:  return slot["id"]         # sid
        if role == 1:  return btype or ""         # building
        if role == 2:  return slot.get("level", 1)  # level
        if role == 7:  return bname               # buildingName
        if role == 8:  return False               # locked

        if not btype:
            if role == 3: return "empty"
            if role == 4: return ""
            if role == 5: return False
            if role == 6: return ""
            if role == 9: return ""
            return None

        # Compute status
        order = slot.get("order")
        if not order:
            if role == 3: return "idle"
            if role == 4: return ""
            if role == 5: return False
            if role == 6: return ""
            if role == 9: return BUILDING_EMOJI.get(btype, "🏗️")
            return None

        check_agro_ready(slot)
        ready = slot.get("ready", False)
        done = slot.get("done_batches", 0)
        total = slot.get("total_batches", 0)

        if role == 5: return ready
        if role == 6: return f"{done}/{total}"
        if role == 9: return BUILDING_EMOJI.get(btype, "🏗️")

        if ready:
            if role == 3: return "ready"
            if role == 4: return ""
        else:
            if role == 3: return "processing"
            # compute remaining time
            st = _parse_dt(slot.get("start_time", ""))
            all_recipes = get_recipe_list(btype)
            recipe = next((r for r in all_recipes if r["name"] == order), None)
            if recipe:
                elapsed = (datetime.datetime.now() - st).total_seconds() / 60.0
                remaining = recipe["time"] - elapsed
                if role == 4: return _fmt_time_left(remaining) if remaining > 0 else "<1m"
            else:
                if role == 4: return ""

        return None

    def roleNames(self):
        return {
            0: b"sid", 1: b"building", 2: b"level",
            3: b"status", 4: b"timeLeft", 5: b"ready",
            6: b"batches", 7: b"buildingName", 8: b"locked",
            9: b"buildingEmoji",
        }

    def refresh(self):
        n = self.rowCount()
        if n > 0:
            self.dataChanged.emit(self.index(0), self.index(n - 1), [])


# ============ 事件日志模型 ============
class EventLogModel(QObject):
    logChanged = Signal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self._logs = []

    @Property(str, notify=logChanged)
    def logText(self):
        return "\n".join(self._logs[-50:])  # keep last 50 lines

    @Slot(str)
    def addLog(self, msg):
        ts = datetime.datetime.now().strftime("[%H:%M:%S] ")
        self._logs.append(ts + msg)
        self.logChanged.emit()

    @Slot()
    def clearLogs(self):
        self._logs = []
        self.logChanged.emit()

    def add(self, msg):
        """Python-side log"""
        self._logs.append(msg)
        self.logChanged.emit()


# ============ 游戏操作控制器 ============
class GameController(QObject):
    """暴露给 QML 的游戏操作方法"""

    def __init__(self, data, crops, event_log, parent=None):
        super().__init__(parent)
        self._data = data
        self._crops = crops
        self._log = event_log

    def _log_msg(self, msg):
        if self._log:
            self._log.add(msg)

    # ---- 土地操作 ----

    @Slot(result="QVariantList")
    def getEmptyLands(self):
        """获取空地列表 [{id, level}]"""
        lands = self._data["lands"]
        unlocked = self._data.get("unlocked_lands", INITIAL_LANDS)
        result = []
        for land in lands[:unlocked]:
            if not land.get("crop"):
                result.append({"id": land["id"], "level": land.get("upgrade_level", 1)})
        return result

    @Slot(result="QVariantList")
    def getAvailableCrops(self):
        """获取可种植作物列表 [{name, emoji, seedPrice, sellPrice, growthMin, exp, level, seedCount}]"""
        player_level = self._data.get("level", 1)
        seed_bag = self._data.get("seed_bag", {})
        result = []
        for name, info in self._crops.items():
            if info.get("hidden"):
                continue
            if player_level < info["level"]:
                continue
            result.append({
                "name": name,
                "emoji": CROP_EMOJI.get(name, "🌱"),
                "seedPrice": info["seed_price"],
                "sellPrice": info["sell_price"],
                "growthMin": info["growth_minutes"],
                "exp": info["exp"],
                "level": info["level"],
                "seedCount": seed_bag.get(name, 0),
            })
        result.sort(key=lambda x: x["level"])
        return result

    @Slot(int, str, result=str)
    def plantCrop(self, land_id, crop_name):
        """种植作物"""
        # 找土地
        land = None
        for l in self._data["lands"]:
            if l["id"] == land_id:
                land = l
                break
        if land is None:
            return "❌ 土地不存在"
        if land.get("crop"):
            return "❌ 该土地已有作物"

        crop = self._crops.get(crop_name)
        if not crop:
            return "❌ 未知作物"

        # 先用种子袋
        seed_bag = self._data.setdefault("seed_bag", {})
        if seed_bag.get(crop_name, 0) > 0:
            seed_bag[crop_name] -= 1
        else:
            price = crop["seed_price"]
            if self._data["gold"] < price:
                return f"❌ 金币不足，需要 {price}💰"
            self._data["gold"] -= price

        land["crop"] = crop_name
        land["plant_time"] = now_str()
        land["golden_pumpkin"] = False
        land["_maturity_roll_done"] = False
        land["_wind_delay"] = 0
        land["_pest_reduced_yield"] = None
        write_save_v2(self._data)
        self._log_msg(f"🌱 第 {land_id} 号土地种下 {crop_name}！")
        return f"✅ 第 {land_id} 号土地种下 {crop_name}！"

    @Slot(result=str)
    def harvestAll(self):
        """收获所有成熟作物"""
        now = datetime.datetime.now()
        talent_tree = self._data.get("talent_tree", {})
        season = get_season(self._data)[0]
        unlocked = self._data.get("unlocked_lands", INITIAL_LANDS)

        total_gold = 0
        total_exp = 0
        total_count = 0
        harvested_items = []

        for land in self._data["lands"][:unlocked]:
            crop_name = land.get("crop")
            if not crop_name or not land.get("plant_time"):
                continue
            crop = self._crops.get(crop_name)
            if not crop:
                continue

            growth = calc_growth_time(crop_name, land.get("upgrade_level", 1), talent_tree, land)
            pt = _parse_dt(land["plant_time"])
            elapsed = (now - pt).total_seconds() / 60.0
            if elapsed < growth:
                continue

            # 跳过金色南瓜
            if land.get("golden_pumpkin"):
                continue

            # 计算产量
            mult = calc_yield_multiplier(land.get("upgrade_level", 1), talent_tree, crop_name, season)
            base_yield = max(1, int(round(crop["growth_minutes"] / 10.0)))
            qty = calc_harvest_yield(land, base_yield, mult)

            # 虫灾减产
            if land.get("_pest_reduced_yield"):
                qty = land["_pest_reduced_yield"]
                land["_pest_reduced_yield"] = None

            # 双倍概率
            if random.random() < get_double_chance(land.get("upgrade_level", 1), talent_tree):
                qty *= 2
            if self._data.get("lucky_clover"):
                if random.random() < 0.5:
                    qty *= 2
                self._data["lucky_clover"] = False

            # 加入仓库
            inv = self._data.setdefault("inventory", {}).setdefault("crops", {})
            inv[crop_name] = inv.get(crop_name, 0) + qty

            gold = crop["sell_price"] * qty
            exp = crop["exp"]
            # 售价加成天赋
            sell_bonus = 1.0
            from farm_game_v2 import get_talent_value
            sell_bonus += get_talent_value(talent_tree, "sell_bonus")
            gold = int(gold * sell_bonus)
            exp = int(exp * apply_exp_bonus(self._data))

            self._data["gold"] = self._data.get("gold", 0) + gold
            self._data["exp"] = self._data.get("exp", 0) + exp

            total_gold += gold
            total_exp += exp
            total_count += 1
            harvested_items.append(f"{crop_name}×{qty}")

            # 清除土地
            land["crop"] = None
            land["plant_time"] = None
            land["golden_pumpkin"] = False
            land["_maturity_roll_done"] = False
            land["_yield_remainder"] = 0.0

            # 天赋果实
            check_talent_fruit_drop(self._data)

        if total_count == 0:
            return "🌾 没有可收获的作物"

        try_level_up(self._data)
        self._data["total_harvests"] = self._data.get("total_harvests", 0) + total_count
        self._data["total_earnings"] = self._data.get("total_earnings", 0) + total_gold
        write_save_v2(self._data)
        self._log_msg(f"🌾 收获 {total_count} 块地！获得 {total_gold}💰 {total_exp}✨")
        return f"🌾 收获 {total_count} 块地！+{total_gold}💰 +{total_exp}✨\n{', '.join(harvested_items[:5])}"

    @Slot(result="QVariantList")
    def getLandUpgradeList(self):
        """获取可升级土地列表 [{id, crop, level, cost, canUpgrade, isMax}]"""
        lands = self._data["lands"]
        unlocked = self._data.get("unlocked_lands", INITIAL_LANDS)
        gold = self._data.get("gold", 0)
        result = []
        for land in lands[:unlocked]:
            lv = land.get("upgrade_level", 1)
            cost = land_upgrade_cost(lv)
            is_max = cost is None
            result.append({
                "id": land["id"],
                "crop": land.get("crop") or "空",
                "level": lv,
                "cost": cost if not is_max else 0,
                "canUpgrade": not is_max and gold >= cost,
                "isMax": is_max,
            })
        return result

    @Slot(int, result=str)
    def upgradeLand(self, land_id):
        """升级指定土地"""
        land = None
        for l in self._data["lands"]:
            if l["id"] == land_id:
                land = l
                break
        if land is None:
            return "❌ 土地不存在"

        lv = land.get("upgrade_level", 1)
        cost = land_upgrade_cost(lv)
        if cost is None:
            return "❌ 已满级"
        if self._data["gold"] < cost:
            return f"❌ 金币不足，需要 {cost}💰"

        self._data["gold"] -= cost
        land["upgrade_level"] = lv + 1
        write_save_v2(self._data)
        self._log_msg(f"⬆ 第 {land_id} 号土地升级至 Lv.{lv + 1}！花费 {cost}💰")
        return f"✅ 第 {land_id} 号土地 Lv.{lv}→Lv.{lv + 1}！"

    @Slot(result="QVariantMap")
    def getUnlockLandInfo(self):
        """获取解锁下一块土地的信息 {nextId, cost, levelNeed}"""
        unlocked = self._data.get("unlocked_lands", INITIAL_LANDS)
        if unlocked >= MAX_LANDS:
            return {"nextId": 0, "cost": 0, "levelNeed": 0, "canUnlock": False, "isMax": True}
        next_id = unlocked + 1
        cost = 200 * next_id
        level_need = (next_id - 1) // 5 + 1
        can = self._data.get("gold", 0) >= cost and self._data.get("level", 1) >= level_need
        return {
            "nextId": next_id, "cost": cost, "levelNeed": level_need,
            "canUnlock": can, "isMax": False,
        }

    @Slot(result=str)
    def unlockLand(self):
        """解锁下一块土地"""
        unlocked = self._data.get("unlocked_lands", INITIAL_LANDS)
        if unlocked >= MAX_LANDS:
            return "❌ 所有土地已解锁"
        next_id = unlocked + 1
        cost = 200 * next_id
        level_need = (next_id - 1) // 5 + 1
        if self._data.get("gold", 0) < cost:
            return f"❌ 金币不足，需要 {cost}💰"
        if self._data.get("level", 1) < level_need:
            return f"❌ 需要 Lv.{level_need}"

        self._data["gold"] -= cost
        self._data["unlocked_lands"] = next_id
        write_save_v2(self._data)
        self._log_msg(f"🔓 解锁 {next_id} 号土地！花费 {cost}💰")
        return f"✅ 解锁 {next_id} 号土地！花费 {cost}💰"

    # ---- 养殖场操作 ----

    @Slot(result="QVariantMap")
    def getBarnBuyData(self):
        """获取购买动物数据 {freeSlots, animals: [...]}"""
        from farm_game_v2 import BARN_ANIMALS_LIST, get_talent_value
        ub = self._data.get("unlocked_barns", INITIAL_BARNS)
        free_slots = []
        for i in range(ub):
            barn = self._data["barns"][i]
            if barn["animal"] is None and barn.get("unlocked", False):
                free_slots.append(i + 1)

        discount = 1.0 - get_talent_value(self._data["talent_tree"], "animal_discount")
        player_level = self._data.get("level", 1)
        gold = self._data.get("gold", 0)

        animals = []
        for a in BARN_ANIMALS_LIST:
            if a.get("hidden"):
                continue
            price = int(a["price"] * discount)
            unlocked = player_level >= a["level"]
            feed_desc = "+".join(f"{k}×{v}" for k, v in a["feed"].items())
            animals.append({
                "name": a["name"],
                "emoji": ANIMAL_EMOJI.get(a["name"], "🐾"),
                "level": a["level"],
                "price": price,
                "originalPrice": a["price"],
                "product": a["product"],
                "productEmoji": ANIMAL_PRODUCT_EMOJI.get(a["product"], "📦"),
                "sellPrice": a["sell_price"],
                "feedDesc": feed_desc,
                "canBuy": unlocked and gold >= price and len(free_slots) > 0,
                "unlocked": unlocked,
            })

        return {"freeSlots": free_slots, "hasFreeSlot": len(free_slots) > 0, "animals": animals}

    @Slot(str, result=str)
    def buyBarnAnimal(self, name):
        """购买动物放入空闲栏位"""
        from farm_game_v2 import get_talent_value
        a = get_barn_animal(name)
        if a is None:
            return "❌ 未知动物"
        ub = self._data.get("unlocked_barns", INITIAL_BARNS)
        free_idx = None
        for i in range(ub):
            if self._data["barns"][i]["animal"] is None and self._data["barns"][i].get("unlocked", False):
                free_idx = i
                break
        if free_idx is None:
            return "❌ 没有空闲栏位"
        discount = 1.0 - get_talent_value(self._data["talent_tree"], "animal_discount")
        price = int(a["price"] * discount)
        if self._data["gold"] < price:
            return f"❌ 金币不足，需要 {price}💰"
        self._data["gold"] -= price
        barn = self._data["barns"][free_idx]
        barn["animal"] = name
        barn["animal_type"] = name
        barn["purchase_time"] = now_str()
        barn["age_stage"] = "juvenile"
        barn["production_count"] = 0
        barn["last_produce_time"] = None
        barn["pending_product"] = 0
        barn["breed_cooldown"] = None
        barn["fed_time"] = None
        write_save_v2(self._data)
        self._log_msg(f"✅ 栏位 {free_idx+1} 放入 {name}，花费 {price}💰")
        return f"✅ 购买 {name}，放入栏位 {free_idx+1}！"

    @Slot(result=str)
    def feedAnimals(self):
        """投喂动物"""
        from farm_game_v2 import feed_barn_animals
        fed, no_feed, already = feed_barn_animals(self._data)
        process_barn_production(self._data)
        write_save_v2(self._data)
        total_feeds = sum(self._data.get("inventory", {}).get("feeds", {}).values())
        msg = f"🍽️ 投喂: 新增 {len(fed)} 只, 已喂 {len(already)} 只"
        if no_feed:
            msg += f", 缺饲料 {len(no_feed)} 只"
        msg += f" | 饲料库存 {total_feeds}"
        self._log_msg(msg)
        return msg

    @Slot(result=str)
    def collectBarn(self):
        """收集所有栏位产品"""
        from farm_game_v2 import collect_all_barns
        process_barn_production(self._data)
        total, collected = collect_all_barns(self._data)
        write_save_v2(self._data)
        if total > 0:
            items_str = ", ".join(collected)
            self._log_msg(f"📦 收集 {total} 件: {items_str}")
            return f"✅ 收集 {total} 件产品！"
        return "📦 没有可收集的产品"

    @Slot(int, int, result=str)
    def breed(self, barn1Id, barn2Id):
        """繁殖两只动物"""
        from farm_game_v2 import can_breed, do_breed
        bi1 = barn1Id - 1
        bi2 = barn2Id - 1
        b1 = self._data["barns"][bi1]
        b2 = self._data["barns"][bi2]
        ok, msg = can_breed(b1, b2, self._data)
        if not ok:
            return f"❌ {msg}"
        result, detail = do_breed(self._data, bi1, bi2)
        write_save_v2(self._data)
        self._log_msg(detail)
        return detail

    @Slot(result="QVariantMap")
    def getBreedData(self):
        """获取可繁殖的成年动物列表"""
        ub = self._data.get("unlocked_barns", INITIAL_BARNS)
        adults = []
        for i in range(ub):
            barn = self._data["barns"][i]
            if barn["animal"] is not None and get_age_stage(barn) == "adult":
                cd = barn.get("breed_cooldown")
                if cd and now_str() < cd:
                    continue
                adults.append({
                    "id": i + 1,
                    "animal": barn["animal"],
                    "animalType": barn["animal_type"],
                    "level": barn.get("level", 1),
                    "emoji": ANIMAL_EMOJI.get(barn["animal_type"], "🐾"),
                })
        return {"adults": adults, "canBreed": len(adults) >= 2}

    @Slot(result="QVariantMap")
    def getUnlockBarnInfo(self):
        """获取解锁栏位信息"""
        if self._data.get("unlocked_barns", INITIAL_BARNS) >= MAX_BARNS:
            return {"isMax": True, "nextId": 0, "cost": 0, "levelNeed": 0, "canUnlock": False}
        next_id = self._data["unlocked_barns"] + 1
        cost = 200 * next_id
        req_level = (next_id - 1) // 5 + 1
        can = self._data["level"] >= req_level and self._data["gold"] >= cost
        return {"isMax": False, "nextId": next_id, "cost": cost, "levelNeed": req_level, "canUnlock": can}

    @Slot(result=str)
    def unlockBarn(self):
        """解锁养殖栏位"""
        info = self.getUnlockBarnInfo()
        if info["isMax"]:
            return "所有栏位已解锁！"
        if not info["canUnlock"]:
            return f"❌ 金币或等级不足"
        self._data["gold"] -= info["cost"]
        next_id = info["nextId"]
        self._data["unlocked_barns"] = next_id
        self._data["barns"][next_id - 1]["unlocked"] = True
        write_save_v2(self._data)
        self._log_msg(f"🔓 解锁第 {next_id} 号栏位，花费 {info['cost']}💰")
        return f"✅ 解锁第 {next_id} 号栏位！"

    # ---- 农业建筑操作 ----

    @Slot(result="QVariantMap")
    def getAgroBuildData(self):
        """获取建造数据 {slots: [...], canBuild: bool, buildOptions: [...]}"""
        from farm_game_v2 import agro_build_cost
        unlocked = self._data.get("unlocked_agro_buildings", INITIAL_AGRO_BUILDINGS)
        gold = self._data.get("gold", 0)

        # 所有已解锁的 slot 状态
        slots = []
        free_slots = []
        for i in range(unlocked):
            s = self._data["agro_buildings"][i]
            btype = s.get("building")
            bname = ""
            if btype == "feed_mill":
                bname = "饲料加工厂"
            elif btype == "brewery":
                bname = "酿酒厂"
            status = "empty" if not btype else "built"
            emoji = BUILDING_EMOJI.get(btype, "🏗️")
            slots.append({
                "id": i + 1,
                "building": btype or "",
                "buildingName": bname,
                "level": s.get("level", 1),
                "status": status,
                "emoji": emoji,
            })
            if not btype:
                free_slots.append(i + 1)

        build_options = []
        if free_slots:
            for btype_name, btype_key in [("饲料加工厂", "feed_mill"), ("酿酒厂", "brewery")]:
                cost = agro_build_cost(btype_key)
                build_options.append({
                    "name": btype_name,
                    "typeKey": btype_key,
                    "cost": cost,
                    "emoji": BUILDING_EMOJI.get(btype_key, "🏗️"),
                    "canAfford": gold >= cost,
                })

        return {
            "slots": slots,
            "freeSlots": free_slots,
            "hasFreeSlot": len(free_slots) > 0,
            "buildOptions": build_options,
        }

    @Slot(int, str, result=str)
    def buildAgroBuilding(self, slotId, buildingType):
        """在指定位置建造建筑"""
        from farm_game_v2 import build_agro_building
        ok, msg = build_agro_building(self._data, slotId - 1, buildingType)
        if ok:
            write_save_v2(self._data)
            self._log_msg(f"🏗️ #{slotId} {msg}")
        return ("✅ " if ok else "❌ ") + msg

    @Slot(result="QVariantMap")
    def getAgroUpgradeList(self):
        """获取可升级建筑列表"""
        from farm_game_v2 import agro_upgrade_cost
        unlocked = self._data.get("unlocked_agro_buildings", INITIAL_AGRO_BUILDINGS)
        gold = self._data.get("gold", 0)
        upgrades = []
        for i in range(unlocked):
            s = self._data["agro_buildings"][i]
            btype = s.get("building")
            if not btype:
                continue
            lv = s.get("level", 1)
            if lv >= 4:
                continue
            cost = agro_upgrade_cost(lv)
            bname = "酿酒厂" if btype == "brewery" else "饲料加工厂"
            upgrades.append({
                "id": i + 1,
                "building": btype,
                "buildingName": bname,
                "level": lv,
                "nextLevel": lv + 1,
                "cost": cost,
                "canUpgrade": cost is not None and gold >= cost,
                "emoji": BUILDING_EMOJI.get(btype, "🏗️"),
            })
        return {"upgrades": upgrades, "hasUpgrades": len(upgrades) > 0}

    @Slot(int, result=str)
    def upgradeAgroBuilding(self, slotId):
        """升级指定建筑"""
        from farm_game_v2 import upgrade_agro_building
        ok, msg = upgrade_agro_building(self._data, slotId - 1)
        if ok:
            write_save_v2(self._data)
            self._log_msg(f"⬆️ #{slotId} {msg}")
        return ("✅ " if ok else "❌ ") + msg

    @Slot(result="QVariantMap")
    def getAgroStartData(self):
        """获取可开始加工的建筑列表及配方"""
        from farm_game_v2 import get_available_recipes
        unlocked = self._data.get("unlocked_agro_buildings", INITIAL_AGRO_BUILDINGS)
        available = []
        for i in range(unlocked):
            s = self._data["agro_buildings"][i]
            btype = s.get("building")
            if not btype:
                continue
            if s.get("order") and not s.get("ready"):
                continue  # 正在加工中
            lv = s.get("level", 1)
            recipes = get_available_recipes(lv, btype)
            if not recipes:
                continue
            bname = "酿酒厂" if btype == "brewery" else "饲料加工厂"
            recipe_list = []
            for r in recipes:
                # 检查原料
                ings_str = ", ".join(f"{k}×{v}" for k, v in r["ingredients"].items())
                recipe_list.append({
                    "name": r["name"],
                    "time": r["time"],
                    "yield_": r["yield"],
                    "ingredients": ings_str,
                })
            available.append({
                "id": i + 1,
                "building": btype,
                "buildingName": bname,
                "level": lv,
                "recipes": recipe_list,
                "emoji": BUILDING_EMOJI.get(btype, "🏗️"),
            })
        return {"slots": available, "hasAvailable": len(available) > 0}

    @Slot(int, str, int, result=str)
    def startAgroProduction(self, slotId, recipeName, batches):
        """开始加工"""
        from farm_game_v2 import start_agro_production
        ok, msg = start_agro_production(self._data, slotId - 1, recipeName, batches)
        if ok:
            write_save_v2(self._data)
            self._log_msg(f"🔧 #{slotId} {msg}")
        return ("✅ " if ok else "❌ ") + msg

    @Slot(result=str)
    def collectAgro(self):
        """收取所有建筑位已完成产品"""
        from farm_game_v2 import collect_agro_product, process_all_agro_buildings
        process_all_agro_buildings(self._data)
        unlocked = self._data.get("unlocked_agro_buildings", INITIAL_AGRO_BUILDINGS)
        total_all = 0
        msgs = []
        for i in range(unlocked):
            s = self._data["agro_buildings"][i]
            if s.get("ready") or s.get("done_batches", 0) > 0:
                total, msg = collect_agro_product(self._data, i)
                if total > 0:
                    total_all += total
                    msgs.append(f"#{i+1} {msg}")
        if total_all > 0:
            write_save_v2(self._data)
            summary = ", ".join(msgs)
            self._log_msg(f"📦 收取农业产品: {summary}")
            return f"✅ 收取 {total_all} 件产品！"
        return "📦 没有可收取的产品"

    @Slot(result="QVariantMap")
    def getUnlockAgroInfo(self):
        """获取解锁建筑位信息"""
        from farm_game_v2 import agro_unlock_cost
        unlocked = self._data.get("unlocked_agro_buildings", INITIAL_AGRO_BUILDINGS)
        if unlocked >= MAX_AGRO_BUILDINGS:
            return {"isMax": True, "nextId": 0, "cost": 0, "canUnlock": False}
        next_id = unlocked + 1
        cost = agro_unlock_cost(next_id)
        can = self._data["gold"] >= cost
        return {"isMax": False, "nextId": next_id, "cost": cost, "canUnlock": can}

    @Slot(result=str)
    def unlockAgroSlot(self):
        """解锁农业建筑位"""
        info = self.getUnlockAgroInfo()
        if info["isMax"]:
            return "所有建筑位已解锁！"
        if not info["canUnlock"]:
            return f"❌ 金币不足，需要 {info['cost']}💰"
        self._data["gold"] -= info["cost"]
        next_id = info["nextId"]
        self._data["unlocked_agro_buildings"] = next_id
        self._data["agro_buildings"][next_id - 1]["unlocked"] = True
        write_save_v2(self._data)
        self._log_msg(f"🔓 解锁第 {next_id} 号建筑位，花费 {info['cost']}💰")
        return f"✅ 解锁第 {next_id} 号建筑位！"

    # ---- 仓库操作 ----

    def _get_feed_price(self, name):
        """估算饲料售价（基于原料成本/产量）"""
        prices = {"基础饲料": 6, "精制饲料": 50, "高级饲料": 550, "特殊饲料": 1500}
        return prices.get(name, 10)

    def _get_product_price(self, name):
        """获取加工品售价"""
        from farm_game_v2 import FACTORY_LIST, BREW_RECIPES
        for f in FACTORY_LIST:
            if f.get("product") == name:
                return f.get("sell_price", 0)
        for r in BREW_RECIPES:
            if r.get("name") == name:
                return r.get("sell_price", 0)
        return 0

    @Slot(result="QVariantMap")
    def getWarehouseData(self):
        """获取仓库数据 {capacity, usage, space, categories: [{name, label, items}]}"""
        inv = self._data.get("inventory", {})
        locked = self._data.get("locked", {})
        capacity = 100 + (self._data.get("level", 1) // 5) * 10 + self._data.get("warehouse_expansions", 0) * 10

        categories = []
        total_usage = 0

        # 作物类
        crops = inv.get("crops", {})
        crop_items = []
        for name, qty in sorted(crops.items()):
            if qty <= 0:
                continue
            crop_info = self._crops.get(name, {})
            price = crop_info.get("sell_price", 10)
            crop_items.append({
                "name": name, "qty": qty, "price": price,
                "emoji": CROP_EMOJI.get(name, "📦"),
                "locked": name in locked.get("crops", []),
                "category": "crops",
            })
        categories.append({"name": "crops", "label": "🌾 作物", "items": crop_items})
        total_usage += len(crop_items)

        # 加工品
        products = inv.get("products", {})
        prod_items = []
        for name, qty in sorted(products.items()):
            if qty <= 0:
                continue
            price = self._get_product_price(name)
            prod_items.append({
                "name": name, "qty": qty, "price": price,
                "emoji": "🏭", "locked": name in locked.get("products", []),
                "category": "products",
            })
        categories.append({"name": "products", "label": "🏭 加工品", "items": prod_items})
        total_usage += len(prod_items)

        # 饲料
        feeds = inv.get("feeds", {})
        feed_items = []
        for name, qty in sorted(feeds.items()):
            if qty <= 0:
                continue
            price = self._get_feed_price(name)
            feed_items.append({
                "name": name, "qty": qty, "price": price,
                "emoji": "🍽️", "locked": name in locked.get("feeds", []),
                "category": "feeds",
            })
        categories.append({"name": "feeds", "label": "🍽️ 饲料", "items": feed_items})
        total_usage += len(feed_items)

        return {
            "capacity": capacity,
            "usage": total_usage,
            "space": capacity - total_usage,
            "categories": categories,
        }

    @Slot(str, str, int, result=str)
    def sellItem(self, category, itemName, qty):
        """出售仓库物品"""
        inv = self._data.get("inventory", {})
        cat_dict = inv.get(category, {})
        current = cat_dict.get(itemName, 0)
        if current <= 0:
            return "❌ 没有该物品"
        qty = min(qty, current)
        price = 0
        if category == "crops":
            price = self._crops.get(itemName, {}).get("sell_price", 10)
        elif category == "products":
            price = self._get_product_price(itemName)
        elif category == "feeds":
            price = self._get_feed_price(itemName)

        total = price * qty
        cat_dict[itemName] = current - qty
        if cat_dict[itemName] <= 0:
            del cat_dict[itemName]
        self._data["gold"] = self._data.get("gold", 0) + total
        write_save_v2(self._data)
        self._log_msg(f"💰 出售 {itemName}×{qty}，获得 {total}💰")
        return f"✅ 出售 {itemName}×{qty}，+{total}💰"

    @Slot(str, result=str)
    def sellAllCategory(self, category):
        """批量出售某类所有物品"""
        inv = self._data.get("inventory", {})
        locked = self._data.get("locked", {})
        cat_dict = inv.get(category, {})
        locked_names = set(locked.get(category, []))
        total_gold = 0
        total_qty = 0

        for name, qty in list(cat_dict.items()):
            if name in locked_names:
                continue
            price = 0
            if category == "crops":
                price = self._crops.get(name, {}).get("sell_price", 10)
            elif category == "products":
                price = self._get_product_price(name)
            elif category == "feeds":
                price = self._get_feed_price(name)
            total_gold += price * qty
            total_qty += qty
            del cat_dict[name]

        if total_qty == 0:
            return "没有可出售的物品（已锁定的已跳过）"
        self._data["gold"] = self._data.get("gold", 0) + total_gold
        write_save_v2(self._data)
        self._log_msg(f"💰 批量出售 {total_qty} 件，获得 {total_gold}💰")
        return f"✅ 出售 {total_qty} 件，+{total_gold}💰"

    @Slot(str, str, result=str)
    def toggleLockItem(self, category, itemName):
        """锁定/解锁物品"""
        locked = self._data.setdefault("locked", {})
        locked.setdefault("crops", [])
        locked.setdefault("products", [])
        locked.setdefault("feeds", [])
        lst = locked.get(category, [])
        if itemName in lst:
            lst.remove(itemName)
            return f"🔓 已解锁 {itemName}"
        else:
            lst.append(itemName)
            return f"🔒 已锁定 {itemName}"

    @Slot(result=str)
    def expandWarehouse(self):
        """钻石扩容仓库"""
        count = self._data.get("warehouse_expansions", 0)
        cost = 100 + count * 50
        diamond = self._data.get("diamond", 0)
        if diamond < cost:
            return f"❌ 💎不足，需要 {cost}💎"
        self._data["diamond"] = diamond - cost
        self._data["warehouse_expansions"] = count + 1
        write_save_v2(self._data)
        self._log_msg(f"📦 仓库扩容！容量 +10")
        return f"✅ 仓库扩容成功！花费 {cost}💎"

    # ---- 商店操作 ----

    @Slot(result="QVariantMap")
    def getShopData(self):
        """获取商店数据 {discount, crops: [...]}"""
        from farm_game_v2 import get_merchant_discount
        discount = get_merchant_discount(self._data)
        seed_bag = self._data.get("seed_bag", {})
        player_level = self._data.get("level", 1)
        gold = self._data.get("gold", 0)
        season = get_season(self._data)[0]

        crops_list = []
        for name, info in self._crops.items():
            if info.get("hidden"):
                continue
            price = info["seed_price"]
            if discount > 0:
                price = int(price * (1.0 - discount))
            bonus = season_crop_bonus(name, season) > 1.0
            crops_list.append({
                "name": name,
                "emoji": CROP_EMOJI.get(name, "🌱"),
                "level": info["level"],
                "seedPrice": price,
                "originalPrice": info["seed_price"],
                "sellPrice": info["sell_price"],
                "growthMin": info["growth_minutes"],
                "exp": info["exp"],
                "canBuy": player_level >= info["level"] and gold >= price,
                "seedCount": seed_bag.get(name, 0),
                "seasonBonus": bonus,
            })
        crops_list.sort(key=lambda x: x["level"])
        return {
            "discount": discount,
            "hasDiscount": discount > 0,
            "crops": crops_list,
        }

    @Slot(str, int, result=str)
    def buySeeds(self, cropName, qty):
        """购买种子"""
        crop = self._crops.get(cropName)
        if not crop:
            return "❌ 未知作物"
        from farm_game_v2 import get_merchant_discount
        discount = get_merchant_discount(self._data)
        price = crop["seed_price"]
        if discount > 0:
            price = int(price * (1.0 - discount))
        total = price * qty
        if self._data["gold"] < total:
            return f"❌ 金币不足，需要 {total}💰"
        self._data["gold"] -= total
        seed_bag = self._data.setdefault("seed_bag", {})
        seed_bag[cropName] = seed_bag.get(cropName, 0) + qty
        write_save_v2(self._data)
        self._log_msg(f"🛒 购买 {cropName} 种子 ×{qty}，花费 {total}💰")
        return f"✅ 购买 {cropName} 种子 ×{qty}！"

    # ---- 天赋操作 ----

    @Slot(result="QVariantMap")
    def getTalentData(self):
        """获取天赋树数据"""
        from farm_game_v2 import TALENTS_LIST, TALENT_GROUPS
        tree = self._data.get("talent_tree", {})
        points = self._data.get("talent_points", 0)
        groups = {}
        for t in TALENTS_LIST:
            tid, grp, name, max_lv, desc, effect, title = t
            level = tree.get(name, 0)
            if grp not in groups:
                groups[grp] = []
            groups[grp].append({
                "name": name,
                "title": title,
                "desc": desc,
                "level": level,
                "maxLevel": max_lv,
                "effectPerLevel": effect,
                "isMax": level >= max_lv,
                "canUpgrade": points > 0 and level < max_lv,
            })

        result_groups = []
        for grp_name in TALENT_GROUPS:
            if grp_name in groups:
                result_groups.append({"name": grp_name, "talents": groups[grp_name]})

        fruit_count = self._data.get("inventory", {}).get("crops", {}).get("天赋果实", 0)
        fruit_used = self._data.get("talent_fruits_used", 0)
        diamond = self._data.get("diamond", 0)
        gold = self._data.get("gold", 0)

        return {
            "points": points,
            "groups": result_groups,
            "fruitCount": fruit_count,
            "fruitUsed": fruit_used,
            "canUseFruit": fruit_count > 0 and fruit_used < 10,
            "canResetDiamond": diamond >= 50,
            "canResetGold": gold >= 5000,
        }

    @Slot(str, result=str)
    def upgradeTalent(self, talentName):
        """升级天赋"""
        if self._data.get("talent_points", 0) <= 0:
            return "❌ 天赋点不足"
        from farm_game_v2 import TALENTS_LIST
        talent = next((t for t in TALENTS_LIST if t[2] == talentName), None)
        if talent is None:
            return "❌ 未知天赋"
        max_lv = talent[3]
        tree = self._data.setdefault("talent_tree", {})
        current = tree.get(talentName, 0)
        if current >= max_lv:
            return "❌ 已满级"
        tree[talentName] = current + 1
        self._data["talent_points"] -= 1
        write_save_v2(self._data)
        self._log_msg(f"⭐ 学习 {talent[6]} Lv.{current + 1}")
        return f"✅ {talent[6]} Lv.{current} → Lv.{current + 1}"

    @Slot(bool, result=str)
    def resetTalents(self, payWithDiamond):
        """重置天赋"""
        from farm_game_v2 import reset_talents
        ok, msg = reset_talents(self._data, payWithDiamond)
        if ok:
            write_save_v2(self._data)
            self._log_msg(f"🔄 {msg}")
        return ("✅ " if ok else "❌ ") + msg

    @Slot(result=str)
    def useTalentFruit(self):
        """使用天赋果实"""
        from farm_game_v2 import use_talent_fruit
        ok, msg = use_talent_fruit(self._data)
        if ok:
            write_save_v2(self._data)
            self._log_msg(f"🍎 {msg}")
        return ("✅ " if ok else "❌ ") + msg

    # ---- 成就操作 ----

    @Slot(result="QVariantMap")
    def getAchievementData(self):
        """获取成就列表"""
        from farm_game_v2 import ACHIEVEMENTS_LIST, check_achievements
        check_achievements(self._data)
        completed = set(self._data.get("achievements", []))
        items = []
        for name, cond_str, _, reward in ACHIEVEMENTS_LIST:
            done = name in completed
            if name == "完美主义者":
                done = all(a[0] in completed or a[0] == "完美主义者" for a in ACHIEVEMENTS_LIST)
            r_text = ", ".join(f"{v}{k}" for k, v in reward.items() if v)
            items.append({
                "name": name,
                "condition": cond_str,
                "reward": r_text,
                "done": done,
                "icon": "✅" if done else "🔲",
            })
        total = len(items)
        done_count = sum(1 for it in items if it["done"])
        return {"items": items, "total": total, "doneCount": done_count}

    # ---- 钻石商店 ----

    @Slot(result="QVariantMap")
    def getDiamondShopData(self):
        """获取钻石商店数据"""
        from farm_game_v2 import DIAMOND_SHOP_ITEMS
        diamond = self._data.get("diamond", 0)
        items = []
        for i, item in enumerate(DIAMOND_SHOP_ITEMS):
            owned = False
            if item["action"] == "skin_rainbow" and self._data.get("skin_rainbow"):
                owned = True
            items.append({
                "idx": i,
                "name": item["name"],
                "diamond": item["diamond"],
                "desc": item["desc"],
                "canBuy": diamond >= item["diamond"] and not owned,
                "owned": owned,
            })
        return {"diamond": diamond, "items": items}

    @Slot(int, result=str)
    def buyDiamondItem(self, idx):
        """购买钻石商品"""
        from farm_game_v2 import diamond_shop_purchase
        ok, msg = diamond_shop_purchase(self._data, idx)
        if ok:
            write_save_v2(self._data)
            self._log_msg(f"💎 {msg}")
        return ("✅ " if ok else "❌ ") + msg

    # ---- 工厂加工 ----

    @Slot(result="QVariantMap")
    def getFactoryData(self):
        """获取工厂数据"""
        from farm_game_v2 import FACTORY_LIST, check_factories_ready
        check_factories_ready(self._data)
        player_level = self._data.get("level", 1)
        factories = []
        for f in FACTORY_LIST:
            fc = self._data["factories"].get(f["factory"], {})
            unlocked = player_level >= f["level"]
            has_order = bool(fc.get("current_order"))
            is_ready = fc.get("ready", False)
            is_processing = has_order and not is_ready

            # 计算原料
            ings = []
            can_make = True
            save_lv = get_talent_value(self._data.get("talent_tree", {}), "save_materials")
            for ing_name, ing_qty in f["ingredients"].items():
                need = max(1, ing_qty - save_lv)
                have = self._data.get("inventory", {}).get("crops", {}).get(ing_name, 0)
                ings.append({"name": ing_name, "need": need, "have": have})
                if have < need:
                    can_make = can_make or self._data.get("inventory", {}).get("products", {}).get(ing_name, 0) >= need

            # 剩余时间
            remain_text = ""
            if is_processing:
                st = _parse_dt(fc["start_time"])
                elapsed = (datetime.datetime.now() - st).total_seconds() / 60.0
                remain = max(0, f["time"] - elapsed)
                remain_text = _fmt_time_left(remain)

            factories.append({
                "factory": f["factory"],
                "product": f["product"],
                "level": f["level"],
                "unlocked": unlocked,
                "isReady": is_ready,
                "isProcessing": is_processing,
                "hasOrder": has_order,
                "canStart": unlocked and not has_order and can_make,
                "ingredients": ings,
                "canMake": can_make,
                "remainText": remain_text,
            })
        return {"factories": factories}

    @Slot(str, result=str)
    def startFactory(self, factoryName):
        """开始工厂加工"""
        from farm_game_v2 import FACTORY_LIST
        f = next((x for x in FACTORY_LIST if x["factory"] == factoryName), None)
        if f is None:
            return "❌ 未知工厂"
        fc = self._data["factories"][factoryName]
        if fc.get("current_order"):
            return "❌ 已有订单进行中"

        # 检查原料
        inv = self._data["inventory"]
        save_lv = get_talent_value(self._data.get("talent_tree", {}), "save_materials")
        for ing_name, ing_qty in f["ingredients"].items():
            need = max(1, ing_qty - save_lv)
            have = inv["crops"].get(ing_name, 0)
            if have < need:
                return f"❌ {ing_name}不足（需要{need}，有{have}）"

        # 消耗原料
        for ing_name, ing_qty in f["ingredients"].items():
            need = max(1, ing_qty - save_lv)
            inv["crops"][ing_name] -= need

        fc["current_order"] = factoryName
        fc["start_time"] = now_str()
        fc["ready"] = False
        write_save_v2(self._data)
        self._log_msg(f"🏭 开始加工 {f['product']}")
        return f"✅ 开始加工 {f['product']}！"

    @Slot(str, result=str)
    def collectFactory(self, factoryName):
        """收取工厂产品"""
        from farm_game_v2 import FACTORY_LIST
        f = next((x for x in FACTORY_LIST if x["factory"] == factoryName), None)
        if f is None:
            return "❌ 未知工厂"
        fc = self._data["factories"][factoryName]
        if not fc.get("ready"):
            return "❌ 产品尚未完成"

        qty = 1
        dp = get_talent_value(self._data.get("talent_tree", {}), "double_process")
        if random.random() < dp:
            qty = 2

        prod_inv = self._data["inventory"].setdefault("products", {})
        prod_inv[f["product"]] = prod_inv.get(f["product"], 0) + qty
        fc["current_order"] = None
        fc["start_time"] = None
        fc["ready"] = False
        self._data["total_processed"] = self._data.get("total_processed", 0) + 1
        write_save_v2(self._data)
        self._log_msg(f"🏭 收取 {f['product']}×{qty}")
        return f"✅ 收取 {f['product']}×{qty}！"

    # ---- 通用操作 ----

    @Slot(result=str)
    def openShop(self): return ""  # 由 QML 弹窗处理
    @Slot(result=str)
    def openWarehouse(self): return ""  # 由 QML 弹窗处理
    @Slot(result=str)
    def openTalents(self): return ""  # 由 QML 弹窗处理
    @Slot(result=str)
    def openAchievements(self): return ""  # 由 QML 弹窗处理

    @Slot()
    def saveGame(self):
        write_save_v2(self._data)
        self._log_msg("💾 游戏已保存")

    @Slot(result=str)
    def openHelp(self): return "📖 农场手册即将开放（P7）"


# ============ 主入口 ============
def main():
    app = QGuiApplication(sys.argv)
    engine = QQmlApplicationEngine()

    # 加载游戏数据
    data = load_save_v2()
    crops = load_crops()

    # 离线收益
    calc_offline_v2(data)
    check_baby_mature(data)
    check_golden_pumpkin(data)
    check_factories_ready(data)
    process_all_agro_buildings(data)
    try_trigger_event(data, crops)
    process_barn_production(data)

    # 事件日志
    event_log = EventLogModel()
    event_log.add("🎮 欢迎来到开心农场 v3.0！")

    # 玩家模型
    player_model = PlayerModel(data)

    # 三种数据模型
    farm_model = FarmPlotModel(data, crops)
    barn_model = BarnModel(data)
    agro_model = AgroBuildingModel(data)

    # 游戏控制器
    controller = GameController(data, crops, event_log)

    # 注册到 QML
    ctx = engine.rootContext()
    ctx.setContextProperty("playerModel", player_model)
    ctx.setContextProperty("farmModel", farm_model)
    ctx.setContextProperty("barnModel", barn_model)
    ctx.setContextProperty("agroModel", agro_model)
    ctx.setContextProperty("eventLog", event_log)
    ctx.setContextProperty("gameCtrl", controller)

    # 图片目录
    pics_path = os.path.join(
        os.path.dirname(os.path.abspath(__file__)), "pictures"
    ).replace(os.sep, "/")
    ctx.setContextProperty("picturesDir", pics_path)

    # 加载 QML
    qml_path = os.path.join(
        os.path.dirname(os.path.abspath(__file__)), "qml", "main.qml"
    )
    engine.load(qml_path)

    if not engine.rootObjects():
        print("ERROR: Failed to load QML")
        sys.exit(-1)

    # 定时刷新
    ticks = [0]

    def on_tick():
        farm_model.refresh()
        barn_model.refresh()
        agro_model.refresh()
        player_model.refresh()
        ticks[0] += 1
        if ticks[0] >= 30:
            process_barn_production(data)
            try_trigger_event(data, crops)
            check_baby_mature(data)
            check_golden_pumpkin(data)
            check_factories_ready(data)
            process_all_agro_buildings(data)
            write_save_v2(data)
            ticks[0] = 0

    timer = QTimer()
    timer.timeout.connect(on_tick)
    timer.start(1000)

    sys.exit(app.exec())


if __name__ == "__main__":
    main()
