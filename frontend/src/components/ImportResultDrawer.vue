<template>
  <el-drawer
    :model-value="visible"
    :title="title"
    direction="rtl"
    size="420px"
    @update:model-value="$emit('update:visible', $event)"
  >
    <div class="space-y-4 p-4">
      <!-- Success -->
      <div v-if="successMessage" class="flex items-start gap-3 p-3 bg-emerald-50 text-emerald-700 rounded-xl border border-emerald-100 text-sm">
        <el-icon class="mt-0.5 flex-shrink-0"><CircleCheckFilled /></el-icon>
        <span>{{ successMessage }}</span>
      </div>

      <!-- Errors -->
      <div v-if="errors.length" class="space-y-2">
        <div class="text-xs font-bold text-rose-500 uppercase tracking-wider">
          错误（{{ errors.length }}）
        </div>
        <div
          v-for="(err, index) in errors"
          :key="'e-' + index"
          class="flex items-start gap-3 p-3 bg-rose-50 text-rose-700 rounded-xl border border-rose-100 text-sm"
        >
          <el-icon class="mt-0.5 flex-shrink-0"><WarningFilled /></el-icon>
          <span>{{ err }}</span>
        </div>
      </div>

      <!-- Warnings -->
      <div v-if="warnings.length" class="space-y-2">
        <div class="text-xs font-bold text-amber-500 uppercase tracking-wider">
          警告（{{ warnings.length }}）
        </div>
        <div
          v-for="(warn, index) in warnings"
          :key="'w-' + index"
          class="flex items-start gap-3 p-3 bg-amber-50 text-amber-700 rounded-xl border border-amber-100 text-sm"
        >
          <el-icon class="mt-0.5 flex-shrink-0"><InfoFilled /></el-icon>
          <span>{{ warn }}</span>
        </div>
      </div>

      <!-- Empty state -->
      <div v-if="!successMessage && !errors.length && !warnings.length"
        class="text-center text-slate-400 py-8 text-sm">
        暂无校验结果
      </div>
    </div>
  </el-drawer>
</template>

<script setup lang="ts">
import { CircleCheckFilled, InfoFilled, WarningFilled } from '@element-plus/icons-vue'

withDefaults(defineProps<{
  visible: boolean
  title?: string
  errors?: string[]
  warnings?: string[]
  successMessage?: string
}>(), {
  title: '导入结果',
  errors: () => [],
  warnings: () => [],
  successMessage: '',
})

defineEmits<{
  'update:visible': [value: boolean]
}>()
</script>
