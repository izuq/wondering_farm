import QtQuick 6.0

/* 单个地块组件 */
Item {
    id: root
    width: 160
    height: 200

    /* 需要从 delegate context 绑定的属性 */
    property int pLid: 0
    property string pCrop: ""
    property int pStage: 0
    property bool pReady: false
    property bool pLocked: false
    property int pLevel: 1
    property string pTimeLeft: ""
    property bool pHasImage: false
    property string pEmoji: "🌱"
    property bool pGolden: false

    readonly property var stageScales: [0.35, 0.55, 0.80, 1.0]

    /* 木制外框 */
    Rectangle {
        id: frame
        anchors.fill: parent
        anchors.margins: 4
        radius: 8
        color: "#5a3a1c"
        border { color: "#3d2510"; width: 2 }

        /* 内部泥土 */
        Rectangle {
            anchors.fill: parent
            anchors.margins: 5
            radius: 5
            color: "#6b4a2a"

            /* 作物图片（按生长阶段缩放） */
            Image {
                id: cropImage
                anchors.centerIn: parent
                source: pHasImage && pStage > 0
                    ? "file:///" + picturesDir + "/" + pCrop + ".png" : ""
                sourceSize { width: 100; height: 100 }
                fillMode: Image.PreserveAspectFit
                scale: stageScales[pStage]
                visible: status === Image.Ready && pStage > 0

                Behavior on scale {
                    NumberAnimation { duration: 400; easing.type: Easing.OutBounce }
                }
            }

            /* Emoji 后备显示 */
            Text {
                anchors.centerIn: parent
                text: pStage === 0 ? "🌱" : (pHasImage ? "" : pEmoji)
                font.pixelSize: 48
                visible: text !== ""
            }
        }

        /* 地块编号 */
        Text {
            anchors { top: parent.top; left: parent.left; margins: 5 }
            text: "#" + pLid
            color: "#c0b090"
            font.pixelSize: 10
            visible: !pLocked
        }

        /* 土地等级星星 */
        Text {
            anchors { top: parent.top; right: parent.right; margins: 4 }
            text: "★".repeat(pLevel)
            color: "#d4a030"
            font.pixelSize: 13
            visible: !pLocked
        }

        /* 剩余时间 */
        Text {
            anchors { bottom: parent.bottom; horizontalCenter: parent.horizontalCenter; bottomMargin: 3 }
            text: pTimeLeft
            color: "#e0d5c0"
            font.pixelSize: 11
            visible: pTimeLeft !== ""
        }

        /* 成熟作物名称 */
        Text {
            anchors { bottom: parent.bottom; bottomMargin: 14; horizontalCenter: parent.horizontalCenter }
            text: pGolden ? "🎃✨金色" : pCrop
            color: pGolden ? "#ffa500" : "#c0b090"
            font.pixelSize: 10
            visible: pCrop !== "" && !pLocked && pReady
        }
    }

    /* 锁定遮罩 */
    Rectangle {
        anchors.fill: parent
        anchors.margins: 4
        radius: 8
        color: "#80000000"
        visible: pLocked

        Text {
            anchors.centerIn: parent
            text: "🔒"
            font.pixelSize: 36
        }
        Text {
            anchors { bottom: parent.bottom; bottomMargin: 10; horizontalCenter: parent.horizontalCenter }
            text: "Lv." + pLevel + " 解锁"
            color: "#cccccc"
            font.pixelSize: 11
        }
    }

    /* 成熟闪烁金框 */
    Rectangle {
        anchors.fill: parent
        anchors.margins: 4
        radius: 8
        color: "transparent"
        border { width: pReady ? 3 : 0 }
        visible: pReady

        SequentialAnimation on border.color {
            loops: Animation.Infinite
            running: pReady
            ColorAnimation { from: pGolden ? "#ffaa00" : "#ffd700"
                             to: pGolden ? "#ff6600" : "#ff8c00"; duration: 800 }
            ColorAnimation { from: pGolden ? "#ff6600" : "#ff8c00"
                             to: pGolden ? "#ffaa00" : "#ffd700"; duration: 800 }
        }
    }
}
