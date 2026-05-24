import QtQuick 6.0
import QtQuick.Controls 6.0
import QtQuick.Layouts 6.0

/* 钻石商店对话框 */
Popup {
    id: root
    width: 460
    height: 420
    anchors.centerIn: Overlay.overlay
    modal: true
    closePolicy: Popup.CloseOnEscape | Popup.CloseOnPressOutside

    property var shopData: null
    property var eventLogRef: null

    onOpened: {
        shopData = gameCtrl.getDiamondShopData()
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
            text: shopData ? "💎 钻石商店  钻石: " + shopData.diamond : "💎 钻石商店"
            font { pixelSize: 16; bold: true }
            color: "#2d4a1e"
        }

        ListView {
            id: shopListView
            Layout.fillWidth: true
            Layout.fillHeight: true
            clip: true
            model: shopData ? shopData.items : []
            spacing: 4

            delegate: Rectangle {
                width: shopListView.width
                height: 54
                radius: 4
                color: modelData.owned ? "#e8e8e8" : "#f8f5e8"
                border { color: "#d0d0c0"; width: 1 }

                RowLayout {
                    anchors { fill: parent; margins: 6 }
                    spacing: 8

                    Text {
                        text: "💎"
                        font.pixelSize: 24
                    }
                    ColumnLayout {
                        spacing: 1
                        Text {
                            text: modelData.name
                            font.pixelSize: 13
                            color: "#2d4a1e"
                        }
                        Text {
                            text: modelData.desc
                            font.pixelSize: 10
                            color: "#809080"
                        }
                    }

                    Item { Layout.fillWidth: true }

                    Text {
                        text: modelData.diamond + "💎"
                        font.pixelSize: 13
                        color: modelData.canBuy ? "#2d4a1e" : "#c03030"
                    }

                    Button {
                        text: modelData.owned ? "已拥有" : "购买"
                        enabled: modelData.canBuy
                        font.pixelSize: 10
                        implicitWidth: 52
                        implicitHeight: 28
                        onClicked: {
                            let r = gameCtrl.buyDiamondItem(modelData.idx)
                            if (eventLogRef) eventLogRef.addLog(r)
                            shopData = gameCtrl.getDiamondShopData()
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
