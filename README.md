# Easy Exam

Easy Exam 是一个面向学校考试组织场景的 Windows 桌面应用，用于管理考试科目、监考编排、考场编排、资料打印、软件授权和帮助中心内容。

当前仓库采用 `Electron + Vue 3 + TypeScript + Python` 架构。前端通过 Electron IPC 管理 Python sidecar，再以基于 `stdin/stdout` 的轻量 RPC 协议与后端通信。

## 当前能力

- 科目管理：导入、编辑、校验、导出科目，支持为单个科目单独设置考场数量
- 监考编排：导入教师、导入已有安排、导入/导出预设、手动交换，并通过 CP-SAT 后台任务执行智能编排或补全编排
- 考场编排：支持顺序编排、随机编排、`3+1+2` 选科编排和高考模式，支持导入既有结果继续使用；高考模式高级设置支持可编辑科目名称、唯一性校验和系统当日默认日期
- 资料打印：支持台角纸、桌角纸、准考证、考生信息表、试卷袋，支持空白模板、文件导入和考场编排三种数据源
- 系统支持：机器码注册、证书读写、帮助中心全文搜索、状态持久化与自动备份

## 文档导航

开发文档：

- [docs/README.md](docs/README.md)
- [docs/architecture.md](docs/architecture.md)
- [docs/modules.md](docs/modules.md)
- [docs/development.md](docs/development.md)
- [docs/testing-and-release.md](docs/testing-and-release.md)
- [docs/授权证书文件路径说明.md](docs/授权证书文件路径说明.md)
- [docs/前端设计要求](docs/前端设计要求)

前端专项说明：

- [frontend/README.md](frontend/README.md)

用户手册：

- [使用说明书.md](backend/resources/使用说明书.md)
- [使用说明书.pdf](使用说明书.pdf)

归档方案与历史设计：

- [docs/archive/plans](docs/archive/plans)

## 仓库结构

```text
Easy-Exam/
├─ backend/                 Python 后端、业务模块、RPC 服务、测试
├─ docs/                    开发文档
├─ frontend/                Electron + Vue 前端工程
├─ testdata/                示例数据与压力用例
├─ tools/                   辅助脚本
├─ package.py               一键打包脚本
├─ pytest.ini               pytest 入口配置
└─ 使用说明书.pdf            用户手册 PDF
```

几个关键目录：

- `backend/application/`：前端可见的服务边界
- `backend/proctoring/`：监考编排导入、导出与核心算法
- `backend/examroom/`：考场编排逻辑与高考模式导出
- `backend/printing/`：打印适配、生成器与校验器
- `backend/manual/`：说明书加载、Markdown 处理、搜索与 PDF 导出工具
- `frontend/electron/`：Electron 主进程与 preload
- `frontend/src/views/`：页面入口、局部组件与 composables
- `frontend/src/lib/pythonBackend.ts`：前端 RPC 客户端

## 快速开始

### 1. 安装前端依赖

```bash
cd frontend
npm install
```

### 2. 安装后端依赖

```bash
cd ..
conda run --no-capture-output -n exam_scheduler python -m pip install -r backend/requirements.txt
```

如果你使用的是项目约定的运行时配置，建议先确认 `.env.runtime.local` 中的环境名，再在对应环境里安装依赖，避免把包装到系统默认 Python。

### 3. 配置本机运行环境

开发运行、测试命令与打包时使用的 Python 环境统一读取仓库根目录的运行时配置：

- 模板文件：`.env.runtime.example`
- 本机文件：`.env.runtime.local`（不提交）

首次使用时，请先在仓库根目录复制模板文件：

```bash
cp .env.runtime.example .env.runtime.local
```

然后按本机环境修改 `.env.runtime.local`。推荐优先填写 Conda 环境名，而不是写死 Python 绝对路径。

### 4. 启动开发环境

```bash
cd frontend
npm run dev
```

开发态固定使用 Vite `5173` 端口，Electron 主进程会拉起或复用 Python 后端，并在仓库根目录写入 `debug.log`。

## 常用命令

前端：

```bash
cd frontend
npm run dev
npm run test
npm run build
npm run electron:build
```

后端测试：

```bash
# macOS / Linux
./tools/test-backend.sh

# Windows
powershell -ExecutionPolicy Bypass -File .\tools\test-backend.ps1
```

定向测试示例：

```bash
# macOS / Linux
./tools/test-backend.sh backend/tests/test_update_guard.py backend/tests/test_system_service.py

# Windows
powershell -ExecutionPolicy Bypass -File .\tools\test-backend.ps1 backend/tests/test_update_guard.py backend/tests/test_system_service.py
```

后端调试：

```bash
# macOS / Linux
./tools/run-backend.sh

# Windows
powershell -ExecutionPolicy Bypass -File .\tools\run-backend.ps1
```

后端自检：

```bash
# macOS / Linux
./tools/selfcheck-backend.sh

# Windows
powershell -ExecutionPolicy Bypass -File .\tools\selfcheck-backend.ps1
```

一键打包：

```bash
cd ..
python package.py
```

## 当前运行链路

```text
用户操作
  -> Vue 页面 / composables / store
  -> frontend/src/lib/pythonBackend.ts
  -> preload 暴露的 IPC
  -> Electron 主进程
  -> Python sidecar (python -m backend / engine.exe)
  -> backend/rpc_server.py
  -> backend/application/*_service.py
  -> feature modules / repository / resources
  -> 结构化结果返回前端
```

监考编排是当前最重的后端链路。前端通过 `proctoring.startSolverJob` 发起后台任务，再轮询 `proctoring.getJobStatus` 获取阶段进度、预览结果和最终结果。

## 数据与状态

- 应用状态默认写入 `data/state.json`
- 若设置 `EXAMFLOW_DATA_DIR` 或 `EXAMDESK_DATA_DIR`，则状态写入 `<dir>/data/state.json`
- `backend/repository/state_repository.py` 会在 `data/backups/` 下自动保留最近 10 份备份
- 授权证书默认使用 `license.cert`，可由 `EXAMFLOW_CERT_DIR` / `EXAMDESK_CERT_DIR` 覆盖
- 帮助中心实际加载的源文件是 `backend/resources/使用说明书.md`

## 打包说明

当前正式打包入口是：

```powershell
python package.py
```

它会串联两步：

1. 按 `.env.runtime.local` 解析出的运行环境，通过 `frontend/engine.spec` 构建 Python sidecar
2. 在 `frontend/` 下执行 `npm.cmd run electron:build` 产出安装包

当前实现仍有一个固定约束：

- Electron 产物目录固定为 `frontend/release_v6/`

## 建议阅读顺序

1. [docs/architecture.md](docs/architecture.md)
2. [docs/modules.md](docs/modules.md)
3. [docs/development.md](docs/development.md)
4. [docs/testing-and-release.md](docs/testing-and-release.md)
5. [frontend/README.md](frontend/README.md)
