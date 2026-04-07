# 架构说明

## 1. 总体结构

Easy Exam 是一个桌面端应用，采用 `Electron + Vue 3 + Python` 的分层架构。

- Electron 主进程负责窗口、IPC、日志、系统能力和 Python 子进程管理
- Vue 前端负责页面交互、状态展示和用户操作编排
- Python 后端负责业务规则、Excel 处理、导出、打印和状态持久化

整体调用链大致如下：

```text
用户操作
  -> Vue 页面 / composable / 组件
  -> frontend/src/lib/pythonBackend.ts
  -> Electron 主进程拉起并管理 Python 进程
  -> backend/rpc_server.py 分发 RPC
  -> application service
  -> domain / repository / examroom / printing 等模块
  -> 返回结果给前端
```

## 2. 前端层

前端代码主要位于 `frontend/src/`。

### 2.1 页面入口

路由定义在 `frontend/src/router.ts`，当前主要页面包括：

- `/dashboard` 仪表盘
- `/registration` 注册授权
- `/subjects` 科目管理
- `/proctoring` 监考编排
- `/rooms` 考场编排
- `/printing` 资料打印
- `/help` 帮助中心

### 2.2 前端与后端通信

`frontend/src/lib/pythonBackend.ts` 封装了前端调用后端的 RPC 客户端。

它负责：

- 启动和连接 Python 后端
- 维护请求序号和超时
- 监听标准输出 / 标准错误
- 解析 JSON-RPC 风格响应
- 在后端退出时清理挂起请求

前端通常以这种方式调用后端：

```ts
pythonBackend.request("rooms.export", { path })
```

方法名与后端 `backend/rpc_server.py` 中注册的 RPC 一一对应。

### 2.3 页面组织方式

当前前端页面主要有两种组织方式：

- 简单页面直接使用单个 `*.vue` 文件，例如 `DashboardPage.vue`、`RegistrationPage.vue`
- 复杂页面使用“页面入口 + 同名目录”的方式拆分，例如：
- `frontend/src/views/RoomsPage.vue` + `frontend/src/views/RoomsPage/`
- `frontend/src/views/HelpPage.vue` + `frontend/src/views/HelpPage/`
- `frontend/src/views/PrintingPage.vue` + `frontend/src/views/PrintingPage/composables/`

同名目录通常承载：

- 子组件
- composable
- 与页面强相关但不适合继续堆在主页面中的局部逻辑

目前 `PrintingPage.vue` 已调整为“页面编排层”，主要负责模板、状态接线和模块协调；核心逻辑已经拆到 `frontend/src/views/PrintingPage/composables/`。

## 3. Electron 主进程

Electron 主进程代码位于 `frontend/electron/main.ts`。

主要职责：

- 创建桌面窗口
- 提供 IPC 能力
- 管理本地日志文件 `frontend/debug.log`
- 启动、写入、终止 Python 子进程
- 为前端提供应用目录、打开路径、打开外链等系统能力

与后端联动较强的 IPC 包括：

- `backend_project_root`
- `app_exe_dir`
- `spawn_python`
- `write_python`
- `kill_python`

## 4. Python 后端

后端入口是 `backend/__main__.py`，实际主循环位于 `backend/rpc_server.py`。

后端启动后会：

1. 初始化日志
2. 创建应用状态 `AppState`
3. 从状态仓库恢复数据
4. 创建各类 Service
5. 注册 RPC 方法
6. 从标准输入按行读取 JSON 请求
7. 将结果以 JSON 写回标准输出

## 5. 后端分层

### 5.1 application

`backend/application/` 是后端应用服务层，对外提供 RPC 入口对应的业务方法。

当前主要服务包括：

- `SubjectsService`
- `ProctoringService`
- `RoomsService`
- `PrintingService`
- `LicensingService`
- `SystemService`
- `DashboardService`

### 5.2 domain

`backend/domain/` 放领域模型、状态对象和业务错误定义，例如：

- `AppState`
- 各模块状态对象
- 业务错误类型

### 5.3 repository

`backend/repository/` 负责状态持久化。当前项目以文件持久化为主，而不是数据库。

### 5.4 examroom

`backend/examroom/` 负责考场编排核心算法与导出逻辑，是考场业务的核心模块。

其中 `backend/examroom/core/arrangement.py` 负责：

- 常规编排
- 随机编排
- 选科模式编排
- 高考模式编排
- 结果导出
- 统计表生成

### 5.5 printing

`backend/printing/` 负责打印数据适配、预览和 PDF / Excel 生成。

前端对应页面为 `frontend/src/views/PrintingPage.vue`。当前这页已经拆成以下前端模块：

- `usePrintingFileSource.ts`
  负责文件选择、字段映射、预览缓存与文件数据源恢复
- `usePrintingPreview.ts`
  负责预览缩放、拖拽、自适应和预览容器交互
- `usePrintingPreviewData.ts`
  负责角标、准考证、考生信息表、试卷袋等预览数据加工
- `usePrintingGenerate.ts`
  负责生成导出流程与生成前校验
- `usePrintingSubjects.ts`
  负责科目与时间配置、同步与编辑弹窗
- `usePrintingDeskLayout.ts`
  负责座位布局草稿、排位算法与桌贴预览
- `usePrintingScheduleSource.ts`
  负责从考场编排结果加载打印预览数据

### 5.6 licensing

`backend/licensing/` 负责机器码、注册、证书文件路径和授权状态管理。

## 6. RPC 方法分布

RPC 方法集中注册在 `backend/rpc_server.py`。

主要命名空间：

- `system.*`
- `licensing.*`
- `dashboard.*`
- `subjects.*`
- `proctoring.*`
- `rooms.*`
- `printing.*`

这种组织方式的优点是：

- 前端调用语义清晰
- 模块边界相对稳定
- 新功能扩展时容易找到挂载点

## 7. 状态与持久化

项目当前不是数据库驱动，而是以内存状态 + 文件持久化为主。

关键点：

- 应用运行时状态集中在 `AppState`
- 部分数据通过 `StateRepository` 保存到 `state.json`
- `exam_arrangement` 是运行时对象，不直接整体持久化
- 某些页面会根据持久化数据重新构建运行时对象

## 8. 打包形态

打包时项目分为两部分：

1. Python 后端通过 PyInstaller 打成 sidecar
2. 前端与桌面壳通过 Electron Builder 打包

根目录 `package.py` 会串联这两个步骤。

## 9. 当前架构特征与注意事项

### 9.1 优点

- 前后端职责划分明确
- Python 适合处理 Excel 和复杂编排逻辑
- Electron 适合提供桌面能力和安装包
- 无数据库依赖，部署门槛较低

### 9.2 维护注意点

- 很多业务逻辑在 Python 后端，修功能时不要只看前端页面
- `rooms` 和 `printing` 之间耦合较强，打印通常依赖编排结果
- 状态恢复、导入导出和高考模式会改变数据结构，改动时要带样例验证
- 复杂前端页面优先继续采用“页面入口 + 同名目录 + composable”的拆分方式
- Windows 下要持续注意编码、中文路径和 PowerShell / `npm.cmd` 的兼容性
