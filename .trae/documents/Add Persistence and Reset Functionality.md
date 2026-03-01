
# 增加本地数据持久化与系统初始化功能

我将实现自动数据保存功能，确保软件关闭后再次打开时能自动恢复之前的数据（包括已导入的数据、监考编排结果、考场编排结果等）。同时，在工作台增加“初始化系统”按钮，用于一键清空所有数据。

## 后端实现 (`backend/rpc_server.py`)

1.  **状态管理**:
    *   定义 `STATE_FILE` 路径（保存到应用数据目录 `data/state.json`）。
    *   实现 `_save_state()` 函数：将以下全局变量序列化为 JSON 并保存：
        *   `current_subjects` (科目信息)
        *   `current_proctoring_teachers`, `current_proctoring_schedule`, `current_proctoring_config` (监考相关)
        *   `current_rooms_settings_data`, `current_rooms_config`, `current_rooms_student_path` (考场设置)
        *   `current_rooms_results` (新增：用于存储考场编排结果)
    *   实现 `_load_state()` 函数：在启动时读取 JSON 文件并恢复这些变量。

2.  **集成**:
    *   在所有数据变更操作（如导入教师、生成课表、考场编排）后自动调用 `_save_state()`。
    *   在 Python 后端启动时自动调用 `_load_state()`。
    *   更新 `rooms_export` 和打印相关函数，使其支持从恢复的数据中重建 `ExamArrangement` 对象。

3.  **重置功能**:
    *   添加 `system.resetData` RPC 接口。
    *   该接口将清空所有内存中的变量并删除 `state.json` 文件。

## 前端实现 (`DashboardPage.vue`)

1.  **界面更新**:
    *   在工作台头部增加“初始化系统”按钮。
    *   添加确认对话框，防止误操作。

2.  **逻辑处理**:
    *   用户确认后调用 `pythonBackend.request('system.resetData')`。
    *   重置成功后刷新页面统计数据。
