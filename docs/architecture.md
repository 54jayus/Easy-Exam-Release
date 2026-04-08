# 架构说明

## 1. 架构概览

Easy Exam 是一个面向学校考试业务的桌面端应用，采用 `Electron + Vue 3 + Python` 的分层架构。

- `Electron` 负责桌面窗口、IPC、文件对话框、外部链接打开、日志落盘，以及 Python 子进程生命周期管理。
- `Vue 3 + TypeScript` 负责页面交互、状态展示、工作流编排和用户输入。
- `Python` 负责业务规则、Excel/ PDF 生成、状态持久化、授权校验和帮助文档读取。

当前运行时的主链路如下：

```text
用户操作
  -> Vue 页面 / composables / store
  -> frontend/src/lib/pythonBackend.ts
  -> Electron IPC
  -> Electron 主进程启动或复用 Python 进程
  -> backend/rpc_server.py
  -> backend/rpc/dispatcher.py
  -> backend/application/*_service.py
  -> domain / repository / feature modules
  -> 结果回到前端页面
```

这套架构的核心特点是：

- 前端不直接接触 Python 进程，只通过统一 RPC 客户端访问后端能力。
- 后端以 `application service` 作为对外边界，业务细节继续下沉到各模块。
- 应用状态由 Python 侧统一持有和持久化，前端只维护界面态与短期交互态。

## 2. 运行时分层

### 2.1 Electron 主进程

主进程代码位于 `frontend/electron/main.ts`，主要职责包括：

- 创建桌面窗口并加载 Vite 页面
- 暴露 `spawn_python`、`write_python`、`kill_python` 等 IPC 能力
- 提供 `dialog:open`、`dialog:save`、`open_path`、`open_external` 等系统能力
- 转发前端日志并写入 `debug.log`
- 管理 Python 子进程的启动、复用、退出和异常日志

开发环境下，主进程会将后端映射为：

```text
python -m backend
```

打包环境下，主进程优先启动随应用分发的 sidecar：

```text
resources/engine/engine.exe
```

### 2.2 Preload 安全桥

`frontend/electron/preload.ts` 使用 `contextBridge` 向渲染进程暴露受限的 `ipcRenderer` 能力，只允许白名单频道被调用，从而把 Electron API 的使用范围限制在可控边界内。

### 2.3 前端渲染层

前端入口位于：

- `frontend/src/main.ts`
- `frontend/src/App.vue`
- `frontend/src/router.ts`

前端主要负责：

- 组织页面路由与工作流导航
- 启动时检查授权状态
- 管理页面级交互、弹窗、预览和导入导出流程
- 通过 `pythonBackend.request(...)` 调用后端 RPC

当前路由入口包括：

- `/dashboard`
- `/registration`
- `/subjects`
- `/proctoring`
- `/rooms`
- `/printing`
- `/help`

其中：

- `RegistrationPage` 负责授权注册
- `HelpPage` 负责帮助中心
- `DashboardPage` 负责展示工作流总体状态
- `Subjects / Proctoring / Rooms / Printing` 构成主业务闭环

### 2.4 Python 后端

后端入口为：

- `backend/__main__.py`
- `backend/rpc_server.py`

`backend/__main__.py` 负责初始化日志，再进入 `rpc_server.main()`。

`backend/rpc_server.py` 负责：

- 创建 `AppState`
- 创建 `StateRepository`
- 初始化各个 application service
- 向 `RpcDispatcher` 注册 RPC 方法
- 从 `stdin` 读取 JSON 请求并从 `stdout` 写回 JSON 响应

通信协议采用“基于标准输入输出的轻量 JSON-RPC 风格协议”，不是 HTTP 服务，也不对外开放网络端口。

## 3. 前后端通信设计

前端到后端的调用统一收敛在 `frontend/src/lib/pythonBackend.ts`。

这个客户端封装了以下责任：

- 通过 Electron IPC 请求主进程启动 Python
- 维护请求 `id`、挂起请求表和超时
- 监听 `python-stdout`、`python-stderr`、`python-exit`、`python-error`
- 解析按行返回的 JSON 响应
- 在后端退出或报错时，统一清理未完成请求

典型调用链如下：

```text
页面事件
  -> pythonBackend.request("rooms.arrange", params)
  -> preload 暴露的 IPC
  -> main.ts 写入 Python stdin
  -> rpc_server.py 分发到 rooms_service
  -> service 调用 examroom / repository / domain
  -> JSON 响应写回 stdout
  -> pythonBackend resolve Promise
  -> 页面更新视图
```

这样做的收益是：

- 页面无需关心进程启动与通信细节
- Electron 能集中处理异常、日志和系统权限
- Python 后端可以保持为纯业务服务，不混入桌面交互代码

## 4. 前端结构

前端代码主要位于 `frontend/src/`，当前已经形成“页面入口 + 同名目录 + composables + 公共基础设施”的组织方式。

### 4.1 基础目录

```text
frontend/src/
  App.vue
  main.ts
  router.ts
  components/
  composables/
  lib/
  stores/
  types/
  views/
```

各目录职责如下：

- `views/`：页面入口和页面专属逻辑
- `views/<Page>/composables/`：复杂页面逻辑拆分
- `views/<Page>/components/`：页面专属子组件
- `components/`：跨页面复用组件
- `lib/`：RPC、日志、环境识别、对话框等基础设施
- `stores/`：Pinia 状态，目前最典型的是授权状态
- `types/`：RPC 类型、业务类型和外部库补充声明
- `composables/`：跨页面可复用能力，例如页面缓存控制

### 4.2 页面分层

当前主要页面的职责边界如下：

- `DashboardPage.vue`
  展示统计信息、工作流状态和系统总览
- `RegistrationPage.vue`
  展示机器码、注册状态和激活入口
- `SubjectsPage.vue`
  管理考试科目、导入导出和规则校验
- `ProctoringPage.vue`
  管理监考教师导入、排监考、优化、交换和导出
- `RoomsPage.vue`
  管理考场设置、学生数据导入、排考场和结果导出
- `PrintingPage.vue`
  负责打印数据源映射、预览、布局配置和最终生成
- `HelpPage.vue`
  负责说明文档渲染、目录生成、全文检索和滚动定位

### 4.3 复杂页面的拆分方式

目前几个复杂业务页都在沿用同一模式：

- 页面 `.vue` 文件承担页面级编排、生命周期接线和模板渲染
- 复杂逻辑下沉到 composables
- 对话框和独立面板下沉为页面局部组件

典型例子：

- `SubjectsPage/composables/`
  `useSubjectsData`、`useSubjectsForm`、`useSubjectsLogs`、`useSubjectsReset`
- `ProctoringPage/composables/`
  `useProctoringBootstrap`、`useProctoringDataManagement`、`useProctoringScheduling`、`useProctoringSwap`、`useProctoringOptimizationMetrics`、`useProctoringViewData`
- `RoomsPage/composables/`
  `useRoomsState`、`useRoomsPersistence`、`useRoomsLogging`、`useRoomsIO`、`useRoomsArrangement`
- `PrintingPage/composables/`
  `usePrintingSubjects`、`usePrintingPreview`、`usePrintingFileSource`、`usePrintingGenerate`、`usePrintingPreviewData`、`usePrintingDeskLayout`、`usePrintingScheduleSource`
- `HelpPage/composables/`
  `useMarkdown`、`useFullTextSearch`、`useScrollSpy`、`useTocGeneration`

这说明前端已经从“页面文件堆积全部业务逻辑”演进为“页面编排层 + 页面逻辑层 + 局部组件层”的结构。

### 4.4 前端状态与守卫

当前前端的关键状态机制包括：

- `stores/license.ts`
  在应用启动时调用 `licensing.verify`，控制是否允许进入主流程页面
- `useAppCacheControl.ts`
  控制部分页面在重置数据后的缓存失效
- 路由守卫
  在首次进入时触发授权检查，并在无授权时重定向到注册页

## 5. 后端结构

后端代码主要位于 `backend/`，当前可以看作“RPC 入口 + 应用服务 + 领域状态/仓储 + 功能模块”的结构。

### 5.1 目录总览

```text
backend/
  __main__.py
  rpc_server.py
  rpc/
  application/
  domain/
  repository/
  subjects/
  proctoring/
  examroom/
  printing/
  licensing/
  manual/
  resources/
  tests/
```

### 5.2 RPC 与应用服务层

`backend/rpc_server.py` 当前注册的服务主要有：

- `SystemService`
- `LicensingService`
- `DashboardService`
- `SubjectsService`
- `ProctoringService`
- `RoomsService`
- `PrintingService`

这一层的职责是：

- 接收前端请求
- 进行参数编排与流程控制
- 调用领域模块、仓储和文件处理逻辑
- 返回适合前端消费的结构化结果

它是后端对前端的统一边界，前端不直接依赖更深层模块。

### 5.3 领域状态与持久化

状态模型位于：

- `backend/domain/state.py`
- `backend/domain/models.py`

当前 `AppState` 主要承载：

- `subjects`
- `proctoring`
- `rooms`
- `printing`
- `exam_arrangement`

其中：

- `subjects`、`proctoring`、`rooms`、`printing` 是可持久化状态
- `exam_arrangement` 是运行时对象，不直接写入磁盘

状态持久化由 `backend/repository/state_repository.py` 负责，特点包括：

- 默认保存为 JSON
- 带版本号 `VERSION`
- 保存前自动备份旧文件
- 最多保留最近 10 份备份
- 对高考排考结果中的 `DataFrame` 做序列化与反序列化适配

### 5.4 业务模块划分

#### Subjects

位置：

- `backend/application/subjects_service.py`
- `backend/subjects/`

职责：

- 科目导入、更新、导出
- 科目模板生成
- 科目规则校验

它是监考编排和打印模块的重要上游。

#### Proctoring

位置：

- `backend/application/proctoring_service.py`
- `backend/proctoring/`
- `backend/proctoring/core/`

职责：

- 教师导入
- 监考安排生成与继续编排
- 优化与均衡
- 手动交换
- 结果导出与预设导入导出

`backend/proctoring/core/` 已经拆分为多个专职模块，例如：

- `scheduler.py`
- `optimizer.py`
- `swap.py`
- `balance.py`
- `selectors.py`
- `statistics.py`
- `validators.py`
- `postprocess.py`
- `entities.py`
- `models.py`

#### Rooms / Exam Arrangement

位置：

- `backend/application/rooms_service.py`
- `backend/examroom/core/`

职责：

- 考场设置模板生成与导入
- 学生名单导入
- 常规模式与高考模式排考场
- 结果导出与结果回灌

`backend/examroom/core/` 当前已经按策略与导出职责拆分，例如：

- `arrangement.py`
- `sequential_strategy.py`
- `subject_strategy.py`
- `gaokao_helpers.py`
- `gaokao_exports.py`
- `gaokao_defaults.py`
- `standard_exports.py`
- `stats_sheet.py`
- `helpers.py`

`rooms_service.py` 也拆出了一些辅助模块以降低入口文件复杂度：

- `rooms_input_importers.py`
- `rooms_result_importers.py`
- `rooms_templates.py`

#### Printing

位置：

- `backend/application/printing_service.py`
- `backend/printing/`

职责：

- 读取打印数据源
- 根据字段映射生成预览数据
- 从排考结果加载打印数据
- 生成 Excel / PDF 输出
- 校验台贴、座位贴等打印输入

`backend/printing/core/` 目前包含三类关键子模块：

1. `adapters/`
   用于衔接排考结果和打印数据，例如 `examroom_adapter.py`
2. `generators/excel/` 与 `generators/pdf/`
   用于生成准考证、角标、座位贴、考生信息表、试卷袋等输出
3. `validators/` 与 `utils/`
   用于校验输入和加载打印源数据

#### Licensing

位置：

- `backend/application/licensing_service.py`
- `backend/licensing/`

职责：

- 读取机器码
- 校验注册码或证书
- 保存授权证书

授权是整个应用的入口守卫之一，前端在初始化阶段就会访问该模块。

#### System / Help / Manual

位置：

- `backend/application/system_service.py`
- `backend/manual/`
- `backend/resources/`

职责：

- 重置系统数据
- 读取内置帮助文档
- 支持帮助中心的 Markdown 加载、搜索与 PDF 导出能力

这里补足了一个旧文档没有明确写出的事实：帮助中心并不是纯前端静态页，而是“前端渲染 + 后端读取内置手册资源”的组合结构。

## 6. 数据与状态流

当前几个核心模块之间的依赖关系大致如下：

```text
Licensing
  -> 控制应用可用性

Subjects
  -> Proctoring
  -> Printing

Rooms
  -> Printing

System
  -> 重置 Subjects / Proctoring / Rooms / Printing 持久化状态
```

从业务流程看：

1. 先配置考试科目
2. 再进行监考编排和考场编排
3. 最后基于上游结果生成打印资料

`Dashboard` 模块负责把这些状态汇总成首页统计与工作流进度，而不是持有独立业务数据。

## 7. 状态文件、资源和打包

### 7.1 状态文件位置

状态文件由 `backend/rpc_server.py` 中的 `_get_state_file()` 决定，优先读取以下环境变量：

- `EXAMFLOW_DATA_DIR`
- `EXAMDESK_DATA_DIR`
- `EXAMFLOW_APP_DIR`
- `EXAMDESK_APP_DIR`
- `EXAMFLOW_CERT_DIR`
- `EXAMDESK_CERT_DIR`

最终状态文件一般落在：

```text
data/state.json
```

打包环境下，Electron 主进程还会为后端注入 `EXAMFLOW_DATA_DIR` / `EXAMDESK_DATA_DIR`，使状态与证书优先保存在应用用户数据目录。

### 7.2 内置资源

当前仓库中的内置资源主要包括：

- `backend/resources/使用说明书.md`
- `backend/printing/assets/templates/`
- `backend/printing/assets/images/`

这些资源被用于帮助中心、打印模板和示例图。

### 7.3 打包链路

当前打包分为两段：

1. 使用 `frontend/engine.spec` 将 Python 后端构建为 sidecar
2. 使用 `electron-builder` 打包 Electron 安装包

仓库根目录的 `package.py` 用于把这两段流程串起来。

## 8. 当前架构的边界与约束

当前实现明显遵循以下约束：

- 不把业务规则放在 Electron 主进程
- 不让前端页面直接管理 Python 进程
- 不让前端直接读写状态文件
- 通过 application service 保持前后端协议边界稳定
- 通过页面 composables 拆分复杂页面，而不是继续堆大单文件

这意味着后续扩展时，推荐继续遵守同一原则：

- 新业务入口先落到 `application/*_service.py`
- 复杂算法继续下沉到 feature module
- 前端页面优先做编排，逻辑拆到 composables
- 与系统能力相关的逻辑通过 Electron IPC 统一暴露

## 9. 与旧版文档相比的修订重点

本文件现在更强调“当前真实架构”，而不是某一轮重构进度，因此做了这些调整：

- 删除了容易过时的页面行数、文件长度和阶段性拆分统计
- 补充了 `Dashboard`、`Licensing`、`System`、`Help`、`Manual` 等旧文档未完整覆盖的模块
- 补充了状态持久化、备份、环境变量和 sidecar 打包链路
- 用运行时调用链替代“仅按目录列举”的说明方式

如果需要看更细的业务模块职责，建议继续结合 `docs/modules.md` 一起阅读。
