# 业务模块说明

## 1. 模块总览

当前产品的主流程可以概括为：

1. 配置考试科目
2. 编排监考
3. 编排考场
4. 生成与打印资料
5. 管理授权
6. 在帮助中心查看内置说明

## 2. Dashboard

前端页面：

- `frontend/src/views/DashboardPage.vue`

后端服务：

- `backend/application/dashboard_service.py`

职责：

- 汇总系统状态
- 展示工作流完成度
- 展示科目、监考、考场、打印等摘要信息

## 3. Subjects

前端页面：

- `frontend/src/views/SubjectsPage.vue`
- `frontend/src/views/SubjectsPage/composables/`

后端服务：

- `backend/application/subjects_service.py`

职责：

- 导入和维护考试科目
- 校验科目时间冲突
- 导出科目数据
- 为监考和打印模块提供基础科目数据

当前前端已拆出的核心 composable：

- `useSubjectsLogs.ts`
- `useSubjectsData.ts`
- `useSubjectsForm.ts`
- `useSubjectsReset.ts`

## 4. Proctoring

前端页面：

- `frontend/src/views/ProctoringPage.vue`
- `frontend/src/views/ProctoringPage/composables/`

后端服务：

- `backend/application/proctoring_service.py`
- `backend/proctoring/core/`

职责：

- 导入教师数据
- 生成监考安排
- 继续编排与优化
- 手动交换监考
- 导出监考结果

当前前端已拆出的核心 composable：

- `useProctoringBootstrap.ts`
- `useProctoringDataManagement.ts`
- `useProctoringOptimizationMetrics.ts`
- `useProctoringScheduling.ts`
- `useProctoringSwap.ts`
- `useProctoringViewData.ts`

当前后端已拆出的核心模块：

- `entities.py`
- `balance.py`
- `selectors.py`
- `swap.py`
- `optimizer.py`
- `validators.py`
- `statistics.py`
- `postprocess.py`
- `scheduler.py`

## 5. Rooms / Exam Arrangement

前端页面：

- `frontend/src/views/RoomsPage.vue`
- `frontend/src/views/RoomsPage/composables/`

后端服务：

- `backend/application/rooms_service.py`
- `backend/examroom/core/`

职责：

- 导入考场设置
- 导入学生名单
- 按不同模式编排考场
- 导出考场结果
- 为打印模块提供下游结果

当前 `backend/examroom/core/` 的核心结构：

- `arrangement.py`
- `helpers.py`
- `gaokao_helpers.py`
- `gaokao_exports.py`
- `sequential_strategy.py`
- `subject_strategy.py`
- `standard_exports.py`
- `stats_sheet.py`

当前 `rooms_service.py` 已拆出的辅助模块：

- `rooms_input_importers.py`
- `rooms_result_importers.py`
- `rooms_templates.py`

## 6. Printing

前端页面：

- `frontend/src/views/PrintingPage.vue`
- `frontend/src/views/PrintingPage/composables/`

后端服务：

- `backend/application/printing_service.py`
- `backend/printing/`

职责：

- 读取打印数据源
- 加工预览数据
- 生成准考证、角标、座位贴、试卷袋等打印内容
- 与考场结果适配

当前前端已拆出的核心 composable：

- `usePrintingSubjects.ts`
- `usePrintingPreview.ts`
- `usePrintingFileSource.ts`
- `usePrintingGenerate.ts`
- `usePrintingPreviewData.ts`
- `usePrintingDeskLayout.ts`
- `usePrintingScheduleSource.ts`

当前前端已拆出的模板子组件：

- `components/PrintingMappingDialog.vue`
- `components/PrintingSubjectsDialog.vue`
- `components/PrintingDeskLayoutDialog.vue`

## 7. Licensing

前端页面：

- `frontend/src/views/RegistrationPage.vue`

后端服务：

- `backend/application/licensing_service.py`
- `backend/licensing/`

职责：

- 读取机器码
- 校验授权
- 注册授权

## 8. Help

前端页面：

- `frontend/src/views/HelpPage.vue`

职责：

- 提供内置帮助
- 汇总使用说明入口

## 9. 模块依赖关系

业务依赖大致如下：

```text
Subjects
  -> Proctoring
  -> Printing

Rooms / Exam Arrangement
  -> Printing

Licensing
  -> 全局启动与授权检查
```

也就是说：

- 科目是监考与打印的上游
- 考场结果是打印的重要上游
- 授权影响整个应用的可用性
