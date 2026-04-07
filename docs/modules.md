# 业务模块说明

## 1. 模块总览

当前产品工作流可以概括为：

1. 配置考试科目
2. 编排监考
3. 编排考场
4. 生成和打印资料
5. 管理注册授权
6. 在帮助中心查看内置手册

下面按模块说明职责、主要入口和关键依赖。

## 2. 仪表盘

前端页面：

- `frontend/src/views/DashboardPage.vue`

后端服务：

- `backend/application/dashboard_service.py`

职责：

- 汇总当前系统数据状态
- 展示工作流完成度
- 给出科目、监考、考场、打印等统计摘要

依赖：

- `subjects`
- `proctoring`
- `rooms`
- `exam_arrangement`

## 3. 注册授权

前端页面：

- `frontend/src/views/RegistrationPage.vue`

后端服务：

- `backend/application/licensing_service.py`
- `backend/licensing/`

主要 RPC：

- `licensing.machineCode`
- `licensing.verify`
- `licensing.register`

职责：

- 获取机器码
- 校验授权状态
- 写入注册码和证书

相关文档：

- [授权证书文件路径说明](授权证书文件路径说明.md)

## 4. 科目管理

前端页面：

- `frontend/src/views/SubjectsPage.vue`

后端服务：

- `backend/application/subjects_service.py`

主要 RPC：

- `subjects.list`
- `subjects.update`
- `subjects.import`
- `subjects.export`
- `subjects.template`
- `subjects.validate`

职责：

- 维护考试科目、时间、时长等信息
- 导入导出科目配置
- 校验时间冲突与配置合法性

它是后续监考编排与打印配置的重要前置依赖。

## 5. 监考编排

前端页面：

- `frontend/src/views/ProctoringPage.vue`

后端服务：

- `backend/application/proctoring_service.py`
- `backend/proctoring/`

主要 RPC：

- `proctoring.getState`
- `proctoring.importTeachers`
- `proctoring.generateSchedule`
- `proctoring.optimize`
- `proctoring.swap`
- `proctoring.export`
- `proctoring.importSchedule`

职责：

- 导入教师名单
- 基于科目与配置生成监考安排
- 优化结果、手动调换、继续编排
- 导出监考排班结果

特点：

- 业务规则较多
- 对均衡性和约束条件比较敏感
- 通常需要样例验证，而不只是看代码

## 6. 考场编排

前端页面：

- `frontend/src/views/RoomsPage.vue`
- `frontend/src/views/RoomsPage/`

后端服务：

- `backend/application/rooms_service.py`
- `backend/examroom/`

主要 RPC：

- `rooms.getState`
- `rooms.resetState`
- `rooms.generateTemplate`
- `rooms.importSettings`
- `rooms.importStudents`
- `rooms.arrange`
- `rooms.export`
- `rooms.importResults`
- `rooms.getSubjectPriority`
- `rooms.setSubjectPriority`
- `rooms.getGaokaoTimeSettings`
- `rooms.setGaokaoTimeSettings`

职责：

- 管理考场设置与考生导入
- 执行多种编排模式
- 导入已有编排结果
- 导出考场结果与统计表

编排模式大致包括：

- 普通顺序模式
- 随机模式
- 选科模式
- 高考模式

这是当前项目业务复杂度最高的模块之一，尤其是高考模式与导入导出链路。

## 7. 资料打印

前端页面：

- `frontend/src/views/PrintingPage.vue`
- `frontend/src/views/PrintingPage/composables/`

后端服务：

- `backend/application/printing_service.py`
- `backend/printing/`

主要 RPC：

- `printing.getState`
- `printing.saveConfig`
- `printing.resetState`
- `printing.readHeaders`
- `printing.previewData`
- `printing.loadFromSchedule`
- `printing.previewPdf`
- `printing.generate`

职责：

- 从文件或编排结果加载打印数据
- 映射字段
- 预览打印内容
- 生成 Excel / PDF 材料

前端当前已拆分为以下职责模块：

- `usePrintingFileSource.ts`
  负责文件选择、字段映射、预览缓存与文件数据源恢复
- `usePrintingPreview.ts`
  负责预览缩放、拖拽、自适应和预览容器交互
- `usePrintingPreviewData.ts`
  负责角标、准考证、考生信息表、试卷袋等预览数据加工
- `usePrintingGenerate.ts`
  负责生成导出流程与生成前校验
- `usePrintingSubjects.ts`
  负责科目与时间配置、同步与编辑弹窗
- `usePrintingDeskLayout.ts`
  负责座位布局草稿、排位算法与桌贴预览
- `usePrintingScheduleSource.ts`
  负责从考场编排结果加载打印预览数据

常见输出类型包括：

- 考场角标
- 准考证
- 考生信息表
- 试卷袋相关标签
- 桌贴

此模块与 `rooms` 模块强耦合，因为很多打印数据直接依赖考场编排结果。

## 8. 帮助中心

前端页面：

- `frontend/src/views/HelpPage.vue`
- `frontend/src/views/HelpPage/`

后端服务：

- `backend/application/system_service.py`

主要 RPC：

- `system.getHelpManual`

职责：

- 读取内置 Markdown 用户手册
- 在前端提供搜索、目录和内容浏览能力

## 9. 系统级能力

后端系统服务：

- `backend/application/system_service.py`

主要 RPC：

- `system.resetData`

职责：

- 重置系统状态
- 清空主要业务数据

这是高风险操作，运维或管理文档里应单独强调。

## 10. 模块间依赖关系

可以简化理解为：

```text
科目管理 -> 监考编排
科目管理 -> 考场编排
考场编排 -> 资料打印
系统服务 -> 帮助中心 / 数据重置 / 公共能力
注册授权 -> 整个应用的可用状态
```

其中最值得重点关注的是：

- `subjects` 是多个模块的上游输入
- `rooms` 是打印模块的重要数据来源
- `licensing` 会影响功能可用性

## 11. 维护建议

- 修业务问题时，先确认它属于哪条工作流
- 改导入导出逻辑时，同时检查对应页面和打印适配器
- 改高考模式时，优先联查 `rooms_service.py` 与 `examroom/core/arrangement.py`
- 改打印内容时，不要只看前端，数据来源、预览适配和生成器都要一起检查
