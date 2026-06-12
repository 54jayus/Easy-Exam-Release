# 开发文档索引

本目录维护 Easy Exam 当前实现对应的开发文档。这里的内容以“当前仓库真实可运行状态”为准，不再重复记录已经归档的阶段性重构方案。

## 活跃文档

1. [architecture.md](architecture.md)
   说明 Electron、Vue、Python、RPC、状态持久化、打包链路和关键运行约束。
2. [modules.md](modules.md)
   说明 Dashboard、Licensing、Subjects、Proctoring、Rooms、Printing、Help/System 等模块的职责、入口与 RPC。
3. [development.md](development.md)
   说明本地开发环境、环境变量、启动命令、调试入口和排查路径。
4. [testing-and-release.md](testing-and-release.md)
   说明当前前后端测试入口、自检脚本和打包发布流程。
5. [授权证书文件路径说明.md](授权证书文件路径说明.md)
   说明 `license.cert` 在开发态、打包态和直跑 Python 时的查找/保存规则。
6. [proctoring-cp-sat-structure.md](proctoring-cp-sat-structure.md)
   说明监考编排 CP-SAT 求解器的变量、约束、目标函数和 Mermaid 结构图。
7. [proctoring-cp-sat-final-strategy.md](proctoring-cp-sat-final-strategy.md)
   说明监考编排 CP-SAT 当前定版策略，包括普通/特殊老师划分、`<=1/<=2/回退` 机制和时长均衡阶段顺序。
8. [前端设计要求](前端设计要求)
   说明当前前端视觉风格与维护约束。
9. [打包代码.txt](打包代码.txt)
   保留当前打包命令速查。

## 其他入口

- 仓库总入口：[../README.md](../README.md)
- 前端专项说明：[../frontend/README.md](../frontend/README.md)
- 用户手册：[../backend/resources/使用说明书.md](../backend/resources/使用说明书.md)

## 文档维护约定

- 文档优先描述现有代码，而不是预期方案。
- 目录、接口、测试文件名和命令必须与仓库实际一致。
- 历史方案、分析笔记和阶段性设计稿统一放在 [archive/plans](archive/plans)。
