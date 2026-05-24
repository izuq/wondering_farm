import QtQuick 6.0
import QtQuick.Controls 6.0
import QtQuick.Layouts 6.0

/* 商店对话框 */
Popup {
    id: root
    width: 580
    height: 500
    anchors.centerIn: Overlay.overlay
    modal: true
    closePolicy: Popup.CloseOnEscape | Popup.CloseOnPressOutside

    property var shopData: null
    property var eventLogRef: null

    onOpened: {
        shopData = gameCtrl.getShopData()
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
            text: "🏪 种子商店"
            font { pixelSize: 16; bold: true }
            color: "#2d4a1e"
        }

        // 折扣横幅
        Rectangle {
            Layout.fillWidth: true
            height: 28
            radius: 5
            color: "#fff3cd"
            border { color: "#ffc107"; width: 1 }
            visible: shopData && shopData.hasDiscount

            Text {
                anchors.centerIn: parent
                text: shopData ? "🎉 商人来访！种子价格 " + (shopData.discount * 100).toFixed(0) + "% OFF" : ""
                font.pixelSize: 12
                color: "#856404"
            }
        }

        // 表头
        RowLayout {
            Layout.fillWidth: true
            spacing: 6
            Text { text: "作物"; font.pixelSize: 10; color: "#809080"; Layout.preferredWidth: 75 }
            Text { text: "等级"; font.pixelSize: 10; color: "#809080"; Layout.preferredWidth: 35 }
            Text { text: "生长"; font.pixelSize: 10; color: "#809080"; Layout.preferredWidth: 42 }
            Text { text: "价格"; font.pixelSize: 10; color: "#809080"; Layout.preferredWidth: 55 }
            Text { text: "数量"; font.pixelSize: 10; color: "#809080"; Layout.preferredWidth: 90 }
            Text { text: "库存"; font.pixelSize: 10; color: "#809080"; Layout.preferredWidth: 55 }
            Text { text: ""; font.pixelSize: 10; Layout.preferredWidth: 50 }
        }

        ListView {
            id: cropListView
            Layout.fillWidth: true
            Layout.fillHeight: true
            clip: true
            model: shopData ? shopData.crops : []
            spacing: 3

            delegate: Rectangle {
                id: row
                width: cropListView.width
                height: 40
                radius: 4
                color: modelData.canBuy ? "#f8f5e8" : "#f0e8e8"
                border { color: "#d0d0c0"; width: 1 }

                property int buyQty: 1

                RowLayout {
                    anchors { fill: parent; margins: 4 }
                    spacing: 4

                    Text {
                        text: modelData.emoji + " " + modelData.name
                        font.pixelSize: 12
                        color: "#2d4a1e"
                        Layout.preferredWidth: 75
                    }
                    Text {
                        text: "Lv." + modelData.level
                        font.pixelSize: 10
                        color: modelData.canBuy ? "#604020" : "#c03030"
                        Layout.preferredWidth: 35
                    }
                    Text {
                        text: modelData.growthMin + "min"
                        font.pixelSize: 10
                        color: "#604020"
                        Layout.preferredWidth: 42
                    }
                    ColumnLayout {
                        Layout.preferredWidth: 55
                        spacing: 0
                        Text {
                            text: modelData.seedPrice + "💰"
                            font.pixelSize: 11
                            color: modelData.canBuy ? "#2d4a1e" : "#c03030"
                        }
                        Text {
                            visible: shopData && shopData.hasDiscount
                            text: "原" + modelData.originalPrice
                            font.pixelSize: 8
                            color: "#a0a0a0"
                            font.strikeout: true
                        }
                    }
                    RowLayout {
                        Layout.preferredWidth: 90
                        spacing: 2
                        Button {
                            text: "−"
                            font.pixelSize: 10
                            implicitWidth: 22
                            implicitHeight: 22
                            onClicked: { if (row.buyQty > 1) row.buyQty-- }
                        }
                        Text {
                            text: row.buyQty
                            font.pixelSize: 12
                            color: "#2d4a1e"
                            Layout.preferredWidth: 20
                            horizontalAlignment: Text.AlignHCenter
                        }
                        Button {
                            text: "+"
                            font.pixelSize: 10
                            implicitWidth: 22
                            implicitHeight: 22
                            onClicked: { row.buyQty++ }
                        }
                    }
                    Text {
                        text: "×" + modelData.seedCount
                        font.pixelSize: 10
                        color: "#809080"
                        Layout.preferredWidth: 45
                    }
                    Text {
                        visible: modelData.seasonBonus
                        text: "🌿当季"
                        font.pixelSize: 9
                        color: "#40a040"
                    }
                    Button {
                        text: "购买"
                        enabled: modelData.canBuy
                        font.pixelSize: 10
                        implicitWidth: 44
                        implicitHeight: 26
                        onClicked: {
                            let r = gameCtrl.buySeeds(modelData.name, row.buyQty)
                            if (eventLogRef) eventLogRef.addLog(r)
                            row.buyQty = 1
                            shopData = gameCtrl.getShopData()
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
