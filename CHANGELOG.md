# 更新日志

## 2026-05-21

### 修复
- **修复神秘商人折扣函数缺失**：`farm_tkinter_v2.py` 导入 `get_merchant_discount` 报错，在 `farm_game_v2.py` 中新增该函数及对应的 `merchant_visit` 随机事件
- **修复天赋树界面空白**：`farm_tkinter_v2.py` 中天赋元组解包索引错位，导致 `name` 拿到分组名而非天赋 ID，渲染异常
