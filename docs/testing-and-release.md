# 测试与发布说明

## 1. 测试入口概览

当前仓库的主要测试入口分为两类：

- 前端：`frontend/tests/`，使用 `vitest`
- 后端：`backend/tests/`，使用 `pytest`

发布前建议同时完成前端验证、后端验证、自检和一次打包验证，而不是只跑其中一项。

## 2. 前端验证

在 `frontend/` 目录执行：

```powershell
npm.cmd run test
npm.cmd run build
```

当前前端测试覆盖：

- `frontend/tests/subjects/useSubjectsForm.test.ts`
- `frontend/tests/proctoring/useProctoringOptimizationMetrics.test.ts`
- `frontend/tests/printing/usePrintingDeskLayout.test.ts`

如果改动涉及路由、缓存恢复、打印预览、帮助中心滚动或 Electron 交互，除单测外建议额外做一次桌面端手动回归。

## 3. 后端验证

### 3.1 全量测试

在仓库根目录执行：

```powershell
$env:PYTHONPATH='.'
pytest
```

`pytest.ini` 已把默认测试路径指向 `backend/tests/`。

### 3.2 按模块执行

科目相关：

```powershell
$env:PYTHONPATH='.'
pytest backend/tests/test_subjects_service.py backend/tests/test_subjects_excel.py
```

监考相关：

```powershell
$env:PYTHONPATH='.'
pytest backend/tests/test_proctoring_service.py backend/tests/test_proctoring_jobs.py backend/tests/test_proctoring_validators.py backend/tests/test_cp_sat_solver.py
```

考场相关：

```powershell
$env:PYTHONPATH='.'
pytest backend/tests/test_rooms_service.py backend/tests/test_rooms_imports_and_templates.py backend/tests/test_rooms_arrange_flow.py backend/tests/test_rooms_export_flow.py backend/tests/test_exam_arrangement.py backend/tests/test_exam_arrangement_gaokao_exports.py
```

打印相关：

```powershell
$env:PYTHONPATH='.'
pytest backend/tests/test_printing_service.py backend/tests/test_printing_excel_generators.py backend/tests/test_printing_examroom_adapter.py backend/tests/test_data_loader_and_desk_validator.py backend/tests/test_generator_factory.py backend/tests/test_pdf_export.py
```

系统、授权、状态与帮助中心：

```powershell
$env:PYTHONPATH='.'
pytest backend/tests/test_licensing_service.py backend/tests/test_license_manager.py backend/tests/test_cert_store.py backend/tests/test_state_repository.py backend/tests/test_state_repository_edges.py backend/tests/test_system_service.py backend/tests/test_system_service_edges.py backend/tests/test_dashboard_service.py backend/tests/test_manual_loader.py backend/tests/test_manual_markdown_edges.py backend/tests/test_manual_search_edges.py backend/tests/test_manual_utils.py
```

## 4. 自检与冒烟验证

发布前建议额外执行：

```powershell
$env:PYTHONPATH='.'
python -m backend.selfcheck
```

该脚本会验证：

- 关键后端模块能否正常导入
- 打印生成器能否完成一次最小输出
- 基础运行环境是否满足后端启动要求

此外，建议手动完成一次最小业务闭环：

1. 打开应用并完成授权状态检查
2. 导入或维护科目
3. 导入教师并完成监考编排
4. 导入名册并完成考场编排
5. 打开资料打印页完成一次预览与生成
6. 打开帮助中心确认说明书可读取和搜索

## 5. 打包流程

当前推荐的正式打包方式：

```powershell
python package.py
```

`package.py` 会依次执行：

1. 清理 `frontend/python-dist/`、`frontend/build-python/`、`frontend/release_v6/`
2. 使用 `frontend/engine.spec` 构建 Python sidecar
3. 调用 `npm.cmd run electron:build` 构建 Electron 安装包

当前真实约束：

- `frontend/package.json` 将 Electron 输出目录固定为 `release_v6`
- sidecar 构建依赖 `ortools` 与 PyInstaller

## 6. 发布前检查清单

- `npm.cmd run test` 通过
- `npm.cmd run build` 通过
- `pytest` 通过，或已明确记录未执行范围
- `python -m backend.selfcheck` 通过
- 应用启动后能成功连接 Python 后端
- 注册页能读取机器码并完成授权校验
- 科目导入、导出、校验正常
- 监考编排、补全、手动交换、导出正常
- 考场编排、导入结果、导出正常
- 打印预览与生成正常
- 帮助中心加载与搜索正常

## 7. 关于构建告警

前端构建过程如果出现体积提醒，应将其视为优化信号，而不是自动判定发布失败。是否阻塞发布，应以实际启动速度、页面加载与桌面端可用性为准。

## 8. 文档维护约定

测试与发布文档只记录当前仓库真实存在的测试文件、命令和打包脚本。历史打包方案和阶段性改造记录统一归档到 `docs/archive/plans/`。
