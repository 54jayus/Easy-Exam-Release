# 测试与发布说明

## 1. 测试原则

当前项目的重构策略是：

- 先拆结构
- 不改业务逻辑
- 每一轮都做最小可验证闭环

因此测试分为两层：

- 构建验证
- 模块定向测试

## 2. 前端验证

前端最低要求：

```bash
cd frontend
npm.cmd run test
npm.cmd run build
```

当前前端已经具备最小单测基线和路由拆包能力。构建可以通过，但会保留既有的 chunk size warning。这是现有包体偏大的提醒，不表示本轮重构失败。

## 3. 后端定向测试

### 3.1 监考模块

```bash
$env:PYTHONPATH='.'
pytest backend/tests/test_proctoring_service.py backend/tests/test_rpc_dispatcher.py
```

如果本轮改动触及调度、优化、后处理或校验，还应补跑：

```bash
$env:PYTHONPATH='.'
pytest backend/tests/test_proctoring_scheduler.py backend/tests/test_proctoring_postprocess.py backend/tests/test_proctoring_optimizer.py backend/tests/test_proctoring_validators.py
```

### 3.2 考场模块

```bash
$env:PYTHONPATH='.'
pytest backend/tests/test_rooms_service.py backend/tests/test_rooms_arrange_flow.py backend/tests/test_rooms_export_flow.py
```

如果本轮改动触及编排核心或高考导出，还应补跑：

```bash
$env:PYTHONPATH='.'
pytest backend/tests/test_exam_arrangement.py backend/tests/test_exam_arrangement_gaokao_exports.py backend/tests/test_printing_examroom_adapter.py
```

### 3.3 打印模块

如果改动触及打印服务、打印预览适配或导出生成，应补跑对应打印测试。

## 4. 当前测试策略

### 4.1 characterization tests

对于高风险重构，优先补“特征测试”，目的不是证明算法最优，而是锁定：

- 输入不变时输出结构不变
- 关键错误提示不变
- 关键排序、映射、分配结果不变

### 4.2 每轮重构的最低闭环

每一轮应至少满足：

1. 代码拆分完成
2. 原入口仍可用
3. 前端构建通过
4. 对应后端测试通过
5. 文档同步更新

## 5. 发布前检查

发布前建议至少确认：

- 授权校验正常
- 科目导入、导出正常
- 监考生成、优化、交换正常
- 考场编排与导出正常
- 打印页预览、生成、导出正常
- Electron 主进程与 Python 后端能正常连接

## 6. 打包注意事项

当前 `package.py` 已完成本轮环境变量化，优先按以下顺序解析 Python：

- `EXAM_PYTHON_PATH`
- `VITE_PYTHON_PATH`
- `sys.executable`
- `python` in PATH

因此在换机或 CI 环境下，优先确认：

- Python 路径是否可用
- 打包命令是否能找到正确解释器
- 授权证书路径在打包态是否正确

## 7. 当前已知风险

当前不是功能风险，而是工程风险更值得注意：

- `element-plus` 相关 chunk 仍偏大
- 前端自动化测试基线已建立，但覆盖率仍偏低
- 仓库临时产物管理已收紧，但输出目录仍可继续统一
