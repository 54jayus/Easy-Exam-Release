<template>
  <div class="h-full flex flex-col">
    <!-- Search Results Header -->
    <div class="px-4 py-3 border-b border-slate-200 bg-white shrink-0">
      <div class="flex items-center justify-between">
        <div class="flex items-center gap-2">
          <el-icon class="text-primary-600"><Search /></el-icon>
          <span class="text-sm font-medium text-slate-700">
            搜索结果
            <span v-if="resultCount > 0" class="text-primary-600">({{ resultCount }})</span>
          </span>
        </div>
        <button
          @click="$emit('close')"
          class="p-1 hover:bg-slate-100 rounded transition-colors"
          aria-label="关闭搜索结果"
        >
          <el-icon class="text-slate-400 hover:text-slate-600"><Close /></el-icon>
        </button>
      </div>
    </div>

    <!-- Search Results List -->
    <div class="flex-1 overflow-y-auto custom-scrollbar">
      <!-- Loading State -->
      <div v-if="isSearching" class="p-8 text-center">
        <el-icon class="animate-spin text-primary-600 text-2xl"><Loading /></el-icon>
        <p class="text-sm text-slate-500 mt-2">搜索中...</p>
      </div>

      <!-- No Results -->
      <div v-else-if="!hasResults && searchQuery" class="p-8 text-center">
        <el-icon class="text-slate-300 text-4xl mb-3"><DocumentDelete /></el-icon>
        <p class="text-sm text-slate-500">未找到匹配的内容</p>
        <p class="text-xs text-slate-400 mt-1">试试其他关键词</p>
      </div>

      <!-- Empty State -->
      <div v-else-if="!searchQuery" class="p-8 text-center">
        <el-icon class="text-slate-300 text-4xl mb-3"><Search /></el-icon>
        <p class="text-sm text-slate-500">输入关键词搜索</p>
        <p class="text-xs text-slate-400 mt-1">支持搜索标题和正文内容</p>
      </div>

      <!-- Results List -->
      <div v-else class="p-3 space-y-2">
        <div
          v-for="result in searchResults"
          :key="result.id"
          @click="$emit('result-click', result)"
          class="p-3 bg-white hover:bg-primary-50 border border-slate-200 hover:border-primary-300 rounded-lg cursor-pointer transition-all group"
        >
          <!-- Section Title -->
          <div class="flex items-start gap-2 mb-2">
            <el-icon class="text-primary-600 mt-0.5 shrink-0"><Document /></el-icon>
            <h4 class="text-sm font-medium text-slate-700 group-hover:text-primary-700 line-clamp-1">
              {{ result.title }}
            </h4>
          </div>

          <!-- Matched Content -->
          <div class="text-xs text-slate-600 leading-relaxed pl-6">
            <span class="text-slate-400">{{ result.beforeText }}</span>
            <mark class="bg-yellow-200 text-slate-900 px-1 py-0.5 rounded font-medium">{{ result.matchedText }}</mark>
            <span class="text-slate-400">{{ result.afterText }}</span>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { Search, Close, Loading, DocumentDelete, Document } from '@element-plus/icons-vue'
import type { SearchResult } from './composables/useFullTextSearch'

defineProps<{
  searchResults: SearchResult[]
  isSearching: boolean
  hasResults: boolean
  resultCount: number
  searchQuery: string
}>()

defineEmits<{
  close: []
  'result-click': [result: SearchResult]
}>()
</script>

<style scoped>
.custom-scrollbar::-webkit-scrollbar {
  width: 5px;
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

.line-clamp-1 {
  display: -webkit-box;
  -webkit-line-clamp: 1;
  -webkit-box-orient: vertical;
  overflow: hidden;
}

@keyframes spin {
  from { transform: rotate(0deg); }
  to { transform: rotate(360deg); }
}
.animate-spin {
  animation: spin 1s linear infinite;
}
</style>
