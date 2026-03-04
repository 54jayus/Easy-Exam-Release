# Easy Exam 前端开发指南

## 环境配置

### 1. 安装 Node.js 依赖

```bash
npm install
```

### 2. 配置 Python 环境

复制 `.env.development.example` 为 `.env.development`：

```bash
cp .env.development.example .env.development
```

然后编辑 `.env.development`，设置你本地的 Python 路径：

**使用 Conda 环境（推荐）：**
```
VITE_PYTHON_PATH=D:/Anaconda3/envs/exam_scheduler/python.exe
```

**或使用系统 Python：**
```
VITE_PYTHON_PATH=python
```

### 3. 安装 Python 依赖

进入 backend 目录安装依赖：

```bash
pip install -r ../backend/requirements.txt
```

或在 Conda 环境中：

```bash
conda activate exam_scheduler
pip install -r ../backend/requirements.txt
```

### 4. 启动开发服务器

```bash
npm run dev
```

## 打包

```bash
npm run electron:build
```
