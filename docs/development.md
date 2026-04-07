# 开发与调试手册

## 1. 环境建议

项目当前主要面向 Windows 桌面环境开发，建议使用：

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

## 3. 配置本地 Python

开发时通常通过 `frontend/.env.development` 指定 Python 路径。

先复制模板：

```bash
cd frontend
copy .env.development.example .env.development
```

然后填写：

```env
VITE_PYTHON_PATH=D:/Anaconda3/envs/exam_scheduler/python.exe
```

如果系统环境里直接可用 `python`，也可以写：

```env
VITE_PYTHON_PATH=python
```

## 4. 启动与构建

### 4.1 开发启动

```bash
cd frontend
npm run dev
```

当前仓库里 `frontend/package.json` 的 `dev` 和 `electron:dev` 脚本等价。调试启动链路时，建议同时看：

- `frontend/electron/main.ts`
- `frontend/src/lib/pythonBackend.ts`

### 4.2 后端单独检查

如果只想做 Python 语法检查，可以在仓库根目录执行：

```bash
python -m py_compile backend/application/rooms_service.py backend/examroom/core/arrangement.py
```

也可以替换成你当前正在修改的后端文件。

### 4.3 前端构建检查

```bash
cd frontend
npm.cmd run build
```

在 PowerShell 下优先使用 `npm.cmd`。直接运行 `npm run build` 可能受到执行策略影响。

## 5. 调试入口

### 5.1 前端排查

重点目录：

- `frontend/src/router.ts`
- `frontend/src/views/`
- `frontend/src/components/`
- `frontend/src/lib/pythonBackend.ts`

适用场景：

- 页面展示异常
- 交互问题
- 请求未发出
- 前端状态未刷新

复杂页面建议优先按“入口页 / 子目录 / composable”三层看结构。例如打印页当前应优先看：

- `frontend/src/views/PrintingPage.vue`
- `frontend/src/views/PrintingPage/composables/usePrintingFileSource.ts`
- `frontend/src/views/PrintingPage/composables/usePrintingPreview.ts`
- `frontend/src/views/PrintingPage/composables/usePrintingPreviewData.ts`
- `frontend/src/views/PrintingPage/composables/usePrintingGenerate.ts`
- `frontend/src/views/PrintingPage/composables/usePrintingSubjects.ts`
- `frontend/src/views/PrintingPage/composables/usePrintingDeskLayout.ts`
- `frontend/src/views/PrintingPage/composables/usePrintingScheduleSource.ts`

### 5.2 Electron 排查

重点文件：

- `frontend/electron/main.ts`

适用场景：

- Python 后端起不来
- IPC 失效
- 打开目录 / 外链失败
- 日志文件写入失败

### 5.3 后端排查

重点文件：

- `backend/rpc_server.py`
- `backend/application/*.py`
- `backend/examroom/core/arrangement.py`
- `backend/printing/`

适用场景：

- 导入导出报错
- 业务结果异常
- 高考模式统计不正确
- 打印生成失败

## 6. 日志与常见输出

Electron 主进程会写本地日志：

- 开发态通常在 `frontend/debug.log`
- 日志轮转后可能出现 `frontend/debug.log.1`

日志里常见内容：

- 前端发出的 RPC 请求
- Python 标准错误输出
- 子进程启动与退出信息
- 文件打开或外链失败信息

## 7. 常见问题排查路径

### 7.1 Python 后端无法启动

优先检查：

1. `frontend/.env.development` 中的 `VITE_PYTHON_PATH`
2. 本机 Python / Conda 环境是否存在
3. `backend/requirements.txt` 是否安装完成
4. `frontend/debug.log` 中是否有启动异常

### 7.2 页面点了按钮但没反应

排查顺序：

1. 页面模板是否正确触发事件
2. 对应 composable 是否更新了本地状态
3. 如果需要后端数据，对应 composable 是否调用了 `pythonBackend.request(...)`
4. 对应 RPC 是否在 `backend/rpc_server.py` 注册
5. 对应 Service 是否真正处理了请求

### 7.3 导入 Excel 报错

排查重点：

- 列名是否和模板一致
- pandas 读取后的列类型是否符合预期
- 中文列名、空值、`nan` 字符串是否被正确处理
- 导入流程是否与当前模式匹配

### 7.4 导出结果不正确

排查重点：

- `rooms_service.py` 是否正确构造运行时数据
- `examroom/core/arrangement.py` 是否按当前模式导出
- `printing` 模块是否使用了错误的数据适配器
- 前端生成前校验是否和后端生成器假设一致

### 7.5 打印页改动后异常

建议优先按职责定位问题：

- 文件导入 / 字段映射：`usePrintingFileSource.ts`
- 预览缩放 / 拖拽：`usePrintingPreview.ts`
- 预览内容不对：`usePrintingPreviewData.ts`
- 科目与时间不同步：`usePrintingSubjects.ts`
- 座位布局异常：`usePrintingDeskLayout.ts`
- 从编排加载失败：`usePrintingScheduleSource.ts`
- 点击生成后失败：`usePrintingGenerate.ts`

### 7.6 打包失败

排查重点：

- `package.py` 里的 Python 路径是否为本机真实路径
- `frontend/engine.spec` 是否仍与目录结构匹配
- 是否有正在运行的应用占用了输出目录

## 8. 推荐调试策略

- 改前端交互时，先确认是不是纯 UI / 状态问题，不要急着改后端
- 改业务结果时，优先抓一组最小样例 Excel 做重复验证
- 改高考模式时，至少同时验证导入、统计和打印下游
- 改导出功能时，同时看按钮 loading、保存路径和后端异常处理
- 超过 800 到 1000 行的页面优先考虑拆 composable，而不是继续把逻辑堆回主页面

## 9. 开发时的安全建议

- 不要轻易删除本地测试样例，尤其是能复现问题的 Excel
- 提交前尽量只纳入与当前任务直接相关的文件
- 日志、临时脚本、临时导出的 Excel / PDF 建议保持未跟踪状态，必要时加入 `.gitignore`
