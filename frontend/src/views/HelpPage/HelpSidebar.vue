<template>
  <aside
    ref="asideRef"
    class="shrink-0 flex flex-col border-r border-slate-100 bg-slate-50/30 hidden md:flex h-full relative"
    :style="{ width: sidebarWidth + 'px' }"
  >
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
              class="group flex items-center gap-2.5 py-2 px-3 w-full rounded-md transition-all duration-200 border-l-[3px] my-0.5"
              :class="[
                node.isCurrent
                  ? 'bg-white border-primary-500 text-primary-700 shadow-sm'
                  : 'border-transparent hover:bg-slate-200/50 text-slate-600 hover:text-slate-900'
              ]"
            >
              <span
                v-if="data.level === 1 && data.sectionNum"
                class="text-[11px] font-mono text-slate-400 shrink-0 w-5 text-right"
                :class="{ '!text-primary-500': node.isCurrent }"
              >{{ data.sectionNum }}</span>
              <span
                class="text-sm leading-tight transition-colors"
                :class="{
                  'font-semibold': data.level === 1,
                  'truncate': !isResizing,
                  'pl-0': data.level === 1,
                  'pl-7': data.level !== 1
                }"
              >{{ node.label }}</span>
            </div>
          </template>
        </el-tree>
      </div>
    </div>

    <!-- Resize handle -->
    <div
      class="absolute top-0 right-0 w-1.5 h-full cursor-col-resize z-10 group/handle"
      @mousedown.prevent="onResizeStart"
    >
      <div
        class="absolute top-0 right-0 w-px h-full transition-colors duration-200"
        :class="isResizing ? 'bg-primary-400' : 'bg-transparent group-hover/handle:bg-slate-300'"
      ></div>
    </div>
  </aside>
</template>

<script setup lang="ts">
import { ref, watch, onMounted, computed } from 'vue'
import { List } from '@element-plus/icons-vue'
import { useDebounceFn } from '@vueuse/core'
import type { TocItem } from './composables/useTocGeneration'

const props = defineProps<{
  tocData: TocItem[]
  searchQuery: string
}>()

const emit = defineEmits<{
  nodeClick: [data: TocItem]
  'width-change': [width: number]
}>()

const tocTreeRef = ref()
const tocScrollRef = ref<HTMLElement>()
const asideRef = ref<HTMLElement>()
const isResizing = ref(false)

const defaultProps = {
  children: 'children',
  label: 'label'
}

// --- Width management ---
const SIDEBAR_MIN = 200
const SIDEBAR_MAX = 420
const SIDEBAR_DEFAULT = 240
const STORAGE_KEY = 'help-sidebar-width'

function loadSavedWidth(): number | null {
  try {
    const saved = localStorage.getItem(STORAGE_KEY)
    if (saved) {
      const n = parseInt(saved, 10)
      if (!isNaN(n) && n >= SIDEBAR_MIN && n <= SIDEBAR_MAX) return n
    }
  } catch { /* ignore */ }
  return null
}

function saveWidth(w: number) {
  try { localStorage.setItem(STORAGE_KEY, String(w)) } catch { /* ignore */ }
}

const sidebarWidth = ref(loadSavedWidth() ?? SIDEBAR_DEFAULT)

// Auto-fit width based on longest visible label (runs once when tocData arrives)
function calcAutoWidth() {
  if (loadSavedWidth() !== null) return // user has a saved preference, respect it
  const canvas = document.createElement('canvas')
  const ctx = canvas.getContext('2d')
  if (!ctx) return
  ctx.font = '14px Inter, system-ui, sans-serif' // matches text-sm

  let maxTextWidth = 0
  const measure = (items: TocItem[]) => {
    for (const item of items) {
      const prefix = item.sectionNum ? `${item.sectionNum}  ` : ''
      const indent = item.level === 2 ? '      ' : ''
      const w = ctx.measureText(indent + prefix + item.label).width
      if (w > maxTextWidth) maxTextWidth = w
      if (item.children?.length) measure(item.children)
    }
  }
  measure(props.tocData)

  // padding: 16 (p-4) + 12 (px-3) + 8 (pr-2) + 24 (border-l + gap + margin) ≈ 60
  const autoWidth = Math.ceil(maxTextWidth + 60)
  const clamped = Math.max(SIDEBAR_MIN, Math.min(SIDEBAR_MAX, autoWidth))
  sidebarWidth.value = clamped
}

watch(() => props.tocData, () => {
  calcAutoWidth()
}, { once: true })

onMounted(() => {
  emit('width-change', sidebarWidth.value)
})

watch(sidebarWidth, (w) => {
  emit('width-change', w)
})

// --- Drag resize ---
let startX = 0
let startWidth = 0

function onResizeStart(e: MouseEvent) {
  isResizing.value = true
  startX = e.clientX
  startWidth = sidebarWidth.value
  document.addEventListener('mousemove', onResizeMove)
  document.addEventListener('mouseup', onResizeEnd)
  document.body.style.cursor = 'col-resize'
  document.body.style.userSelect = 'none'
}

function onResizeMove(e: MouseEvent) {
  const delta = e.clientX - startX
  const newWidth = Math.max(SIDEBAR_MIN, Math.min(SIDEBAR_MAX, startWidth + delta))
  sidebarWidth.value = newWidth
}

function onResizeEnd() {
  isResizing.value = false
  document.removeEventListener('mousemove', onResizeMove)
  document.removeEventListener('mouseup', onResizeEnd)
  document.body.style.cursor = ''
  document.body.style.userSelect = ''
  saveWidth(sidebarWidth.value)
}

// --- Tree filter ---
function filterNode(value: string, data: TocItem) {
  if (!value) return true
  return data.label.toLowerCase().includes(value.toLowerCase())
}

function handleNodeClick(data: TocItem) {
  emit('nodeClick', data)
}

// Debounced search filter (skip when search results panel is showing)
const debouncedFilter = useDebounceFn((val: string) => {
  tocTreeRef.value?.filter(val)
}, 300)

watch(() => props.searchQuery, (val) => {
  if (val.length >= 2) return // search results panel is active, skip tree filtering
  debouncedFilter(val)
})

defineExpose({
  tocTreeRef,
  tocScrollRef
})
</script>

<style scoped>
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
