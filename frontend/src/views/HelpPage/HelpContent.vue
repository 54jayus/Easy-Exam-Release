<template>
  <main
    id="main-content"
    ref="contentScrollRef"
    class="flex-1 relative flex flex-col min-w-0 bg-white overflow-y-auto scroll-smooth custom-scrollbar"
    @scroll="$emit('scroll')"
  >
    <!-- Scroll Progress Bar -->
    <div class="sticky top-0 left-0 right-0 h-0.5 bg-slate-100 z-20">
      <div class="h-full bg-primary-500 transition-all duration-150" :style="{ width: scrollProgress + '%' }"></div>
    </div>

    <!-- 响应式内容包装容器 -->
    <div class="w-full pt-4 pb-0 px-6 md:px-8 lg:px-12 max-w-full md:max-w-none lg:max-w-4xl xl:max-w-5xl mb-0">
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
        <div v-if="loading" class="flex flex-col items-center animate-pulse">
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
      <div class="mt-3 pt-2 pb-0 border-t border-slate-100 text-center" v-if="html">
        <p class="text-slate-400 text-xs mb-0 leading-none py-1">Powered by 智能考务系统 &copy; {{ new Date().getFullYear() }}</p>
      </div>

      <!-- Back to Top -->
      <button
        @click="$emit('scrollToTop')"
        aria-label="返回顶部"
        class="absolute bottom-8 right-8 p-3 bg-white text-slate-600 rounded-full shadow-lg border border-slate-100 hover:text-primary-600 hover:border-primary-200 hover:-translate-y-1 transition-all duration-300 z-30 flex items-center justify-center"
        :class="showBackToTop ? 'opacity-100 translate-y-0' : 'opacity-0 translate-y-4 pointer-events-none'"
      >
        <el-icon :size="20"><ArrowUp /></el-icon>
      </button>
    </div>
  </main>
</template>

<script setup lang="ts">
import { ref } from 'vue'
import { Document, ArrowUp } from '@element-plus/icons-vue'

defineProps<{
  html: string
  loading: boolean
  scrollProgress: number
  showBackToTop: boolean
}>()

defineEmits<{
  scroll: []
  scrollToTop: []
}>()

const contentScrollRef = ref<HTMLElement>()

defineExpose({
  contentScrollRef
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
</style>
