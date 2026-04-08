# 开发文档索引

本目录维护 Easy Exam 的开发者文档、运行架构说明、模块说明、测试发布说明和设计规范。用户手册仍以仓库根目录下的 `使用说明书.md` / `使用说明书.pdf` 为主。

## 活跃文档

1. [架构说明](architecture.md)
2. [业务模块说明](modules.md)
3. [开发与调试手册](development.md)
4. [测试与发布说明](testing-and-release.md)
5. [授权证书文件路径说明](授权证书文件路径说明.md)
6. [前端设计要求](前端设计要求)
7. [打包命令速查](打包代码.txt)

## 文档用途

- [architecture.md](architecture.md)
  说明 Electron、Vue、Python、RPC、状态持久化、打包链路和模块边界。
- [modules.md](modules.md)
  说明 Dashboard、Licensing、Subjects、Proctoring、Rooms、Printing、Help 等模块的职责与依赖。
- [development.md](development.md)
  说明本地开发环境、环境变量、启动命令、调试入口和常见排查路径。
- [testing-and-release.md](testing-and-release.md)
  说明前端测试、后端测试、发布前验证和打包发布流程。
- [授权证书文件路径说明.md](授权证书文件路径说明.md)
  说明 `license.cert` 在 Electron 开发态、打包态和直接运行 Python 时的查找与保存规则。
- [前端设计要求](前端设计要求)
  说明当前前端界面的视觉方向、布局模式和维护约束。
- [打包代码.txt](打包代码.txt)
  提供当前仓库可用的打包命令速查。

## 其他入口

- 仓库总入口：[../README.md](../README.md)
- 前端专项说明：[../frontend/README.md](../frontend/README.md)
- 用户手册：[../使用说明书.md](../使用说明书.md)

## 归档文档

历史重构方案、项目分析和专题设计稿已统一放入 [archive/plans](archive/plans)。这些文档保留历史决策背景，但不再作为当前实现的权威说明。
