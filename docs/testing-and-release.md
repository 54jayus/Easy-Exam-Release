# 测试与发布说明

## 1. 测试入口总览

当前仓库的主要测试入口有两类：

- 前端：`frontend/tests/`，使用 `vitest`
- 后端：`backend/tests/`，使用 `pytest`

发布前建议同时做前端验证、后端验证和打包验证，而不是只跑其中一项。

## 2. 前端验证

在 `frontend/` 目录下执行：

```powershell
npm.cmd run test
npm.cmd run build
```

当前前端测试主要覆盖：

- `SubjectsPage` 表单逻辑
- `ProctoringPage` 优化指标逻辑
- `PrintingPage` 座位布局逻辑

如果改动影响路由、状态缓存、打印预览或页面编排，除了单测外，建议再做一次桌面端手动回归。

## 3. 后端验证

### 3.1 全量测试

在仓库根目录下执行：

```powershell
$env:PYTHONPATH='.'
pytest
```

`pytest.ini` 已将默认测试路径收敛到 `backend/tests/`。

### 3.2 按模块定向执行

科目相关：

```powershell
$env:PYTHONPATH='.'
pytest backend/tests/test_subjects_service.py backend/tests/test_subjects_excel.py
```

监考相关：

```powershell
$env:PYTHONPATH='.'
pytest backend/tests/test_proctoring_service.py backend/tests/test_proctoring_scheduler.py backend/tests/test_proctoring_optimizer.py backend/tests/test_proctoring_postprocess.py backend/tests/test_proctoring_validators.py
```

考场相关：

```powershell
$env:PYTHONPATH='.'
pytest backend/tests/test_rooms_service.py backend/tests/test_rooms_arrange_flow.py backend/tests/test_rooms_export_flow.py backend/tests/test_exam_arrangement.py backend/tests/test_exam_arrangement_gaokao_exports.py
```

打印相关：

```powershell
$env:PYTHONPATH='.'
pytest backend/tests/test_printing_service.py backend/tests/test_printing_excel_generators.py backend/tests/test_printing_examroom_adapter.py backend/tests/test_pdf_export.py
```

系统、授权与状态：

```powershell
$env:PYTHONPATH='.'
pytest backend/tests/test_licensing_service.py backend/tests/test_license_manager.py backend/tests/test_cert_store.py backend/tests/test_state_repository.py backend/tests/test_system_service.py backend/tests/test_dashboard_service.py
```

## 4. 自检与冒烟验证

如果准备发布安装包，建议额外执行：

```powershell
$env:PYTHONPATH='.'
python -m backend.selfcheck
```

这个脚本会验证：

- 后端关键模块是否能导入
- 打印生成器是否能完成一次最小输出
- 基础运行环境是否满足后端启动要求

此外，建议在桌面端手动走一遍以下最小业务闭环：

1. 打开应用并完成授权状态检查
2. 导入或维护科目
3. 导入教师并生成监考安排
4. 导入学生并完成考场编排
5. 打开打印页面，完成一次预览和一次导出

## 5. 打包流程

当前推荐的正式打包方式是：

```powershell
python package.py
```

`package.py` 会执行两段流程：

1. 使用 `frontend/engine.spec` 构建 Python sidecar
2. 调用 `npm.cmd run electron:build` 构建 Electron 安装包

打包前建议确认：

- `EXAM_PYTHON_PATH` 或 `VITE_PYTHON_PATH` 指向可用 Python
- 前端依赖和后端依赖都已安装
- 没有正在运行的旧版应用占用输出目录

## 6. 发布前检查清单

发布前至少确认以下项目：

- `npm.cmd run test` 通过
- `npm.cmd run build` 通过
- `pytest` 通过，或已明确记录未执行范围
- `python -m backend.selfcheck` 通过
- 应用启动后能连接 Python 后端
- 授权页面能读取机器码、校验并保存证书
- 科目导入导出正常
- 监考生成、优化、交换正常
- 考场编排、导出和结果导入正常
- 打印预览与生成正常

## 7. 关于构建输出的说明

如果前端构建时出现包体大小提醒，应将其视为后续优化信号，而不是自动判定发布失败。是否阻塞发布，应以实际启动速度、页面加载和桌面端可用性为准。

## 8. 文档维护约定

测试与发布文档应始终描述当前仓库真实可执行的命令、脚本和检查项。阶段性治理策略、历史重构节奏和旧打包方案，统一保留在 `docs/archive/plans/` 中。
