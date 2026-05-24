import QtQuick 6.0
import QtQuick.Controls 6.0
import QtQuick.Layouts 6.0

/* 种植对话框 */
Popup {
    id: root
    width: 520
    height: 440
    anchors.centerIn: Overlay.overlay
    modal: true
    closePolicy: Popup.CloseOnEscape | Popup.CloseOnPressOutside

    property var emptyLands: []
    property var availableCrops: []
    property int selectedLandId: -1
    property string selectedCropName: ""
    property var eventLogRef: null

    onOpened: {
        emptyLands = gameCtrl.getEmptyLands()
        availableCrops = gameCtrl.getAvailableCrops()
        selectedLandId = -1
        selectedCropName = ""
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
            text: "🌱 种植作物"
            font { pixelSize: 16; bold: true }
            color: "#2d4a1e"
        }

        RowLayout {
            Layout.fillWidth: true
            Layout.fillHeight: true
            spacing: 8

            // 左侧：空地列表
            Rectangle {
                Layout.preferredWidth: 200
                Layout.fillHeight: true
                radius: 6
                color: "#f0ede0"
                border { color: "#c0c0a0"; width: 1 }

                ColumnLayout {
                    anchors { fill: parent; margins: 6 }
                    spacing: 4

                    Text {
                        text: "选择土地："
                        font.pixelSize: 12
                        color: "#604020"
                    }

                    ListView {
                        id: landList
                        Layout.fillWidth: true
                        Layout.fillHeight: true
                        clip: true
                        model: emptyLands
                        spacing: 3

                        delegate: Rectangle {
                            width: landList.width
                            height: 36
                            radius: 4
                            color: selectedLandId === modelData.id ? "#c8e0c0" : "#f8f5e8"
                            border { color: selectedLandId === modelData.id ? "#60a060" : "#d0d0c0"; width: 1 }

                            RowLayout {
                                anchors { fill: parent; margins: 6 }
                                Text {
                                    text: "#" + modelData.id
                                    font.pixelSize: 13
                                    color: "#2d4a1e"
                                }
                                Text {
                                    text: "★".repeat(modelData.level)
                                    font.pixelSize: 11
                                    color: "#d4a030"
                                }
                                Text {
                                    text: "Lv." + modelData.level
                                    font.pixelSize: 11
                                    color: "#604020"
                                }
                            }

                            MouseArea {
                                anchors.fill: parent
                                onClicked: {
                                    selectedLandId = modelData.id
                                }
                            }
                        }

                        Text {
                            anchors.centerIn: parent
                            text: emptyLands.length === 0 ? "没有空闲土地" : ""
                            color: "#a0a0a0"
                            font.pixelSize: 13
                        }
                    }
                }
            }

            // 右侧：作物列表
            Rectangle {
                Layout.fillWidth: true
                Layout.fillHeight: true
                radius: 6
                color: "#f0ede0"
                border { color: "#c0c0a0"; width: 1 }

                ColumnLayout {
                    anchors { fill: parent; margins: 6 }
                    spacing: 4

                    Text {
                        text: "选择作物："
                        font.pixelSize: 12
                        color: "#604020"
                    }

                    ListView {
                        id: cropList
                        Layout.fillWidth: true
                        Layout.fillHeight: true
                        clip: true
                        model: availableCrops
                        spacing: 3

                        delegate: Rectangle {
                            width: cropList.width
                            height: 44
                            radius: 4
                            color: selectedCropName === modelData.name ? "#c8e0c0" : "#f8f5e8"
                            border { color: selectedCropName === modelData.name ? "#60a060" : "#d0d0c0"; width: 1 }

                            RowLayout {
                                anchors { fill: parent; margins: 4 }
                                spacing: 6

                                Text {
                                    text: modelData.emoji
                                    font.pixelSize: 20
                                }

                                ColumnLayout {
                                    spacing: 1
                                    Text {
                                        text: modelData.name
                                        font.pixelSize: 12
                                        color: "#2d4a1e"
                                    }
                                    Text {
                                        text: "Lv." + modelData.level + " | " + modelData.growthMin + "min | " + modelData.sellPrice + "💰"
                                        font.pixelSize: 9
                                        color: "#809080"
                                    }
                                }

                                Item { Layout.fillWidth: true }

                                Rectangle {
                                    radius: 3
                                    color: modelData.seedCount > 0 ? "#c0e8c0" : "#e8d8c0"
                                    width: 50
                                    height: 20
                                    Text {
                                        anchors.centerIn: parent
                                        text: modelData.seedCount > 0 ? "种子×" + modelData.seedCount : modelData.seedPrice + "💰"
                                        font.pixelSize: 9
                                        color: "#604020"
                                    }
                                }
                            }

                            MouseArea {
                                anchors.fill: parent
                                onClicked: {
                                    selectedCropName = modelData.name
                                }
                            }
                        }
                    }
                }
            }
        }

        // 底部按钮
        RowLayout {
            Layout.fillWidth: true
            spacing: 8

            Item { Layout.fillWidth: true }

            Button {
                text: "❌ 取消"
                onClicked: root.close()
            }

            Button {
                text: "🌱 种植"
                enabled: selectedLandId > 0 && selectedCropName !== ""
                onClicked: {
                    let result = gameCtrl.plantCrop(selectedLandId, selectedCropName)
                    if (eventLogRef) eventLogRef.addLog(result)
                    root.close()
                }
            }
        }
    }
}
