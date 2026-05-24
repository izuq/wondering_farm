import QtQuick 6.0

/* 农业建筑位 */
Item {
    id: root
    width: 64
    height: 70

    property int aSid: 0
    property string aBuilding: ""
    property int aLevel: 1
    property string aStatus: "empty"
    property string aTimeLeft: ""
    property bool aReady: false
    property string aBatches: ""
    property string aBuildingName: ""
    property bool aLocked: false
    property string aBuildingEmoji: ""

    readonly property color bgEmpty: "#d4c4a8"
    readonly property color bgIdle: "#e0dcc8"
    readonly property color bgProcessing: "#fff5cc"
    readonly property color bgReady: "#c8e8c0"

    function bgColor() {
        switch (aStatus) {
            case "empty":      return bgEmpty
            case "idle":       return bgIdle
            case "processing": return bgProcessing
            case "ready":      return bgReady
            default:           return bgEmpty
        }
    }

    Rectangle {
        anchors.fill: parent
        anchors.margins: 2
        radius: 5
        color: bgColor()
        border { color: Qt.darker(bgColor(), 1.3); width: 1 }

        // 编号
        Text {
            anchors { top: parent.top; left: parent.left; topMargin: 2; leftMargin: 4 }
            text: "#" + aSid
            font.pixelSize: 8
            color: "#809080"
        }

        // 等级
        Text {
            anchors { top: parent.top; right: parent.right; topMargin: 2; rightMargin: 4 }
            text: "Lv." + aLevel
            font.pixelSize: 7
            color: "#604020"
            visible: aStatus !== "empty"
        }

        // emoji 图标
        Text {
            anchors.centerIn: parent
            anchors.verticalCenterOffset: -6
            text: aStatus === "empty" ? "⬜" : aBuildingEmoji
            font.pixelSize: 22
        }

        // 建筑名
        Text {
            anchors { top: parent.top; horizontalCenter: parent.horizontalCenter; topMargin: 14 }
            text: aStatus === "empty" ? "空地" : aBuildingName
            font.pixelSize: 7
            color: "#604020"
        }

        // 批量进度
        Text {
            anchors { bottom: parent.bottom; horizontalCenter: parent.horizontalCenter; bottomMargin: 2 }
            text: {
                if (aStatus === "ready") return "✅" + aBatches
                if (aStatus === "processing") return aBatches
                if (aStatus === "idle") return "⬜"
                return ""
            }
            font.pixelSize: 7
            color: "#604020"
        }

        // 剩余时间
        Text {
            anchors { bottom: parent.bottom; horizontalCenter: parent.horizontalCenter; bottomMargin: 2 }
            text: aTimeLeft
            font.pixelSize: 7
            color: "#604020"
            visible: aTimeLeft !== "" && aStatus === "processing"
        }
    }
}
