import QtQuick 6.0
import QtQuick.Controls 6.0
import QtQuick.Layouts 6.0

ApplicationWindow {
    id: window
    visible: true
    width: 720
    height: 720
    title: "开心农场 v3.0"
    minimumWidth: 720
    minimumHeight: 700

    /* 渐变背景 */
    Rectangle {
        anchors.fill: parent
        gradient: Gradient {
            GradientStop { position: 0.0; color: "#87CEEB" }
            GradientStop { position: 0.3; color: "#b5d491" }
            GradientStop { position: 1.0; color: "#8fc47a" }
        }
    }

    /* 装饰 */
    Text {
        anchors { top: parent.top; right: parent.right; topMargin: 10; rightMargin: 20 }
        text: "🌼"
        font.pixelSize: 16
    }

    /* 主布局 */
    ColumnLayout {
        anchors {
            fill: parent
            topMargin: 6
            bottomMargin: 6
            leftMargin: 12
            rightMargin: 12
        }
        spacing: 4

        // ---- 标题 + 信息栏 ----
        RowLayout {
            Layout.fillWidth: true
            spacing: 10

            Text {
                text: "开心农场"
                font { pixelSize: 22; bold: true }
                color: "#2d4a1e"
                style: Text.Raised
                styleColor: "#ffffff"
            }

            InfoBar {
                id: infoBar
                Layout.fillWidth: true
                pm: playerModel
            }
        }

        // ---- 标签栏 + 全局按钮 ----
        RowLayout {
            Layout.fillWidth: true
            spacing: 6

            Repeater {
                model: ["🌱 土地", "🐔 养殖场", "🏗️ 农业建筑"]
                Button {
                    text: modelData
                    checkable: true
                    checked: tabIndex === index
                    onClicked: tabIndex = index
                    flat: true
                    font.pixelSize: 12
                    background: Rectangle {
                        radius: 6
                        color: parent.checked ? "#90c8e090" : "#40e0d8b0"
                        border { color: "#60a0a060"; width: 1 }
                    }
                }
            }

            Item { Layout.fillWidth: true }

            // 全局按钮
            Button {
                text: "🏪 商店"
                flat: true
                font.pixelSize: 11
                background: Rectangle {
                    radius: 5
                    color: "#40e8d0b0"
                    border { color: "#60a0a060"; width: 1 }
                }
                onClicked: { shopDialog.open() }
            }
            Button {
                text: "💾 保存"
                flat: true
                font.pixelSize: 11
                background: Rectangle {
                    radius: 5
                    color: "#40d4e8b0"
                    border { color: "#60a0a060"; width: 1 }
                }
                onClicked: {
                    gameCtrl.saveGame()
                    eventLogObj.addLog("💾 游戏已保存")
                }
            }
            Button {
                text: "💎 钻石"
                flat: true
                font.pixelSize: 11
                background: Rectangle {
                    radius: 5
                    color: "#40d0d0f0"
                    border { color: "#60a0a060"; width: 1 }
                }
                onClicked: { diamondShopDialog.open() }
            }
            Button {
                text: "📖 手册"
                flat: true
                font.pixelSize: 11
                background: Rectangle {
                    radius: 5
                    color: "#40e0ccb0"
                    border { color: "#60a0a060"; width: 1 }
                }
                onClicked: { helpDialog.open() }
            }
        }

        // ---- 页面内容 ----
        StackLayout {
            id: tabStack
            Layout.fillWidth: true
            Layout.fillHeight: true
            currentIndex: tabIndex

            // ========== 土地页面 ==========
            ColumnLayout {
                spacing: 4

                RowLayout {
                    Layout.fillWidth: true
                    spacing: 4
                    Button { text: "🌱 种植"; font.pixelSize: 11; onClicked: plantDialog.open() }
                    Button { text: "🌾 收获"; font.pixelSize: 11; onClicked: { eventLogObj.addLog(gameCtrl.harvestAll()) } }
                    Button { text: "⬆ 升级"; font.pixelSize: 11; onClicked: upgradeDialog.open() }
                    Button { text: "🔓 解锁"; font.pixelSize: 11; onClicked: { unlockPopup.open() } }
                    Button { text: "📦 仓库"; font.pixelSize: 11; onClicked: { warehouseDialog.open() } }
                    Button { text: "⭐ 天赋"; font.pixelSize: 11; onClicked: { talentDialog.open() } }
                    Button { text: "🏆 成就"; font.pixelSize: 11; onClicked: { achievementDialog.open() } }
                }

                ScrollView {
                    Layout.fillWidth: true
                    Layout.fillHeight: true
                    clip: true

                    GridLayout {
                        columns: 4
                        columnSpacing: 8
                        rowSpacing: 8

                        Repeater {
                            model: farmModel
                            FarmPlot {
                                pLid: lid
                                pCrop: crop
                                pStage: stage
                                pReady: ready
                                pLocked: locked
                                pLevel: level
                                pTimeLeft: timeLeft
                                pHasImage: hasImage
                                pEmoji: emoji
                                pGolden: goldenPumpkin
                            }
                        }
                    }
                }
            }

            // ========== 养殖场页面 ==========
            ColumnLayout {
                spacing: 4

                RowLayout {
                    Layout.fillWidth: true
                    spacing: 4
                    Button { text: "🐣 购买"; font.pixelSize: 11; onClicked: { barnBuyDialog.open() } }
                    Button { text: "🍽 投喂"; font.pixelSize: 11; onClicked: { eventLogObj.addLog(gameCtrl.feedAnimals()) } }
                    Button { text: "📦 收集"; font.pixelSize: 11; onClicked: { eventLogObj.addLog(gameCtrl.collectBarn()) } }
                    Button { text: "🧬 繁殖"; font.pixelSize: 11; onClicked: { breedDialog.open() } }
                    Button { text: "📦 仓库"; font.pixelSize: 11; onClicked: { warehouseDialog.open() } }
                    Button { text: "⭐ 天赋"; font.pixelSize: 11; onClicked: { talentDialog.open() } }
                    Button { text: "🔓 解锁"; font.pixelSize: 11; onClicked: { barnUnlockPopup.open() } }
                }

                ScrollView {
                    Layout.fillWidth: true
                    Layout.fillHeight: true
                    clip: true

                    GridLayout {
                        columns: 10
                        columnSpacing: 3
                        rowSpacing: 3

                        Repeater {
                            model: barnModel
                            BarnSlot {
                                sBid: bid
                                sAnimal: animal
                                sAnimalType: animalType
                                sLevel: level
                                sPending: pending
                                sTimeLeft: timeLeft
                                sStatus: status
                                sEmoji: emoji
                                sLocked: locked
                            }
                        }
                    }
                }
            }

            // ========== 农业建筑页面 ==========
            ColumnLayout {
                spacing: 4

                RowLayout {
                    Layout.fillWidth: true
                    spacing: 4
                    Button { text: "🏗 建造"; font.pixelSize: 11; onClicked: { agroBuildDialog.open() } }
                    Button { text: "⬆ 升级"; font.pixelSize: 11; onClicked: { agroUpgradeDialog.open() } }
                    Button { text: "🔧 加工"; font.pixelSize: 11; onClicked: { agroProcessDialog.open() } }
                    Button { text: "📦 收取"; font.pixelSize: 11; onClicked: { eventLogObj.addLog(gameCtrl.collectAgro()) } }
                    Button { text: "📦 仓库"; font.pixelSize: 11; onClicked: { warehouseDialog.open() } }
                    Button { text: "⭐ 天赋"; font.pixelSize: 11; onClicked: { talentDialog.open() } }
                    Button { text: "🔓 解锁"; font.pixelSize: 11; onClicked: { agroUnlockPopup.open() } }
                    Button { text: "🏭 工厂"; font.pixelSize: 11; onClicked: { factoryDialog.open() } }
                }

                ScrollView {
                    Layout.fillWidth: true
                    Layout.fillHeight: true
                    clip: true

                    GridLayout {
                        columns: 10
                        columnSpacing: 3
                        rowSpacing: 3

                        Repeater {
                            model: agroModel
                            AgroSlot {
                                aSid: sid
                                aBuilding: building
                                aLevel: level
                                aStatus: status
                                aTimeLeft: timeLeft
                                aReady: ready
                                aBatches: batches
                                aBuildingName: buildingName
                                aLocked: locked
                                aBuildingEmoji: buildingEmoji
                            }
                        }
                    }
                }
            }
        }

        // ---- 事件日志 ----
        EventLog {
            id: eventLogObj
            Layout.fillWidth: true
            log: eventLog
        }
    }

    property int tabIndex: 0

    // ---- 弹窗 ----
    PlantDialog {
        id: plantDialog
        eventLogRef: eventLogObj
    }

    LandUpgradeDialog {
        id: upgradeDialog
        eventLogRef: eventLogObj
    }

    ShopDialog {
        id: shopDialog
        eventLogRef: eventLogObj
    }

    WarehouseDialog {
        id: warehouseDialog
        eventLogRef: eventLogObj
    }

    BarnBuyDialog {
        id: barnBuyDialog
        eventLogRef: eventLogObj
    }

    BreedDialog {
        id: breedDialog
        eventLogRef: eventLogObj
    }

    AgroBuildDialog {
        id: agroBuildDialog
        eventLogRef: eventLogObj
    }

    AgroUpgradeDialog {
        id: agroUpgradeDialog
        eventLogRef: eventLogObj
    }

    AgroProcessDialog {
        id: agroProcessDialog
        eventLogRef: eventLogObj
    }

    TalentDialog {
        id: talentDialog
        eventLogRef: eventLogObj
    }

    AchievementDialog {
        id: achievementDialog
    }

    DiamondShopDialog {
        id: diamondShopDialog
        eventLogRef: eventLogObj
    }

    FactoryDialog {
        id: factoryDialog
        eventLogRef: eventLogObj
    }

    HelpDialog {
        id: helpDialog
    }

    // 解锁土地确认
    Popup {
        id: unlockPopup
        width: 340
        height: 180
        anchors.centerIn: Overlay.overlay
        modal: true
        closePolicy: Popup.CloseOnEscape | Popup.CloseOnPressOutside

        property var info: null

        onOpened: {
            info = gameCtrl.getUnlockLandInfo()
        }

        background: Rectangle {
            radius: 10
            color: "#f5f0e0"
            border { color: "#80a080"; width: 2 }
        }

        ColumnLayout {
            anchors { fill: parent; margins: 16 }
            spacing: 8

            Text {
                text: "🔓 解锁新土地"
                font { pixelSize: 15; bold: true }
                color: "#2d4a1e"
            }

            Text {
                visible: info && info.isMax
                text: "所有土地已解锁！"
                font.pixelSize: 13
                color: "#a0a0a0"
            }

            ColumnLayout {
                visible: info && !info.isMax
                spacing: 4
                Text {
                    text: "解锁第 " + (info ? info.nextId : "?") + " 号土地"
                    font.pixelSize: 13
                    color: "#2d4a1e"
                }
                Text {
                    text: "花费：" + (info ? info.cost : "?") + "💰  需要：Lv." + (info ? info.levelNeed : "?")
                    font.pixelSize: 12
                    color: "#604020"
                }
                Text {
                    visible: info && !info.canUnlock
                    text: "❌ 金币或等级不足"
                    font.pixelSize: 11
                    color: "#c03030"
                }
            }

            RowLayout {
                Layout.fillWidth: true
                spacing: 8
                Item { Layout.fillWidth: true }
                Button {
                    text: "取消"
                    onClicked: unlockPopup.close()
                }
                Button {
                    text: "🔓 解锁"
                    visible: info && !info.isMax
                    enabled: info && info.canUnlock
                    onClicked: {
                        let r = gameCtrl.unlockLand()
                        eventLogObj.addLog(r)
                        unlockPopup.close()
                    }
                }
            }
        }
    }

    // 解锁养殖栏位确认
    Popup {
        id: barnUnlockPopup
        width: 340
        height: 180
        anchors.centerIn: Overlay.overlay
        modal: true
        closePolicy: Popup.CloseOnEscape | Popup.CloseOnPressOutside

        property var info: null

        onOpened: {
            info = gameCtrl.getUnlockBarnInfo()
        }

        background: Rectangle {
            radius: 10
            color: "#f5f0e0"
            border { color: "#80a080"; width: 2 }
        }

        ColumnLayout {
            anchors { fill: parent; margins: 16 }
            spacing: 8

            Text {
                text: "🔓 解锁养殖栏位"
                font { pixelSize: 15; bold: true }
                color: "#2d4a1e"
            }

            Text {
                visible: info && info.isMax
                text: "所有栏位已解锁！"
                font.pixelSize: 13
                color: "#a0a0a0"
            }

            ColumnLayout {
                visible: info && !info.isMax
                spacing: 4
                Text {
                    text: "解锁第 " + (info ? info.nextId : "?") + " 号栏位"
                    font.pixelSize: 13
                    color: "#2d4a1e"
                }
                Text {
                    text: "花费：" + (info ? info.cost : "?") + "💰  需要：Lv." + (info ? info.levelNeed : "?")
                    font.pixelSize: 12
                    color: "#604020"
                }
                Text {
                    visible: info && !info.canUnlock
                    text: "❌ 金币或等级不足"
                    font.pixelSize: 11
                    color: "#c03030"
                }
            }

            RowLayout {
                Layout.fillWidth: true
                spacing: 8
                Item { Layout.fillWidth: true }
                Button {
                    text: "取消"
                    onClicked: barnUnlockPopup.close()
                }
                Button {
                    text: "🔓 解锁"
                    visible: info && !info.isMax
                    enabled: info && info.canUnlock
                    onClicked: {
                        let r = gameCtrl.unlockBarn()
                        eventLogObj.addLog(r)
                        barnUnlockPopup.close()
                    }
                }
            }
        }
    }

    // 解锁农业建筑位确认
    Popup {
        id: agroUnlockPopup
        width: 340
        height: 180
        anchors.centerIn: Overlay.overlay
        modal: true
        closePolicy: Popup.CloseOnEscape | Popup.CloseOnPressOutside

        property var info: null

        onOpened: {
            info = gameCtrl.getUnlockAgroInfo()
        }

        background: Rectangle {
            radius: 10
            color: "#f5f0e0"
            border { color: "#80a080"; width: 2 }
        }

        ColumnLayout {
            anchors { fill: parent; margins: 16 }
            spacing: 8

            Text {
                text: "🔓 解锁建筑位"
                font { pixelSize: 15; bold: true }
                color: "#2d4a1e"
            }

            Text {
                visible: info && info.isMax
                text: "所有建筑位已解锁！"
                font.pixelSize: 13
                color: "#a0a0a0"
            }

            ColumnLayout {
                visible: info && !info.isMax
                spacing: 4
                Text {
                    text: "解锁第 " + (info ? info.nextId : "?") + " 号建筑位"
                    font.pixelSize: 13
                    color: "#2d4a1e"
                }
                Text {
                    text: "花费：" + (info ? info.cost : "?") + "💰"
                    font.pixelSize: 12
                    color: "#604020"
                }
                Text {
                    visible: info && !info.canUnlock
                    text: "❌ 金币不足"
                    font.pixelSize: 11
                    color: "#c03030"
                }
            }

            RowLayout {
                Layout.fillWidth: true
                spacing: 8
                Item { Layout.fillWidth: true }
                Button {
                    text: "取消"
                    onClicked: agroUnlockPopup.close()
                }
                Button {
                    text: "🔓 解锁"
                    visible: info && !info.isMax
                    enabled: info && info.canUnlock
                    onClicked: {
                        let r = gameCtrl.unlockAgroSlot()
                        eventLogObj.addLog(r)
                        agroUnlockPopup.close()
                    }
                }
            }
        }
    }
}
