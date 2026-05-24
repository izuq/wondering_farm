import QtQuick 6.0
import QtQuick.Controls 6.0
import QtQuick.Layouts 6.0

/* 升级农业建筑对话框 */
Popup {
    id: root
    width: 460
    height: 360
    anchors.centerIn: Overlay.overlay
    modal: true
    closePolicy: Popup.CloseOnEscape | Popup.CloseOnPressOutside

    property var upgradeList: null
    property var eventLogRef: null

    onOpened: {
        upgradeList = gameCtrl.getAgroUpgradeList()
    }

    background: Rectangle {
        radius: 10
        color: "#f5f0e0"
        border { color: "#80a080"; width: 2 }
    }

    ColumnLayout {
        anchors { fill: parent; margins: 12 }
        spacing: 8

        Text {
            text: "⬆️ 升级建筑"
            font { pixelSize: 16; bold: true }
            color: "#2d4a1e"
        }

        Text {
            text: "升级解锁新配方，提升加工速度。最高 Lv.4"
            font.pixelSize: 11
            color: "#809080"
        }

        ListView {
            id: upgradeListView
            Layout.fillWidth: true
            Layout.fillHeight: true
            clip: true
            model: upgradeList ? upgradeList.upgrades : []
            spacing: 3

            delegate: Rectangle {
                width: upgradeListView.width
                height: 44
                radius: 4
                color: "#f8f5e8"
                border { color: "#d0d0c0"; width: 1 }

                RowLayout {
                    anchors { fill: parent; margins: 6 }
                    spacing: 8

                    Text {
                        text: modelData.emoji
                        font.pixelSize: 20
                    }
                    Text {
                        text: "#" + modelData.id
                        font.pixelSize: 12
                        color: "#2d4a1e"
                    }
                    Text {
                        text: modelData.buildingName
                        font.pixelSize: 12
                        color: "#2d4a1e"
                        Layout.preferredWidth: 70
                    }
                    Text {
                        text: "Lv." + modelData.level + " → Lv." + modelData.nextLevel
                        font.pixelSize: 11
                        color: "#40a040"
                    }

                    Item { Layout.fillWidth: true }

                    Button {
                        text: modelData.canUpgrade ? "⬆ " + modelData.cost + "💰" : "💰" + modelData.cost
                        enabled: modelData.canUpgrade
                        font.pixelSize: 10
                        onClicked: {
                            let r = gameCtrl.upgradeAgroBuilding(modelData.id)
                            if (eventLogRef) eventLogRef.addLog(r)
                            upgradeList = gameCtrl.getAgroUpgradeList()
                        }
                    }
                }
            }

            Text {
                anchors.centerIn: parent
                text: upgradeList && !upgradeList.hasUpgrades ? "没有可升级的建筑" : ""
                font.pixelSize: 13
                color: "#a0a0a0"
            }
        }

        Button {
            text: "关闭"
            Layout.alignment: Qt.AlignRight
            onClicked: root.close()
        }
    }
}
