# 开发文档索引

本目录用于维护 Easy Exam 的开发、架构、测试与重构文档。用户使用说明仍以仓库根目录下的说明文档为主，这里的内容更偏向开发者接手、定位问题和持续重构。

## 建议阅读顺序

1. [架构说明](architecture.md)
2. [业务模块说明](modules.md)
3. [开发与调试手册](development.md)
4. [测试与发布说明](testing-and-release.md)
5. [授权证书文件路径说明](授权证书文件路径说明.md)
6. [项目整体分析（2026-04-07，已归档）](archive/plans/2026-04-07-project-analysis.md)
7. [代码架构优化方案（2026-04-07，已按 2026-04-08 完成并归档）](archive/plans/2026-04-07-architecture-optimization-plan.md)

## 文档说明

- [architecture.md](architecture.md)
  说明 Electron、Vue、Python、RPC、状态恢复和当前重构后的代码组织方式。
- [modules.md](modules.md)
  说明 dashboard、subjects、proctoring、rooms、printing、licensing 等业务模块的职责与入口。
- [development.md](development.md)
  说明本地开发环境、常用命令、PowerShell 约定、调试方式和重构时的操作边界。
- [testing-and-release.md](testing-and-release.md)
  说明构建、测试、打包、发布前检查和常见风险点。
- [授权证书文件路径说明.md](授权证书文件路径说明.md)
  说明授权证书在开发态和打包态的查找规则。
- [archive/plans/2026-04-07-project-analysis.md](archive/plans/2026-04-07-project-analysis.md)
  记录这轮治理开始前后的项目热点、测试现状、构建体积与后续优化重点，现已归档。
- [archive/plans/2026-04-07-architecture-optimization-plan.md](archive/plans/2026-04-07-architecture-optimization-plan.md)
  记录“只做架构优化、不改业务逻辑”的分阶段方案、已完成进度、测试策略与后续可选优化方向，现已归档。
