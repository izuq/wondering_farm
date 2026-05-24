import QtQuick 6.0
import QtQuick.Controls 6.0
import QtQuick.Layouts 6.0

/* 建造农业建筑对话框 */
Popup {
    id: root
    width: 480
    height: 360
    anchors.centerIn: Overlay.overlay
    modal: true
    closePolicy: Popup.CloseOnEscape | Popup.CloseOnPressOutside

    property var buildData: null
    property int selectedSlotId: -1
    property var eventLogRef: null

    onOpened: {
        buildData = gameCtrl.getAgroBuildData()
        selectedSlotId = -1
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
            text: "🏗️ 建造农业建筑"
            font { pixelSize: 16; bold: true }
            color: "#2d4a1e"
        }

        Text {
            visible: buildData && !buildData.hasFreeSlot
            text: "⚠️ 没有空闲建筑位，请先解锁"
            font.pixelSize: 12
            color: "#c03030"
        }

        // 选择空地
        Text {
            text: "选择空地："
            font.pixelSize: 12
            color: "#604020"
            visible: buildData && buildData.hasFreeSlot
        }

        RowLayout {
            Layout.fillWidth: true
            spacing: 4
            visible: buildData && buildData.hasFreeSlot

            Repeater {
                model: buildData ? buildData.slots : []
                Button {
                    text: modelData.status === "empty" ? "#" + modelData.id + " 空地" : modelData.buildingName + " Lv." + modelData.level
                    enabled: modelData.status === "empty"
                    checkable: true
                    checked: selectedSlotId === modelData.id && modelData.status === "empty"
                    font.pixelSize: 10
                    background: Rectangle {
                        radius: 4
                        color: parent.checked ? "#c8e0c0" : (modelData.status === "empty" ? "#e8e0d0" : "#d8d8d0")
                        border { color: parent.checked ? "#60a060" : "#c0c0a0"; width: 1 }
                    }
                    onClicked: {
                        if (modelData.status === "empty") selectedSlotId = modelData.id
                    }
                }
            }
        }

        // 选择建筑类型
        Text {
            text: "选择建筑类型："
            font.pixelSize: 12
            color: "#604020"
            visible: buildData && buildData.hasFreeSlot && selectedSlotId > 0
        }

        ListView {
            id: buildList
            Layout.fillWidth: true
            Layout.fillHeight: true
            clip: true
            visible: buildData && buildData.hasFreeSlot && selectedSlotId > 0
            model: buildData ? buildData.buildOptions : []
            spacing: 4

            delegate: Rectangle {
                width: buildList.width
                height: 48
                radius: 4
                color: "#f8f5e8"
                border { color: "#d0d0c0"; width: 1 }

                RowLayout {
                    anchors { fill: parent; margins: 6 }
                    spacing: 8

                    Text {
                        text: modelData.emoji
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
                            text: "建造费用: " + modelData.cost + "💰"
                            font.pixelSize: 11
                            color: modelData.canAfford ? "#40a040" : "#c03030"
                        }
                    }

                    Item { Layout.fillWidth: true }

                    Button {
                        text: "🏗 建造"
                        enabled: modelData.canAfford
                        font.pixelSize: 11
                        onClicked: {
                            let r = gameCtrl.buildAgroBuilding(selectedSlotId, modelData.typeKey)
                            if (eventLogRef) eventLogRef.addLog(r)
                            buildData = gameCtrl.getAgroBuildData()
                            selectedSlotId = -1
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
