# 开发与调试手册

## 1. 环境建议

当前项目主要面向 Windows 桌面环境开发，建议使用：

- Windows 10 或 Windows 11
- Node.js
- npm
- Python 3
- 可选：Conda

## 2. 安装依赖

### 2.1 前端依赖

```bash
cd frontend
npm install
```

### 2.2 后端依赖

```bash
pip install -r backend/requirements.txt
```

## 3. 本地 Python 配置

开发时通常通过 `frontend/.env.development` 指定 Python 路径。

```bash
cd frontend
copy .env.development.example .env.development
```

示例：

```env
VITE_PYTHON_PATH=D:/Anaconda3/envs/exam_scheduler/python.exe
```

根目录 `package.py` 也会优先读取：

```env
EXAM_PYTHON_PATH=D:/Anaconda3/envs/exam_scheduler/python.exe
```

## 4. 常用命令

### 4.1 前端开发与构建

PowerShell 下建议统一使用 `npm.cmd`：

```bash
cd frontend
npm.cmd run dev
npm.cmd run test
npm.cmd run build
```

### 4.2 后端测试

在仓库根目录下执行：

```bash
$env:PYTHONPATH='.'
pytest
```

按模块跑测试时常用命令：

```bash
$env:PYTHONPATH='.'
pytest backend/tests/test_proctoring_service.py backend/tests/test_rpc_dispatcher.py

$env:PYTHONPATH='.'
pytest backend/tests/test_rooms_service.py backend/tests/test_rooms_arrange_flow.py backend/tests/test_rooms_export_flow.py

$env:PYTHONPATH='.'
pytest backend/tests/test_exam_arrangement.py backend/tests/test_exam_arrangement_gaokao_exports.py
```

## 5. 调试入口

### 5.1 前端日志

前端页面日志主要来自：

- 浏览器控制台 / Electron 控制台
- `createLogger(...)`
- 页面内日志抽屉，例如 `SubjectsPage`、`PrintingPage`

### 5.2 后端日志

前端通过 `pythonBackend.onLog(...)` 监听后端 stdout/stderr。

如果页面出现：

- 导入失败
- 导出失败
- RPC 超时
- 打印预览为空
- 监考生成异常

优先检查：

1. 页面对应 composable 的日志入口
2. `frontend/src/lib/pythonBackend.ts`
3. 对应的 `backend/application/*_service.py`
4. 具体领域模块

## 6. 当前推荐的排查路径

### 6.1 打印相关问题

优先查看：

1. `frontend/src/views/PrintingPage.vue`
2. `frontend/src/views/PrintingPage/composables/`
3. `backend/application/printing_service.py`
4. `backend/printing/`
5. `backend/tests/test_printing_*`

### 6.2 监考相关问题

优先查看：

1. `frontend/src/views/ProctoringPage.vue`
2. `frontend/src/views/ProctoringPage/composables/`
3. `backend/application/proctoring_service.py`
4. `backend/proctoring/core/`
5. `backend/tests/test_proctoring_*`

### 6.3 考场相关问题

优先查看：

1. `frontend/src/views/RoomsPage.vue`
2. `frontend/src/views/RoomsPage/composables/`
3. `backend/application/rooms_service.py`
4. `backend/examroom/core/`
5. `backend/tests/test_rooms_*` 和 `backend/tests/test_exam_arrangement*`

### 6.4 科目页相关问题

优先查看：

1. `frontend/src/views/SubjectsPage.vue`
2. `frontend/src/views/SubjectsPage/composables/`
3. `backend/application/subjects_service.py`

## 7. 当前重构约定

本轮代码治理必须遵守这些约定：

- 只调整架构，不改业务逻辑
- 不修改 RPC 方法名、参数结构、返回结构
- 不顺手夹带业务需求
- 每一轮重构后都先过构建和相关测试
- 文档要跟着代码同步更新

## 8. 仓库卫生建议

当前工作区容易产生：

- `frontend/debug.log.*`
- 导出的 `pdf/xlsx`

当前 `.gitignore` 已忽略常见调试日志与示例导出文件；如果后续新增产物目录，也应及时补充忽略规则或统一收敛到固定输出目录。
