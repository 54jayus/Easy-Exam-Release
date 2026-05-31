<template>
  <div class="shrink-0 bg-white border-b border-slate-100 relative z-10">
    <div class="px-6 py-3.5">
      <div class="flex items-center gap-6">
        <!-- Title Group -->
        <div class="flex items-center gap-2.5 shrink-0">
          <div class="p-2 bg-primary-50 rounded-lg text-primary-600">
            <el-icon :size="20"><Reading /></el-icon>
          </div>
          <p class="text-sm font-semibold text-slate-700">使用说明书</p>
        </div>

        <!-- Search Box -->
        <div class="relative group flex-1 max-w-lg">
          <label for="help-search" class="sr-only">搜索说明书内容</label>
          <div class="absolute inset-y-0 left-0 pl-3.5 flex items-center pointer-events-none">
            <el-icon class="text-slate-400 group-focus-within:text-primary-500 transition-colors" :size="15"><Search /></el-icon>
          </div>
          <input
            ref="inputRef"
            :value="modelValue"
            @input="$emit('update:modelValue', ($event.target as HTMLInputElement).value)"
            type="text"
            id="help-search"
            :placeholder="`搜索说明书内容...  ${isMac ? '⌘' : 'Ctrl+'}K`"
            class="w-full pl-10 pr-4 py-2 bg-slate-50 border border-slate-200/80 rounded-lg text-sm focus:outline-none focus:bg-white focus:border-primary-400 focus:ring-2 focus:ring-primary-500/10 transition-all placeholder-slate-400 text-slate-700"
          />
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed } from 'vue'
import { Search, Reading } from '@element-plus/icons-vue'

defineProps<{
  modelValue: string
}>()

defineEmits<{
  'update:modelValue': [value: string]
}>()

const inputRef = ref<HTMLInputElement>()
const isMac = computed(() => navigator.platform.includes('Mac') || navigator.userAgent.includes('Mac'))

defineExpose({
  inputRef
})
</script>
