import QtQuick 6.0
import QtQuick.Controls 6.0
import QtQuick.Layouts 6.0

/* 加工对话框 */
Popup {
    id: root
    width: 540
    height: 460
    anchors.centerIn: Overlay.overlay
    modal: true
    closePolicy: Popup.CloseOnEscape | Popup.CloseOnPressOutside

    property var startData: null
    property int selectedSlotIdx: -1
    property string selectedRecipe: ""
    property int batchQty: 1
    property var eventLogRef: null

    onOpened: {
        startData = gameCtrl.getAgroStartData()
        selectedSlotIdx = -1
        selectedRecipe = ""
        batchQty = 1
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
            text: "🔧 加工"
            font { pixelSize: 16; bold: true }
            color: "#2d4a1e"
        }

        Text {
            visible: startData && !startData.hasAvailable
            text: "没有空闲的建筑"
            font.pixelSize: 12
            color: "#c03030"
        }

        // 选择建筑
        Text {
            text: "1. 选择建筑："
            font.pixelSize: 12
            color: "#604020"
            visible: startData && startData.hasAvailable
        }

        ListView {
            id: slotListView
            Layout.fillWidth: true
            Layout.preferredHeight: 90
            clip: true
            visible: startData && startData.hasAvailable
            model: startData ? startData.slots : []
            spacing: 2

            delegate: Rectangle {
                width: slotListView.width
                height: 28
                radius: 3
                color: selectedSlotIdx === index ? "#c8e0c0" : "#f8f5e8"
                border { color: selectedSlotIdx === index ? "#60a060" : "#d0d0c0"; width: 1 }

                RowLayout {
                    anchors { fill: parent; margins: 4 }
                    spacing: 6
                    Text { text: modelData.emoji; font.pixelSize: 14 }
                    Text {
                        text: "#" + modelData.id + " " + modelData.buildingName + " Lv." + modelData.level + " (" + modelData.recipes.length + "配方)"
                        font.pixelSize: 11
                        color: "#2d4a1e"
                    }
                }

                MouseArea {
                    anchors.fill: parent
                    onClicked: {
                        selectedSlotIdx = index
                        selectedRecipe = ""
                        batchQty = 1
                    }
                }
            }
        }

        // 选择配方
        Text {
            text: "2. 选择配方："
            font.pixelSize: 12
            color: "#604020"
            visible: startData && startData.hasAvailable && selectedSlotIdx >= 0
        }

        ListView {
            id: recipeListView
            Layout.fillWidth: true
            Layout.fillHeight: true
            clip: true
            visible: startData && startData.hasAvailable && selectedSlotIdx >= 0
            model: {
                if (!startData || selectedSlotIdx < 0) return []
                var slot = startData.slots[selectedSlotIdx]
                return slot ? slot.recipes : []
            }
            spacing: 2

            delegate: Rectangle {
                width: recipeListView.width
                height: 36
                radius: 3
                color: selectedRecipe === modelData.name ? "#c8e0c0" : "#f8f5e8"
                border { color: selectedRecipe === modelData.name ? "#60a060" : "#d0d0c0"; width: 1 }

                RowLayout {
                    anchors { fill: parent; margins: 4 }
                    spacing: 6

                    Text {
                        text: "📦"
                        font.pixelSize: 16
                    }
                    ColumnLayout {
                        spacing: 0
                        Text {
                            text: modelData.name
                            font.pixelSize: 11
                            color: "#2d4a1e"
                        }
                        Text {
                            text: "⏱" + modelData.time + "min → ×" + modelData.yield_ + " | 材料: " + modelData.ingredients
                            font.pixelSize: 9
                            color: "#809080"
                        }
                    }
                }

                MouseArea {
                    anchors.fill: parent
                    onClicked: {
                        selectedRecipe = modelData.name
                        batchQty = 1
                    }
                }
            }
        }

        // 批次数量 + 确认
        RowLayout {
            Layout.fillWidth: true
            spacing: 8
            visible: startData && startData.hasAvailable && selectedSlotIdx >= 0 && selectedRecipe !== ""

            Text {
                text: "批次数："
                font.pixelSize: 12
                color: "#604020"
            }
            Button {
                text: "−"
                font.pixelSize: 10
                implicitWidth: 24
                implicitHeight: 24
                onClicked: { if (batchQty > 1) batchQty-- }
            }
            Text {
                text: batchQty
                font.pixelSize: 14
                color: "#2d4a1e"
                Layout.preferredWidth: 24
                horizontalAlignment: Text.AlignHCenter
            }
            Button {
                text: "+"
                font.pixelSize: 10
                implicitWidth: 24
                implicitHeight: 24
                onClicked: { if (batchQty < 20) batchQty++ }
            }

            Item { Layout.fillWidth: true }

            Button {
                text: "🔧 开始加工"
                font.pixelSize: 11
                onClicked: {
                    if (selectedSlotIdx < 0 || !startData) return
                    var slot = startData.slots[selectedSlotIdx]
                    var r = gameCtrl.startAgroProduction(slot.id, selectedRecipe, batchQty)
                    if (eventLogRef) eventLogRef.addLog(r)
                    startData = gameCtrl.getAgroStartData()
                    selectedSlotIdx = -1
                    selectedRecipe = ""
                    batchQty = 1
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
