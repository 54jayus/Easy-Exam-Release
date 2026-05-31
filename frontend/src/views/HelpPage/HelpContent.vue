<template>
  <main
    id="main-content"
    ref="contentScrollRef"
    class="flex-1 relative flex flex-col min-w-0 bg-white overflow-y-auto scroll-smooth custom-scrollbar"
    @scroll="$emit('scroll')"
  >
    <!-- Scroll Progress Bar -->
    <div class="sticky top-0 left-0 right-0 h-[3px] bg-slate-100 z-20" role="progressbar" :aria-valuenow="Math.round(scrollProgress)" aria-valuemin="0" aria-valuemax="100" aria-label="阅读进度">
      <div class="h-full bg-gradient-to-r from-primary-500 to-primary-400 transition-all duration-150 rounded-r-full" :style="{ width: scrollProgress + '%' }"></div>
    </div>

    <!-- 响应式内容包装容器 -->
    <div class="w-full pt-6 pb-8 px-6 md:px-10 lg:px-16 max-w-full md:max-w-none lg:max-w-5xl xl:max-w-6xl mx-auto">
      <div
        v-if="html"
        class="prose prose-slate prose-lg max-w-none
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
        v-html="html"
      ></div>

      <div v-else class="min-h-[400px] flex flex-col items-center justify-center text-slate-400">
        <div v-if="loading" class="w-full max-w-2xl animate-pulse space-y-6 pt-8">
          <div class="space-y-3">
            <div class="h-7 w-64 bg-slate-100 rounded-md"></div>
            <div class="h-4 w-40 bg-slate-50 rounded"></div>
          </div>
          <div class="space-y-3">
            <div class="h-4 w-full bg-slate-50 rounded"></div>
            <div class="h-4 w-5/6 bg-slate-50 rounded"></div>
            <div class="h-4 w-4/6 bg-slate-50 rounded"></div>
          </div>
          <div class="h-5 w-48 bg-slate-100 rounded-md mt-6"></div>
          <div class="space-y-3">
            <div class="h-4 w-full bg-slate-50 rounded"></div>
            <div class="h-4 w-3/4 bg-slate-50 rounded"></div>
          </div>
          <div class="space-y-3">
            <div class="h-4 w-full bg-slate-50 rounded"></div>
            <div class="h-4 w-5/6 bg-slate-50 rounded"></div>
            <div class="h-4 w-2/3 bg-slate-50 rounded"></div>
          </div>
        </div>
        <div v-else-if="error" class="flex flex-col items-center">
          <div class="w-16 h-16 bg-red-50 rounded-2xl flex items-center justify-center mb-4">
            <el-icon :size="32" class="text-red-300"><WarningFilled /></el-icon>
          </div>
          <p class="text-slate-600 font-medium mb-1">说明书加载失败</p>
          <p class="text-slate-400 text-sm mb-4">请检查网络连接后重试</p>
          <button
            @click="$emit('retry')"
            class="px-5 py-2.5 bg-primary-600 text-white rounded-lg hover:bg-primary-700 active:scale-[0.98] transition-all text-sm font-medium shadow-sm"
          >
            重新加载
          </button>
        </div>
        <div v-else class="flex flex-col items-center">
          <div class="w-16 h-16 bg-slate-50 rounded-2xl flex items-center justify-center mb-4">
            <el-icon :size="32" class="text-slate-200"><Document /></el-icon>
          </div>
          <p class="text-slate-500 font-medium">暂无说明书内容</p>
        </div>
      </div>

      <!-- Footer -->
      <div class="mt-8 pt-4 pb-6 border-t border-slate-100 text-center" v-if="html">
        <p class="text-slate-400 text-xs leading-relaxed">Powered by 智能考务系统 &copy; {{ new Date().getFullYear() }}</p>
      </div>
    </div>

    <!-- Back to Top (fixed position, stays visible while scrolling) -->
    <transition name="fade-up">
      <button
        v-if="showBackToTop"
        @click="$emit('scrollToTop')"
        aria-label="返回顶部"
        class="fixed bottom-8 right-8 p-3 bg-white/90 backdrop-blur-sm text-slate-600 rounded-full shadow-lg shadow-slate-200/50 border border-slate-200/60 hover:text-primary-600 hover:border-primary-200 hover:shadow-primary-100/50 hover:-translate-y-0.5 active:scale-95 transition-all duration-300 z-30 flex items-center justify-center"
      >
        <el-icon :size="18"><ArrowUp /></el-icon>
      </button>
    </transition>
  </main>
</template>

<script setup lang="ts">
import { ref } from 'vue'
import { Document, ArrowUp, WarningFilled } from '@element-plus/icons-vue'

defineProps<{
  html: string
  loading: boolean
  error: boolean
  scrollProgress: number
  showBackToTop: boolean
}>()

defineEmits<{
  scroll: []
  scrollToTop: []
  retry: []
}>()

const contentScrollRef = ref<HTMLElement>()

defineExpose({
  contentScrollRef
})
</script>

<style scoped>
/* Markdown Content Refinements */
:deep(.prose) {
  font-family: 'Inter', system-ui, -apple-system, sans-serif;
  margin-bottom: 0 !important;
  padding-bottom: 0 !important;
}

/* Remove bottom margin from last child in prose */
:deep(.prose > *:last-child) {
  margin-bottom: 0 !important;
  padding-bottom: 0 !important;
}

/* Ensure main content has no bottom spacing */
main {
  padding-bottom: 0 !important;
  margin-bottom: 0 !important;
}

/* Anchor scroll offset — compensate for sticky progress bar */
:deep(.prose h2[id]),
:deep(.prose h3[id]) {
  scroll-margin-top: 16px;
}

/* Back-to-top button transition */
.fade-up-enter-active,
.fade-up-leave-active {
  transition: all 0.25s ease;
}
.fade-up-enter-from,
.fade-up-leave-to {
  opacity: 0;
  transform: translateY(8px);
}
</style>
