# Easy Exam 前端说明

## 1. 技术栈

前端工程当前使用：

- Vue 3
- TypeScript
- Vite
- Electron
- Pinia
- Vue Router
- Element Plus
- Tailwind CSS
- Vitest

## 2. 目录结构

```text
frontend/
├─ electron/               Electron 主进程与 preload
├─ public/                 静态资源
├─ src/
│  ├─ components/          通用组件
│  ├─ composables/         跨页面复用逻辑
│  ├─ lib/                 RPC、日志、环境工具
│  ├─ stores/              Pinia 状态
│  ├─ types/               RPC 与业务类型定义
│  └─ views/               页面入口、局部组件与 composables
├─ tests/                  Vitest 测试
├─ engine.spec             Python sidecar 打包规格
└─ package.json            前端脚本与 Electron 构建配置
```

## 3. 当前页面结构

主要页面位于 `src/views/`：

- `DashboardPage.vue`
- `RegistrationPage.vue`
- `SubjectsPage.vue`
- `ProctoringPage.vue`
- `RoomsPage.vue`
- `PrintingPage.vue`
- `HelpPage.vue`

复杂页面采用“页面入口 + 同名目录”的组织方式，例如：

- `src/views/SubjectsPage.vue` + `src/views/SubjectsPage/`
- `src/views/ProctoringPage.vue` + `src/views/ProctoringPage/`
- `src/views/RoomsPage.vue` + `src/views/RoomsPage/`
- `src/views/PrintingPage.vue` + `src/views/PrintingPage/`
- `src/views/HelpPage.vue` + `src/views/HelpPage/`

页面 `.vue` 文件主要承担页面编排，复杂逻辑优先拆入 composables 或局部组件。

## 4. 当前关键实现

### 4.1 App Shell

[src/App.vue](/d:/coding%20make%20work%20easy/Easy-Exam/frontend/src/App.vue) 当前负责：

- 左侧导航与页面标题
- 工作流步骤条
- 顶部日期时间
- 用户设置对话框
- 开发者模式开关
- 授权检查后的路由联动

### 4.2 路由

[src/router.ts](/d:/coding%20make%20work%20easy/Easy-Exam/frontend/src/router.ts) 当前路由：

- `/dashboard`
- `/registration`
- `/subjects`
- `/proctoring`
- `/rooms`
- `/printing`
- `/help`

其中：

- `RegistrationPage` 和 `PrintingPage` 使用 `keepAlive`
- `RegistrationPage` 在应用重置时保留

### 4.3 页面拆分

Subjects：

- `useSubjectsData.ts`
- `useSubjectsForm.ts`
- `useSubjectsReset.ts`

Proctoring：

- `useProctoringBootstrap.ts`
- `useProctoringDataManagement.ts`
- `useProctoringOptimizationMetrics.ts`
- `useProctoringScheduling.ts`
- `useProctoringSwap.ts`
- `useProctoringViewData.ts`

Rooms：

- `useRoomsState.ts`
- `useRoomsPersistence.ts`
- `useRoomsIO.ts`
- `useRoomsArrangement.ts`

Printing：

- `usePrintingFileSource.ts`
- `usePrintingDeskLayout.ts`
- `usePrintingGenerate.ts`
- `usePrintingPreview.ts`
- `usePrintingPreviewData.ts`
- `usePrintingScheduleSource.ts`
- `usePrintingSubjects.ts`

Help：

- `useMarkdown.ts`
- `useFullTextSearch.ts`
- `useScrollSpy.ts`
- `useTocGeneration.ts`

## 5. 前后端通信

前端统一通过 [src/lib/pythonBackend.ts](/d:/coding%20make%20work%20easy/Easy-Exam/frontend/src/lib/pythonBackend.ts) 调用 Python 后端。

调用链大致如下：

```text
页面 / composable
  -> pythonBackend.request(...)
  -> preload 暴露的 IPC
  -> Electron 主进程
  -> Python 后端
```

页面不直接管理 Python 进程生命周期。

当前监考编排前端还使用了异步后台任务模式：

- 发起：`proctoring.startSolverJob`
- 轮询：`proctoring.getJobStatus`

## 6. 开发环境配置

安装依赖：

```powershell
npm.cmd install
```

配置 Python 路径：

```env
VITE_PYTHON_PATH=D:/Anaconda3/envs/exam_scheduler/python.exe
```

如果系统已能直接调用 `python`，也可以写为：

```env
VITE_PYTHON_PATH=python
```

## 7. 常用命令

启动开发环境：

```powershell
npm.cmd run dev
```

运行前端测试：

```powershell
npm.cmd run test
```

构建前端资源：

```powershell
npm.cmd run build
```

构建 Electron 安装包：

```powershell
npm.cmd run electron:build
```

## 8. 当前测试入口

当前前端测试位于：

- `tests/subjects/useSubjectsForm.test.ts`
- `tests/proctoring/useProctoringOptimizationMetrics.test.ts`
- `tests/printing/usePrintingDeskLayout.test.ts`

## 9. 打包说明

- `engine.spec` 会把 Python 后端打成 `engine` sidecar
- `package.json` 的 Electron 构建产物输出到 `release_v6/`
- `extraResources` 会把 `python-dist/engine` 打到安装包的 `resources/engine/`

## 10. 相关文档

- [../README.md](../README.md)
- [../docs/architecture.md](../docs/architecture.md)
- [../docs/modules.md](../docs/modules.md)
- [../docs/development.md](../docs/development.md)
- [../docs/testing-and-release.md](../docs/testing-and-release.md)
- [../docs/前端设计要求](../docs/前端设计要求)
