import QtQuick 6.0
import QtQuick.Controls 6.0
import QtQuick.Layouts 6.0

/* 工厂加工对话框 */
Popup {
    id: root
    width: 520
    height: 460
    anchors.centerIn: Overlay.overlay
    modal: true
    closePolicy: Popup.CloseOnEscape | Popup.CloseOnPressOutside

    property var factoryData: null
    property var eventLogRef: null

    onOpened: {
        factoryData = gameCtrl.getFactoryData()
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
            text: "🏭 工厂加工"
            font { pixelSize: 16; bold: true }
            color: "#2d4a1e"
        }

        ListView {
            id: factoryListView
            Layout.fillWidth: true
            Layout.fillHeight: true
            clip: true
            model: factoryData ? factoryData.factories : []
            spacing: 4

            delegate: Rectangle {
                width: factoryListView.width
                height: modelData.unlocked ? 80 : 36
                radius: 5
                color: {
                    if (!modelData.unlocked) return "#e8e8e8"
                    if (modelData.isReady) return "#d4edda"
                    if (modelData.isProcessing) return "#fff3cd"
                    return "#f8f5e8"
                }
                border {
                    color: {
                        if (modelData.isReady) return "#80c080"
                        if (modelData.isProcessing) return "#d4a030"
                        return "#d0d0c0"
                    }
                    width: 1
                }

                ColumnLayout {
                    anchors { fill: parent; margins: 6 }
                    spacing: 3

                    // 标题行
                    RowLayout {
                        Layout.fillWidth: true
                        spacing: 6

                        Text {
                            text: modelData.unlocked ? "🏭" : "🔒"
                            font.pixelSize: 18
                        }
                        Text {
                            text: modelData.factory + " → " + modelData.product
                            font.pixelSize: 12
                            color: "#2d4a1e"
                            Layout.fillWidth: true
                        }
                        Text {
                            visible: !modelData.unlocked
                            text: "需Lv." + modelData.level
                            font.pixelSize: 10
                            color: "#c03030"
                        }
                    }

                    // 状态/原料行（已解锁）
                    RowLayout {
                        Layout.fillWidth: true
                        spacing: 6
                        visible: modelData.unlocked

                        // 原料列表
                        ColumnLayout {
                            Layout.fillWidth: true
                            spacing: 1

                            Text {
                                text: "原料: " + modelData.ingredients.map(function(ing) {
                                    return ing.name + "×" + ing.need + "(" + ing.have + ")"
                                }).join(", ")
                                font.pixelSize: 10
                                color: modelData.canMake ? "#40a040" : "#c03030"
                            }
                            Text {
                                visible: modelData.isProcessing
                                text: "⏳ 剩余 " + modelData.remainText
                                font.pixelSize: 10
                                color: "#604020"
                            }
                            Text {
                                visible: modelData.isReady
                                text: "✅ 已完成，可收取！"
                                font.pixelSize: 10
                                color: "#40a040"
                            }
                        }

                        Button {
                            visible: modelData.isReady
                            text: "收取"
                            font.pixelSize: 10
                            implicitWidth: 44
                            implicitHeight: 26
                            onClicked: {
                                let r = gameCtrl.collectFactory(modelData.factory)
                                if (eventLogRef) eventLogRef.addLog(r)
                                factoryData = gameCtrl.getFactoryData()
                            }
                        }
                        Button {
                            visible: modelData.canStart
                            text: "加工"
                            font.pixelSize: 10
                            implicitWidth: 44
                            implicitHeight: 26
                            onClicked: {
                                let r = gameCtrl.startFactory(modelData.factory)
                                if (eventLogRef) eventLogRef.addLog(r)
                                factoryData = gameCtrl.getFactoryData()
                            }
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
