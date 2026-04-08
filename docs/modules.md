# 业务模块说明

## 1. 主流程总览

Easy Exam 当前围绕以下主流程组织：

1. 配置考试科目
2. 编排监考
3. 编排考场
4. 生成与打印资料
5. 管理授权
6. 查看帮助中心与使用说明

对应的前端页面主要位于 `frontend/src/views/`，后端入口服务主要位于 `backend/application/`。

## 2. Dashboard

前端入口：

- `frontend/src/views/DashboardPage.vue`

后端入口：

- `backend/application/dashboard_service.py`

主要职责：

- 汇总当前系统状态
- 展示工作流完成度
- 提供科目、监考、考场、打印等模块的摘要信息

主要 RPC：

- `dashboard.getStats`

## 3. Licensing / Registration

前端入口：

- `frontend/src/views/RegistrationPage.vue`
- `frontend/src/stores/license.ts`

后端入口：

- `backend/application/licensing_service.py`
- `backend/licensing/`

主要职责：

- 读取机器码
- 校验当前证书或注册码状态
- 写入并保存授权证书
- 在应用启动时决定是否允许进入业务页面

主要 RPC：

- `licensing.machineCode`
- `licensing.verify`
- `licensing.register`

## 4. Subjects

前端入口：

- `frontend/src/views/SubjectsPage.vue`
- `frontend/src/views/SubjectsPage/composables/`

后端入口：

- `backend/application/subjects_service.py`
- `backend/subjects/`

主要职责：

- 导入和维护考试科目
- 校验考试时间冲突和字段合法性
- 导出科目数据和模板
- 为监考编排和打印模块提供上游数据

主要前端 composables：

- `useSubjectsData.ts`
- `useSubjectsForm.ts`
- `useSubjectsLogs.ts`
- `useSubjectsReset.ts`

主要 RPC：

- `subjects.list`
- `subjects.update`
- `subjects.import`
- `subjects.export`
- `subjects.template`
- `subjects.validate`

## 5. Proctoring

前端入口：

- `frontend/src/views/ProctoringPage.vue`
- `frontend/src/views/ProctoringPage/composables/`

后端入口：

- `backend/application/proctoring_service.py`
- `backend/proctoring/`
- `backend/proctoring/core/`

主要职责：

- 导入教师数据
- 生成监考安排
- 继续编排、均衡优化和手动交换
- 导入或导出排班结果与预设

主要前端 composables：

- `useProctoringBootstrap.ts`
- `useProctoringDataManagement.ts`
- `useProctoringOptimizationMetrics.ts`
- `useProctoringScheduling.ts`
- `useProctoringSwap.ts`
- `useProctoringViewData.ts`

主要后端核心模块：

- `scheduler.py`
- `optimizer.py`
- `swap.py`
- `balance.py`
- `selectors.py`
- `statistics.py`
- `validators.py`
- `postprocess.py`
- `entities.py`
- `models.py`

主要 RPC：

- `proctoring.getState`
- `proctoring.clearState`
- `proctoring.importTeachers`
- `proctoring.generateSchedule`
- `proctoring.template`
- `proctoring.export`
- `proctoring.continue`
- `proctoring.optimize`
- `proctoring.importSchedule`
- `proctoring.swap`
- `proctoring.export_empty_preset`
- `proctoring.import_preset`

## 6. Rooms / Exam Arrangement

前端入口：

- `frontend/src/views/RoomsPage.vue`
- `frontend/src/views/RoomsPage/composables/`
- `frontend/src/views/RoomsPage/*.vue`

后端入口：

- `backend/application/rooms_service.py`
- `backend/examroom/core/`

主要职责：

- 生成并导入考场设置模板
- 导入学生名单
- 执行常规模式或高考模式考场编排
- 导出编排结果并支持结果回灌
- 为打印模块提供考场和学生结果数据

主要前端 composables：

- `useRoomsState.ts`
- `useRoomsPersistence.ts`
- `useRoomsLogging.ts`
- `useRoomsIO.ts`
- `useRoomsArrangement.ts`

主要后端核心模块：

- `arrangement.py`
- `sequential_strategy.py`
- `subject_strategy.py`
- `gaokao_helpers.py`
- `gaokao_exports.py`
- `gaokao_defaults.py`
- `standard_exports.py`
- `stats_sheet.py`
- `helpers.py`

`rooms_service.py` 的辅助模块：

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

## 7. Printing

前端入口：

- `frontend/src/views/PrintingPage.vue`
- `frontend/src/views/PrintingPage/composables/`
- `frontend/src/views/PrintingPage/components/`

后端入口：

- `backend/application/printing_service.py`
- `backend/printing/`

主要职责：

- 读取文件源或排考结果作为打印数据源
- 处理字段映射和预览数据
- 配置台贴、准考证、试卷袋等输出参数
- 生成 Excel 或 PDF 文件

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

## 8. Help / Manual / System

前端入口：

- `frontend/src/views/HelpPage.vue`
- `frontend/src/views/HelpPage/composables/`

后端入口：

- `backend/application/system_service.py`
- `backend/manual/`
- `backend/resources/`

主要职责：

- 读取内置帮助文档
- 渲染 Markdown、目录和全文搜索结果
- 提供系统级数据重置能力

主要前端 composables：

- `useMarkdown.ts`
- `useFullTextSearch.ts`
- `useScrollSpy.ts`
- `useTocGeneration.ts`

主要 RPC：

- `system.resetData`
- `system.getHelpManual`

## 9. 模块依赖关系

模块依赖大致如下：

```text
Licensing
  -> 控制应用可用性

Subjects
  -> Proctoring
  -> Printing

Rooms
  -> Printing

Dashboard
  -> 汇总 Subjects / Proctoring / Rooms / Printing 的状态

System
  -> 重置 Subjects / Proctoring / Rooms / Printing 的持久化数据
```

也就是说：

- 科目是监考与打印的重要上游
- 考场结果是打印的重要上游
- Dashboard 负责汇总，不持有独立业务规则
- Licensing 影响整个应用是否可进入主流程
- Help / Manual 属于系统支持能力，不直接参与业务编排
