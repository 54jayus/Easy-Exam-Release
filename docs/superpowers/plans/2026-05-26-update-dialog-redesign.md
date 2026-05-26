# 软件更新弹窗重构 Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 重构 `frontend/src/App.vue` 中的软件更新弹窗，解决高度失控、说明无折叠、历史记录无限堆叠、版本卡片冗余、内容重复无区分五个问题。

**Architecture:** 所有改动集中在 `frontend/src/App.vue` 一个文件。新增两个响应式状态（`showAllNotes`、`visibleNotes`），修改弹窗模板的版本卡片区、更新说明区、历史记录区三个部分，并在两处重置点追加状态重置。

**Tech Stack:** Vue 3 Composition API、Element Plus、Tailwind CSS

---

## 文件变更清单

| 文件 | 操作 | 说明 |
|---|---|---|
| `frontend/src/App.vue` | 修改 | 唯一改动文件，脚本 + 模板均有变更 |

---

### Task 1：新增 `showAllNotes` 状态与 `visibleNotes` computed

**Files:**
- Modify: `frontend/src/App.vue`

- [ ] **Step 1：在 `updateHistory` ref 后追加 `showAllNotes`**

在 `frontend/src/App.vue` 第 501 行（`const updateHistory = ref<UpdateHistoryEntry[]>([])`）后插入：

```typescript
const showAllNotes = ref(false)
```

- [ ] **Step 2：在 `updateStatusTitleClass` computed 后追加 `visibleNotes`**

在 `updateStatusTitleClass` computed 结束的 `})` 后插入：

```typescript
const visibleNotes = computed(() =>
  showAllNotes.value || notes.value.length <= 4 ? notes.value : notes.value.slice(0, 4)
)
```

- [ ] **Step 3：在 `applyUpdateResult` 函数开头重置 `showAllNotes`**

找到 `const applyUpdateResult = (result: UpdateCheckResult, manual: boolean) => {`，在函数体第一行插入：

```typescript
showAllNotes.value = false
```

- [ ] **Step 4：在 `watch(frontendResetEpoch)` 回调中追加重置**

找到 `watch(frontendResetEpoch, () => {` 回调，在 `updateHistory.value = []` 后追加：

```typescript
showAllNotes.value = false
```

- [ ] **Step 5：类型检查**

```bash
cd frontend && npx vue-tsc -p tsconfig.json --noEmit
```

预期：无报错输出。

- [ ] **Step 6：提交**

```bash
git add frontend/src/App.vue
git commit -m "feat(update-dialog): add showAllNotes state and visibleNotes computed"
```

---

### Task 2：弹窗内容区加高度限制

**Files:**
- Modify: `frontend/src/App.vue`（模板部分）

- [ ] **Step 1：找到弹窗内容区 div**

定位 `<el-dialog v-model="showUpdateDialog"` 下方的第一个 div：

```html
<div class="space-y-5 py-1">
```

- [ ] **Step 2：替换为带高度限制的版本**

将该行改为：

```html
<div class="space-y-5 py-1 max-h-[calc(80vh-160px)] overflow-y-auto pr-1 custom-scrollbar">
```

- [ ] **Step 3：类型检查**

```bash
cd frontend && npx vue-tsc -p tsconfig.json --noEmit
```

预期：无报错。

- [ ] **Step 4：提交**

```bash
git add frontend/src/App.vue
git commit -m "feat(update-dialog): constrain dialog content height with scroll"
```

---

### Task 3：版本卡片区域 — 已最新时合并为单卡片

**Files:**
- Modify: `frontend/src/App.vue`（模板部分）

- [ ] **Step 1：找到版本卡片区域**

定位模板中：

```html
<div class="grid grid-cols-2 gap-3">
  <div class="rounded-2xl border border-slate-200 bg-slate-50 px-4 py-3">
```

- [ ] **Step 2：替换整个版本卡片区域**

将 `<div class="grid grid-cols-2 gap-3">` 整块（含两个子卡片，到对应 `</div>` 结束）替换为：

```html
<template v-if="updateStatus === 'up_to_date'">
  <div class="rounded-2xl border border-emerald-200 bg-emerald-50 px-4 py-3 flex items-center gap-3">
    <div class="w-9 h-9 rounded-full bg-emerald-500 flex items-center justify-center flex-shrink-0">
      <el-icon class="text-white text-base"><Check /></el-icon>
    </div>
    <div>
      <div class="text-sm font-semibold text-emerald-800">当前已是最新版本</div>
      <div class="mt-0.5 text-xs text-emerald-600">
        v{{ currentVersion }}{{ releaseDate ? ` · 发布于 ${releaseDate}` : '' }}
      </div>
    </div>
  </div>
</template>
<template v-else>
  <div class="grid grid-cols-2 gap-3">
    <div class="rounded-2xl border border-slate-200 bg-slate-50 px-4 py-3">
      <div class="text-xs font-medium text-slate-500">当前版本</div>
      <div class="mt-1 text-lg font-bold text-slate-900">v{{ currentVersion }}</div>
    </div>
    <div class="rounded-2xl border border-primary-100 bg-primary-50 px-4 py-3">
      <div class="text-xs font-medium text-primary-500">最新版本</div>
      <div class="mt-1 text-lg font-bold text-primary-700">
        {{ latestVersion ? `v${latestVersion}` : '暂无可用更新' }}
      </div>
      <div v-if="releaseDate" class="mt-1 text-xs text-primary-500">发布时间：{{ releaseDate }}</div>
    </div>
  </div>
</template>
```

- [ ] **Step 3：类型检查**

```bash
cd frontend && npx vue-tsc -p tsconfig.json --noEmit
```

预期：无报错。

- [ ] **Step 4：提交**

```bash
git add frontend/src/App.vue
git commit -m "feat(update-dialog): merge version cards when up-to-date"
```

---

### Task 4：更新说明区域 — 折叠 + 入口按钮下移

**Files:**
- Modify: `frontend/src/App.vue`（模板部分）

- [ ] **Step 1：找到更新说明区域**

定位：

```html
<div class="rounded-2xl border border-slate-200 bg-white px-4 py-4">
  <div class="flex items-center justify-between gap-3">
    <div class="text-sm font-semibold text-slate-800">更新内容</div>
    <el-button link class="!px-0 !text-primary-600" @click="toggleHistoryPanel">
      {{ showHistoryPanel ? '收起历史记录' : '查看历史更新' }}
    </el-button>
  </div>
  <ul v-if="notes.length" class="mt-3 space-y-2 text-sm text-slate-600">
    <li v-for="item in notes" :key="item" class="flex items-start gap-2">
      <span class="mt-1 h-1.5 w-1.5 rounded-full bg-primary-400" />
      <span>{{ item }}</span>
    </li>
  </ul>
  <div v-else class="mt-3 text-sm text-slate-500">当前版本暂未提供额外更新说明。</div>
</div>
```

- [ ] **Step 2：替换为折叠版本**

```html
<div class="rounded-2xl border border-slate-200 bg-white px-4 py-4">
  <div class="text-sm font-semibold text-slate-800 mb-3">更新内容</div>
  <ul v-if="notes.length" class="space-y-2 text-sm text-slate-600">
    <li v-for="item in visibleNotes" :key="item" class="flex items-start gap-2">
      <span class="mt-1 h-1.5 w-1.5 rounded-full bg-primary-400 flex-shrink-0" />
      <span>{{ item }}</span>
    </li>
  </ul>
  <div v-else class="text-sm text-slate-500">当前版本暂未提供额外更新说明。</div>
  <div class="mt-3 flex items-center justify-between">
    <el-button
      v-if="notes.length > 4"
      link
      class="!px-0 !text-primary-600 !text-xs"
      @click="showAllNotes = !showAllNotes"
    >
      {{ showAllNotes ? '▴ 收起' : `▾ 展开全部 ${notes.length} 条` }}
    </el-button>
    <span v-else />
    <el-button link class="!px-0 !text-primary-600 !text-xs" @click="toggleHistoryPanel">
      {{ showHistoryPanel ? '收起历史记录' : '查看历史更新' }}
    </el-button>
  </div>
</div>
```

- [ ] **Step 3：类型检查**

```bash
cd frontend && npx vue-tsc -p tsconfig.json --noEmit
```

预期：无报错。

- [ ] **Step 4：提交**

```bash
git add frontend/src/App.vue
git commit -m "feat(update-dialog): collapse notes beyond 4 items, move history toggle"
```

---

### Task 5：历史记录区域 — 时间线样式 + 高度限制

**Files:**
- Modify: `frontend/src/App.vue`（模板部分）

- [ ] **Step 1：找到历史记录条目列表**

定位：

```html
<div v-else-if="updateHistory.length" class="mt-4 space-y-4">
  <div
    v-for="entry in updateHistory"
    :key="entry.version"
    class="rounded-2xl border border-white bg-white px-4 py-4 shadow-sm"
  >
```

- [ ] **Step 2：替换为时间线布局（含高度限制）**

将 `<div v-else-if="updateHistory.length" class="mt-4 space-y-4">` 整块（到对应 `</div>` 结束，包含内部所有内容）替换为：

```html
<div v-else-if="updateHistory.length" class="mt-4 max-h-60 overflow-y-auto pr-1 custom-scrollbar">
  <div
    v-for="(entry, index) in updateHistory"
    :key="entry.version"
    class="flex gap-3"
  >
    <!-- 时间线左侧 -->
    <div class="flex flex-col items-center flex-shrink-0">
      <div
        class="w-2.5 h-2.5 rounded-full mt-1 flex-shrink-0"
        :class="entry.version === currentVersion ? 'bg-primary-500' : 'bg-slate-300'"
      />
      <div
        v-if="index < updateHistory.length - 1"
        class="w-px flex-1 bg-slate-200 my-1"
      />
    </div>
    <!-- 条目内容 -->
    <div class="flex-1 pb-4">
      <div class="flex items-center gap-2 flex-wrap">
        <span class="text-sm font-semibold text-slate-800">v{{ entry.version }}</span>
        <span
          v-if="entry.version === currentVersion"
          class="rounded-full bg-primary-50 px-2 py-0.5 text-[10px] font-semibold text-primary-600"
        >
          当前版本
        </span>
        <span class="text-xs text-slate-400 ml-auto">{{ entry.releaseDate || '未提供' }}</span>
        <el-button
          v-if="entry.releasePageUrl"
          link
          class="!px-0 !text-primary-600 !text-xs"
          @click="openReleasePage(entry.releasePageUrl!)"
        >
          查看发布页
        </el-button>
      </div>
      <ul v-if="entry.notes.length" class="mt-2 space-y-1 text-xs text-slate-600">
        <li
          v-for="item in entry.notes"
          :key="`${entry.version}-${item}`"
          class="flex items-start gap-1.5"
        >
          <span class="mt-1 h-1 w-1 rounded-full bg-primary-300 flex-shrink-0" />
          <span>{{ item }}</span>
        </li>
      </ul>
    </div>
  </div>
</div>
```

- [ ] **Step 3：类型检查**

```bash
cd frontend && npx vue-tsc -p tsconfig.json --noEmit
```

预期：无报错。

- [ ] **Step 4：提交**

```bash
git add frontend/src/App.vue
git commit -m "feat(update-dialog): redesign history panel as timeline with height cap"
```

---

### Task 6：验收检查

**Files:**
- Read: `frontend/src/App.vue`

- [ ] **Step 1：最终类型检查**

```bash
cd frontend && npx vue-tsc -p tsconfig.json --noEmit
```

预期：无报错。

- [ ] **Step 2：人工验收清单**

启动开发服务器：

```bash
cd frontend && npm run dev
```

逐项验证：

| 场景 | 预期行为 |
|---|---|
| 已最新（版本相同） | 版本区显示单个绿色成功卡片，含勾选图标 |
| 有新版本（版本不同） | 版本区显示双卡片对比，左旧右新 |
| 更新说明 ≤ 4 条 | 全部展示，无展开按钮 |
| 更新说明 > 4 条 | 默认显示 4 条，底部显示「▾ 展开全部 N 条」 |
| 点击展开按钮 | 显示全部，按钮变为「▴ 收起」 |
| 重新检查更新 | 说明列表重置为折叠状态 |
| 展开历史记录 | 时间线样式，当前版本有蓝色圆点和「当前版本」标签 |
| 历史记录条目多 | 面板内部滚动，不撑高弹窗 |
| 弹窗整体 | 内容超长时内部滚动，弹窗不超出视口 |

- [ ] **Step 3：最终提交**

```bash
git add frontend/src/App.vue
git commit -m "feat(update-dialog): complete redesign - height control, notes fold, timeline history"
```
