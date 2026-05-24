import QtQuick 6.0
import QtQuick.Controls 6.0

/* 底部事件日志 */
Rectangle {
    id: root
    height: 72
    radius: 6
    color: "#ddf0e8c0"
    border { color: "#80a080"; width: 1 }

    property var log: null

    ScrollView {
        anchors {
            fill: parent
            margins: 4
            rightMargin: 28
        }
        clip: true

        TextArea {
            id: logArea
            readOnly: true
            text: log ? log.logText : ""
            font.pixelSize: 11
            color: "#2d4a1e"
            background: Rectangle { color: "transparent" }
            wrapMode: Text.Wrap
            onTextChanged: {
                logArea.cursorPosition = logArea.length
            }
        }
    }

    // 清空按钮
    Rectangle {
        anchors { top: parent.top; right: parent.right; margins: 2 }
        width: 20
        height: 20
        radius: 10
        color: mouseArea.containsMouse ? "#e0d0c0" : "#d0c8b0"
        border { color: "#a0a0a0"; width: 1 }

        Text {
            anchors.centerIn: parent
            text: "✕"
            font.pixelSize: 10
            color: "#604020"
        }

        MouseArea {
            id: mouseArea
            anchors.fill: parent
            hoverEnabled: true
            onClicked: {
                if (log) log.clearLogs()
            }
        }
    }
}
