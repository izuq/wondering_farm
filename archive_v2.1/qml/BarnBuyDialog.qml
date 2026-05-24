import QtQuick 6.0
import QtQuick.Controls 6.0
import QtQuick.Layouts 6.0

/* 购买动物对话框 */
Popup {
    id: root
    width: 560
    height: 480
    anchors.centerIn: Overlay.overlay
    modal: true
    closePolicy: Popup.CloseOnEscape | Popup.CloseOnPressOutside

    property var buyData: null
    property var eventLogRef: null

    onOpened: {
        buyData = gameCtrl.getBarnBuyData()
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
            text: "🐣 购买动物"
            font { pixelSize: 16; bold: true }
            color: "#2d4a1e"
        }

        Text {
            visible: buyData && !buyData.hasFreeSlot
            text: "⚠️ 没有空闲栏位，请先解锁或清空栏位"
            font.pixelSize: 12
            color: "#c03030"
        }

        Text {
            visible: buyData && buyData.hasFreeSlot
            text: buyData ? "空闲栏位: " + buyData.freeSlots.join(", ") : ""
            font.pixelSize: 11
            color: "#604020"
        }

        // 表头
        RowLayout {
            Layout.fillWidth: true
            spacing: 4
            Text { text: "动物"; font.pixelSize: 10; color: "#809080"; Layout.preferredWidth: 60 }
            Text { text: "等级"; font.pixelSize: 10; color: "#809080"; Layout.preferredWidth: 35 }
            Text { text: "价格"; font.pixelSize: 10; color: "#809080"; Layout.preferredWidth: 55 }
            Text { text: "产品"; font.pixelSize: 10; color: "#809080"; Layout.preferredWidth: 100 }
            Text { text: "饲料"; font.pixelSize: 10; color: "#809080"; Layout.preferredWidth: 90 }
            Text { text: ""; font.pixelSize: 10; Layout.preferredWidth: 50 }
        }

        ListView {
            id: animalListView
            Layout.fillWidth: true
            Layout.fillHeight: true
            clip: true
            model: buyData ? buyData.animals : []
            spacing: 3

            delegate: Rectangle {
                width: animalListView.width
                height: 38
                radius: 4
                color: modelData.canBuy ? "#f8f5e8" : (modelData.unlocked ? "#f0e8e8" : "#e8e8e8")
                border { color: "#d0d0c0"; width: 1 }

                RowLayout {
                    anchors { fill: parent; margins: 4 }
                    spacing: 4

                    Text {
                        text: modelData.emoji + " " + modelData.name
                        font.pixelSize: 12
                        color: "#2d4a1e"
                        Layout.preferredWidth: 65
                    }
                    Text {
                        text: "Lv." + modelData.level
                        font.pixelSize: 10
                        color: modelData.unlocked ? "#604020" : "#c03030"
                        Layout.preferredWidth: 35
                    }
                    Text {
                        text: modelData.price + "💰"
                        font.pixelSize: 11
                        color: modelData.canBuy ? "#2d4a1e" : "#c03030"
                        Layout.preferredWidth: 55
                    }
                    Text {
                        text: modelData.productEmoji + " " + modelData.product + "(" + modelData.sellPrice + "💰)"
                        font.pixelSize: 10
                        color: "#604020"
                        Layout.preferredWidth: 110
                    }
                    Text {
                        text: "🍽" + modelData.feedDesc
                        font.pixelSize: 9
                        color: "#809080"
                        Layout.preferredWidth: 90
                    }

                    // 折扣标记
                    Text {
                        visible: modelData.price !== modelData.originalPrice
                        text: "折"
                        font.pixelSize: 9
                        color: "#d4a030"
                    }

                    Button {
                        text: modelData.unlocked ? "购买" : "🔒"
                        enabled: modelData.canBuy
                        font.pixelSize: 10
                        implicitWidth: 48
                        implicitHeight: 26
                        onClicked: {
                            let r = gameCtrl.buyBarnAnimal(modelData.name)
                            if (eventLogRef) eventLogRef.addLog(r)
                            buyData = gameCtrl.getBarnBuyData()
                        }
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
