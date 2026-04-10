# 业务模块说明

## 1. 工作流概览

Easy Exam 当前围绕以下工作流组织：

1. 配置考试科目
2. 编排监考
3. 编排考场
4. 生成打印资料
5. 管理授权
6. 查阅帮助中心

前端页面主要位于 `frontend/src/views/`，后端服务边界主要位于 `backend/application/`。

## 2. Dashboard

前端入口：

- [frontend/src/views/DashboardPage.vue](/d:/coding%20make%20work%20easy/Easy-Exam/frontend/src/views/DashboardPage.vue)

后端入口：

- [backend/application/dashboard_service.py](/d:/coding%20make%20work%20easy/Easy-Exam/backend/application/dashboard_service.py)

职责：

- 汇总科目、监考、考场、打印的状态
- 展示工作流进度和统计卡片
- 提供系统重置快捷入口

主要 RPC：

- `dashboard.getStats`

## 3. Licensing / Registration

前端入口：

- [frontend/src/views/RegistrationPage.vue](/d:/coding%20make%20work%20easy/Easy-Exam/frontend/src/views/RegistrationPage.vue)
- [frontend/src/stores/license.ts](/d:/coding%20make%20work%20easy/Easy-Exam/frontend/src/stores/license.ts)

后端入口：

- [backend/application/licensing_service.py](/d:/coding%20make%20work%20easy/Easy-Exam/backend/application/licensing_service.py)
- `backend/licensing/`

职责：

- 读取机器码
- 校验当前授权状态
- 保存注册码/证书
- 在应用启动时决定是否允许进入业务页面

主要 RPC：

- `licensing.machineCode`
- `licensing.verify`
- `licensing.register`

## 4. Subjects

前端入口：

- [frontend/src/views/SubjectsPage.vue](/d:/coding%20make%20work%20easy/Easy-Exam/frontend/src/views/SubjectsPage.vue)
- `frontend/src/views/SubjectsPage/composables/`

后端入口：

- [backend/application/subjects_service.py](/d:/coding%20make%20work%20easy/Easy-Exam/backend/application/subjects_service.py)
- `backend/subjects/`

职责：

- 科目录入、导入、导出
- 时间冲突与字段合法性校验
- 维护科目时长与考场数
- 为监考编排和资料打印提供上游数据

主要前端 composables：

- `useSubjectsData.ts`
- `useSubjectsForm.ts`
- `useSubjectsReset.ts`

主要 RPC：

- `subjects.list`
- `subjects.update`
- `subjects.import`
- `subjects.export`
- `subjects.template`
- `subjects.validate`

测试：

- `backend/tests/test_subjects_service.py`
- `backend/tests/test_subjects_excel.py`
- `frontend/tests/subjects/useSubjectsForm.test.ts`

## 5. Proctoring

前端入口：

- [frontend/src/views/ProctoringPage.vue](/d:/coding%20make%20work%20easy/Easy-Exam/frontend/src/views/ProctoringPage.vue)
- `frontend/src/views/ProctoringPage/composables/`

后端入口：

- [backend/application/proctoring_service.py](/d:/coding%20make%20work%20easy/Easy-Exam/backend/application/proctoring_service.py)
- [backend/application/proctoring_jobs.py](/d:/coding%20make%20work%20easy/Easy-Exam/backend/application/proctoring_jobs.py)
- `backend/proctoring/`
- `backend/proctoring/core/`

职责：

- 导入教师数据
- 生成监考安排或补全已有安排
- 导入已有安排、导入预设、导出总览表
- 手动交换监考老师
- 统计空缺、均衡指标与 CP-SAT 阶段信息

当前前端 composables：

- `useProctoringBootstrap.ts`
- `useProctoringDataManagement.ts`
- `useProctoringOptimizationMetrics.ts`
- `useProctoringScheduling.ts`
- `useProctoringSwap.ts`
- `useProctoringViewData.ts`

当前后端核心模块：

- `data_import.py`
- `entities.py`
- `models.py`
- `statistics.py`
- `swap.py`
- `validators.py`
- `cp_sat/assignment.py`
- `cp_sat/common.py`
- `cp_sat/diagnostics.py`
- `cp_sat/metrics.py`
- `cp_sat/objectives.py`
- `cp_sat/progress.py`
- `cp_sat/solver.py`

主要 RPC：

- `proctoring.getState`
- `proctoring.startSolverJob`
- `proctoring.getJobStatus`
- `proctoring.clearState`
- `proctoring.importTeachers`
- `proctoring.generateSchedule`
- `proctoring.template`
- `proctoring.export`
- `proctoring.continue`
- `proctoring.importSchedule`
- `proctoring.swap`
- `proctoring.export_empty_preset`
- `proctoring.import_preset`

补充说明：

- 当前界面主流程使用 `startSolverJob` / `getJobStatus`
- `generateSchedule` / `continue` 仍然保留为同步服务方法
- “优化明细”目前属于开发者模式中的 CP-SAT 结果查看，不是旧的独立 `proctoring.optimize` 接口

测试：

- `backend/tests/test_proctoring_service.py`
- `backend/tests/test_proctoring_jobs.py`
- `backend/tests/test_proctoring_validators.py`
- `backend/tests/test_cp_sat_solver.py`
- `frontend/tests/proctoring/useProctoringOptimizationMetrics.test.ts`

## 6. Rooms / Exam Arrangement

前端入口：

- [frontend/src/views/RoomsPage.vue](/d:/coding%20make%20work%20easy/Easy-Exam/frontend/src/views/RoomsPage.vue)
- [frontend/src/views/RoomsPage/RoomsSidebar.vue](/d:/coding%20make%20work%20easy/Easy-Exam/frontend/src/views/RoomsPage/RoomsSidebar.vue)
- [frontend/src/views/RoomsPage/RoomsDataTabs.vue](/d:/coding%20make%20work%20easy/Easy-Exam/frontend/src/views/RoomsPage/RoomsDataTabs.vue)
- `frontend/src/views/RoomsPage/composables/`

后端入口：

- [backend/application/rooms_service.py](/d:/coding%20make%20work%20easy/Easy-Exam/backend/application/rooms_service.py)
- `backend/examroom/core/`

职责：

- 生成设置模板和名册模板
- 导入考场设置和考生名册
- 执行顺序、随机、`3+1+2`、高考模式编排
- 配置高考模式时间设置和 `3+1+2` 科目优先级
- 导出结果或导入已有结果

主要前端 composables：

- `useRoomsState.ts`
- `useRoomsPersistence.ts`
- `useRoomsIO.ts`
- `useRoomsArrangement.ts`

主要后端模块：

- `arrangement.py`
- `sequential_strategy.py`
- `subject_strategy.py`
- `gaokao_helpers.py`
- `gaokao_exports.py`
- `gaokao_defaults.py`
- `standard_exports.py`
- `stats_sheet.py`
- `helpers.py`
- `rooms_input_importers.py`
- `rooms_result_importers.py`
- `rooms_templates.py`

主要 RPC：

- `rooms.resetState`
- `rooms.getState`
- `rooms.getSubjectPriority`
- `rooms.setSubjectPriority`
- `rooms.getGaokaoTimeSettings`
- `rooms.setGaokaoTimeSettings`
- `rooms.generateTemplate`
- `rooms.importSettings`
- `rooms.importStudents`
- `rooms.arrange`
- `rooms.export`
- `rooms.importResults`

测试：

- `backend/tests/test_rooms_service.py`
- `backend/tests/test_rooms_imports_and_templates.py`
- `backend/tests/test_rooms_arrange_flow.py`
- `backend/tests/test_rooms_export_flow.py`
- `backend/tests/test_exam_arrangement.py`
- `backend/tests/test_exam_arrangement_gaokao_exports.py`

## 7. Printing

前端入口：

- [frontend/src/views/PrintingPage.vue](/d:/coding%20make%20work%20easy/Easy-Exam/frontend/src/views/PrintingPage.vue)
- `frontend/src/views/PrintingPage/components/`
- `frontend/src/views/PrintingPage/composables/`

后端入口：

- [backend/application/printing_service.py](/d:/coding%20make%20work%20easy/Easy-Exam/backend/application/printing_service.py)
- `backend/printing/`

职责：

- 管理打印数据源
- 处理字段映射与预览数据
- 从考场编排结果加载打印数据
- 生成 Excel / PDF 文件
- 校验桌角标签排序和布局溢出

主要前端 composables：

- `usePrintingSubjects.ts`
- `usePrintingPreview.ts`
- `usePrintingFileSource.ts`
- `usePrintingGenerate.ts`
- `usePrintingPreviewData.ts`
- `usePrintingDeskLayout.ts`
- `usePrintingScheduleSource.ts`

主要前端局部组件：

- `PrintingMappingDialog.vue`
- `PrintingSubjectsDialog.vue`
- `PrintingDeskLayoutDialog.vue`

主要后端子模块：

- `core/adapters/`
- `core/generators/excel/`
- `core/generators/pdf/`
- `core/validators/`
- `core/utils/`

主要 RPC：

- `printing.getState`
- `printing.saveConfig`
- `printing.resetState`
- `printing.readHeaders`
- `printing.previewData`
- `printing.loadFromSchedule`
- `printing.previewPdf`
- `printing.generate`

测试：

- `backend/tests/test_printing_service.py`
- `backend/tests/test_printing_excel_generators.py`
- `backend/tests/test_printing_examroom_adapter.py`
- `backend/tests/test_data_loader_and_desk_validator.py`
- `backend/tests/test_generator_factory.py`
- `backend/tests/test_pdf_export.py`
- `frontend/tests/printing/usePrintingDeskLayout.test.ts`

## 8. Help / Manual / System

前端入口：

- [frontend/src/views/HelpPage.vue](/d:/coding%20make%20work%20easy/Easy-Exam/frontend/src/views/HelpPage.vue)
- `frontend/src/views/HelpPage/composables/`

后端入口：

- [backend/application/system_service.py](/d:/coding%20make%20work%20easy/Easy-Exam/backend/application/system_service.py)
- `backend/manual/`
- `backend/resources/`

职责：

- 读取内置使用说明书
- 构建帮助中心的 Markdown、目录和全文搜索输入
- 执行系统级数据重置

主要前端 composables：

- `useMarkdown.ts`
- `useFullTextSearch.ts`
- `useScrollSpy.ts`
- `useTocGeneration.ts`

主要 RPC：

- `system.resetData`
- `system.getHelpManual`

补充说明：

- `backend/manual/pdf_export.py` 当前为可复用工具和测试对象
- 现有帮助中心界面只提供阅读和搜索，没有前端“导出 PDF”按钮

测试：

- `backend/tests/test_system_service.py`
- `backend/tests/test_system_service_edges.py`
- `backend/tests/test_manual_loader.py`
- `backend/tests/test_manual_markdown_edges.py`
- `backend/tests/test_manual_search_edges.py`
- `backend/tests/test_manual_utils.py`

## 9. 模块依赖关系

```text
Licensing
  -> 控制应用是否可进入主流程

Subjects
  -> Proctoring
  -> Printing

Rooms
  -> Printing

Dashboard
  -> 汇总 Subjects / Proctoring / Rooms / Printing 状态

System
  -> 重置 Subjects / Proctoring / Rooms / Printing 持久化数据
```

也就是说：

- 科目是监考与打印的重要上游
- 考场结果是打印的重要上游
- Dashboard 负责汇总，不持有独立业务规则
- Licensing 影响整个应用的入口可用性
- Help / Manual / System 属于系统支持能力，不直接参与编排计算
