# 代码架构优化方案（2026-04-07，更新至 2026-04-08）

## 1. 目标与边界

本轮优化的目标是：

- 降低超大文件的维护成本
- 提升模块边界清晰度
- 保持现有业务逻辑、数据语义、导出结果、排序规则与交互行为不变
- 在每个阶段都保持可测试、可回滚、可验证

本轮优化明确不做以下事情：

- 不新增业务功能
- 不修改业务规则
- 不改 RPC 方法名、请求结构、返回结构
- 不改变导入、编排、导出、打印的业务语义
- 不把“顺手优化”型需求夹带进结构重构

一句话原则：

> 只做架构重组、职责拆分、代码迁移与测试加固，不做业务行为修改。

## 2. 测试守护策略

### 2.1 每轮的最低验证要求

每轮重构至少执行：

- 前端：`cd frontend && npm.cmd run build`
- 后端：按改动模块执行定向 `pytest`

### 2.2 高风险模块优先补特征测试

对于高风险模块，先补 characterization tests，再做拆分。目标是锁定：

- 输入不变时输出结构不变
- 关键错误信息不变
- 关键排序、映射、分配结果不变

### 2.3 阶段完成标准

某一阶段只有满足以下条件后才算完成：

1. 代码已完成拆分
2. 原有入口保持不变
3. 构建通过
4. 相关测试通过
5. 文档同步更新

## 3. 当前阶段划分

当前按以下顺序推进：

1. 前端 `ProctoringPage.vue`
2. 后端 `backend/proctoring/core/models.py`
3. 后端 `backend/examroom/core/arrangement.py`
4. 后端 `backend/application/rooms_service.py`
5. 前端 `SubjectsPage.vue`
6. 前端 `PrintingPage.vue` 模板层与工程化收尾

## 3.1 完成状态说明

这份计划文档里的事项已经全部完成。

当前已经完成的是：

- `ProctoringPage.vue` 的核心脚本拆分
- `backend/proctoring/core/models.py` 的分层拆分
- `backend/examroom/core/arrangement.py` 的分层拆分
- `backend/application/rooms_service.py` 的入口层收敛
- `SubjectsPage.vue` 的脚本层拆分
- `PrintingPage.vue` 的模板层子组件化
- 前端 composable 级自动化测试补齐
- 路由懒加载和 chunk 拆分
- `package.py` 的环境变量化与打包链路治理
- `.gitignore` 与导出目录规范收尾

## 4. 已完成进度

### 4.1 PrintingPage

当前结果：

- `frontend/src/views/PrintingPage.vue` 约 `1617` 行

已拆出的 composable：

- `usePrintingSubjects.ts`
- `usePrintingPreview.ts`
- `usePrintingFileSource.ts`
- `usePrintingGenerate.ts`
- `usePrintingPreviewData.ts`
- `usePrintingDeskLayout.ts`
- `usePrintingScheduleSource.ts`

已拆出的模板子组件：

- `components/PrintingMappingDialog.vue`
- `components/PrintingSubjectsDialog.vue`
- `components/PrintingDeskLayoutDialog.vue`

已完成的重构重点：

- 科目与时间管理拆出
- 预览缩放与拖拽拆出
- 文件数据源、字段映射、缓存拆出
- 生成导出流程拆出
- 预览数据加工拆出
- 座位布局与编排加载拆出
- 字段映射、科目设置、座位布局 3 个模板弹窗子组件化
- 修复 `PrintingPage` 与其子组件中的历史乱码，恢复到可构建、可维护状态

### 4.2 ProctoringPage

当前结果：

- `frontend/src/views/ProctoringPage.vue` 约 `964` 行

已拆出的 composable：

- `useProctoringBootstrap.ts`
- `useProctoringDataManagement.ts`
- `useProctoringOptimizationMetrics.ts`
- `useProctoringScheduling.ts`
- `useProctoringSwap.ts`
- `useProctoringViewData.ts`

已完成的重构重点：

- 页面启动与状态恢复拆出
- 导入导出、模板、预设与清理拆出
- 智能排监考与优化流程编排拆出
- 手动调换监考交互拆出
- 页面派生视图状态拆出

验证方式：

- `npm.cmd run build`
- `$env:PYTHONPATH='.'; pytest backend/tests/test_proctoring_service.py backend/tests/test_rpc_dispatcher.py`

### 4.3 proctoring 后端核心

当前结果：

- `backend/proctoring/core/models.py` 约 `145` 行

已拆出的模块：

- `entities.py`
- `balance.py`
- `selectors.py`
- `swap.py`
- `optimizer.py`
- `validators.py`
- `statistics.py`
- `postprocess.py`
- `scheduler.py`

已完成的重构重点：

- 监考实体拆分
- 平衡与角色分配拆分
- 教师选择器拆分
- 手动交换逻辑拆分
- 优化后处理拆分
- 预设房间后处理拆分
- 可行性与完整性校验拆分
- 统计输出拆分
- 生成与继续编排主流程拆分

补充测试：

- `test_proctoring_optimizer.py`
- `test_proctoring_postprocess.py`
- `test_proctoring_validators.py`
- `test_proctoring_scheduler.py`

### 4.4 examroom 后端核心

当前结果：

- `backend/examroom/core/arrangement.py` 约 `303` 行

已拆出的模块：

- `helpers.py`
- `gaokao_helpers.py`
- `gaokao_exports.py`
- `sequential_strategy.py`
- `subject_strategy.py`
- `standard_exports.py`

已完成的重构重点：

- 基础辅助函数拆分
- 高考辅助逻辑拆分
- 高考导出拆分
- 顺序编排策略拆分
- 选科编排策略拆分
- 普通导出拆分

补充测试：

- `test_exam_arrangement.py`
- `test_exam_arrangement_gaokao_exports.py`
- `test_printing_examroom_adapter.py`

### 4.5 rooms_service

当前结果：

- `backend/application/rooms_service.py` 约 `313` 行

已拆出的模块：

- `rooms_input_importers.py`
- `rooms_result_importers.py`
- `rooms_templates.py`

已完成的重构重点：

- 输入导入拆分
- 结果导入拆分
- 模板生成拆分

### 4.6 SubjectsPage

当前结果：

- `frontend/src/views/SubjectsPage.vue` 约 `532` 行

已拆出的文件：

- `types.ts`
- `useSubjectsLogs.ts`
- `useSubjectsData.ts`
- `useSubjectsForm.ts`
- `useSubjectsReset.ts`

已完成的重构重点：

- 日志抽屉与后端日志监听拆出
- `subjects.list / update / validate / import / export / template` 这一组数据 IO 拆出
- 表单状态、校验规则、时间联动、增删改提交流程拆出
- 清空导入、页面初始化、状态失效同步流程拆出
- 修复页面模板中历史遗留的坏标签和坏属性，恢复到可构建状态

验证方式：

- `cd frontend && npm.cmd run build`

### 4.7 前端工程化与测试收尾

已完成的工程化项：

- `frontend/src/router.ts` 已改为路由懒加载
- `frontend/vite.config.ts` 已补充 `manualChunks`
- `frontend/package.json` 已增加 `npm.cmd run test`
- `frontend/vitest.config.ts` 与 `frontend/tests/` 已建立最小前端单测基线
- `package.py` 已改为优先读取 `EXAM_PYTHON_PATH` / `VITE_PYTHON_PATH`
- `.gitignore` 已补充 `frontend/debug.log.*` 与导出文件忽略规则

当前已补的前端测试：

- `frontend/tests/printing/usePrintingDeskLayout.test.ts`
- `frontend/tests/proctoring/useProctoringOptimizationMetrics.test.ts`
- `frontend/tests/subjects/useSubjectsForm.test.ts`

## 5. 当前状态总结

到目前为止，这轮架构优化已经完成了既定目标：

- 前端最重的三个页面都已经不再是“全逻辑堆在单文件里”
- `proctoring` 和 `examroom` 两个最核心后端热点都已明显分层
- `rooms_service` 已从混合服务文件回到入口编排层
- `PrintingPage` 已从“重脚本 + 重模板”进一步收敛到“页面编排层 + composable + 子组件”
- 前端已经具备最小单测能力，工程化收尾项已落地
- 所有重构都保持在“结构调整，不改业务逻辑”的边界内

## 6. 后续可选优化方向

### 6.1 PrintingPage 继续细化

当前 `PrintingPage` 已完成关键模板子组件化；如果后续继续治理，可再考虑把：

- 预览区
- 配置区
- 更细粒度的表单分区

继续拆成子组件，让页面进一步向“轻页面 + 视图片区块”过渡。

### 6.2 前端测试扩展

当前已建立 `Vitest` 基线；如果继续扩展，建议优先补：

- `PrintingPage` 其余 composable
- `ProctoringPage` 的数据编排 composable
- `SubjectsPage` 的数据导入导出 composable

### 6.3 构建体积治理

当前已经完成懒加载与 chunk 拆分，但 `element-plus` 相关 chunk 仍偏大。后续可继续治理：

- `element-plus` 按需优化
- 更细的 vendor chunk 策略
- 发布态体积监控

### 6.4 打包与仓库卫生

当前 `package.py` 和 `.gitignore` 已完成本轮目标；后续如继续工程化，可考虑：

- 把导出产物统一收敛到固定输出目录
- 为打包链路补 CI / 发布前检查脚本

## 7. 当前结论

这轮重构已经完成既定收口，证明项目可以在不改业务逻辑的前提下持续完成大规模结构治理。后续如果继续推进，不需要推倒重来，只需要继续按同样的方法扩展：

1. 锁定一个热点
2. 先补验证
3. 小步拆分
4. 构建与测试通过
5. 同步文档
