# 开发与调试手册

## 1. 环境建议

项目当前主要面向 Windows 桌面环境开发，建议使用:

- Windows 10 或 Windows 11
- Node.js
- npm
- Python 3
- 可选: Conda

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

前端开发时，Python 路径通常通过 `frontend/.env.development` 指定。

先复制模板:

```bash
cd frontend
copy .env.development.example .env.development
```

再填写:

```env
VITE_PYTHON_PATH=D:/Anaconda3/envs/exam_scheduler/python.exe
```

如果系统环境中可直接使用 `python`，也可以写:

```env
VITE_PYTHON_PATH=python
```

## 4. 启动方式

### 4.1 开发启动

```bash
cd frontend
npm run dev
```

当前仓库中 `frontend/package.json` 里的 `dev` 和 `electron:dev` 脚本相同。实际调试时，建议结合 `frontend/electron/main.ts` 和 `frontend/src/lib/pythonBackend.ts` 一起理解启动流程。

### 4.2 后端单独检查

如果只想做 Python 语法检查，可以在仓库根目录执行:

```bash
python -m py_compile backend/application/rooms_service.py backend/examroom/core/arrangement.py
```

也可以替换成你当前正在改的后端文件。

### 4.3 前端构建检查

```bash
cd frontend
npm.cmd run build
```

在 PowerShell 中，`npm` 可能受执行策略影响，此时直接使用 `npm.cmd` 更稳妥。

## 5. 调试入口

### 5.1 前端排查

重点文件:

- `frontend/src/router.ts`
- `frontend/src/views/`
- `frontend/src/components/`
- `frontend/src/lib/pythonBackend.ts`

适用场景:

- 页面展示异常
- 交互问题
- 请求未发送
- 前端状态未刷新

### 5.2 Electron 排查

重点文件:

- `frontend/electron/main.ts`

适用场景:

- Python 后端起不来
- IPC 失效
- 打开目录 / 外链失败
- 日志文件写入失败

### 5.3 后端排查

重点文件:

- `backend/rpc_server.py`
- `backend/application/*.py`
- `backend/examroom/core/arrangement.py`
- `backend/printing/`

适用场景:

- 导入导出报错
- 业务结果异常
- 高考模式统计不正确
- 打印生成失败

## 6. 日志与常见输出

Electron 主进程会写本地日志:

- 开发态通常在 `frontend/debug.log`
- 日志轮转后可能出现 `frontend/debug.log.1`

日志里常见内容:

- 前端发出的 RPC 请求
- Python 标准错误输出
- 子进程启动与退出信息
- 文件打开或外链失败信息

## 7. 常见问题排查路径

### 7.1 Python 后端无法启动

优先检查:

1. `frontend/.env.development` 中的 `VITE_PYTHON_PATH`
2. 本机 Python / Conda 环境是否存在
3. `backend/requirements.txt` 是否安装完成
4. `frontend/debug.log` 中是否有启动异常

### 7.2 页面点了按钮但没反应

排查顺序:

1. 页面组件是否正确触发事件
2. composable 是否调用了 `pythonBackend.request(...)`
3. 对应 RPC 是否在 `backend/rpc_server.py` 注册
4. 对应 Service 是否真正处理了请求

### 7.3 导入 Excel 报错

排查重点:

- 列名是否和模板一致
- pandas 读取后的列类型是否符合预期
- 中文列名、空值、`nan` 字符串是否被正确处理
- 导入流程是否与当前模式匹配

### 7.4 导出结果不正确

排查重点:

- `rooms_service.py` 是否正确构造运行时数据
- `examroom/core/arrangement.py` 是否按当前模式导出
- `printing` 模块是否用了错误的数据适配器

### 7.5 打包失败

排查重点:

- `package.py` 里的 Python 路径是否是你本机真实路径
- `frontend/engine.spec` 是否仍与目录结构匹配
- 是否有正在运行的应用占用了输出目录

## 8. 推荐调试策略

- 改前端交互时，先确认是否只是 UI 问题，不要急着改后端
- 改业务结果时，优先抓一组最小样例 Excel 做重复验证
- 改高考模式时，至少同时验证导入、统计和打印下游
- 改导出功能时，同时看按钮 loading、保存路径和后端异常处理

## 9. 开发时的安全建议

- 不要轻易删除本地测试样例，尤其是能复现问题的 Excel
- 提交前尽量只纳入与当前任务直接相关的文件
- 日志、临时脚本、临时导出的 Excel 建议保持未跟踪状态，必要时加入 `.gitignore`
