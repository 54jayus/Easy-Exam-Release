<template>
  <div class="h-full flex flex-col bg-white overflow-hidden font-sans text-slate-600 animate-fade-in -mt-6 -mx-6 md:-mt-8 md:-mx-8">
    <!-- Skip to main content link for accessibility -->
    <a
      href="#main-content"
      class="sr-only focus:not-sr-only focus:absolute focus:top-4 focus:left-4 focus:z-50 focus:px-4 focus:py-2 focus:bg-primary-600 focus:text-white focus:rounded"
    >
      跳转到主内容
    </a>

    <!-- Header -->
    <HelpHeader
      ref="headerRef"
      v-model="searchQuery"
    />

    <!-- Main Content Layout -->
    <div class="flex-1 flex w-full relative overflow-hidden min-h-0">
      <!-- Sidebar Navigation or Search Results -->
      <transition name="slide-fade" mode="out-in">
        <!-- Search Results Panel -->
        <HelpSearchResults
          v-if="showSearchResults"
          :search-results="searchResults"
          :is-searching="isSearching"
          :has-results="hasResults"
          :result-count="resultCount"
          :search-query="searchQuery"
          @close="clearSearch"
          @result-click="handleSearchResultClick"
          class="shrink-0 flex flex-col border-r border-slate-100 bg-slate-50/30 h-full hidden md:flex"
          :style="{ width: sidebarWidth + 'px' }"
        />

        <!-- Sidebar Navigation -->
        <HelpSidebar
          v-else
          ref="sidebarRef"
          :toc-data="tocData"
          :search-query="searchQuery"
          @node-click="handleNodeClick"
          @width-change="sidebarWidth = $event"
        />
      </transition>

      <!-- Content -->
      <HelpContent
        ref="contentRef"
        :html="highlightedHtml"
        :loading="loading.manual"
        :error="loadError"
        :scroll-progress="scrollProgress"
        :show-back-to-top="showBackToTop"
        @scroll="onContentScroll"
        @scroll-to-top="scrollToTop"
        @retry="handleRetry"
      />
    </div>

    <!-- Mobile TOC floating button -->
    <button
      class="md:hidden fixed bottom-6 right-6 z-40 w-12 h-12 bg-primary-600 text-white rounded-full shadow-lg shadow-primary-600/25 hover:bg-primary-700 active:scale-95 transition-all flex items-center justify-center"
      @click="mobileDrawerVisible = true"
      aria-label="打开目录导航"
    >
      <el-icon :size="20"><List /></el-icon>
    </button>

    <!-- Mobile TOC drawer -->
    <el-drawer
      v-model="mobileDrawerVisible"
      direction="ltr"
      size="78%"
      :with-header="false"
      class="md:hidden"
    >
      <div class="h-full flex flex-col bg-slate-50/30">
        <div class="px-4 py-3.5 border-b border-slate-100 bg-white flex items-center justify-between shrink-0">
          <h3 class="text-xs font-bold text-slate-400 uppercase tracking-wider flex items-center gap-2">
            <el-icon :size="14"><List /></el-icon> 目录导航
          </h3>
          <button
            @click="mobileDrawerVisible = false"
            class="p-1.5 hover:bg-slate-100 rounded-md transition-colors"
            aria-label="关闭目录"
          >
            <el-icon class="text-slate-400" :size="16"><Close /></el-icon>
          </button>
        </div>
        <div class="flex-1 overflow-y-auto p-3 custom-scrollbar">
          <el-tree
            :data="tocData"
            :props="{ children: 'children', label: 'label' }"
            node-key="id"
            :highlight-current="true"
            default-expand-all
            @node-click="handleMobileNodeClick"
            class="bg-transparent !p-0"
            :indent="12"
          >
            <template #default="{ node, data }">
              <div
                class="flex items-center gap-2 py-2 px-2 w-full rounded-md"
                :class="[
                  node.isCurrent
                    ? 'bg-primary-50 text-primary-700'
                    : 'text-slate-600'
                ]"
              >
                <span
                  v-if="data.level === 1 && data.sectionNum"
                  class="text-[10px] font-mono text-slate-400 shrink-0"
                  :class="{ '!text-primary-500': node.isCurrent }"
                >{{ data.sectionNum }}</span>
                <span
                  class="text-sm truncate"
                  :class="{
                    'font-semibold': data.level === 1,
                    'pl-0': data.level === 1,
                    'pl-4': data.level !== 1
                  }"
                >{{ node.label }}</span>
              </div>
            </template>
          </el-tree>
        </div>
      </div>
    </el-drawer>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, onActivated, onDeactivated, onBeforeUnmount, watch, computed } from 'vue'
import { ElMessage } from 'element-plus'
import { useDebounceFn } from '@vueuse/core'
import { List, Close } from '@element-plus/icons-vue'
import HelpHeader from './HelpPage/HelpHeader.vue'
import HelpSidebar from './HelpPage/HelpSidebar.vue'
import HelpSearchResults from './HelpPage/HelpSearchResults.vue'
import HelpContent from './HelpPage/HelpContent.vue'
import { useMarkdown, useTocGeneration, useScrollSpy, useFullTextSearch } from './HelpPage/composables'
import type { TocItem, SearchResult } from './HelpPage/composables'

// State
const searchQuery = ref('')
const sidebarRef = ref()
const contentRef = ref()
const headerRef = ref()
const mobileDrawerVisible = ref(false)
const sidebarWidth = ref(240)

// Composables
const { manualHtml, loading, loadError, loadManual } = useMarkdown()
const { tocData, generateToc, injectHeadingIds } = useTocGeneration()
const {
  searchResults,
  isSearching,
  hasResults,
  resultCount,
  performSearch: performSearchRaw,
  clearSearch: clearSearchResults,
  highlightText
} = useFullTextSearch()

// Get refs from child components
const tocTreeRef = ref()
const tocScrollRef = ref<HTMLElement>()
const contentScrollRef = ref<HTMLElement>()

// Initialize scroll spy after refs are available
const {
  scrollProgress,
  showBackToTop,
  rebuildScrollSpyIndex,
  onContentScroll,
  scrollToTop
} = useScrollSpy(tocData, contentScrollRef, tocTreeRef, tocScrollRef)

// Computed
const showSearchResults = computed(() => searchQuery.value.trim().length >= 2)

// Highlighted HTML — updated together with search results inside debounce
const highlightedContent = ref('')
const highlightedHtml = computed(() => {
  if (!searchQuery.value || searchQuery.value.trim().length < 2) {
    return manualHtml.value
  }
  return highlightedContent.value || manualHtml.value
})

// Watch search query
const debouncedSearch = useDebounceFn((query: string) => {
  performSearchRaw(manualHtml.value, query)
  highlightedContent.value = highlightText(manualHtml.value, query)
}, 300)

watch(searchQuery, (newQuery) => {
  if (newQuery.trim().length >= 2) {
    debouncedSearch(newQuery)
  } else {
    clearSearchResults()
    highlightedContent.value = ''
  }
})

// Keyboard shortcut: Ctrl/Cmd+K to focus search
function handleKeydown(e: KeyboardEvent) {
  if ((e.metaKey || e.ctrlKey) && e.key === 'k') {
    e.preventDefault()
    headerRef.value?.inputRef?.focus()
  }
}

// Initialization
onMounted(async () => {
  // Get refs from child components
  if (sidebarRef.value) {
    tocTreeRef.value = sidebarRef.value.tocTreeRef
    tocScrollRef.value = sidebarRef.value.tocScrollRef
  }
  if (contentRef.value) {
    contentScrollRef.value = contentRef.value.contentScrollRef
  }

  // Load manual
  const content = await loadManual()
  if (content) {
    generateToc(content)
    await injectHeadingIds(contentScrollRef)
    rebuildScrollSpyIndex()
  }

  document.addEventListener('keydown', handleKeydown)
})

onBeforeUnmount(() => {
  document.removeEventListener('keydown', handleKeydown)
})

// Re-establish refs and keyboard listener when re-activated by keepAlive
onActivated(() => {
  if (sidebarRef.value) {
    tocTreeRef.value = sidebarRef.value.tocTreeRef
    tocScrollRef.value = sidebarRef.value.tocScrollRef
  }
  if (contentRef.value) {
    contentScrollRef.value = contentRef.value.contentScrollRef
  }
  document.removeEventListener('keydown', handleKeydown)
  document.addEventListener('keydown', handleKeydown)
})

onDeactivated(() => {
  document.removeEventListener('keydown', handleKeydown)
})

// Methods
function handleNodeClick(data: TocItem) {
  scrollToAnchor(data.anchor)
}

function handleMobileNodeClick(data: TocItem) {
  mobileDrawerVisible.value = false
  setTimeout(() => scrollToAnchor(data.anchor), 300)
}

function handleSearchResultClick(result: SearchResult) {
  scrollToAnchor(result.anchor)
}

function scrollToAnchor(anchor: string) {
  const element = document.getElementById(anchor)
  if (element && contentScrollRef.value) {
    element.scrollIntoView({ behavior: 'smooth', block: 'start' })

    // Move focus to target heading for accessibility
    element.setAttribute('tabindex', '-1')
    element.focus()

    // Remove tabindex after a delay to avoid affecting normal tab order
    setTimeout(() => {
      element.removeAttribute('tabindex')
    }, 1000)
  }
}

function clearSearch() {
  searchQuery.value = ''
  clearSearchResults()
}

async function handleRetry() {
  const content = await loadManual()
  if (content) {
    generateToc(content)
    await injectHeadingIds(contentScrollRef)
    rebuildScrollSpyIndex()
  }
}
</script>

<style scoped>
@keyframes fade-in {
  from { opacity: 0; transform: translateY(10px); }
  to { opacity: 1; transform: translateY(0); }
}
.animate-fade-in {
  animation: fade-in 0.5s ease-out forwards;
}

/* Transition animations */
.slide-fade-enter-active,
.slide-fade-leave-active {
  transition: all 0.3s ease;
}

.slide-fade-enter-from {
  opacity: 0;
  transform: translateX(-20px);
}

.slide-fade-leave-to {
  opacity: 0;
  transform: translateX(-20px);
}

/* Search highlight styles */
:deep(mark) {
  background-color: #fef9c3;
  color: #0f172a;
  padding: 2px 5px;
  border-radius: 3px;
  font-weight: 600;
  box-decoration-break: clone;
  -webkit-box-decoration-break: clone;
}
</style>
