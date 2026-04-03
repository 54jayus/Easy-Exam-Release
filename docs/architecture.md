# 架构说明

## 1. 总体结构

Easy Exam 是一个桌面应用，采用 Electron + Vue 3 + Python 的分层架构。

- Electron 主进程负责窗口、IPC、系统能力和 Python 子进程管理
- Vue 前端负责页面交互、状态展示和用户操作编排
- Python 后端负责业务规则、Excel 处理、导出、打印和状态持久化

整体调用关系如下:

```text
用户操作
  -> Vue 页面 / 组件
  -> pythonBackend RPC 客户端
  -> Electron 主进程拉起 / 管理 Python 进程
  -> backend.rpc_server 分发方法
  -> application Service
  -> domain / repository / examroom / printing 等模块
  -> 返回结果给前端
```

## 2. 前端层

前端主要位于 `frontend/src/`。

### 2.1 页面入口

路由在 `frontend/src/router.ts` 中定义，当前主要页面包括:

- `/dashboard` 仪表盘
- `/registration` 注册授权
- `/subjects` 科目管理
- `/proctoring` 监考编排
- `/rooms` 考场编排
- `/printing` 资料打印
- `/help` 帮助中心

### 2.2 前端与后端通信

`frontend/src/lib/pythonBackend.ts` 封装了前端调用后端的 RPC 客户端。

它的职责包括:

- 启动 Python 后端
- 维护请求序号和超时
- 监听标准输出 / 标准错误
- 解析 JSON-RPC 风格的响应
- 在后端退出时清理待处理请求

前端业务页面通常直接调用:

```ts
pythonBackend.request("rooms.export", { path })
```

这类方法名与后端 `dispatcher.register(...)` 注册的方法名一一对应。

## 3. Electron 主进程

Electron 主进程代码位于 `frontend/electron/main.ts`。

主要职责:

- 创建桌面窗口
- 提供 IPC 能力
- 管理本地日志文件 `debug.log`
- 启动、写入、终止 Python 子进程
- 为前端提供应用目录、打开路径、打开外链等系统能力

与后端相关的关键 IPC 包括:

- `backend_project_root`
- `app_exe_dir`
- `spawn_python`
- `write_python`
- `kill_python`

## 4. Python 后端

后端入口是 `backend/__main__.py`，实际主循环在 `backend/rpc_server.py`。

后端启动后会:

1. 初始化日志
2. 创建应用状态 `AppState`
3. 从状态仓库恢复数据
4. 创建各类 Service
5. 将 RPC 方法注册到 `RpcDispatcher`
6. 从标准输入按行读取 JSON 请求
7. 将结果以 JSON 写回标准输出

## 5. 后端分层

### 5.1 application

`backend/application/` 是最核心的应用服务层，对外提供 RPC 方法对应的业务入口。

当前主要服务包括:

- `SubjectsService`
- `ProctoringService`
- `RoomsService`
- `PrintingService`
- `LicensingService`
- `SystemService`
- `DashboardService`
- `AssistantService`

### 5.2 domain

`backend/domain/` 放领域模型、状态对象和错误定义，例如:

- `AppState`
- 各模块状态对象
- 业务错误类型

### 5.3 repository

`backend/repository/` 负责状态持久化。当前项目通过状态仓库保存应用状态，而不是使用数据库。

### 5.4 examroom

`backend/examroom/` 负责考场编排核心算法与导出逻辑，是考场业务的核心模块。

其中 `backend/examroom/core/arrangement.py` 负责:

- 常规编排
- 随机编排
- 选科模式编排
- 高考模式编排
- 结果导出
- 统计表生成

### 5.5 printing

`backend/printing/` 负责打印数据适配、预览和 PDF / Excel 生成。

### 5.6 licensing

`backend/licensing/` 负责机器码、注册、证书文件路径和授权状态管理。

## 6. RPC 方法分布

所有 RPC 方法注册集中在 `backend/rpc_server.py`。

主要命名空间:

- `system.*`
- `licensing.*`
- `assistant.*`
- `dashboard.*`
- `subjects.*`
- `proctoring.*`
- `rooms.*`
- `printing.*`

这种组织方式的优点是:

- 前端调用语义清晰
- 模块边界相对稳定
- 新功能扩展时容易找到挂载点

## 7. 状态与持久化

项目当前不是数据库驱动，而是以内存状态 + 文件持久化为主。

关键点:

- 应用运行时状态集中在 `AppState`
- 部分数据由 `StateRepository` 保存到 `state.json`
- `exam_arrangement` 是运行时对象，不直接整体持久化
- 某些页面会根据持久化数据重新构建 `exam_arrangement`

`backend/rpc_server.py` 中的 `_get_state_file()` 会根据环境变量决定状态文件路径。

## 8. 打包形态

打包时项目分为两部分:

1. Python 后端通过 PyInstaller 打成 sidecar
2. 前端与桌面壳通过 Electron Builder 打包

根目录 `package.py` 会串联这两个步骤。

## 9. 当前架构特征与注意事项

### 9.1 优点

- 前后端职责划分明确
- Python 适合处理 Excel 与复杂编排逻辑
- Electron 适合提供桌面能力与安装包
- 不依赖数据库，部署门槛较低

### 9.2 维护注意点

- 很多业务逻辑在 Python 后端，前端只是界面层，修功能时不要只改页面
- `rooms` 和 `printing` 之间存在较强联动，打印通常依赖编排结果
- 状态恢复、导入导出和高考模式会改变数据结构，改动时要带样例验证
- 当前编码和中文路径兼容是一个长期关注点，Windows 环境下尤其要留意
