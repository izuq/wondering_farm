# -*- coding: utf-8 -*-
"""
开心农场 v3.0 — 终端版
"""
import sys
import os
import datetime
import time
import threading

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from farm import (
    MAX_LANDS, REFRESH_INTERVAL, AUTO_SAVE_INTERVAL, SAVE_FILE,
    load_crops, try_level_up, write_save, calc_offline,
    header, menu, clear, read_int, pause, get_key,
)
from farm_game_v2 import (
    FACTORY_LIST, TALENTS_LIST, TALENT_GROUPS,
    ACHIEVEMENTS_LIST, FEED_RECIPES,
    MAX_BARNS, INITIAL_BARNS, warehouse_capacity,
    get_talent_value, get_talent_level, land_upgrade_cost,
    get_merchant_discount, now_dt, now_str, parse_dt,
    get_season, season_crop_bonus,
    load_save_v2, write_save_v2, calc_offline_v2,
    get_barn_animal, get_age_stage, can_barn_produce, check_feed_available,
    process_barn_production, collect_all_barns, barn_upgrade_cost, barn_upgrade_effects,
    start_feed_production, collect_feed, process_all_agro_buildings,
    do_breed, can_breed, check_baby_mature,
    check_factories_ready, check_achievements,
    check_golden_pumpkin, try_trigger_event,
    cancel_event_warning, calc_harvest_yield, apply_exp_bonus, check_talent_fruit_drop,
    reset_talents, use_talent_fruit, diamond_shop_purchase, DIAMOND_SHOP_ITEMS,
    get_animal_feed_name, get_feed_consume,
    FEED_FRUIT_NAMES, BARN_ANIMALS_LIST, init_game,
    # 农业建筑
    MAX_AGRO_BUILDINGS, INITIAL_AGRO_BUILDINGS, FEED_RECIPES_BY_LEVEL,
    agro_build_cost, agro_upgrade_cost, agro_unlock_cost,
    get_available_recipes, check_agro_ready, process_all_agro_buildings,
    _consume_recipe_ingredients, start_agro_production, collect_agro_product,
    build_agro_building, upgrade_agro_building, get_agro_slot_status,
    _feed_inv,
    # 酿酒
    BREW_RECIPES, get_recipe_list, get_recipes_by_level,
)


# ============ 终端版功能函数 ============

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
        ch = read_int(f"\n选择工厂? (1-{len(FACTORY_LIST)} 收取, 0返回): ", 0, len(FACTORY_LIST))
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
                _, _, name, max_lv, desc, _ = t
                level = data.get("talent_tree", {}).get(name, 0)
                bar = "■" * level + "□" * (max_lv - level)
                status = "MAX" if level >= max_lv else f"{level}/{max_lv}"
                print(f"    {name:<16} {bar} {status}  {desc}")
        ch = read_int("\n输入天赋名学习 (0返回): ", 0, 0)
        if ch == 0:
            break
        all_talents = [t for t in TALENTS_LIST]
        for i, t in enumerate(all_talents, 1):
            print(f"  {i}. {t[2]}")
        sel = read_int(f"\n选择 (1-{len(all_talents)}, 0返回): ", 0, len(all_talents))
        if sel == 0:
            break
        t = all_talents[sel - 1]
        _, _, name, max_lv, desc, _ = t
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


# ============ 养殖场UI ============

def show_barn_header(data):
    """养殖场状态栏"""
    total = data.get("unlocked_barns", INITIAL_BARNS)
    occupied = sum(1 for b in data["barns"][:total] if b["animal"] is not None)
    pending = sum(b.get("pending_product", 0) for b in data["barns"][:total])
    feed_total = sum(data.get("inventory", {}).get("feeds", {}).values())
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

    feed_inv = data.get("inventory", {}).get("feeds", {})
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

        print(f"  [1]购买动物  [2]收集产出  [3]繁殖  [4]农业建筑")
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
            do_agro_menu(data)
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


def do_agro_menu(data):
    """农业建筑终端菜单"""
    while True:
        clear()
        header(data)
        unlocked = data.get("unlocked_agro_buildings", INITIAL_AGRO_BUILDINGS)
        slots = data.get("agro_buildings", [])
        feed_inv = data.get("inventory", {}).get("feeds", {})

        print(f"\n  🏗️ 农业建筑\n" + "=" * 50)
        print(f"  已解锁：{unlocked}/{MAX_AGRO_BUILDINGS}")
        print(f"  饲料库存：")
        parts = [f"{k}: {v}份" for k, v in feed_inv.items() if v > 0]
        print(f"    {' | '.join(parts) if parts else '空'}")
        print()

        if not any(s.get("building") for s in slots[:unlocked]):
            print(f"  暂无建筑，请先建造！")
        else:
            for i in range(unlocked):
                slot = slots[i]
                if not slot.get("building"):
                    continue
                status = get_agro_slot_status(slot)
                print(f"  #{i+1} {status}")

        print(f"\n  [B]建造  [U]升级  [P]加工  [C]收取")
        print(f"  [L]解锁地块  [0]返回")
        print()

        key = get_key(None)
        if key is None:
            continue
        try:
            s = key.decode().lower()
        except Exception:
            continue

        if s == "0":
            break
        elif s == "b":
            do_build_agro(data)
        elif s == "u":
            do_upgrade_agro_term(data)
        elif s == "p":
            do_start_agro_term(data)
        elif s == "c":
            do_collect_agro_term(data)
        elif s == "l":
            do_unlock_agro_term(data)


def do_build_agro(data):
    """建造农业建筑"""
    unlocked = data.get("unlocked_agro_buildings", INITIAL_AGRO_BUILDINGS)
    slots = data.get("agro_buildings", [])
    free = [i for i in range(unlocked) if not slots[i].get("building")]
    if not free:
        print("\n❌ 所有已解锁地块都有建筑了！")
        pause()
        return
    print(f"\n空地：{', '.join(str(i+1) for i in free)}")
    idx = read_int(f"选择地块 (1-{unlocked}): ", 1, unlocked)
    if idx is None:
        return
    # 选择建筑类型
    print(f"\n建筑类型：")
    print(f"  [1] 饲料加工厂（{agro_build_cost('feed_mill')}💰）")
    print(f"  [2] 酿酒厂（{agro_build_cost('brewery')}💰）")
    t = read_int("选择类型 (1-2): ", 1, 2)
    if t is None:
        return
    btype = "brewery" if t == 2 else "feed_mill"
    ok, msg = build_agro_building(data, idx - 1, btype)
    print(f"\n{'✅' if ok else '❌'} {msg}")
    pause()


def do_upgrade_agro_term(data):
    """升级建筑"""
    unlocked = data.get("unlocked_agro_buildings", INITIAL_AGRO_BUILDINGS)
    slots = data.get("agro_buildings", [])
    built = [(i, s) for i in range(unlocked) if slots[i].get("building") and slots[i].get("level", 1) < 4]
    if not built:
        print("\n❌ 没有可升级的建筑！")
        pause()
        return
    print(f"\n可升级建筑：")
    for i, slot in built:
        lv = slot.get("level", 1)
        cost = agro_upgrade_cost(lv)
        can = "✅" if data.get("gold", 0) >= cost else "❌"
        btype = slot.get("building", "feed_mill")
        bname = "酿酒厂" if btype == "brewery" else "加工厂"
        print(f"  #{i+1} {bname} Lv.{lv}→Lv.{lv+1} {cost}💰 {can}")
    idx = read_int(f"选择建筑 (1-{unlocked}): ", 1, unlocked)
    if idx is None:
        return
    ok, msg = upgrade_agro_building(data, idx - 1)
    print(f"\n{'✅' if ok else '❌'} {msg}")
    pause()


def do_start_agro_term(data):
    """开始加工饲料"""
    unlocked = data.get("unlocked_agro_buildings", INITIAL_AGRO_BUILDINGS)
    slots = data.get("agro_buildings", [])
    avail = [(i, s) for i in range(unlocked) if s.get("building") and (not s.get("order") or s.get("ready"))]
    if not avail:
        print("\n❌ 所有建筑都在加工中！")
        pause()
        return
    print(f"\n可选建筑：")
    for i, slot in avail:
        btype = slot.get("building", "feed_mill")
        bname = "酿酒厂" if btype == "brewery" else "加工厂"
        recipes = get_available_recipes(slot.get("level", 1), btype)
        recipe_names = ", ".join(r["name"] for r in recipes)
        print(f"  #{i+1} {bname} Lv.{slot.get('level', 1)} → {recipe_names}")
    idx = read_int(f"选择建筑 (1-{unlocked}): ", 1, unlocked)
    if idx is None:
        return
    slot = slots[idx - 1]
    btype = slot.get("building")
    if not btype:
        print("❌ 该地块没有建筑！")
        pause()
        return
    recipes = get_available_recipes(slot.get("level", 1), btype)
    if not recipes:
        print("❌ 没有可用配方！")
        pause()
        return
    print(f"\n可选配方：")
    inv = data["inventory"]["crops"]
    for j, re in enumerate(recipes, 1):
        can = True
        ing_parts = []
        for ing_name, ing_qty in re["ingredients"].items():
            if ing_name == "任意水果":
                have = sum(inv.get(f, 0) for f in FEED_FRUIT_NAMES)
            else:
                have = inv.get(ing_name, 0)
            stock = f"(库存:{have})" if have > 0 else "(库存:0)"
            ing_parts.append(f"{ing_name}×{ing_qty}{stock}")
            if have < ing_qty:
                can = False
        ings = ", ".join(ing_parts)
        flag = "✅" if can else "❌"
        print(f"  {j}. {re['name']} {ings} {re['time']}min/批 → {re['yield']}个 {flag}")
    r_idx = read_int(f"选择配方 (1-{len(recipes)}): ", 1, len(recipes))
    if r_idx is None:
        return
    recipe = recipes[r_idx - 1]
    qty = read_int("批次数量: ", 1, 999)
    if qty is None:
        return
    ok, msg = start_agro_production(data, idx - 1, recipe["name"], qty)
    print(f"\n{'✅' if ok else '❌'} {msg}")
    pause()


def do_collect_agro_term(data):
    """收取所有已完成饲料"""
    unlocked = data.get("unlocked_agro_buildings", INITIAL_AGRO_BUILDINGS)
    slots = data.get("agro_buildings", [])
    ready_slots = [(i, s) for i in range(unlocked) if s.get("ready") or s.get("done_batches", 0) > 0]
    if not ready_slots:
        print("\n❌ 没有可收取的产品！")
        pause()
        return
    total_all = 0
    msgs = []
    for idx, slot in ready_slots:
        total, msg = collect_agro_product(data, idx)
        if total > 0:
            total_all += total
            msgs.append(f"#{idx+1} {msg}")
    if total_all > 0:
        print(f"\n✅ 收取：{', '.join(msgs)}")
    pause()


def do_unlock_agro_term(data):
    """解锁农业建筑地块"""
    unlocked = data.get("unlocked_agro_buildings", INITIAL_AGRO_BUILDINGS)
    if unlocked >= MAX_AGRO_BUILDINGS:
        print("\n所有地块已解锁！")
        pause()
        return
    cost = agro_unlock_cost(unlocked + 1)
    if data.get("gold", 0) < cost:
        print(f"❌ 金币不足！需要 {cost}💰")
        pause()
        return
    ch = read_int(f"解锁第 {unlocked+1} 号地块（{cost}💰）？(1=是, 0=否): ", 0, 1)
    if ch == 1:
        data["gold"] = data.get("gold", 0) - cost
        data["unlocked_agro_buildings"] = unlocked + 1
        if unlocked < len(data.get("agro_buildings", [])):
            data["agro_buildings"][unlocked]["unlocked"] = True
        print(f"✅ 解锁农业建筑 #{unlocked+1} 号地块！")
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


# ============ 增强版主循环 ============

def main_v2():
    """v3.0 主循环"""
    init_game()
    crops_game = load_crops()
    data = load_save_v2()

    # 离线收益
    gold, exp, count = calc_offline_v2(data)
    if count > 0:
        print(f"\n📦 离线 {gold}💰 {exp}✨")
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
        season, cycles = get_season(data)
        if cycles != data.get("_last_cycles", 0):
            data["_last_cycles"] = cycles
            data["season_cycles"] = data.get("season_cycles", 0) + 1
        check_factories_ready(data)
        process_all_agro_buildings(data)
        check_baby_mature(data)

        header(data)
        show_barn_header(data)
        print()
        print("  [1]种植    [2]收获    [3]土地    [4]养殖场")
        print("  [5]农业建筑 [6]出售    [7]升级    [8]天赋")
        print("  [9]成就    [U]解锁   [A]自动收集 [S]保存")
        print("  [H]农场手册   [X]退出")
        print()

        key = get_key(REFRESH_INTERVAL)

        if key is None:
            check_factories_ready(data)
            process_all_agro_buildings(data)
            check_baby_mature(data)
            check_golden_pumpkin(data)
            process_barn_production(data)
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

        elif key == b"4":
            do_barn_main(data)

        elif key == b"5":
            clear()
            header(data)
            do_agro_menu(data)
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
            show_help(crops_game)
            print(f"  [A] 自动收集动物产品")
            print(f"  [4] 进入养殖场（购买、繁殖、投喂等）")
            print(f"  [5] 农业建筑（建造饲料工厂、加工饲料）")
            pause()

    # end while


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
