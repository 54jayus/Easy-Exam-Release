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
      v-model="searchQuery"
      @export="handleExport"
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
          class="shrink-0 flex flex-col border-r border-slate-100 bg-slate-50/30 md:w-60 lg:w-70 xl:w-80 h-full"
        />

        <!-- Sidebar Navigation -->
        <HelpSidebar
          v-else
          ref="sidebarRef"
          :toc-data="tocData"
          :search-query="searchQuery"
          @node-click="handleNodeClick"
        />
      </transition>

      <!-- Content -->
      <HelpContent
        ref="contentRef"
        :html="highlightedHtml"
        :loading="loading.manual"
        :scroll-progress="scrollProgress"
        :show-back-to-top="showBackToTop"
        @scroll="onContentScroll"
        @scroll-to-top="scrollToTop"
      />
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, watch, computed } from 'vue'
import { ElMessage } from 'element-plus'
import html2pdf from 'html2pdf.js'
import HelpHeader from './HelpPage/HelpHeader.vue'
import HelpSidebar from './HelpPage/HelpSidebar.vue'
import HelpSearchResults from './HelpPage/HelpSearchResults.vue'
import HelpContent from './HelpPage/HelpContent.vue'
import { useMarkdown } from './HelpPage/composables/useMarkdown'
import { useTocGeneration } from './HelpPage/composables/useTocGeneration'
import { useScrollSpy } from './HelpPage/composables/useScrollSpy'
import { useFullTextSearch } from './HelpPage/composables/useFullTextSearch'
import type { TocItem } from './HelpPage/composables/useTocGeneration'
import type { SearchResult } from './HelpPage/composables/useFullTextSearch'

// State
const searchQuery = ref('')
const sidebarRef = ref()
const contentRef = ref()

// Composables
const { manualHtml, loading, loadManual } = useMarkdown()
const { tocData, generateToc, injectHeadingIds } = useTocGeneration()
const {
  searchResults,
  isSearching,
  hasResults,
  resultCount,
  performSearch,
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
const highlightedHtml = computed(() => {
  if (!manualHtml.value || !searchQuery.value || searchQuery.value.trim().length < 2) {
    return manualHtml.value
  }
  return highlightText(manualHtml.value, searchQuery.value)
})

// Watch search query
let searchDebounceTimer: ReturnType<typeof setTimeout> | null = null
watch(searchQuery, (newQuery) => {
  if (searchDebounceTimer) clearTimeout(searchDebounceTimer)

  if (newQuery.trim().length >= 2) {
    searchDebounceTimer = setTimeout(() => {
      performSearch(manualHtml.value, newQuery)
    }, 300)
  } else {
    clearSearchResults()
  }
})

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
    injectHeadingIds()
    rebuildScrollSpyIndex()
  }
})

// Methods
function handleNodeClick(data: TocItem) {
  scrollToAnchor(data.anchor)
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

async function handleExport() {
  if (!manualHtml.value) {
    ElMessage.warning('暂无内容可导出')
    return
  }

  try {
    ElMessage.info('正在生成 PDF...')

    const element = document.querySelector('.prose')
    if (!element) {
      ElMessage.error('无法找到内容元素')
      return
    }

    const opt = {
      margin: 1,
      filename: '使用说明书.pdf',
      image: { type: 'jpeg', quality: 0.98 },
      html2canvas: { scale: 2 },
      jsPDF: { unit: 'in', format: 'a4', orientation: 'portrait' }
    }

    await html2pdf().set(opt).from(element).save()
    ElMessage.success('导出成功')
  } catch (e) {
    console.error(e)
    ElMessage.error('导出失败')
  }
}
</script>

<style scoped>
/* Screen reader only utility */
.sr-only {
  position: absolute;
  width: 1px;
  height: 1px;
  padding: 0;
  margin: -1px;
  overflow: hidden;
  clip: rect(0, 0, 0, 0);
  white-space: nowrap;
  border-width: 0;
}

.sr-only:not(.focus\:not-sr-only:focus) {
  position: absolute;
  width: 1px;
  height: 1px;
  padding: 0;
  margin: -1px;
  overflow: hidden;
  clip: rect(0, 0, 0, 0);
  white-space: nowrap;
  border-width: 0;
}

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
  background-color: #fef08a;
  color: #0f172a;
  padding: 2px 4px;
  border-radius: 2px;
  font-weight: 500;
}
</style>
