import QtQuick 6.0
import QtQuick.Controls 6.0
import QtQuick.Layouts 6.0

/* 天赋树对话框 */
Popup {
    id: root
    width: 540
    height: 520
    anchors.centerIn: Overlay.overlay
    modal: true
    closePolicy: Popup.CloseOnEscape | Popup.CloseOnPressOutside

    property var talentData: null
    property var eventLogRef: null

    onOpened: {
        talentData = gameCtrl.getTalentData()
    }

    background: Rectangle {
        radius: 10
        color: "#f5f0e0"
        border { color: "#80a080"; width: 2 }
    }

    ColumnLayout {
        anchors { fill: parent; margins: 12 }
        spacing: 6

        Text {
            text: talentData ? "⭐ 天赋树  天赋点: " + talentData.points : "⭐ 天赋树"
            font { pixelSize: 16; bold: true }
            color: "#2d4a1e"
        }

        ScrollView {
            Layout.fillWidth: true
            Layout.fillHeight: true
            clip: true

            ColumnLayout {
                spacing: 4

                Repeater {
                    model: talentData ? talentData.groups : []

                    ColumnLayout {
                        spacing: 2

                        Text {
                            text: "── " + modelData.name + " ──"
                            font { pixelSize: 12; bold: true }
                            color: "#604020"
                            Layout.topMargin: 6
                        }

                        Repeater {
                            model: modelData.talents

                            delegate: Rectangle {
                                width: parent ? parent.width : 200
                                height: 38
                                radius: 4
                                color: modelData.isMax ? "#d4edda" : "#f8f5e8"
                                border { color: "#d0d0c0"; width: 1 }

                                RowLayout {
                                    anchors { fill: parent; margins: 4 }
                                    spacing: 6

                                    Text {
                                        text: modelData.title
                                        font.pixelSize: 12
                                        color: "#2d4a1e"
                                        Layout.preferredWidth: 100
                                    }

                                    // 进度条
                                    RowLayout {
                                        Layout.preferredWidth: 120
                                        spacing: 1

                                        Repeater {
                                            model: modelData.maxLevel
                                            Rectangle {
                                                width: Math.max(8, 110 / modelData.maxLevel - 2)
                                                height: 12
                                                radius: 2
                                                color: index < modelData.level ? "#40a040" : "#d0d0c0"
                                            }
                                        }
                                    }
                                    Text {
                                        text: modelData.level + "/" + modelData.maxLevel
                                        font.pixelSize: 10
                                        color: "#809080"
                                        Layout.preferredWidth: 30
                                    }
                                    Text {
                                        text: modelData.desc
                                        font.pixelSize: 9
                                        color: "#809080"
                                    }

                                    Item { Layout.fillWidth: true }

                                    Button {
                                        text: modelData.isMax ? "MAX" : "⬆"
                                        enabled: modelData.canUpgrade
                                        font.pixelSize: 10
                                        implicitWidth: 36
                                        implicitHeight: 24
                                        onClicked: {
                                            let r = gameCtrl.upgradeTalent(modelData.name)
                                            if (eventLogRef) eventLogRef.addLog(r)
                                            talentData = gameCtrl.getTalentData()
                                        }
                                    }
                                }
                            }
                        }
                    }
                }
            }
        }

        // 底部操作栏
        RowLayout {
            Layout.fillWidth: true
            spacing: 6

            Button {
                text: talentData ? "🍎 天赋果实 (" + talentData.fruitCount + "个)" : "🍎 天赋果实"
                enabled: talentData && talentData.canUseFruit
                font.pixelSize: 10
                onClicked: {
                    let r = gameCtrl.useTalentFruit()
                    if (eventLogRef) eventLogRef.addLog(r)
                    talentData = gameCtrl.getTalentData()
                }
            }

            Item { Layout.fillWidth: true }

            Button {
                text: "🔄 重置 (50💎)"
                enabled: talentData && talentData.canResetDiamond
                font.pixelSize: 10
                onClicked: {
                    let r = gameCtrl.resetTalents(true)
                    if (eventLogRef) eventLogRef.addLog(r)
                    talentData = gameCtrl.getTalentData()
                }
            }
            Button {
                text: "🔄 重置 (5000💰)"
                enabled: talentData && talentData.canResetGold
                font.pixelSize: 10
                onClicked: {
                    let r = gameCtrl.resetTalents(false)
                    if (eventLogRef) eventLogRef.addLog(r)
                    talentData = gameCtrl.getTalentData()
                }
            }

            Button {
                text: "关闭"
                Layout.alignment: Qt.AlignRight
                onClicked: root.close()
            }
        }
    }
}
