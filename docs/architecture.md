# 架构说明

## 1. 总体结构

Easy Exam 是一个桌面端应用，采用 `Electron + Vue 3 + Python` 的分层结构。

- Electron 主进程负责窗口、IPC、日志、系统能力和 Python 子进程管理。
- Vue 前端负责页面交互、状态展示、用户操作编排。
- Python 后端负责业务规则、Excel 处理、导出、打印和状态持久化。

整体调用链如下：

```text
用户操作
  -> Vue 页面 / composable / 组件
  -> frontend/src/lib/pythonBackend.ts
  -> Electron 主进程拉起并管理 Python 进程
  -> backend/rpc_server.py 分发 RPC
  -> application service
  -> domain / examroom / proctoring / printing 等核心模块
  -> 结果返回前端
```

## 2. 前端结构

前端代码主要位于 `frontend/src/`。

### 2.1 页面入口

当前主要页面包括：

- `DashboardPage.vue`
- `RegistrationPage.vue`
- `SubjectsPage.vue`
- `ProctoringPage.vue`
- `RoomsPage.vue`
- `PrintingPage.vue`
- `HelpPage.vue`

### 2.2 当前推荐组织方式

经过本轮重构，项目已经逐步形成“页面入口 + 同名目录 + composables”的结构。

典型模式如下：

```text
views/
  PrintingPage.vue
  PrintingPage/
    composables/
  ProctoringPage.vue
  ProctoringPage/
    composables/
  SubjectsPage.vue
  SubjectsPage/
    composables/
    types.ts
```

页面本身主要负责：

- 页面级状态编排
- 生命周期接线
- 模板渲染
- composable 之间的协调

复杂逻辑优先下沉到 composable，例如：

- 数据加载与导入导出
- 日志处理
- 预览数据加工
- 座位布局与计算
- 智能排监考流程编排
- 页面重置与状态清理

### 2.3 当前重构结果

当前几个主要前端热点已经收敛到以下状态：

- `frontend/src/views/PrintingPage.vue` 约 `1617` 行
  已拆出 `usePrintingSubjects`、`usePrintingPreview`、`usePrintingFileSource`、`usePrintingGenerate`、`usePrintingPreviewData`、`usePrintingDeskLayout`、`usePrintingScheduleSource`
  并已拆出 `PrintingMappingDialog`、`PrintingSubjectsDialog`、`PrintingDeskLayoutDialog`
- `frontend/src/views/ProctoringPage.vue` 约 `964` 行
  已拆出 `useProctoringDataManagement`、`useProctoringViewData`、`useProctoringBootstrap`、`useProctoringOptimizationMetrics`、`useProctoringScheduling`、`useProctoringSwap`
- `frontend/src/views/SubjectsPage.vue` 约 `532` 行
  已拆出 `useSubjectsLogs`、`useSubjectsData`、`useSubjectsForm`、`useSubjectsReset`

这说明前端已经从“重业务页全堆在单文件”过渡到“页面编排层 + composable 逻辑层”的结构。

同时，前端工程层也已经补上：

- 路由懒加载
- `manualChunks` 拆包
- `Vitest` 最小单测基线

## 3. 前端与后端通信

`frontend/src/lib/pythonBackend.ts` 封装了前端调用后端的 RPC 客户端，负责：

- 启动和连接 Python 后端
- 管理请求序号与超时
- 监听 stdout / stderr
- 解析 JSON-RPC 风格响应
- 在后端退出时清理挂起请求

前端页面不直接接触 Python 进程管理，统一通过 `pythonBackend.request(...)` 发起调用。

## 4. 后端结构

后端主要分成四层：

- `backend/application/`
  对外服务入口，负责 RPC 对应的应用服务编排
- `backend/proctoring/`
  监考编排核心逻辑
- `backend/examroom/`
  考场编排核心逻辑
- `backend/printing/`
  打印、导出和适配器逻辑

### 4.1 proctoring 当前结构

`backend/proctoring/core/` 当前已经拆分为：

- `entities.py`
- `balance.py`
- `selectors.py`
- `swap.py`
- `optimizer.py`
- `postprocess.py`
- `scheduler.py`
- `statistics.py`
- `validators.py`
- `models.py`

其中：

- `models.py` 当前约 `145` 行，主要保留兼容入口
- 原本超大的调度、优化、交换、统计和校验逻辑已经拆出

### 4.2 examroom 当前结构

`backend/examroom/core/` 当前已经拆分为：

- `helpers.py`
- `gaokao_helpers.py`
- `gaokao_exports.py`
- `sequential_strategy.py`
- `subject_strategy.py`
- `standard_exports.py`
- `stats_sheet.py`
- `arrangement.py`

其中：

- `arrangement.py` 当前约 `303` 行
- 高考辅助、高考导出、顺序策略、选科策略、普通导出都已经拆出

### 4.3 application service 当前结构

`backend/application/rooms_service.py` 当前约 `313` 行，并已拆出：

- `rooms_input_importers.py`
- `rooms_result_importers.py`
- `rooms_templates.py`

说明 `application service` 也在逐步回到“入口编排层”的定位。

## 5. 当前仍需继续优化的地方

虽然主结构已经明显变清晰，但后续仍有一些“可继续优化”而非“尚未完成”的方向：

- `PrintingPage.vue` 仍然是当前前端最大页面，后续还可以继续细化子组件
- 前端自动化测试已经起步，但覆盖面仍可继续扩大
- 打包脚本已改成环境变量优先，后续还可以继续接入 CI
- `element-plus` 相关 chunk 仍偏大，后续可继续做包体治理

## 6. 当前的重构边界

本轮优化遵循同一原则：

- 只做架构调整
- 不修改 RPC 名称与参数结构
- 不修改业务规则
- 不修改导入导出语义
- 不修改排序、分配、打印结果语义
- 每一轮拆分后都先过构建和相关测试
