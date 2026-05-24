import QtQuick 6.0

/* 养殖场单个栏位 */
Item {
    id: root
    width: 64
    height: 70

    property int sBid: 0
    property string sAnimal: ""
    property string sAnimalType: ""
    property int sLevel: 1
    property int sPending: 0
    property string sTimeLeft: ""
    property string sStatus: "empty"
    property string sEmoji: ""
    property bool sLocked: false

    readonly property color bgEmpty: "#d4c4a8"
    readonly property color bgNotFed: "#f0e0c0"
    readonly property color bgNoFeed: "#f0d0d0"
    readonly property color bgProducing: "#fff5cc"
    readonly property color bgReady: "#c8e8c0"

    function bgColor() {
        switch (sStatus) {
            case "empty":    return bgEmpty
            case "not_fed":  return bgNotFed
            case "no_feed":  return bgNoFeed
            case "producing":return bgProducing
            case "ready":    return bgReady
            default:         return bgEmpty
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
            text: "#" + sBid
            font.pixelSize: 8
            color: "#809080"
        }

        // 等级
        Text {
            anchors { top: parent.top; right: parent.right; topMargin: 2; rightMargin: 4 }
            text: "★".repeat(Math.min(sLevel, 5))
            font.pixelSize: 7
            color: "#c0a020"
            visible: sStatus !== "empty"
        }

        // emoji 图标
        Text {
            anchors.centerIn: parent
            anchors.verticalCenterOffset: -6
            text: sStatus === "empty" ? "⬜" : sEmoji
            font.pixelSize: sStatus === "empty" ? 18 : 22
        }

        // 待收标记
        Rectangle {
            anchors { top: parent.top; topMargin: 2; right: parent.right; rightMargin: 2 }
            visible: sPending > 0
            width: 22
            height: 16
            radius: 4
            color: "#ff8830"
            Text {
                anchors.centerIn: parent
                text: "×" + sPending
                font.pixelSize: 8
                color: "white"
            }
        }

        // 剩余时间
        Text {
            anchors { bottom: parent.bottom; horizontalCenter: parent.horizontalCenter; bottomMargin: 2 }
            text: sTimeLeft
            font.pixelSize: 8
            color: "#604020"
            visible: sTimeLeft !== ""
        }

        // 状态文字
        Text {
            anchors { bottom: parent.bottom; horizontalCenter: parent.horizontalCenter; bottomMargin: 2 }
            text: {
                switch (sStatus) {
                    case "empty":    return "空闲"
                    case "not_fed":  return "未投喂"
                    case "no_feed":  return "缺料"
                    case "ready":    return "✅"
                    default:         return ""
                }
            }
            font.pixelSize: 8
            color: "#604020"
            visible: sTimeLeft === "" && sStatus !== "producing"
        }
    }
}
