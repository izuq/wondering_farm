import QtQuick 6.0
import QtQuick.Layouts 6.0

/* 顶部玩家信息栏 */
Rectangle {
    id: root
    height: 52
    radius: 8
    color: "#ccf0e8c0"
    border { color: "#80a080"; width: 1 }

    property var pm: null  // PlayerModel, set externally

    RowLayout {
        anchors { fill: parent; margins: 6 }
        spacing: 8

        // 金币
        Rectangle {
            Layout.preferredWidth: 100
            Layout.fillHeight: true
            radius: 4
            color: "#40d4a030"
            Text {
                anchors.centerIn: parent
                text: "💰 " + (pm ? pm.gold.toLocaleString() : "0")
                font.pixelSize: 12
                color: "#4a3000"
            }
        }

        // 钻石
        Rectangle {
            Layout.preferredWidth: 70
            Layout.fillHeight: true
            radius: 4
            color: "#4080c0e0"
            Text {
                anchors.centerIn: parent
                text: "💎 " + (pm ? pm.diamond : "0")
                font.pixelSize: 12
                color: "#003060"
            }
        }

        // 等级 + 经验条
        Rectangle {
            Layout.preferredWidth: 140
            Layout.fillHeight: true
            radius: 4
            color: "#4090c090"
            ColumnLayout {
                anchors { fill: parent; margins: 3 }
                spacing: 2
                Text {
                    text: "Lv." + (pm ? pm.level : "1") +
                          "  ✨" + (pm ? pm.exp : "0") + "/" +
                          (pm ? pm.expNeed : "120")
                    font.pixelSize: 10
                    color: "#1a3a1a"
                }
                Rectangle {
                    Layout.fillWidth: true
                    height: 8
                    radius: 3
                    color: "#60ffffff"
                    Rectangle {
                        height: 8
                        radius: 3
                        color: "#60d030"
                        width: parent.width * Math.min(1, (pm ? pm.exp : 0) /
                            Math.max(1, pm ? pm.expNeed : 1))
                    }
                }
            }
        }

        // 季节
        Text {
            text: (pm ? pm.seasonEmoji + " " + pm.season : "🌸 春")
            font.pixelSize: 12
            color: "#2d4a1e"
        }

        // 天赋点
        Text {
            text: "⭐ " + (pm ? pm.talentPoints : "0")
            font.pixelSize: 12
            color: "#4a3000"
        }

        // 土地统计
        Text {
            text: "🌱 " + (pm ? pm.plantedCount : "0") + "/" +
                  (pm ? pm.maxLands : "6")
            font.pixelSize: 12
            color: "#2d4a1e"
        }

        // 养殖场统计
        Text {
            text: "🐔 " + (pm ? pm.barnCount : "0") + "/" +
                  (pm ? pm.maxBarns : "6")
            font.pixelSize: 12
            color: "#2d4a1e"
        }

        // 待收产品
        Rectangle {
            visible: pm && pm.barnPending > 0
            Layout.preferredWidth: 70
            Layout.fillHeight: true
            radius: 4
            color: "#40ffa030"
            Text {
                anchors.centerIn: parent
                text: "📦" + (pm ? pm.barnPending : "0")
                font.pixelSize: 12
                color: "#803000"
            }
        }

        // 农业建筑统计
        Text {
            text: "🏗️ " + (pm ? pm.agroCount : "0")
            font.pixelSize: 12
            color: "#2d4a1e"
        }
        Rectangle {
            visible: pm && pm.agroReadyCount > 0
            Layout.preferredWidth: 60
            Layout.fillHeight: true
            radius: 4
            color: "#4040d040"
            Text {
                anchors.centerIn: parent
                text: "✅" + (pm ? pm.agroReadyCount : "0")
                font.pixelSize: 11
                color: "#006000"
            }
        }
    }
}
