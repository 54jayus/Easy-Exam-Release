# Easy Exam

## 文档导航

开发文档入口:

- [docs/README.md](docs/README.md)
- [docs/architecture.md](docs/architecture.md)
- [docs/modules.md](docs/modules.md)
- [docs/development.md](docs/development.md)
- [docs/testing-and-release.md](docs/testing-and-release.md)

用户手册入口:

- [使用说明书.md](使用说明书.md)
- [使用说明书.pdf](使用说明书.pdf)

Easy Exam 是一个面向学校考试管理场景的桌面应用，用于处理科目管理、监考编排、考场编排、资料打印、注册授权等工作流。项目采用 Electron + Vue 3 + Python 的前后端分层架构，前端通过 JSON-RPC over stdin/stdout 与 Python 后端通信。

当前仓库已经包含较完整的用户使用手册，但此前缺少仓库级开发入口文档。本文档用于帮助开发者快速理解项目结构、启动方式与打包流程。

## 主要能力

- 科目管理
- 监考编排与调换
- 考场编排，包括高考模式
- 打印资料生成与导出
- 软件注册与授权
- 内置帮助中心与说明书加载

## 技术栈

- 桌面容器: Electron
- 前端: Vue 3 + TypeScript + Vite + Element Plus + Tailwind CSS
- 后端: Python
- 数据处理与导出: pandas、openpyxl、xlsxwriter、reportlab
- 通信方式: JSON-RPC over stdin/stdout

## 架构概览

项目运行时由 Electron 主进程拉起前端界面，并负责启动 Python 后端进程。

- `frontend/electron/main.ts` 负责桌面窗口、IPC、日志与 Python 子进程管理
- `frontend/src/lib/pythonBackend.ts` 负责前端侧 RPC 客户端封装
- `backend/rpc_server.py` 负责后端 RPC 分发与服务注册
- `backend/application/` 下的各类 Service 承担具体业务逻辑

整体链路如下:

1. Electron 启动应用窗口
2. 前端通过 IPC 请求主进程启动 Python 后端
3. Python 以后端模块 `backend` 方式运行
4. 前端通过 JSON-RPC 调用后端服务，例如 `rooms.export`、`subjects.list`
5. 后端处理业务后返回结构化结果

## 目录结构

```text
Easy-Exam/
├─ backend/                Python 后端与业务逻辑
│  ├─ application/         应用服务
│  ├─ examroom/            考场编排核心逻辑
│  ├─ licensing/           授权与证书处理
│  ├─ printing/            打印与导出
│  ├─ proctoring/          监考编排
│  ├─ repository/          状态持久化
│  ├─ rpc/                 RPC 基础设施
│  ├─ resources/           内置资源与说明文档
│  ├─ requirements.txt     Python 依赖
│  └─ rpc_server.py        后端 RPC 入口
├─ frontend/               Electron + Vue 前端
│  ├─ electron/            Electron 主进程代码
│  ├─ src/                 Vue 页面、组件、状态与 RPC 调用
│  ├─ public/              静态资源
│  ├─ package.json         前端脚本与打包配置
│  └─ engine.spec          PyInstaller 配置
├─ docs/                   专项技术文档
├─ tools/                  辅助工具
├─ package.py              一键打包脚本
├─ 使用说明书.md           用户手册（Markdown）
└─ 使用说明书.pdf          用户手册（PDF）
```

## 开发环境要求

项目当前明显偏 Windows 桌面应用开发环境，建议在 Windows 10/11 下进行开发。

- Node.js
- npm
- Python 3
- 可选: Conda 环境

后端当前依赖见 [backend/requirements.txt](backend/requirements.txt)，前端脚本见 [frontend/package.json](frontend/package.json)。

## 快速开始

### 1. 安装前端依赖

```bash
cd frontend
npm install
```

### 2. 安装后端依赖

在项目根目录或你的 Python 环境中执行:

```bash
pip install -r backend/requirements.txt
```

如果你使用 Conda，也可以先激活环境后再安装。

### 3. 配置本地 Python 路径

复制前端环境变量模板:

```bash
cd frontend
copy .env.development.example .env.development
```

然后在 `.env.development` 中设置:

```env
VITE_PYTHON_PATH=D:/Anaconda3/envs/exam_scheduler/python.exe
```

如果系统环境变量里已经能直接使用 `python`，也可以改为:

```env
VITE_PYTHON_PATH=python
```

### 4. 启动开发环境

```bash
cd frontend
npm run dev
```

当前项目的 `electron:dev` 与 `dev` 脚本一致，实际开发依赖 Electron 进程与前端集成配置。若本地调试时需要确认启动方式，可优先从 [frontend/electron/main.ts](frontend/electron/main.ts) 和 [frontend/src/lib/pythonBackend.ts](frontend/src/lib/pythonBackend.ts) 入手。

## 常用命令

在 `frontend` 目录下执行:

```bash
npm run dev
```

启动前端开发环境。

```bash
npm run build
```

执行前端 TypeScript 检查并构建前端与 Electron 产物。

```bash
npm run electron:build
```

构建 Electron 安装包。

## 打包流程

项目根目录提供了 [package.py](package.py) 作为一键打包脚本，流程分为两步:

1. 用 PyInstaller 根据 [frontend/engine.spec](frontend/engine.spec) 构建 Python 后端 sidecar
2. 执行 `npm run electron:build` 打包 Electron 安装包

直接执行:

```bash
python package.py
```

需要注意的是，`package.py` 当前写死了一个本地 Anaconda Python 路径:

```text
D:/ANACONDA/envs/exam_scheduler/python.exe
```

如果你的环境路径不同，打包前需要先调整脚本。

## 关键运行机制

### 状态持久化

后端状态通过 `StateRepository` 持久化，默认状态文件位置由 [backend/rpc_server.py](backend/rpc_server.py) 中 `_get_state_file()` 决定，可受以下环境变量影响:

- `EXAMFLOW_DATA_DIR`
- `EXAMDESK_DATA_DIR`
- `EXAMFLOW_APP_DIR`
- `EXAMDESK_APP_DIR`
- `EXAMFLOW_CERT_DIR`
- `EXAMDESK_CERT_DIR`

### 授权证书

授权证书 `license.cert` 的生成与读取路径说明，见 [docs/授权证书文件路径说明.md](docs/授权证书文件路径说明.md)。

### 内置帮助说明

项目内置的用户手册主要位于:

- [使用说明书.md](使用说明书.md)
- [使用说明书.pdf](使用说明书.pdf)
- [backend/resources/使用说明书.md](backend/resources/使用说明书.md)

## 建议的阅读顺序

如果你是第一次接手这个项目，建议按下面顺序阅读:

1. 本 README
2. [使用说明书.md](使用说明书.md)
3. [frontend/electron/main.ts](frontend/electron/main.ts)
4. [frontend/src/lib/pythonBackend.ts](frontend/src/lib/pythonBackend.ts)
5. [backend/rpc_server.py](backend/rpc_server.py)

## 当前文档空白

虽然本轮已经补齐了仓库级开发入口、架构、模块、调试和测试发布说明，但以下内容仍建议后续继续完善:

- 版本变更记录
- 更细的导入导出字段说明
- 高考模式专项设计文档
- 自动化测试方案
