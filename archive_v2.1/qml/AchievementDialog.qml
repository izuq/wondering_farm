import QtQuick 6.0
import QtQuick.Controls 6.0
import QtQuick.Layouts 6.0

/* 成就对话框 */
Popup {
    id: root
    width: 500
    height: 450
    anchors.centerIn: Overlay.overlay
    modal: true
    closePolicy: Popup.CloseOnEscape | Popup.CloseOnPressOutside

    property var achData: null

    onOpened: {
        achData = gameCtrl.getAchievementData()
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
            text: achData ? "🏆 成就 (" + achData.doneCount + "/" + achData.total + ")" : "🏆 成就"
            font { pixelSize: 16; bold: true }
            color: "#2d4a1e"
        }

        ListView {
            id: achListView
            Layout.fillWidth: true
            Layout.fillHeight: true
            clip: true
            model: achData ? achData.items : []
            spacing: 3

            delegate: Rectangle {
                width: achListView.width
                height: 36
                radius: 4
                color: modelData.done ? "#d4edda" : "#f8f5e8"
                border { color: modelData.done ? "#80c080" : "#d0d0c0"; width: 1 }

                RowLayout {
                    anchors { fill: parent; margins: 4 }
                    spacing: 6

                    Text {
                        text: modelData.icon
                        font.pixelSize: 16
                    }
                    Text {
                        text: modelData.name
                        font.pixelSize: 12
                        color: "#2d4a1e"
                        Layout.preferredWidth: 110
                    }
                    Text {
                        text: modelData.condition
                        font.pixelSize: 10
                        color: "#809080"
                        Layout.fillWidth: true
                    }
                    Text {
                        text: "奖励: " + modelData.reward
                        font.pixelSize: 10
                        color: "#d4a030"
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
