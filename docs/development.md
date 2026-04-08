# 开发与调试手册

## 1. 开发环境建议

当前项目主要面向 Windows 桌面环境开发，建议使用：

- Windows 10 或 Windows 11
- Node.js
- npm
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
python -m pip install -r backend/requirements.txt
```

## 3. 本地 Python 配置

开发环境通常通过 `frontend/.env.development` 指定 Python 路径：

```env
VITE_PYTHON_PATH=D:/Anaconda3/envs/exam_scheduler/python.exe
```

如果系统中已经可以直接调用 `python`，也可以写为：

```env
VITE_PYTHON_PATH=python
```

打包脚本 `package.py` 会优先按以下顺序解析 Python：

1. `EXAM_PYTHON_PATH`
2. `VITE_PYTHON_PATH`
3. `sys.executable`
4. `python` in PATH

## 4. 常用命令

### 4.1 启动前端开发环境

```powershell
Set-Location frontend
npm.cmd run dev
```

说明：

- Vite 开发服务器固定端口为 `5173`
- Electron 主进程与 preload 由 `vite-plugin-electron` 一并处理
- 开发时 Python 后端通常以 `python -m backend` 方式启动

### 4.2 前端测试与构建

```powershell
Set-Location frontend
npm.cmd run test
npm.cmd run build
```

### 4.3 后端测试

```powershell
Set-Location ..
$env:PYTHONPATH='.'
pytest
```

常用定向测试示例：

```powershell
$env:PYTHONPATH='.'
pytest backend/tests/test_subjects_service.py backend/tests/test_subjects_excel.py

$env:PYTHONPATH='.'
pytest backend/tests/test_proctoring_service.py backend/tests/test_proctoring_scheduler.py backend/tests/test_proctoring_optimizer.py

$env:PYTHONPATH='.'
pytest backend/tests/test_rooms_service.py backend/tests/test_rooms_arrange_flow.py backend/tests/test_exam_arrangement_gaokao_exports.py

$env:PYTHONPATH='.'
pytest backend/tests/test_printing_service.py backend/tests/test_printing_excel_generators.py backend/tests/test_printing_examroom_adapter.py
```

### 4.4 后端自检

```powershell
Set-Location ..
$env:PYTHONPATH='.'
python -m backend.selfcheck
```

这个自检会检查关键模块导入是否正常，并执行一次最小打印生成流程。

### 4.5 一键打包

```powershell
Set-Location ..
python package.py
```

## 5. 关键环境变量

运行和调试时常见的环境变量包括：

- `VITE_PYTHON_PATH`
  开发态指定 Python 解释器
- `EXAM_PYTHON_PATH`
  打包脚本优先使用的 Python 解释器
- `EXAMFLOW_DATA_DIR` / `EXAMDESK_DATA_DIR`
  指定状态数据落盘目录
- `EXAMFLOW_APP_DIR` / `EXAMDESK_APP_DIR`
  指定应用基础目录
- `EXAMFLOW_CERT_DIR` / `EXAMDESK_CERT_DIR`
  指定 `license.cert` 保存目录

Electron 主进程在桌面模式下会自动向后端注入应用目录和数据目录相关变量，因此大多数情况下不需要手动设置后几类变量。

## 6. 调试入口

### 6.1 前端

前端调试重点通常在以下位置：

- 浏览器 DevTools / Electron DevTools
- `frontend/src/lib/pythonBackend.ts`
- `frontend/src/lib/logger.ts`
- 页面级 composables
- 页面内部日志抽屉或状态提示

如果问题出现在页面层，优先顺着以下路径排查：

1. 页面 `.vue` 文件
2. 同名目录下的 composables
3. `pythonBackend.request(...)` 发起点
4. 对应 RPC 名称
5. 对应后端 service 和核心模块

### 6.2 Electron

Electron 相关问题优先查看：

- `frontend/electron/main.ts`
- `frontend/electron/preload.ts`

典型问题包括：

- Python 子进程没有启动
- IPC 白名单缺少频道
- 文件对话框无法返回路径
- `debug.log` 中出现主进程异常

### 6.3 后端

后端调试重点通常在以下位置：

- `backend/rpc_server.py`
- `backend/application/*_service.py`
- 具体业务模块
- `backend/repository/state_repository.py`
- `backend/licensing/cert_store.py`

## 7. 常见问题排查路径

### 7.1 科目问题

优先查看：

1. `frontend/src/views/SubjectsPage.vue`
2. `frontend/src/views/SubjectsPage/composables/`
3. `backend/application/subjects_service.py`
4. `backend/subjects/`

### 7.2 监考问题

优先查看：

1. `frontend/src/views/ProctoringPage.vue`
2. `frontend/src/views/ProctoringPage/composables/`
3. `backend/application/proctoring_service.py`
4. `backend/proctoring/core/`
5. `backend/tests/test_proctoring_*`

### 7.3 考场问题

优先查看：

1. `frontend/src/views/RoomsPage.vue`
2. `frontend/src/views/RoomsPage/composables/`
3. `backend/application/rooms_service.py`
4. `backend/examroom/core/`
5. `backend/tests/test_rooms_*`
6. `backend/tests/test_exam_arrangement*`

### 7.4 打印问题

优先查看：

1. `frontend/src/views/PrintingPage.vue`
2. `frontend/src/views/PrintingPage/composables/`
3. `frontend/src/views/PrintingPage/components/`
4. `backend/application/printing_service.py`
5. `backend/printing/`
6. `backend/tests/test_printing_*`

### 7.5 授权问题

优先查看：

1. `frontend/src/stores/license.ts`
2. `frontend/src/views/RegistrationPage.vue`
3. `backend/application/licensing_service.py`
4. `backend/licensing/`
5. [授权证书文件路径说明.md](授权证书文件路径说明.md)

## 8. 状态文件与产物管理

常见运行产物包括：

- `data/state.json`
- `data/backups/`
- `frontend/debug.log`
- `frontend/debug.log.*`
- 导出的 `xlsx/pdf`

建议：

- 调试输出尽量收敛到固定目录
- 不要把临时导出文件直接放进仓库受管目录
- 新增运行产物时同步更新 `.gitignore`

## 9. 修改文档的约定

文档应优先描述“当前实现”和“当前命令”，而不是某一轮治理计划。历史设计稿、重构方案和阶段性说明统一放入 `docs/archive/plans/`。
