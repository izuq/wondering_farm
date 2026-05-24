import QtQuick 6.0
import QtQuick.Controls 6.0
import QtQuick.Layouts 6.0

/* 繁殖对话框 */
Popup {
    id: root
    width: 480
    height: 400
    anchors.centerIn: Overlay.overlay
    modal: true
    closePolicy: Popup.CloseOnEscape | Popup.CloseOnPressOutside

    property var breedData: null
    property int parent1Idx: -1
    property int parent2Idx: -1
    property var eventLogRef: null

    onOpened: {
        breedData = gameCtrl.getBreedData()
        parent1Idx = -1
        parent2Idx = -1
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
            text: "🧬 繁殖"
            font { pixelSize: 16; bold: true }
            color: "#2d4a1e"
        }

        Text {
            text: "选择两只同种成年动物作为亲本 | 花费1000💰 | 成功率70%"
            font.pixelSize: 11
            color: "#809080"
        }

        Text {
            visible: breedData && !breedData.canBreed
            text: "需要至少2只不在冷却中的成年动物"
            font.pixelSize: 12
            color: "#c03030"
        }

        // 亲本 1
        Text {
            text: "亲本 1："
            font.pixelSize: 12
            color: "#604020"
            visible: breedData && breedData.canBreed
        }

        ListView {
            id: parent1List
            Layout.fillWidth: true
            Layout.preferredHeight: 100
            clip: true
            visible: breedData && breedData.canBreed
            model: breedData ? breedData.adults : []
            spacing: 2

            delegate: Rectangle {
                width: parent1List.width
                height: 30
                radius: 3
                color: parent1Idx === index ? "#c8e0c0" : "#f8f5e8"
                border { color: parent1Idx === index ? "#60a060" : "#d0d0c0"; width: 1 }

                RowLayout {
                    anchors { fill: parent; margins: 4 }
                    spacing: 6
                    Text { text: modelData.emoji; font.pixelSize: 16 }
                    Text {
                        text: "栏位#" + modelData.id + " " + modelData.animalType + " Lv." + modelData.level
                        font.pixelSize: 11
                        color: "#2d4a1e"
                    }
                }

                MouseArea {
                    anchors.fill: parent
                    onClicked: { parent1Idx = index }
                }
            }
        }

        // 亲本 2
        Text {
            text: "亲本 2："
            font.pixelSize: 12
            color: "#604020"
            visible: breedData && breedData.canBreed
        }

        ListView {
            id: parent2List
            Layout.fillWidth: true
            Layout.preferredHeight: 100
            clip: true
            visible: breedData && breedData.canBreed
            model: breedData ? breedData.adults : []
            spacing: 2

            delegate: Rectangle {
                width: parent2List.width
                height: 30
                radius: 3
                color: parent2Idx === index ? "#c8e0c0" : "#f8f5e8"
                border { color: parent2Idx === index ? "#60a060" : "#d0d0c0"; width: 1 }

                RowLayout {
                    anchors { fill: parent; margins: 4 }
                    spacing: 6
                    Text { text: modelData.emoji; font.pixelSize: 16 }
                    Text {
                        text: "栏位#" + modelData.id + " " + modelData.animalType + " Lv." + modelData.level
                        font.pixelSize: 11
                        color: "#2d4a1e"
                    }
                }

                MouseArea {
                    anchors.fill: parent
                    onClicked: { parent2Idx = index }
                }
            }
        }

        // 底部按钮
        RowLayout {
            Layout.fillWidth: true
            spacing: 8

            Item { Layout.fillWidth: true }

            Button {
                text: "取消"
                onClicked: root.close()
            }

            Button {
                text: "🧬 开始繁殖"
                enabled: breedData && breedData.canBreed && parent1Idx >= 0 && parent2Idx >= 0 && parent1Idx !== parent2Idx
                onClicked: {
                    let a1 = breedData.adults[parent1Idx]
                    let a2 = breedData.adults[parent2Idx]
                    let r = gameCtrl.breed(a1.id, a2.id)
                    if (eventLogRef) eventLogRef.addLog(r)
                    root.close()
                }
            }
        }
    }
}
