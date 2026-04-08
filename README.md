# Easy Exam

Easy Exam 是一个面向学校考试组织场景的桌面端应用，用于管理考试科目、监考编排、考场编排、资料打印、软件授权和帮助中心内容。项目采用 `Electron + Vue 3 + TypeScript + Python` 架构，前端通过基于 `stdin/stdout` 的 RPC 与 Python 后端通信。

## 文档导航

开发者文档：

- [docs/README.md](docs/README.md)
- [docs/architecture.md](docs/architecture.md)
- [docs/modules.md](docs/modules.md)
- [docs/development.md](docs/development.md)
- [docs/testing-and-release.md](docs/testing-and-release.md)
- [docs/授权证书文件路径说明.md](docs/授权证书文件路径说明.md)
- [docs/前端设计要求](docs/前端设计要求)

前端专项文档：

- [frontend/README.md](frontend/README.md)

用户手册：

- [使用说明书.md](使用说明书.md)
- [使用说明书.pdf](使用说明书.pdf)

历史方案与重构记录：

- [docs/archive/plans](docs/archive/plans)

## 主要能力

- 科目导入、编辑、校验与导出
- 监考教师导入、自动排监考、优化、交换与导出
- 常规模式与高考模式考场编排
- 准考证、角标、座位贴、试卷袋等资料生成
- 机器码读取、授权校验与注册
- 内置帮助中心、全文检索与说明书加载

## 技术栈

- 桌面容器：Electron
- 前端：Vue 3、TypeScript、Vite、Pinia、Vue Router、Element Plus、Tailwind CSS
- 后端：Python
- 数据处理与导出：pandas、openpyxl、xlsxwriter、reportlab
- 通信方式：JSON-RPC 风格消息，经 `stdin/stdout` 在 Electron 与 Python 间传递

## 仓库结构

```text
Easy-Exam/
├─ backend/                Python 后端与业务逻辑
├─ docs/                   开发、架构、测试与设计文档
├─ frontend/               Electron + Vue 前端工程
├─ tools/                  辅助脚本
├─ package.py              一键打包脚本
├─ pytest.ini              pytest 入口配置
├─ 使用说明书.md            用户手册（Markdown）
└─ 使用说明书.pdf           用户手册（PDF）
```

其中几个关键目录：

- `backend/application/`：前端可见的后端服务边界
- `backend/proctoring/`：监考编排逻辑
- `backend/examroom/`：考场编排逻辑
- `backend/printing/`：打印与导出逻辑
- `backend/licensing/`：授权相关逻辑
- `frontend/electron/`：Electron 主进程与 preload
- `frontend/src/views/`：页面入口与页面局部模块
- `frontend/src/lib/pythonBackend.ts`：前端 RPC 客户端

## 快速开始

### 1. 安装前端依赖

```powershell
Set-Location frontend
npm.cmd install
```

### 2. 安装后端依赖

```powershell
Set-Location ..
python -m pip install -r backend/requirements.txt
```

### 3. 配置本地 Python 路径

开发环境通常通过 `frontend/.env.development` 指定 Python：

```env
VITE_PYTHON_PATH=D:/Anaconda3/envs/exam_scheduler/python.exe
```

如果系统环境里已经能直接调用 `python`，也可以写成：

```env
VITE_PYTHON_PATH=python
```

### 4. 启动开发环境

```powershell
Set-Location frontend
npm.cmd run dev
```

Vite 开发服务器固定端口为 `5173`，Electron 会通过 `vite-plugin-electron` 一起启动桌面端入口。

## 常用命令

前端：

```powershell
Set-Location frontend
npm.cmd run dev
npm.cmd run test
npm.cmd run build
npm.cmd run electron:build
```

后端测试：

```powershell
Set-Location ..
$env:PYTHONPATH='.'
pytest
```

后端自检：

```powershell
Set-Location ..
$env:PYTHONPATH='.'
python -m backend.selfcheck
```

一键打包：

```powershell
Set-Location ..
python package.py
```

## 运行时架构摘要

运行时主链路如下：

```text
用户操作
  -> Vue 页面 / composables / store
  -> frontend/src/lib/pythonBackend.ts
  -> Electron IPC
  -> Electron 主进程启动或复用 Python 进程
  -> backend/rpc_server.py
  -> backend/application/*_service.py
  -> proctoring / examroom / printing / licensing / manual 等模块
  -> 结构化结果返回前端
```

更完整的架构说明请看 [docs/architecture.md](docs/architecture.md)。

## 测试与打包

测试入口：

- 前端单测：`frontend/tests/`
- 后端测试：`backend/tests/`

打包流程：

1. 用 `frontend/engine.spec` 构建 Python sidecar
2. 用 `electron-builder` 构建安装包
3. 用仓库根目录的 `package.py` 串联整个流程

详情见 [docs/testing-and-release.md](docs/testing-and-release.md) 和 [docs/打包代码.txt](docs/打包代码.txt)。

## 授权与帮助中心

- 授权证书路径规则见 [docs/授权证书文件路径说明.md](docs/授权证书文件路径说明.md)
- 应用内帮助中心主要读取 `backend/resources/使用说明书.md`
- 仓库根目录保留同名 Markdown 和 PDF 用户手册，方便离线查看

## 建议阅读顺序

1. [docs/architecture.md](docs/architecture.md)
2. [docs/modules.md](docs/modules.md)
3. [docs/development.md](docs/development.md)
4. [docs/testing-and-release.md](docs/testing-and-release.md)
5. [frontend/README.md](frontend/README.md)
