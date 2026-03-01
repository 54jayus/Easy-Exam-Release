<template>
  <div class="shrink-0 bg-gradient-to-b from-slate-50 to-white border-b border-slate-100 relative z-10">
    <div class="px-6 py-4">
      <div class="flex items-center justify-between gap-6">
        <!-- Left: Title & Search -->
        <div class="flex items-center gap-6 flex-1 min-w-0">
          <!-- Title Group -->
          <div class="flex items-start gap-4 shrink-0">
            <div class="p-3 bg-white rounded-xl shadow-sm border border-slate-100 text-primary-600 ring-1 ring-slate-100/50">
              <el-icon :size="26"><Reading /></el-icon>
            </div>
            <div>
              <h1 class="text-2xl font-bold text-slate-900 tracking-tight">帮助中心</h1>
              <p class="text-slate-500 text-sm mt-1">智能考务系统使用说明书</p>
            </div>
          </div>

          <!-- Search Box -->
          <div class="relative group w-full max-w-md">
            <div class="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none">
              <el-icon class="text-slate-400 group-focus-within:text-primary-500 transition-colors"><Search /></el-icon>
            </div>
            <input
              :value="modelValue"
              @input="$emit('update:modelValue', ($event.target as HTMLInputElement).value)"
              type="text"
              placeholder="搜索说明书内容..."
              aria-label="搜索说明书内容"
              class="w-full pl-10 pr-4 py-2.5 bg-white border border-slate-200 rounded-lg text-sm focus:outline-none focus:border-primary-500 focus:ring-4 focus:ring-primary-500/10 transition-all shadow-sm placeholder-slate-400"
            />
          </div>
        </div>

        <!-- Right: Export Button -->
        <button
          @click="$emit('export')"
          class="flex items-center gap-2 px-4 py-2.5 bg-white border border-slate-200 hover:border-primary-200 hover:bg-primary-50 text-slate-700 hover:text-primary-700 rounded-lg text-sm font-medium transition-all shadow-sm active:scale-95 whitespace-nowrap shrink-0"
        >
          <el-icon><Download /></el-icon>
          <span class="hidden sm:inline">导出 PDF</span>
        </button>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { Search, Download, Reading } from '@element-plus/icons-vue'

defineProps<{
  modelValue: string
}>()

defineEmits<{
  'update:modelValue': [value: string]
  export: []
}>()
</script>
