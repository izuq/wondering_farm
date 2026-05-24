import QtQuick 6.0
import QtQuick.Controls 6.0
import QtQuick.Layouts 6.0

/* 仓库对话框 */
Popup {
    id: root
    width: 600
    height: 500
    anchors.centerIn: Overlay.overlay
    modal: true
    closePolicy: Popup.CloseOnEscape | Popup.CloseOnPressOutside

    property var whData: null
    property int catIndex: 0
    property var eventLogRef: null

    onOpened: {
        whData = gameCtrl.getWarehouseData()
        catIndex = 0
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
            text: "📦 仓库"
            font { pixelSize: 16; bold: true }
            color: "#2d4a1e"
        }

        // 容量条
        RowLayout {
            Layout.fillWidth: true
            spacing: 8

            Text {
                text: whData ? whData.usage + "/" + whData.capacity : "?"
                font.pixelSize: 12
                color: "#2d4a1e"
            }
            Rectangle {
                Layout.fillWidth: true
                height: 14
                radius: 3
                color: "#e0d8c0"
                Rectangle {
                    width: whData ? parent.width * Math.min(whData.usage / whData.capacity, 1.0) : 0
                    height: parent.height
                    radius: 3
                    color: {
                        if (!whData) return "#40a040"
                        var r = whData.usage / whData.capacity
                        return r > 0.8 ? "#d04040" : (r > 0.5 ? "#d4a030" : "#40a040")
                    }
                }
            }
            Button {
                text: "+扩容"
                font.pixelSize: 10
                implicitHeight: 24
                onClicked: {
                    let r = gameCtrl.expandWarehouse()
                    if (eventLogRef) eventLogRef.addLog(r)
                    whData = gameCtrl.getWarehouseData()
                }
            }
        }

        // 分类标签
        RowLayout {
            Layout.fillWidth: true
            spacing: 4

            Repeater {
                model: whData ? whData.categories : []
                Button {
                    text: modelData.label + " (" + modelData.items.length + ")"
                    font.pixelSize: 11
                    checkable: true
                    checked: catIndex === index
                    flat: true
                    background: Rectangle {
                        radius: 5
                        color: parent.checked ? "#c0d8a0" : "#e8e0d0"
                        border { color: "#c0c0a0"; width: 1 }
                    }
                    onClicked: { catIndex = index }
                }
            }
        }

        // 当前分类的物品列表
        ListView {
            id: itemListView
            Layout.fillWidth: true
            Layout.fillHeight: true
            clip: true
            model: {
                if (!whData || !whData.categories[catIndex]) return []
                return whData.categories[catIndex].items
            }
            spacing: 3

            delegate: Rectangle {
                id: itemRow
                width: itemListView.width
                height: 36
                radius: 4
                color: modelData.locked ? "#fff8e0" : "#f8f5e8"
                border { color: modelData.locked ? "#d4a030" : "#d0d0c0"; width: 1 }

                property int sellQty: modelData.qty

                RowLayout {
                    anchors { fill: parent; margins: 4 }
                    spacing: 6

                    Text {
                        text: modelData.emoji
                        font.pixelSize: 18
                    }
                    Text {
                        text: modelData.name
                        font.pixelSize: 12
                        color: "#2d4a1e"
                        Layout.preferredWidth: 80
                    }
                    Text {
                        text: "×" + modelData.qty
                        font.pixelSize: 12
                        color: "#604020"
                        Layout.preferredWidth: 50
                    }
                    Text {
                        text: "@" + modelData.price + "💰"
                        font.pixelSize: 11
                        color: "#809080"
                        Layout.preferredWidth: 60
                    }
                    Text {
                        text: modelData.locked ? "🔒" : ""
                        font.pixelSize: 12
                        Layout.preferredWidth: 24
                    }

                    Item { Layout.fillWidth: true }

                    // 数量选择
                    RowLayout {
                        spacing: 2
                        Button {
                            text: "−"
                            font.pixelSize: 10
                            implicitWidth: 22
                            implicitHeight: 22
                            onClicked: { if (itemRow.sellQty > 1) itemRow.sellQty-- }
                        }
                        Text {
                            text: itemRow.sellQty
                            font.pixelSize: 11
                            color: "#2d4a1e"
                            Layout.preferredWidth: 18
                            horizontalAlignment: Text.AlignHCenter
                        }
                        Button {
                            text: "+"
                            font.pixelSize: 10
                            implicitWidth: 22
                            implicitHeight: 22
                            onClicked: {
                                if (itemRow.sellQty < modelData.qty) itemRow.sellQty++
                            }
                        }
                    }

                    Button {
                        text: "出售"
                        font.pixelSize: 10
                        implicitWidth: 40
                        implicitHeight: 24
                        onClicked: {
                            let r = gameCtrl.sellItem(modelData.category, modelData.name, itemRow.sellQty)
                            if (eventLogRef) eventLogRef.addLog(r)
                            whData = gameCtrl.getWarehouseData()
                        }
                    }
                    Button {
                        text: modelData.locked ? "解锁" : "锁定"
                        font.pixelSize: 10
                        implicitWidth: 40
                        implicitHeight: 24
                        onClicked: {
                            let r = gameCtrl.toggleLockItem(modelData.category, modelData.name)
                            if (eventLogRef) eventLogRef.addLog(r)
                            whData = gameCtrl.getWarehouseData()
                        }
                    }
                }
            }

            Text {
                anchors.centerIn: parent
                text: "该分类没有物品"
                font.pixelSize: 13
                color: "#a0a0a0"
                visible: !whData || !whData.categories[catIndex] || whData.categories[catIndex].items.length === 0
            }
        }

        // 底部按钮
        RowLayout {
            Layout.fillWidth: true
            spacing: 8

            Button {
                text: "💰 批量出售此分类"
                font.pixelSize: 11
                onClicked: {
                    if (!whData || !whData.categories[catIndex]) return
                    let cat = whData.categories[catIndex]
                    let r = gameCtrl.sellAllCategory(cat.name)
                    if (eventLogRef) eventLogRef.addLog(r)
                    whData = gameCtrl.getWarehouseData()
                }
            }

            Item { Layout.fillWidth: true }

            Button {
                text: "关闭"
                onClicked: root.close()
            }
        }
    }
}
