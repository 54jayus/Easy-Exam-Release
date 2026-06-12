# 架构说明

## 1. 总览

Easy Exam 是一个 Windows 桌面应用，当前采用 `Electron + Vue 3 + Python` 分层架构：

- `Electron` 负责窗口、IPC、文件对话框、外部链接、日志落盘以及 Python 子进程生命周期
- `Vue 3 + TypeScript` 负责页面交互、工作流编排、页面局部状态和可视化预览
- `Python` 负责业务规则、Excel/PDF 生成、持久化、授权校验和帮助中心资源读取

运行时主链路：

```text
用户操作
  -> Vue 页面 / composables / store
  -> frontend/src/lib/pythonBackend.ts
  -> preload 暴露的 IPC
  -> Electron 主进程
  -> backend/rpc_server.py
  -> backend/rpc/dispatcher.py
  -> backend/application/*_service.py
  -> feature modules / repository / resources
  -> 结果返回前端
```

当前架构最重要的约束：

- 前端不直接管理 Python 进程细节，只通过统一 RPC 客户端访问后端
- Electron 主进程不承载业务规则，只做桌面宿主与进程桥接
- Python 以后端服务层为边界，对外暴露结构化结果
- 业务状态统一由 Python 侧持有并落盘，前端只维护页面态和短期交互态

## 2. Electron 层

### 2.1 主进程

主进程位于 [frontend/electron/main.ts](/d:/coding%20make%20work%20easy/Easy-Exam/frontend/electron/main.ts)。

当前职责包括：

- 创建桌面窗口并加载 Vite 页面
- 管理 `spawn_python`、`write_python`、`kill_python`
- 提供 `dialog:open`、`dialog:save`、`open_path`、`open_external`
- 记录主进程和渲染进程日志到 `debug.log`
- 在开发态拉起 `python -m backend`，在打包态拉起 `resources/engine/engine.exe`
- 注入 `EXAMFLOW_DATA_DIR` / `EXAMDESK_DATA_DIR`，保证状态和证书默认落到用户数据目录

### 2.2 Preload 安全桥

[frontend/electron/preload.ts](/d:/coding%20make%20work%20easy/Easy-Exam/frontend/electron/preload.ts) 使用 `contextBridge` 暴露受限 IPC 能力，渲染进程不会直接接触完整的 Electron API。

## 3. 前端层

### 3.1 页面与路由

路由定义位于 [frontend/src/router.ts](/d:/coding%20make%20work%20easy/Easy-Exam/frontend/src/router.ts)：

- `/dashboard`
- `/registration`
- `/subjects`
- `/proctoring`
- `/rooms`
- `/printing`
- `/help`

其中：

- `RegistrationPage` 与 `PrintingPage` 使用 `keepAlive`
- `RegistrationPage` 在应用重置时保留
- 未授权时，侧边导航除注册页外都不可进入

### 3.2 App Shell

[frontend/src/App.vue](/d:/coding%20make%20work%20easy/Easy-Exam/frontend/src/App.vue) 负责：

- 左侧导航和工作流步骤条
- 用户设置对话框与本地头像/昵称缓存
- 开发者模式开关
- 顶部日期时间显示
- 授权检查后的路由守卫联动

### 3.3 页面组织方式

前端现在已经稳定采用“页面入口 + 同名目录 + composables/局部组件”的结构：

- Subjects
  - [frontend/src/views/SubjectsPage.vue](/d:/coding%20make%20work%20easy/Easy-Exam/frontend/src/views/SubjectsPage.vue)
  - `useSubjectsData.ts`、`useSubjectsForm.ts`、`useSubjectsReset.ts`
- Proctoring
  - [frontend/src/views/ProctoringPage.vue](/d:/coding%20make%20work%20easy/Easy-Exam/frontend/src/views/ProctoringPage.vue)
  - `useProctoringBootstrap.ts`、`useProctoringDataManagement.ts`、`useProctoringScheduling.ts`、`useProctoringSwap.ts`、`useProctoringOptimizationMetrics.ts`、`useProctoringViewData.ts`
- Rooms
  - [frontend/src/views/RoomsPage.vue](/d:/coding%20make%20work%20easy/Easy-Exam/frontend/src/views/RoomsPage.vue)
  - `useRoomsState.ts`、`useRoomsPersistence.ts`、`useRoomsIO.ts`、`useRoomsArrangement.ts`
  - `RoomsSidebar.vue`、`RoomsDataTabs.vue`、`SubjectPriorityDialog.vue`、`GaokaoTimeSettingsDialog.vue`
- Printing
  - [frontend/src/views/PrintingPage.vue](/d:/coding%20make%20work%20easy/Easy-Exam/frontend/src/views/PrintingPage.vue)
  - `usePrintingFileSource.ts`、`usePrintingDeskLayout.ts`、`usePrintingGenerate.ts`、`usePrintingPreview.ts`、`usePrintingPreviewData.ts`、`usePrintingScheduleSource.ts`、`usePrintingSubjects.ts`
- Help
  - [frontend/src/views/HelpPage.vue](/d:/coding%20make%20work%20easy/Easy-Exam/frontend/src/views/HelpPage.vue)
  - `useMarkdown.ts`、`useFullTextSearch.ts`、`useScrollSpy.ts`、`useTocGeneration.ts`

跨页面基础设施主要位于：

- `frontend/src/lib/`：RPC、日志、UI 反馈、环境判断、对话框
- `frontend/src/composables/`：页面缓存控制、会话级偏好存储、UI 日志
- `frontend/src/stores/license.ts`：授权状态

## 4. 前后端通信

[frontend/src/lib/pythonBackend.ts](/d:/coding%20make%20work%20easy/Easy-Exam/frontend/src/lib/pythonBackend.ts) 是统一 RPC 客户端，负责：

- 请求 id 管理
- Promise 挂起与超时
- 监听 `python-stdout`、`python-stderr`、`python-exit`、`python-error`
- 按行解析 JSON 响应
- 在后端退出时清理未完成请求

协议不是 HTTP，也不是完整 JSON-RPC 服务器，而是基于 `stdin/stdout` 的按行 JSON 消息。

典型调用链：

```text
页面事件
  -> pythonBackend.request("rooms.arrange", params)
  -> preload IPC
  -> Electron 主进程写入 Python stdin
  -> rpc_server.py 分发到 service
  -> service 调用业务模块
  -> 结果写回 stdout
  -> 前端更新页面
```

## 5. Python 后端层

### 5.1 入口

后端入口是：

- [backend/__main__.py](/d:/coding%20make%20work%20easy/Easy-Exam/backend/__main__.py)
- [backend/rpc_server.py](/d:/coding%20make%20work%20easy/Easy-Exam/backend/rpc_server.py)

[backend/rpc_server.py](/d:/coding%20make%20work%20easy/Easy-Exam/backend/rpc_server.py) 会：

- 创建 `AppState`
- 通过 `StateRepository` 读取持久化状态
- 初始化各个 application service
- 向 `RpcDispatcher` 注册 RPC 方法
- 按行读取请求并写回结构化响应

### 5.2 服务层

当前已注册的服务包括：

- `SystemService`
- `LicensingService`
- `DashboardService`
- `SubjectsService`
- `ProctoringService`
- `RoomsService`
- `PrintingService`

这一层负责：

- 参数编排
- 状态读写
- 调用领域模块或文件处理逻辑
- 输出适合前端消费的结果

## 6. 状态与持久化

### 6.1 状态模型

状态模型位于：

- [backend/domain/state.py](/d:/coding%20make%20work%20easy/Easy-Exam/backend/domain/state.py)
- [backend/domain/models.py](/d:/coding%20make%20work%20easy/Easy-Exam/backend/domain/models.py)

`AppState` 当前承载：

- `subjects`
- `proctoring`
- `rooms`
- `printing`
- `exam_arrangement`

其中：

- `subjects`、`proctoring`、`rooms`、`printing` 会持久化
- `exam_arrangement` 是运行时对象，必要时由 rooms 状态懒恢复

### 6.2 状态仓储

[backend/repository/state_repository.py](/d:/coding%20make%20work%20easy/Easy-Exam/backend/repository/state_repository.py) 当前特性：

- JSON 持久化
- 内置 `VERSION`
- 保存前自动备份旧文件
- 最多保留最近 10 份备份
- 对高考模式结果中的 `DataFrame` 做序列化与反序列化适配

状态文件默认位于：

```text
data/state.json
```

若设置 `EXAMFLOW_DATA_DIR` 或 `EXAMDESK_DATA_DIR`，则位于：

```text
<data_dir>/data/state.json
```

## 7. 业务模块划分

### 7.1 Subjects

- 服务入口：[backend/application/subjects_service.py](/d:/coding%20make%20work%20easy/Easy-Exam/backend/application/subjects_service.py)
- 核心模块：`backend/subjects/core.py`、`backend/subjects/excel.py`

负责科目导入、导出、模板生成、冲突校验，并在科目变化后清空已失效的监考结果。

### 7.2 Proctoring

- 服务入口：[backend/application/proctoring_service.py](/d:/coding%20make%20work%20easy/Easy-Exam/backend/application/proctoring_service.py)
- 任务管理：[backend/application/proctoring_jobs.py](/d:/coding%20make%20work%20easy/Easy-Exam/backend/application/proctoring_jobs.py)
- 支撑逻辑：`backend/application/proctoring_support.py`
- 核心模块：`backend/proctoring/core/`

当前监考编排已经以 CP-SAT 为核心，模块主要包括：

- `data_import.py`
- `entities.py`
- `models.py`
- `statistics.py`
- `swap.py`
- `validators.py`
- `cp_sat/assignment.py`
- `cp_sat/common.py`
- `cp_sat/diagnostics.py`
- `cp_sat/metrics.py`
- `cp_sat/objectives.py`
- `cp_sat/progress.py`
- `cp_sat/solver.py`

当前前端主流程不是旧的同步“二次优化”按钮，而是：

- 通过 `proctoring.startSolverJob` 发起后台编排任务
- 通过 `proctoring.getJobStatus` 轮询阶段进度和预览结果
- 在开发者模式下可查看 CP-SAT 求解明细

### 7.3 Rooms / Exam Arrangement

- 服务入口：[backend/application/rooms_service.py](/d:/coding%20make%20work%20easy/Easy-Exam/backend/application/rooms_service.py)
- 核心模块：`backend/examroom/core/`
- 支撑模块：`rooms_input_importers.py`、`rooms_result_importers.py`、`rooms_templates.py`

负责：

- 模板生成与导入
- 名册导入
- 顺序/随机/`3+1+2`/高考模式编排
- 高考模式时间设置与考试顺序优先级
- 高考模式时间设置包含科目名称规范化、唯一性校验、系统当日默认日期及打印页同步
- 编排结果导入导出

### 7.4 Printing

- 服务入口：[backend/application/printing_service.py](/d:/coding%20make%20work%20easy/Easy-Exam/backend/application/printing_service.py)
- 核心模块：`backend/printing/core/`

结构分为：

1. `adapters/`
   用于衔接考场编排结果与打印数据
2. `generators/excel/` 与 `generators/pdf/`
   负责生成台角纸、桌角纸、准考证、考生信息表、试卷袋
3. `validators/` 与 `utils/`
   负责字段校验、排序检查和数据加载

### 7.5 Licensing

- 服务入口：[backend/application/licensing_service.py](/d:/coding%20make%20work%20easy/Easy-Exam/backend/application/licensing_service.py)
- 核心模块：`backend/licensing/core.py`、`backend/licensing/cert_store.py`

负责机器码读取、注册码校验、证书保存与加载。

### 7.6 Help / System / Manual

- 系统服务：[backend/application/system_service.py](/d:/coding%20make%20work%20easy/Easy-Exam/backend/application/system_service.py)
- 说明书工具：`backend/manual/`
- 资源目录：`backend/resources/`

当前帮助中心是“前端渲染 + 后端读取资源”的组合结构：

- 前端通过 `system.getHelpManual` 读取 Markdown
- 前端本地完成 TOC、滚动跟踪和全文搜索
- `backend/manual/pdf_export.py` 存在且有测试覆盖，但当前界面未暴露“导出 PDF”按钮

## 8. 打包与资源

### 8.1 Python sidecar

[frontend/engine.spec](/d:/coding%20make%20work%20easy/Easy-Exam/frontend/engine.spec) 当前会打包：

- `backend/__main__.py`
- `backend/resources/`
- `backend/resources/使用说明书.md` 与根目录下的 `使用说明书.pdf`
- `ortools` 相关隐藏导入与动态库

该 spec 会根据当前运行环境自动收集所需 DLL，不再依赖仓库内写死的本机路径。

### 8.2 Electron 构建

[frontend/package.json](/d:/coding%20make%20work%20easy/Easy-Exam/frontend/package.json) 中 `electron-builder` 会把 sidecar 作为 `extraResources` 打进 `resources/engine/`，输出目录固定为 `frontend/release_v6/`。

## 9. 建议延续的约束

- 新业务接口先落到 `backend/application/*_service.py`
- 复杂算法继续下沉到 feature module，而不是塞回 Electron 或 Vue 页面
- 前端页面优先承担编排与展示，复杂交互拆到 composables
- 任何系统能力通过 Electron IPC 暴露，不让页面直接访问 Node/Electron 原生能力
