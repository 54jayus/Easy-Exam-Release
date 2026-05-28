# 开发与调试手册

## 1. 开发环境

当前项目主要面向 Windows 桌面环境开发，建议准备：

- Windows 10 / Windows 11
- Node.js 与 npm
- Python 3
- 可选：Conda

## 2. 安装依赖

### 2.1 前端依赖

```powershell
Set-Location frontend
npm.cmd install
```

### 2.2 后端依赖

```powershell
Set-Location ..
conda run --no-capture-output -n exam_scheduler python -m pip install -r backend/requirements.txt
```

`backend/requirements.txt` 当前包含：

- `pandas`
- `openpyxl`
- `xlsxwriter`
- `reportlab`
- `ortools`
- `pyinstaller`
- `xlrd`
- `pytest`

## 3. 本地 Python 配置

本地运行环境统一读取仓库根目录的配置文件：

- 模板文件：`.env.runtime.example`
- 本机文件：`.env.runtime.local`

推荐优先使用 Conda 环境名，而不是写死 Python 绝对路径。Electron 开发态、PowerShell 辅助脚本与打包脚本 `package.py` 都读取同一份本机配置。

## 4. 常用命令

### 4.1 启动开发环境

```powershell
Set-Location frontend
npm.cmd run dev
```

当前行为：

- Vite 开发服务固定跑在 `5173`
- Electron 主进程通过 `vite-plugin-electron` 一并启动
- 开发态 Python 后端以 `python -m backend` 方式运行

### 4.2 前端测试与构建

```powershell
Set-Location frontend
npm.cmd run test
npm.cmd run build
```

### 4.3 后端测试

```powershell
powershell -ExecutionPolicy Bypass -File .\tools\test-backend.ps1
```

定向执行示例：

```powershell
powershell -ExecutionPolicy Bypass -File .\tools\test-backend.ps1 backend/tests/test_subjects_service.py backend/tests/test_subjects_excel.py

powershell -ExecutionPolicy Bypass -File .\tools\test-backend.ps1 backend/tests/test_proctoring_service.py backend/tests/test_proctoring_jobs.py backend/tests/test_proctoring_validators.py backend/tests/test_cp_sat_solver.py

powershell -ExecutionPolicy Bypass -File .\tools\test-backend.ps1 backend/tests/test_rooms_service.py backend/tests/test_rooms_arrange_flow.py backend/tests/test_rooms_export_flow.py backend/tests/test_exam_arrangement.py backend/tests/test_exam_arrangement_gaokao_exports.py

powershell -ExecutionPolicy Bypass -File .\tools\test-backend.ps1 backend/tests/test_printing_service.py backend/tests/test_printing_excel_generators.py backend/tests/test_printing_examroom_adapter.py backend/tests/test_data_loader_and_desk_validator.py
```

### 4.4 后端自检

```powershell
powershell -ExecutionPolicy Bypass -File .\tools\selfcheck-backend.ps1
```

该脚本会检查关键模块导入，并执行一次最小打印生成流程。

### 4.5 一键打包

```powershell
Set-Location ..
python package.py
```

## 5. 关键环境变量

- `EXAM_PYTHON_MODE`
  运行环境模式，支持 `conda` 与 `system`
- `EXAM_CONDA_ENV`
  当使用 Conda 模式时要启动的环境名
- `EXAM_CONDA_EXE`
  可选，指定 `conda` 命令或绝对路径
- `EXAM_PYTHON_EXE`
  可选，直接指定 Python 可执行文件或命令名
- `EXAMFLOW_DATA_DIR` / `EXAMDESK_DATA_DIR`
  指定状态数据根目录，最终写入 `<dir>/data/state.json`
- `EXAMFLOW_APP_DIR` / `EXAMDESK_APP_DIR`
  指定应用基础目录
- `EXAMFLOW_CERT_DIR` / `EXAMDESK_CERT_DIR`
  指定 `license.cert` 保存目录

多数桌面运行场景下，这些后几类变量由 Electron 主进程自动注入，不需要手动设置。

## 6. 运行产物与日志

开发态常见产物：

- `data/state.json`
- `data/backups/`
- `debug.log`
- `debug.log.1` ~ `debug.log.3`
- 临时导出的 `xlsx` / `pdf`

当前日志路径规则：

- 开发态：仓库根目录 `debug.log`
- 打包态：应用 exe 同目录 `debug.log`

## 7. 调试入口

### 7.1 前端

优先从这些位置排查：

1. 页面 `.vue` 入口
2. 同名目录下的 composables
3. [frontend/src/lib/pythonBackend.ts](/d:/coding%20make%20work%20easy/Easy-Exam/frontend/src/lib/pythonBackend.ts)
4. `frontend/src/lib/logger.ts`
5. `OperationLogsDrawer` 与页面日志

### 7.2 Electron

Electron 相关问题优先查看：

- [frontend/electron/main.ts](/d:/coding%20make%20work%20easy/Easy-Exam/frontend/electron/main.ts)
- [frontend/electron/preload.ts](/d:/coding%20make%20work%20easy/Easy-Exam/frontend/electron/preload.ts)

典型问题包括：

- Python 子进程未启动
- IPC 白名单缺失
- 文件对话框返回异常
- `debug.log` 中主进程报错

### 7.3 后端

后端调试优先查看：

- [backend/rpc_server.py](/d:/coding%20make%20work%20easy/Easy-Exam/backend/rpc_server.py)
- `backend/application/*_service.py`
- 具体业务模块
- [backend/repository/state_repository.py](/d:/coding%20make%20work%20easy/Easy-Exam/backend/repository/state_repository.py)
- [backend/licensing/cert_store.py](/d:/coding%20make%20work%20easy/Easy-Exam/backend/licensing/cert_store.py)

## 8. 常见排查路径

### 8.1 科目问题

1. [frontend/src/views/SubjectsPage.vue](/d:/coding%20make%20work%20easy/Easy-Exam/frontend/src/views/SubjectsPage.vue)
2. `frontend/src/views/SubjectsPage/composables/`
3. [backend/application/subjects_service.py](/d:/coding%20make%20work%20easy/Easy-Exam/backend/application/subjects_service.py)
4. `backend/subjects/`

### 8.2 监考问题

1. [frontend/src/views/ProctoringPage.vue](/d:/coding%20make%20work%20easy/Easy-Exam/frontend/src/views/ProctoringPage.vue)
2. `frontend/src/views/ProctoringPage/composables/`
3. [backend/application/proctoring_service.py](/d:/coding%20make%20work%20easy/Easy-Exam/backend/application/proctoring_service.py)
4. [backend/application/proctoring_jobs.py](/d:/coding%20make%20work%20easy/Easy-Exam/backend/application/proctoring_jobs.py)
5. `backend/proctoring/core/`
6. `backend/tests/test_proctoring_*`
7. `backend/tests/test_cp_sat_solver.py`

### 8.3 考场问题

1. [frontend/src/views/RoomsPage.vue](/d:/coding%20make%20work%20easy/Easy-Exam/frontend/src/views/RoomsPage.vue)
2. `frontend/src/views/RoomsPage/`
3. [backend/application/rooms_service.py](/d:/coding%20make%20work%20easy/Easy-Exam/backend/application/rooms_service.py)
4. `backend/examroom/core/`
5. `backend/tests/test_rooms_*`
6. `backend/tests/test_exam_arrangement*`

### 8.4 打印问题

1. [frontend/src/views/PrintingPage.vue](/d:/coding%20make%20work%20easy/Easy-Exam/frontend/src/views/PrintingPage.vue)
2. `frontend/src/views/PrintingPage/composables/`
3. `frontend/src/views/PrintingPage/components/`
4. [backend/application/printing_service.py](/d:/coding%20make%20work%20easy/Easy-Exam/backend/application/printing_service.py)
5. `backend/printing/`
6. `backend/tests/test_printing_*`

### 8.5 授权问题

1. [frontend/src/stores/license.ts](/d:/coding%20make%20work%20easy/Easy-Exam/frontend/src/stores/license.ts)
2. [frontend/src/views/RegistrationPage.vue](/d:/coding%20make%20work%20easy/Easy-Exam/frontend/src/views/RegistrationPage.vue)
3. [backend/application/licensing_service.py](/d:/coding%20make%20work%20easy/Easy-Exam/backend/application/licensing_service.py)
4. `backend/licensing/`
5. [docs/授权证书文件路径说明.md](授权证书文件路径说明.md)

### 8.6 帮助中心问题

1. [frontend/src/views/HelpPage.vue](/d:/coding%20make%20work%20easy/Easy-Exam/frontend/src/views/HelpPage.vue)
2. `frontend/src/views/HelpPage/composables/`
3. [backend/application/system_service.py](/d:/coding%20make%20work%20easy/Easy-Exam/backend/application/system_service.py)
4. `backend/manual/`
5. `backend/resources/使用说明书.md`

## 9. 打包链路的当前注意事项

当前打包链路是真实可运行的，但仍有一个显式约束：

1. `package.py` 会清理 `frontend/python-dist/`、`frontend/build-python/` 和 `frontend/release_v6/`，打包前要关闭正在运行的旧程序

## 10. 文档维护约定

开发文档应始终描述当前仓库真实存在的目录、测试、命令和接口。历史拆分方案、重构草案和阶段性治理计划，统一保留在 `docs/archive/plans/`。
