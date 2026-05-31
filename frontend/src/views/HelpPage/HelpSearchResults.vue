<template>
  <div class="h-full flex flex-col">
    <!-- Search Results Header -->
    <div class="px-4 py-3 border-b border-slate-100 bg-slate-50/50 shrink-0">
      <div class="flex items-center justify-between">
        <div class="flex items-center gap-2">
          <el-icon class="text-primary-500" :size="15"><Search /></el-icon>
          <span class="text-xs font-bold text-slate-500 uppercase tracking-wider">
            搜索结果
            <span v-if="resultCount > 0" class="text-primary-600 normal-case tracking-normal ml-1">({{ resultCount }})</span>
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
    <div class="flex-1 overflow-y-auto custom-scrollbar" role="status" aria-live="polite">
      <!-- Loading State -->
      <div v-if="isSearching" class="p-8 text-center">
        <div class="w-10 h-10 bg-primary-50 rounded-xl flex items-center justify-center mx-auto mb-3">
          <el-icon class="animate-spin text-primary-500"><Loading /></el-icon>
        </div>
        <p class="text-sm text-slate-500">搜索中...</p>
      </div>

      <!-- No Results -->
      <div v-else-if="!hasResults && searchQuery" class="p-8 text-center">
        <div class="w-12 h-12 bg-slate-50 rounded-xl flex items-center justify-center mx-auto mb-3">
          <el-icon class="text-slate-300" :size="24"><DocumentDelete /></el-icon>
        </div>
        <p class="text-sm text-slate-600 font-medium">未找到匹配内容</p>
        <p class="text-xs text-slate-400 mt-1.5">试试其他关键词，或使用更短的搜索词</p>
      </div>

      <!-- Empty State -->
      <div v-else-if="!searchQuery" class="p-8 text-center">
        <div class="w-12 h-12 bg-slate-50 rounded-xl flex items-center justify-center mx-auto mb-3">
          <el-icon class="text-slate-300" :size="24"><Search /></el-icon>
        </div>
        <p class="text-sm text-slate-600 font-medium">搜索说明书</p>
        <p class="text-xs text-slate-400 mt-1.5">输入至少 2 个字符开始搜索</p>
      </div>

      <!-- Results List -->
      <div v-else class="p-3 space-y-1.5">
        <div
          v-for="(result, idx) in searchResults"
          :key="result.id"
          @click="$emit('result-click', result)"
          class="p-3 bg-white hover:bg-primary-50/70 border border-slate-100 hover:border-primary-200 rounded-lg cursor-pointer transition-all group"
        >
          <!-- Section Title -->
          <div class="flex items-start gap-2 mb-1.5">
            <span class="text-[10px] font-mono text-slate-300 bg-slate-50 group-hover:bg-primary-100 group-hover:text-primary-500 rounded px-1.5 py-0.5 shrink-0 transition-colors">{{ idx + 1 }}</span>
            <h4 class="text-sm font-medium text-slate-700 group-hover:text-primary-700 line-clamp-1">
              {{ result.title }}
            </h4>
          </div>

          <!-- Matched Content -->
          <div class="text-xs text-slate-500 leading-relaxed pl-8">
            <span class="text-slate-400">{{ result.beforeText }}</span>
            <mark class="bg-yellow-100 text-slate-800 px-1 py-0.5 rounded font-medium ring-1 ring-yellow-200/50">{{ result.matchedText }}</mark>
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
