# Easy Exam 前端开发说明

## 环境配置

### 1. 安装 Node.js 依赖

```bash
npm install
```

### 2. 配置 Python 环境

复制 `.env.development.example` 为 `.env.development`：

```bash
copy .env.development.example .env.development
```

然后设置本地 Python 路径：

```env
VITE_PYTHON_PATH=D:/Anaconda3/envs/exam_scheduler/python.exe
```

如果系统环境里直接可用 `python`，也可以写：

```env
VITE_PYTHON_PATH=python
```

### 3. 安装 Python 依赖

```bash
pip install -r ../backend/requirements.txt
```

## 启动开发环境

```bash
npm run dev
```

## 构建检查

在 PowerShell 下建议使用：

```bash
npm.cmd run build
```

## 当前前端结构

简单页面直接使用单个 `*.vue` 文件。

复杂页面使用“页面入口 + 同名目录”的方式拆分，例如：

- `src/views/RoomsPage.vue` + `src/views/RoomsPage/`
- `src/views/HelpPage.vue` + `src/views/HelpPage/`
- `src/views/PrintingPage.vue` + `src/views/PrintingPage/composables/`

其中 `PrintingPage` 当前已拆成：

- `usePrintingFileSource.ts`
- `usePrintingPreview.ts`
- `usePrintingPreviewData.ts`
- `usePrintingGenerate.ts`
- `usePrintingSubjects.ts`
- `usePrintingDeskLayout.ts`
- `usePrintingScheduleSource.ts`

如果继续维护打印页，优先把 `PrintingPage.vue` 当作页面编排层，再按职责进入对应 composable 排查。
