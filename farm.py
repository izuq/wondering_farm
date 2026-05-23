# -*- coding: utf-8 -*-
"""
开心农场 v3.0
基于 Python 标准库的农场模拟游戏
支持离线收益、等级系统、自动保存与自动刷新
"""

import json
import datetime
import time
import threading
import os
import sys

# 解决 Windows GBK 编码无法输出 emoji 的问题
if sys.stdout.encoding and "UTF" not in sys.stdout.encoding.upper():
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass

# ============ 常量配置 ============
CROPS_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "data", "crops.json")
SAVE_FILE = "save.json"
REFRESH_INTERVAL = 10      # 自动刷新间隔（秒）
AUTO_SAVE_INTERVAL = 30    # 自动保存间隔（秒）
MAX_LANDS = 50

# ============ 跨平台键盘输入 ============
try:
    import msvcrt  # Windows

    def get_key(timeout=None):
        """非阻塞读键，超时（秒）返回 None"""
        deadline = time.time() + timeout if timeout else None
        while True:
            if msvcrt.kbhit():
                return msvcrt.getch()
            if deadline and time.time() >= deadline:
                return None
            time.sleep(0.05)

    def read_int(prompt, min_v, max_v):
        """读取一行整数输入，支持退格"""
        print(prompt, end="", flush=True)
        buf = []
        while True:
            ch = get_key(None)
            if ch == b"\r":  # Enter
                print()
                break
            if ch in (b"\x08", b"\x7f"):  # Backspace
                if buf:
                    buf.pop()
                    print("\b \b", end="", flush=True)
            elif b"0" <= ch <= b"9":
                buf.append(ch.decode())
                print(ch.decode(), end="", flush=True)
        if not buf:
            return None
        v = int("".join(buf))
        return v if min_v <= v <= max_v else None

    def pause():
        msvcrt.getch()

except ImportError:
    # Unix 简易方案（使用标准输入，不支持退格编辑）
    import select

    def get_key(timeout=None):
        r, _, _ = select.select([sys.stdin], [], [], timeout)
        if r:
            ch = sys.stdin.read(1)
            return ch.encode()
        return None

    def read_int(prompt, min_v, max_v):
        try:
            v = int(input(prompt))
            return v if min_v <= v <= max_v else None
        except (ValueError, EOFError):
            return None

    def pause():
        sys.stdin.read(1)

# ============ 作物数据 ============

def _default_crops():
    return {
        "小麦": {"level": 1, "growth_minutes": 30, "seed_price": 40, "sell_price": 80, "exp": 10},
        "玉米": {"level": 2, "growth_minutes": 30, "seed_price": 50, "sell_price": 100, "exp": 12},
        "水稻": {"level": 3, "growth_minutes": 45, "seed_price": 100, "sell_price": 200, "exp": 18},
        "玫瑰": {"level": 4, "growth_minutes": 45, "seed_price": 160, "sell_price": 320, "exp": 25},
        "胡萝卜": {"level": 5, "growth_minutes": 60, "seed_price": 220, "sell_price": 450, "exp": 30},
        "南瓜": {"level": 7, "growth_minutes": 120, "seed_price": 600, "sell_price": 1200, "exp": 60},
    }


def load_crops():
    """加载作物配置，文件不存在时自动创建"""
    try:
        with open(CROPS_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        default = _default_crops()
        with open(CROPS_FILE, "w", encoding="utf-8") as f:
            json.dump(default, f, ensure_ascii=False, indent=2)
        return dict(default)


# ============ 存档系统 ============

def new_save():
    """创建新存档"""
    now = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    return {
        "gold": 500,
        "level": 1,
        "exp": 0,
        "talent_points": 0,
        "last_save_time": now,
        "lands": [{"id": i + 1, "crop": None, "plant_time": None} for i in range(MAX_LANDS)],
    }


def load_save():
    """加载存档"""
    try:
        with open(SAVE_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        data = new_save()
        write_save(data)
        return data
    # 兼容旧存档：补齐土地数量
    while len(data["lands"]) < MAX_LANDS:
        data["lands"].append({"id": len(data["lands"]) + 1, "crop": None, "plant_time": None})
    return data


def write_save(data):
    """写入存档"""
    data["last_save_time"] = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    with open(SAVE_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


# ============ 核心逻辑 ============

def calc_offline(data, crops):
    """计算离线收益（启动时调用），返回 (gold, exp, count)"""
    try:
        last = datetime.datetime.strptime(data["last_save_time"], "%Y-%m-%d %H:%M:%S")
    except ValueError:
        return 0, 0, 0
    now = datetime.datetime.now()
    elapsed = (now - last).total_seconds() / 60.0
    if elapsed <= 0:
        return 0, 0, 0

    gold, exp, count = 0, 0, 0
    for land in data["lands"]:
        if not land["crop"] or not land["plant_time"]:
            continue
        c = crops.get(land["crop"])
        if not c:
            continue
        try:
            pt = datetime.datetime.strptime(land["plant_time"], "%Y-%m-%d %H:%M:%S")
        except ValueError:
            continue
        if (now - pt).total_seconds() / 60.0 < c["growth_minutes"]:
            continue
        n = min(int(elapsed / c["growth_minutes"]), 100)
        if n <= 0:
            continue
        gold += c["sell_price"] * n
        exp += c["exp"] * n
        count += n
        land["plant_time"] = (
            pt + datetime.timedelta(minutes=c["growth_minutes"] * n)
        ).strftime("%Y-%m-%d %H:%M:%S")

    if count > 0:
        data["gold"] += gold
        data["exp"] += exp
        try_level_up(data)
    return gold, exp, count


def try_level_up(data):
    """循环检测升级"""
    while data["exp"] >= 80 + data["level"] * 40:
        data["exp"] -= 80 + data["level"] * 40
        data["level"] += 1
        data["talent_points"] += 1
        print(f"🎉 升级！当前 Lv.{data['level']}，获得 1 天赋点！")


# ============ 功能模块 ============

def do_plant(data, crops):
    """种植作物"""
    print("\n  🌱 种植\n" + "=" * 50)

    # 检查空闲土地
    free = [l for l in data["lands"] if not l["crop"]]
    if not free:
        print("\n❌ 所有土地已占满！")
        pause()
        return

    print(f"\n空闲土地：{', '.join(str(l['id']) for l in free[:15])}", end="")
    if len(free) > 15:
        print(f" …等共 {len(free)} 块", end="")
    print()

    lid = read_int(f"\n选择土地编号 (1-{MAX_LANDS}): ", 1, MAX_LANDS)
    if lid is None:
        print("输入无效！")
        pause()
        return
    land = data["lands"][lid - 1]
    if land["crop"]:
        print("该土地已有作物！")
        pause()
        return

    # 列出可种植作物
    avail = [(n, c) for n, c in crops.items() if data["level"] >= c["level"]]
    if not avail:
        print(f"\n❌ 等级 {data['level']} 无法种植任何作物")
        pause()
        return

    print(f"\n可种植作物（等级 {data['level']}）：")
    for i, (n, c) in enumerate(avail, 1):
        ok = "✅" if data["gold"] >= c["seed_price"] else "❌"
        print(f"  {i}. {n}  种子:{c['seed_price']}💰 售价:{c['sell_price']}💰  "
              f"生长:{c['growth_minutes']}min 经验:{c['exp']} {ok}")

    idx = read_int(f"\n选择作物 (1-{len(avail)}): ", 1, len(avail))
    if idx is None:
        print("输入无效！")
        pause()
        return

    name, info = avail[idx - 1]
    if data["gold"] < info["seed_price"]:
        print(f"金币不足！需要 {info['seed_price']}，当前 {data['gold']}")
        pause()
        return

    data["gold"] -= info["seed_price"]
    land["crop"] = name
    land["plant_time"] = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    land["golden_pumpkin"] = False
    land["_maturity_roll_done"] = False
    print(f"\n✅ 第 {lid} 号土地种下 {name}！")
    pause()


def do_harvest(data, crops):
    """收获所有成熟作物"""
    now = datetime.datetime.now()
    gold, exp, count = 0, 0, 0
    for land in data["lands"]:
        if not land["crop"] or not land["plant_time"]:
            continue
        c = crops.get(land["crop"])
        if not c:
            continue
        try:
            pt = datetime.datetime.strptime(land["plant_time"], "%Y-%m-%d %H:%M:%S")
        except ValueError:
            continue
        if (now - pt).total_seconds() / 60.0 >= c["growth_minutes"]:
            gold += c["sell_price"]
            exp += c["exp"]
            count += 1
            land["crop"] = None
            land["plant_time"] = None

    if count == 0:
        print("\n🌾 没有可收获的作物。")
    else:
        data["gold"] += gold
        data["exp"] += exp
        try_level_up(data)
        print(f"\n🌾 收获 {count} 块地！获得 {gold}💰 {exp}✨")
    pause()


def show_status(data):
    """查看玩家状态"""
    planted = sum(1 for l in data["lands"] if l["crop"])
    need = 80 + data["level"] * 40
    print(f"\n{'=' * 45}")
    print(f"  👤 玩家状态")
    print(f"{'=' * 45}")
    print(f"  等级：{data['level']}")
    print(f"  经验：{data['exp']} / {need}")
    print(f"  金币：{data['gold']:,}")
    print(f"  天赋点：{data['talent_points']}")
    print(f"  土地：{planted} / {MAX_LANDS}")
    print(f"{'=' * 45}")
    pause()


def show_lands(data, crops):
    """查看所有土地状态"""
    now = datetime.datetime.now()
    print(f"\n{'=' * 58}")
    print(f"  🌱 土地状况")
    print(f"{'=' * 58}")
    print(f"  {'编号':>4}  {'作物':<8}  {'状态':<10}  {'剩余'}")
    print(f"  " + "-" * 42)
    for land in data["lands"]:
        if not land["crop"]:
            print(f"  {land['id']:>4}  {'空':<8}  {'空闲':<10}  -")
        else:
            c = crops[land["crop"]]
            pt = datetime.datetime.strptime(land["plant_time"], "%Y-%m-%d %H:%M:%S")
            remain = c["growth_minutes"] - (now - pt).total_seconds() / 60.0
            if remain <= 0:
                st, rt = "✅ 可收获", "已成熟"
            else:
                st, rt = "🌱 生长中", f"{remain:.1f}min"
            print(f"  {land['id']:>4}  {land['crop']:<8}  {st:<10}  {rt}")
    print(f"{'=' * 58}")
    pause()


def show_shop(crops):
    """商店"""
    print(f"\n{'=' * 58}")
    print(f"  🏪 商店")
    print(f"{'=' * 58}")
    for n, i in crops.items():
        if i.get("hidden"):
            continue
        print(f"  {n:<8}  种子{i['seed_price']:>5}💰  售{i['sell_price']:>5}💰")
    print(f"{'=' * 58}")
    pause()


def show_help(crops=None):
    """农场手册"""
    print(f"\n{'=' * 50}")
    print(f"  📖 农场手册")
    print(f"{'=' * 50}")
    print(f"  [1] 种植 —— 选择土地播种作物")
    print(f"  [2] 收获 —— 收获所有成熟作物")
    print(f"  [3] 状态 —— 查看玩家信息")
    print(f"  [4] 土地 —— 查看每块土地详情")
    print(f"  [5] 保存 —— 手动存档")
    print(f"  [6] 商店 —— 作物价格一览")
    print(f"  [7] 农场手册 —— 显示本页面")
    print(f"  [8] 退出 —— 保存并退出")

    if crops:
        print(f"\n  🌾 作物一览")
        print(f"  " + "-" * 48)
        for n, i in sorted(crops.items(), key=lambda x: x[1].get("level", 99)):
            if i.get("hidden"):
                continue
            print(f"  {n:<6} Lv.{i['level']:<2} 种子{i['seed_price']:>5}💰 售{i['sell_price']:>5}💰  "
                  f"生长{i['growth_minutes']}min")

    print(f"\n  💡 界面每 {REFRESH_INTERVAL} 秒自动刷新")
    print(f"  💡 游戏每 {AUTO_SAVE_INTERVAL} 秒自动保存")
    print(f"  💡 离线收益自动计算")
    print(f"  💡 快捷键：数字键 1-8 直接操作")
    print(f"{'=' * 50}")
    pause()


# ============ 界面渲染 ============

def clear():
    """清屏"""
    os.system("cls" if os.name == "nt" else "clear")


def header(data):
    """顶部状态栏"""
    planted = sum(1 for l in data["lands"] if l["crop"])
    need = 80 + data["level"] * 40
    print("=" * 58)
    print(f"  🌾 开心农场  |  💰 {data['gold']:>6,}  |  Lv.{data['level']:<3}  |  "
          f"✨ {data['exp']:>3}/{need}")
    print(f"  🌱 种植 {planted:>2}/{MAX_LANDS}  |  💾 {data['last_save_time']}")
    print("=" * 58)


def menu():
    """主菜单"""
    print()
    print("    [1]种植    [2]收获    [3]状态    [4]土地")
    print("    [5]保存    [6]商店    [7]农场手册    [8]退出")
    print()


# ============ 主循环 ============

def main():
    crops = load_crops()
    data = load_save()

    # 离线收益
    gold, exp, count = calc_offline(data, crops)
    if count > 0:
        print(f"\n📦 离线收益：收获 {count} 次，获得 {gold}💰 {exp}✨")
    print("\n💡 按任意键进入游戏...")
    pause()

    # 后台自动保存
    def auto_save_loop():
        while True:
            time.sleep(AUTO_SAVE_INTERVAL)
            write_save(data)

    threading.Thread(target=auto_save_loop, daemon=True).start()

    while True:
        clear()
        header(data)
        menu()

        key = get_key(REFRESH_INTERVAL)

        if key is None:
            continue  # 超时 → 自动刷新

        # 处理按键
        if key == b"8":
            write_save(data)
            clear()
            print("🎮 游戏已保存，再见！")
            break
        elif key == b"5":
            clear()
            header(data)
            write_save(data)
            print("\n✅ 游戏已保存！")
            pause()
        elif key == b"1":
            clear()
            header(data)
            do_plant(data, crops)
        elif key == b"2":
            clear()
            header(data)
            do_harvest(data, crops)
        elif key == b"3":
            clear()
            header(data)
            show_status(data)
        elif key == b"4":
            clear()
            header(data)
            show_lands(data, crops)
        elif key == b"6":
            clear()
            header(data)
            show_shop(crops)
        elif key == b"7":
            clear()
            header(data)
            show_help()


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n👋 再见！")
        try:
            # 尝试保存当前进度
            data = load_save()
            write_save(data)
        except Exception:
            pass
        sys.exit(0)
