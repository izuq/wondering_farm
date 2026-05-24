import QtQuick 6.0
import QtQuick.Controls 6.0
import QtQuick.Layouts 6.0

/* 农场手册对话框 */
Popup {
    id: root
    width: 520
    height: 500
    anchors.centerIn: Overlay.overlay
    modal: true
    closePolicy: Popup.CloseOnEscape | Popup.CloseOnPressOutside

    property int helpTabIndex: 0

    background: Rectangle {
        radius: 10
        color: "#f5f0e0"
        border { color: "#80a080"; width: 2 }
    }

    ColumnLayout {
        anchors { fill: parent; margins: 12 }
        spacing: 8

        Text {
            text: "📖 农场手册 v3.0"
            font { pixelSize: 16; bold: true }
            color: "#2d4a1e"
        }

        // 分类标签
        RowLayout {
            Layout.fillWidth: true
            spacing: 4

            Repeater {
                model: ["🌱 土地", "🐔 养殖", "🏗️ 建筑", "⭐ 系统"]
                Button {
                    text: modelData
                    checkable: true
                    checked: helpTabIndex === index
                    flat: true
                    font.pixelSize: 11
                    background: Rectangle {
                        radius: 5
                        color: parent.checked ? "#c0d8a0" : "#e8e0d0"
                        border { color: "#c0c0a0"; width: 1 }
                    }
                    onClicked: { helpTabIndex = index }
                }
            }
        }

        // 内容
        StackLayout {
            Layout.fillWidth: true
            Layout.fillHeight: true
            currentIndex: helpTabIndex

            // 土地手册
            ScrollView {
                Layout.fillWidth: true
                Layout.fillHeight: true
                clip: true

                Text {
                    width: parent ? parent.width : 400
                    wrapMode: Text.WordWrap
                    font.pixelSize: 11
                    color: "#2d4a1e"
                    lineHeight: 1.5
                    text: "【种植操作】
1. 种植：点击「🌱 种植」打开种植对话框
   选择空闲土地 → 选择作物 → 确认种植
   需要种子：商店购买或收获保留

2. 收获：点击「🌾 收获」批量收获所有成熟作物
   成熟作物有金色闪烁边框
   产量 = 基础产量 × 土地等级倍率 × 天赋加成 × 季节加成
   金色南瓜：收获时额外获得 💎

3. 升级土地：点击「⬆ 升级」→ 选择土地 → 升级
   升级效果：产量+10%/级，生长加速5%/级，双倍概率+2%/级
   最高 Lv.10

4. 解锁土地：点击「🔓 解锁」
   初始 6 块，最多 12 块
   费用随解锁数量递增

5. 季节系统：每 2 小时轮换（🌸春☀️夏🍂秋❄️冬）
   当季作物生长加速 50%！非当季作物减速 30%

6. 暴风/虫灾：负面事件，影响生长时间或产量
   收获特定作物可解除负面效果"
                }
            }

            // 养殖手册
            ScrollView {
                Layout.fillWidth: true
                Layout.fillHeight: true
                clip: true

                Text {
                    width: parent ? parent.width : 400
                    wrapMode: Text.WordWrap
                    font.pixelSize: 11
                    color: "#2d4a1e"
                    lineHeight: 1.5
                    text: "【养殖场操作】
1. 购买动物：点击「🐣 购买」
   选择动物 → 自动放入空闲栏位（需要相应等级）

2. 投喂：点击「🍽 投喂」
   消耗饲料投喂所有动物，已喂动物可补料

3. 收集产品：点击「📦 收集」
   收取所有已产出动物产品到仓库

4. 繁殖：点击「🧬 繁殖」
   选择两只同种成年动物 → 花费 1000💰 → 成功率 70%
   亲本栏位 ≥ 5 级各 +5% 成功率

5. 栏位升级：点击栏位 → 升级
   升级效果：加速生产、提升产量、Lv.8+ 双倍产出概率
   Lv.10 全局加成 +10%

6. 解锁栏位：点击「🔓 解锁」
   费用 = 200 × 栏位号

【动物生命周期】
- 幼年期（前 2 次产出）：产量减半
- 成年期（2-40 次）：正常产出
- 老年期（40 次+）：产量降至 70%

【饲料种
类】
- 基础饲料：小麦×2 → 基础饲料×1（5min）
- 精制饲料：玉米×2+小麦×1 → 精制饲料×1（8min）
- 高级饲料：水稻×3+大豆×2 → 高级饲料×1（12min）
- 特殊饲料：水果×3+高级饲料×1 → 特殊饲料×1（15min）"
                }
            }

            // 建筑手册
            ScrollView {
                Layout.fillWidth: true
                Layout.fillHeight: true
                clip: true

                Text {
                    width: parent ? parent.width : 400
                    wrapMode: Text.WordWrap
                    font.pixelSize: 11
                    color: "#2d4a1e"
                    lineHeight: 1.5
                    text: "【农业建筑】
1. 建造：点击「🏗 建造」
   饲料加工厂（5000💰）→ 加工饲料
   酿酒厂（8000💰）→ 酿造酒类

2. 加工：点击「🔧 加工」→ 选建筑 → 选配方 → 选批次
   批量加工（1-20 批），自动消耗原料

3. 升级：点击「⬆ 升级」→ 选择建筑
   Lv.1→4，每级解锁新配方

4. 收取：点击「📦 收取」收取所有完成的产品
   饲料 → 存入饲料库存，酒类 → 存入产品库存

5. 解锁：点击「🔓 解锁」更多建筑位

【工厂加工】（传统工厂）
- 使用原料直接加工为高价值产品
- 点击「🏭 工厂」查看加工状态
- 天赋「双重加工」可触发双倍产出

【仓库系统】
- 容量：100 基础 + 每 5 级 +10 + 钻石扩容 +10/次
- 锁定物品不会被批量出售
- 分类：作物 / 加工品 / 饲料"
                }
            }

            // 系统手册
            ScrollView {
                Layout.fillWidth: true
                Layout.fillHeight: true
                clip: true

                Text {
                    width: parent ? parent.width : 400
                    wrapMode: Text.WordWrap
                    font.pixelSize: 11
                    color: "#2d4a1e"
                    lineHeight: 1.5
                    text: "【天赋系统】
三大系：种植系 / 经营系 / 养殖系
获得天赋点：升级获得 1 点/级
重置：50💎 或 5000💰，返还所有已分配点数
天赋果实：0.5% 概率掉落（最多使用 10 个）

【成就系统】
自动检查达成条件，获得金币/经验/💎奖励
「完美主义者」在所有其他成就达成后自动完成

【钻石商店】
6 件商品：重置药水 / 扩容券 / 四叶草 / 化肥 / 速长剂 / 彩虹皮肤

【商人折扣】
随机出现，种子价格打折（天赋可提升折扣幅度）
商人来访持续一段时间

【离线收益】
- 离线期间作物继续生长
- 养殖场继续生产（需有饲料）
- 农业建筑继续加工（需有原料）
- 离线时长无上限

【快捷键】
- 暂无（纯鼠标操作）

【数据保存】
- 自动保存每 30 秒
- 手动保存：点击「💾 保存」
- 存档文件：save.json"
                }
            }
        }

        Button {
            text: "关闭"
            Layout.alignment: Qt.AlignRight
            onClicked: root.close()
        }
    }
}
