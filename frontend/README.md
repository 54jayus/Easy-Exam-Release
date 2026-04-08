# Easy Exam 前端说明

## 1. 技术栈

前端工程采用：

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
├─ electron/              Electron 主进程与 preload
├─ public/                静态资源
├─ src/
│  ├─ components/         通用组件
│  ├─ composables/        跨页面复用逻辑
│  ├─ lib/                RPC、日志、环境工具
│  ├─ stores/             Pinia 状态
│  ├─ types/              类型定义
│  └─ views/              页面入口与页面局部模块
├─ tests/                 Vitest 测试
├─ engine.spec            Python sidecar 打包规格
└─ package.json           前端脚本与 Electron 构建配置
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

页面 `.vue` 文件主要承担页面级编排，复杂逻辑优先放进 composables 或页面局部组件。

## 4. 开发环境配置

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

## 5. 常用命令

启动开发环境：

```powershell
npm.cmd run dev
```

运行前端测试：

```powershell
npm.cmd run test
```

构建前端与 Electron 产物：

```powershell
npm.cmd run build
```

构建安装包：

```powershell
npm.cmd run electron:build
```

## 6. 前后端通信

前端统一通过 `src/lib/pythonBackend.ts` 调用 Python 后端。

调用链大致如下：

```text
页面 / composable
  -> pythonBackend.request(...)
  -> preload 暴露的 IPC
  -> Electron 主进程
  -> Python 后端
```

页面不直接管理 Python 进程生命周期。

## 7. 当前测试入口

当前前端测试位于：

- `tests/subjects/useSubjectsForm.test.ts`
- `tests/proctoring/useProctoringOptimizationMetrics.test.ts`
- `tests/printing/usePrintingDeskLayout.test.ts`

## 8. 相关文档

- [../README.md](../README.md)
- [../docs/architecture.md](../docs/architecture.md)
- [../docs/development.md](../docs/development.md)
- [../docs/前端设计要求](../docs/前端设计要求)
