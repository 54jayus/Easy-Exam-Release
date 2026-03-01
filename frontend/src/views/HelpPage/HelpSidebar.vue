<template>
  <aside class="shrink-0 flex flex-col border-r border-slate-100 bg-slate-50/30 hidden md:flex md:w-60 lg:w-70 xl:w-80 h-full">
    <div class="p-4 h-full flex flex-col min-h-0">
      <h3 class="text-xs font-bold text-slate-400 uppercase tracking-wider mb-3 px-2 flex items-center gap-2 shrink-0">
        <el-icon><List /></el-icon> 目录导航
      </h3>
      <div ref="tocScrollRef" class="flex-1 overflow-y-auto custom-scrollbar pr-2 -mr-2 min-h-0">
        <el-tree
          ref="tocTreeRef"
          :data="tocData"
          :props="defaultProps"
          node-key="id"
          :highlight-current="true"
          :filter-node-method="filterNode"
          default-expand-all
          @node-click="handleNodeClick"
          aria-label="文档目录导航"
          class="bg-transparent !p-0 custom-tree-clean"
          empty-text="暂无目录"
        >
          <template #default="{ node, data }">
            <div
              class="group flex items-center gap-3 py-2 px-3 w-full rounded-md transition-all duration-200 border-l-[3px] my-0.5"
              :class="[
                node.isCurrent
                  ? 'bg-white border-primary-500 text-primary-700 shadow-sm'
                  : 'border-transparent hover:bg-slate-200/50 text-slate-600 hover:text-slate-900'
              ]"
            >
              <span
                class="text-sm truncate leading-tight transition-colors"
                :class="{
                  'font-semibold': data.level === 1,
                  'pl-0': data.level === 1,
                  'pl-2': data.level !== 1
                }"
              >{{ node.label }}</span>
            </div>
          </template>
        </el-tree>
      </div>
    </div>
  </aside>
</template>

<script setup lang="ts">
import { ref, watch } from 'vue'
import { List } from '@element-plus/icons-vue'
import type { TocItem } from './composables/useTocGeneration'

const props = defineProps<{
  tocData: TocItem[]
  searchQuery: string
}>()

const emit = defineEmits<{
  nodeClick: [data: TocItem]
}>()

const tocTreeRef = ref()
const tocScrollRef = ref<HTMLElement>()

const defaultProps = {
  children: 'children',
  label: 'label'
}

function filterNode(value: string, data: TocItem) {
  if (!value) return true
  return data.label.toLowerCase().includes(value.toLowerCase())
}

function handleNodeClick(data: TocItem) {
  emit('nodeClick', data)
}

// Debounced search filter
let searchDebounceTimer: ReturnType<typeof setTimeout> | null = null
watch(() => props.searchQuery, (val) => {
  if (searchDebounceTimer) clearTimeout(searchDebounceTimer)
  searchDebounceTimer = setTimeout(() => {
    tocTreeRef.value?.filter(val)
  }, 300)
})

defineExpose({
  tocTreeRef,
  tocScrollRef
})
</script>

<style scoped>
/* Scrollbar Styling */
.custom-scrollbar::-webkit-scrollbar {
  width: 5px;
  height: 5px;
}
.custom-scrollbar::-webkit-scrollbar-track {
  background: transparent;
}
.custom-scrollbar::-webkit-scrollbar-thumb {
  background: #e2e8f0;
  border-radius: 10px;
}
.custom-scrollbar::-webkit-scrollbar-thumb:hover {
  background: #cbd5e1;
}

/* Custom Tree Overrides for cleaner look */
:deep(.custom-tree-clean .el-tree-node__content) {
  height: auto;
  padding: 0 !important;
  background: transparent !important;
  margin-bottom: 2px;
}

:deep(.custom-tree-clean .el-tree-node__expand-icon) {
  display: none;
}
</style>
