import QtQuick 6.0
import QtQuick.Controls 6.0
import QtQuick.Layouts 6.0

/* 升级土地对话框 */
Popup {
    id: root
    width: 480
    height: 400
    anchors.centerIn: Overlay.overlay
    modal: true
    closePolicy: Popup.CloseOnEscape | Popup.CloseOnPressOutside

    property var landList: []
    property var eventLogRef: null

    onOpened: {
        landList = gameCtrl.getLandUpgradeList()
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
            text: "⬆️ 升级土地"
            font { pixelSize: 16; bold: true }
            color: "#2d4a1e"
        }

        Text {
            text: "升级后产量倍率提升、生长加速。最高 Lv.10"
            font.pixelSize: 11
            color: "#809080"
        }

        ListView {
            id: list
            Layout.fillWidth: true
            Layout.fillHeight: true
            clip: true
            model: landList
            spacing: 3

            delegate: Rectangle {
                width: list.width
                height: 36
                radius: 4
                color: "#f8f5e8"
                border { color: "#d0d0c0"; width: 1 }

                RowLayout {
                    anchors { fill: parent; margins: 6 }
                    spacing: 8

                    Text {
                        text: "#" + modelData.id
                        font.pixelSize: 12
                        color: "#2d4a1e"
                    }
                    Text {
                        text: modelData.crop
                        font.pixelSize: 12
                        color: "#2d4a1e"
                        Layout.preferredWidth: 60
                    }
                    Text {
                        text: "★".repeat(Math.min(modelData.level, 5))
                        font.pixelSize: 10
                        color: "#d4a030"
                    }
                    Text {
                        text: "Lv." + modelData.level
                        font.pixelSize: 11
                        color: "#604020"
                    }
                    Text {
                        visible: !modelData.isMax
                        text: "→ Lv." + (modelData.level + 1)
                        font.pixelSize: 11
                        color: "#40a040"
                    }

                    Item { Layout.fillWidth: true }

                    Button {
                        visible: !modelData.isMax
                        text: modelData.canUpgrade ? "⬆ " + modelData.cost + "💰" : "💰" + modelData.cost
                        enabled: modelData.canUpgrade
                        font.pixelSize: 10
                        onClicked: {
                            let r = gameCtrl.upgradeLand(modelData.id)
                            if (eventLogRef) eventLogRef.addLog(r)
                            // refresh
                            landList = gameCtrl.getLandUpgradeList()
                        }
                    }

                    Text {
                        visible: modelData.isMax
                        text: "已满级"
                        font.pixelSize: 10
                        color: "#a0a0a0"
                    }
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
