# 软件更新弹窗重构设计文档

**日期**：2026-05-26  
**文件**：`frontend/src/App.vue`  
**范围**：`showUpdateDialog` 弹窗及相关响应式状态

---

## 1. 背景与问题

当前更新弹窗存在 5 个问题：

1. **弹窗高度失控** — 更新说明条目多时弹窗无限增高，超出屏幕需要整页滚动
2. **更新说明无折叠** — 9 条说明全部展开，视觉负担重
3. **历史记录无高度限制** — 展开后堆叠到按钮区域之外
4. **版本卡片冗余** — 已最新时两个卡片显示完全相同的版本号
5. **历史记录与更新内容重复** — 同一版本的说明在两处展示，无视觉区分

---

## 2. 设计方案（方案 B：全面重构信息层级）

### 2.1 弹窗整体高度控制

弹窗内容区（`<el-dialog>` 默认插槽）加 `max-height: calc(80vh - 160px)` + `overflow-y: auto`，160px 预留弹窗标题栏和底部按钮区高度。任何屏幕尺寸下弹窗都不超出视口。

### 2.2 版本卡片区域

**有新版本时**：保持现有双卡片布局（当前版本 vs 最新版本），对比清晰，不变。

**已最新时**（`updateStatus === 'up_to_date'` 且 `latestVersion === currentVersion`）：合并为单个绿色成功卡片，展示：
- 绿色圆形勾选图标
- 标题：「当前已是最新版本」
- 副文本：`v{version} · 发布于 {releaseDate}`

实现方式：在模板中用 `v-if` 按 `updateStatus` 条件渲染两套卡片 HTML。

### 2.3 更新说明折叠

新增响应式状态：
- `showAllNotes: ref(false)` — 是否展开全部
- `visibleNotes: computed` — `showAllNotes || notes.length <= 4` 时返回全部，否则返回前 4 条

UI 变化：
- 列表改用 `visibleNotes` 渲染
- 条目超过 4 条时，列表下方显示「▾ 展开全部 N 条」按钮；已展开时显示「▴ 收起」
- 弹窗关闭或新一轮检查开始时重置 `showAllNotes = false`

重置时机：`applyUpdateResult()` 函数开头、`watch(frontendResetEpoch)` 回调中。

### 2.4 历史记录时间线

**样式**：改为垂直时间线布局，每个版本条目包含：
- 左侧时间线圆点（当前版本用主色，历史版本用灰色）+ 竖线连接
- 版本号 + 「当前版本」标签（仅当 `entry.version === currentVersion`）+ 发布日期
- 更新说明列表（同样限制显示前 4 条，超出折叠）
- 「查看发布页」链接（有 `releasePageUrl` 时显示）

**高度限制**：时间线容器加 `max-height: 240px` + `overflow-y: auto`，独立滚动，不影响弹窗整体。

**重复内容处理**：保留「更新内容」区域展示当前版本说明，历史记录时间线第一条也是当前版本，通过「当前版本」标签做视觉区分，不删除任何一处。

### 2.5 「查看历史更新」入口调整

将「查看历史更新」按钮从「更新内容」标题行右侧移出，改为独立放在更新说明区域下方，避免标题行过于拥挤。

---

## 3. 状态变更汇总

| 新增/修改 | 类型 | 说明 |
|---|---|---|
| `showAllNotes` | `ref<boolean>` | 新增，控制更新说明展开/折叠 |
| `visibleNotes` | `computed<string[]>` | 新增，当前可见的说明条目 |
| `applyUpdateResult()` | 函数修改 | 开头重置 `showAllNotes = false` |
| `watch(frontendResetEpoch)` | 修改 | 追加重置 `showAllNotes = false` |

其余状态（`updateStatus`、`notes`、`updateHistory` 等）不变。

---

## 4. 不在本次范围内

- 历史记录条目内的说明也做折叠（可后续迭代）
- 更新弹窗拆分为两个独立弹窗（方案 C，本次不做）
- 下载进度、安装逻辑不变
