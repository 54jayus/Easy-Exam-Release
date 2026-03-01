<template>
  <div class="min-h-full -m-6 md:-m-8 flex flex-col bg-white overflow-hidden font-sans text-slate-600 animate-fade-in">
    <!-- Hero Header Section -->
    <div class="shrink-0 bg-gradient-to-b from-slate-50 to-white border-b border-slate-100 relative z-10">
      <div class="max-w-7xl mx-auto px-6 py-6">
        <div class="flex flex-col md:flex-row md:items-center justify-between gap-6">
          <!-- Title Group -->
          <div class="flex items-start gap-4">
             <div class="p-3 bg-white rounded-xl shadow-sm border border-slate-100 text-primary-600 ring-1 ring-slate-100/50">
              <el-icon :size="26"><Reading /></el-icon>
            </div>
            <div>
              <h1 class="text-2xl font-bold text-slate-900 tracking-tight">帮助中心</h1>
              <p class="text-slate-500 text-sm mt-1">智能考务系统使用说明书</p>
            </div>
          </div>

          <!-- Search & Actions -->
          <div class="flex items-center gap-3 w-full md:w-auto">
            <div class="relative group w-full md:w-80">
              <div class="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none">
                <el-icon class="text-slate-400 group-focus-within:text-primary-500 transition-colors"><Search /></el-icon>
              </div>
              <input 
                v-model="searchQuery"
                type="text"
                placeholder="搜索说明书内容..." 
                class="w-full pl-10 pr-4 py-2.5 bg-white border border-slate-200 rounded-lg text-sm focus:outline-none focus:border-primary-500 focus:ring-4 focus:ring-primary-500/10 transition-all shadow-sm placeholder-slate-400"
              />
            </div>
            <button 
              @click="exportManual"
              class="flex items-center gap-2 px-4 py-2.5 bg-white border border-slate-200 hover:border-primary-200 hover:bg-primary-50 text-slate-700 hover:text-primary-700 rounded-lg text-sm font-medium transition-all shadow-sm active:scale-95 whitespace-nowrap"
            >
              <el-icon><Download /></el-icon>
              <span class="hidden sm:inline">导出 PDF</span>
            </button>
          </div>
        </div>
      </div>
    </div>

    <!-- Main Content Layout -->
    <div class="flex-1 flex overflow-hidden max-w-7xl mx-auto w-full px-6">
      <!-- Sidebar Navigation -->
      <aside class="w-72 shrink-0 flex flex-col border-r border-slate-100 bg-slate-50/30 hidden md:flex">
         <div class="p-4 h-full flex flex-col">
          <h3 class="text-xs font-bold text-slate-400 uppercase tracking-wider mb-4 px-2 flex items-center gap-2">
            <el-icon><List /></el-icon> 目录导航
          </h3>
          <div ref="tocScrollRef" class="flex-1 overflow-y-auto custom-scrollbar pr-2 -mr-2">
            <el-tree
              ref="tocTreeRef"
              :data="tocData"
              :props="defaultProps"
              node-key="id"
              :highlight-current="true"
              :filter-node-method="filterNode"
              default-expand-all
              @node-click="handleNodeClick"
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

      <!-- Markdown Content -->
      <main class="flex-1 relative flex flex-col min-w-0 bg-white">
         <!-- Scroll Progress Bar -->
        <div class="absolute top-0 left-0 right-0 h-0.5 bg-slate-100 z-20">
           <div class="h-full bg-primary-500 transition-all duration-150" :style="{ width: scrollProgress + '%' }"></div>
        </div>

        <div 
          ref="contentScrollRef" 
          class="flex-1 overflow-y-auto px-8 py-10 scroll-smooth custom-scrollbar"
          @scroll="onContentScroll"
        >
          <div class="max-w-3xl mx-auto pb-20">
             <div v-if="manualHtml" class="prose prose-slate prose-lg max-w-none 
              prose-headings:font-bold prose-headings:tracking-tight prose-headings:text-slate-900 
              prose-h1:text-3xl prose-h1:mb-8 prose-h2:text-2xl prose-h2:mt-12 prose-h2:mb-6 prose-h2:pb-2 prose-h2:border-b prose-h2:border-slate-100
              prose-h3:text-lg prose-h3:mt-8 prose-h3:mb-3 prose-h3:text-slate-800
              prose-p:text-slate-600 prose-p:leading-7 prose-p:mb-4
              prose-a:text-primary-600 prose-a:no-underline hover:prose-a:text-primary-500 hover:prose-a:underline
              prose-code:text-primary-600 prose-code:bg-primary-50 prose-code:px-1.5 prose-code:py-0.5 prose-code:rounded-md prose-code:font-medium prose-code:text-sm prose-code:before:content-none prose-code:after:content-none
              prose-pre:bg-slate-900 prose-pre:rounded-xl prose-pre:shadow-lg prose-pre:border prose-pre:border-slate-800
              prose-img:rounded-xl prose-img:shadow-md prose-img:border prose-img:border-slate-100 prose-img:my-8
              prose-blockquote:border-l-4 prose-blockquote:border-primary-400 prose-blockquote:bg-slate-50 prose-blockquote:pl-4 prose-blockquote:py-2 prose-blockquote:pr-4 prose-blockquote:rounded-r-lg prose-blockquote:text-slate-600 prose-blockquote:not-italic prose-blockquote:my-6
              prose-li:text-slate-600 prose-li:marker:text-slate-300"
              v-html="manualHtml"
            ></div>
            
            <div v-else class="min-h-[400px] flex flex-col items-center justify-center text-slate-400">
               <div v-if="loading.manual" class="flex flex-col items-center animate-pulse">
                  <div class="w-16 h-16 bg-slate-100 rounded-full mb-4"></div>
                  <div class="h-4 w-48 bg-slate-100 rounded mb-2"></div>
                  <div class="h-4 w-32 bg-slate-100 rounded"></div>
               </div>
               <div v-else class="flex flex-col items-center">
                 <el-icon :size="48" class="mb-4 text-slate-200"><Document /></el-icon>
                 <p>暂无说明书内容</p>
               </div>
            </div>

            <!-- Footer -->
            <div class="mt-20 pt-10 border-t border-slate-100 text-center" v-if="manualHtml">
              <p class="text-slate-400 text-sm">Powered by 智能考务系统 &copy; {{ new Date().getFullYear() }}</p>
            </div>
          </div>
        </div>
        
        <!-- Back to Top -->
        <button 
          @click="scrollToTop"
          class="absolute bottom-8 right-8 p-3 bg-white text-slate-600 rounded-full shadow-lg border border-slate-100 hover:text-primary-600 hover:border-primary-200 hover:-translate-y-1 transition-all duration-300 z-30 flex items-center justify-center"
          :class="showBackToTop ? 'opacity-100 translate-y-0' : 'opacity-0 translate-y-4 pointer-events-none'"
        >
          <el-icon :size="20"><ArrowUp /></el-icon>
        </button>
      </main>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, watch, nextTick, computed } from "vue"
import { ElMessage } from "element-plus"
import { 
  Search, Download, List, Reading, Document, ArrowUp
} from '@element-plus/icons-vue'
import { marked } from 'marked'
import { pythonBackend } from "@/lib/pythonBackend"

// Types
interface TocItem {
  id: string
  label: string
  level: number
  anchor: string
  children?: TocItem[]
}

// State
const searchQuery = ref("")
const manualMarkdown = ref("")
const manualHtml = ref("")
const tocData = ref<TocItem[]>([])
const scrollProgress = ref(0)
const showBackToTop = ref(false)

const loading = ref({
  manual: false
})

// Refs
const tocTreeRef = ref()
const tocScrollRef = ref<HTMLElement>()
const contentScrollRef = ref<HTMLElement>()

// Tree Props
const defaultProps = {
  children: 'children',
  label: 'label'
}

type ScrollSpyItem = {
  anchor: string
  tocId: string
  top: number
}

const activeTocId = ref("")
let scrollSpyIndex: ScrollSpyItem[] = []
let anchorToTocId = new Map<string, string>()
let scrollSyncScheduled = false
let tocEnsureVisibleScheduled = false

function ensureActiveTocVisible() {
  const container = tocScrollRef.value
  if (!container) return

  // Using a more robust selector to find the active node
  const el = container.querySelector<HTMLElement>(".el-tree-node.is-current")
  if (!el) return

  const containerRect = container.getBoundingClientRect()
  const elRect = el.getBoundingClientRect()
  const padding = 20

  if (elRect.top < containerRect.top + padding) {
    container.scrollTop -= (containerRect.top + padding - elRect.top)
  } else if (elRect.bottom > containerRect.bottom - padding) {
    container.scrollTop += (elRect.bottom - (containerRect.bottom - padding))
  }
}

function scheduleEnsureActiveTocVisible() {
  if (tocEnsureVisibleScheduled) return
  tocEnsureVisibleScheduled = true
  requestAnimationFrame(() => {
    tocEnsureVisibleScheduled = false
    ensureActiveTocVisible()
  })
}

// Markdown options and heading anchors
marked.setOptions({
  gfm: true,
  breaks: true
})
function slugify(text: string) {
  return text
    .trim()
    .toLowerCase()
    .replace(/[^\w\u4e00-\u9fa5]+/g, "-")
    .replace(/-+/g, "-")
}
function escapeRegExp(str: string) {
  return str.replace(/[.*+?^${}()|[\]\\]/g, '\\$&')
}
function injectHeadingIds() {
  const html = manualHtml.value || ""
  let updated = html
  tocData.value.forEach(item => {
    const tag = item.level === 1 ? 'h2' : 'h3'
    const escaped = escapeRegExp(item.label)
    // Match heading tags more robustly
    const re = new RegExp(`<${tag}[^>]*>\\s*${escaped}\\s*</${tag}>`, 'i')
    updated = updated.replace(re, `<${tag} id="${item.anchor}">${item.label}</${tag}>`)
    ;(item.children || []).forEach(child => {
      const escapedChild = escapeRegExp(child.label)
      const reChild = new RegExp(`<h3[^>]*>\\s*${escapedChild}\\s*</h3>`, 'i')
      updated = updated.replace(reChild, `<h3 id="${child.anchor}">${child.label}</h3>`)
    })
  })
  manualHtml.value = updated
}

function rebuildScrollSpyIndex() {
  anchorToTocId = new Map<string, string>()
  const stack: TocItem[] = [...(tocData.value || [])]
  while (stack.length) {
    const item = stack.shift()!
    anchorToTocId.set(item.anchor, item.id)
    if (item.children?.length) stack.unshift(...item.children)
  }

  const container = contentScrollRef.value
  if (!container) {
    scrollSpyIndex = []
    return
  }

  const headings = Array.from(container.querySelectorAll<HTMLElement>("h2[id], h3[id]"))
  scrollSpyIndex = headings
    .map((el) => {
      const anchor = el.id
      const tocId = anchorToTocId.get(anchor)
      if (!tocId) return null
      return { anchor, tocId, top: el.offsetTop }
    })
    .filter((x): x is ScrollSpyItem => Boolean(x))
    .sort((a, b) => a.top - b.top)

  syncTocByScroll()
}

function syncTocByScroll() {
  const container = contentScrollRef.value
  if (!container || scrollSpyIndex.length === 0) return

  const scrollTop = container.scrollTop
  const threshold = 120
  const target = scrollTop + threshold

  let candidate: ScrollSpyItem | null = null
  for (const item of scrollSpyIndex) {
    if (item.top <= target) candidate = item
    else break
  }
  // If we are at the bottom, select the last one
  if (container.scrollHeight - container.scrollTop <= container.clientHeight + 50) {
     candidate = scrollSpyIndex[scrollSpyIndex.length - 1]
  }

  if (!candidate && scrollSpyIndex.length > 0) candidate = scrollSpyIndex[0]

  if (candidate && activeTocId.value !== candidate.tocId) {
    activeTocId.value = candidate.tocId
    tocTreeRef.value?.setCurrentKey?.(candidate.tocId)
    nextTick(() => {
      scheduleEnsureActiveTocVisible()
    })
  }
}

// Initialization
onMounted(async () => {
  await loadManual()
})

// Watchers
watch(searchQuery, (val) => {
  tocTreeRef.value?.filter(val)
})

// Methods
async function loadManual() {
  loading.value.manual = true
  try {
    // Call backend to get manual content
    const res = await pythonBackend.request<{ content: string }>("system.getHelpManual", {})
    const content = res.content || ""
    
    if (!content) {
      throw new Error("Empty manual content")
    }

    manualMarkdown.value = content
    manualHtml.value = await marked(content)
    generateToc(content)
    injectHeadingIds()
    await nextTick()
    rebuildScrollSpyIndex()
  } catch (e) {
    console.error(e)
    ElMessage.error("说明书加载失败")
  } finally {
    loading.value.manual = false
  }
}

function generateToc(markdown: string) {
  const lines = markdown.split('\n')
  const toc: TocItem[] = []
  let currentLevel1: TocItem | null = null
  let currentLevel2: TocItem | null = null
  
  lines.forEach((line, index) => {
    const h1Match = line.match(/^#\s+(.+)/)
    const h2Match = line.match(/^##\s+(.+)/)
    const h3Match = line.match(/^###\s+(.+)/)
    
    if (h1Match) {
      // H1 is usually title, skip or add as root
    } else if (h2Match) {
      const anchorId = `header-${slugify(h2Match[1])}`
      const item: TocItem = {
        id: `h2-${index}`,
        label: h2Match[1],
        level: 1,
        anchor: anchorId,
        children: []
      }
      toc.push(item)
      currentLevel1 = item
      currentLevel2 = null
    } else if (h3Match && currentLevel1) {
      const anchorId = `header-${slugify(h3Match[1])}`
      const item: TocItem = {
        id: `h3-${index}`,
        label: h3Match[1],
        level: 2,
        anchor: anchorId
      }
      currentLevel1.children?.push(item)
    }
  })
  
  tocData.value = toc
}

function filterNode(value: string, data: TocItem) {
  if (!value) return true
  return data.label.toLowerCase().includes(value.toLowerCase())
}

function handleNodeClick(data: TocItem) {
  const element = document.getElementById(data.anchor)
  if (element && contentScrollRef.value) {
    element.scrollIntoView({ behavior: 'smooth', block: 'start' })
  }
}

function onContentScroll() {
  if (!contentScrollRef.value) return
  
  const { scrollTop, scrollHeight, clientHeight } = contentScrollRef.value
  scrollProgress.value = (scrollTop / (scrollHeight - clientHeight)) * 100
  showBackToTop.value = scrollTop > 400
  
  if (scrollSyncScheduled) return
  scrollSyncScheduled = true
  requestAnimationFrame(() => {
    scrollSyncScheduled = false
    syncTocByScroll()
  })
}

function scrollToTop() {
  contentScrollRef.value?.scrollTo({ top: 0, behavior: 'smooth' })
}

function exportManual() {
  ElMessage.info("正在准备导出说明书...")
  // Implementation depends on backend capability
}

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
  display: none; /* Hide default arrows */
}

/* Markdown Content Refinements */
:deep(.prose) {
  font-family: 'Inter', system-ui, -apple-system, sans-serif;
}

@keyframes fade-in {
  from { opacity: 0; transform: translateY(10px); }
  to { opacity: 1; transform: translateY(0); }
}
.animate-fade-in {
  animation: fade-in 0.5s ease-out forwards;
}
</style>
