<template>
  <el-drawer
    :model-value="visible"
    @update:model-value="$emit('update:visible', $event)"
    title="系统操作日志"
    direction="rtl"
    :size="size"
    :modal="modal"
    class="!shadow-2xl"
  >
    <div class="flex flex-col h-full">
      <div class="flex justify-between items-center mb-6 px-1">
        <span class="text-xs text-slate-400">{{ description }}</span>
        <el-button size="small" type="danger" plain @click="$emit('clear-logs')" :disabled="logs.length === 0">
          <el-icon class="mr-1"><Delete /></el-icon> 清空
        </el-button>
      </div>
      <div class="flex-1 overflow-y-auto custom-scrollbar pr-2 pb-4">
        <div v-if="logs.length === 0" class="flex flex-col items-center justify-center h-[300px] text-slate-300">
          <el-icon class="text-5xl mb-3 opacity-20"><CollectionTag /></el-icon>
          <span class="text-sm">{{ emptyText }}</span>
        </div>
        <div v-else class="space-y-3">
          <div
            v-for="(log, idx) in logs"
            :key="idx"
            class="group relative"
          >
            <div
              class="absolute left-0 top-0 bottom-0 w-1 rounded-full transition-all"
              :class="{
                'bg-blue-400': log.level === 'info',
                'bg-emerald-400': log.level === 'success',
                'bg-amber-400': log.level === 'warning',
                'bg-rose-400': log.level === 'error'
              }"
            ></div>
            <div class="pl-4">
              <div class="flex items-center justify-between mb-1">
                <span class="text-[10px] font-mono text-slate-400 bg-slate-50 px-1.5 py-0.5 rounded">{{ log.time }}</span>
              </div>
              <div class="text-sm text-slate-600 break-words group-hover:text-slate-900 transition-colors bg-white p-3 rounded-xl border border-slate-100 shadow-sm group-hover:shadow-md group-hover:border-blue-100 group-hover:bg-blue-50/30">
                {{ log.msg }}
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  </el-drawer>
</template>

<script setup lang="ts">
import { computed } from 'vue'
import { Delete, CollectionTag } from '@element-plus/icons-vue'
import type { UiLogEntry } from '@/composables/useUiLogs'

interface Props {
  visible: boolean
  logs: UiLogEntry[]
  description?: string
  emptyText?: string
  size?: string
  modal?: boolean
}

const props = withDefaults(defineProps<Props>(), {
  description: '记录最近的操作与状态',
  emptyText: '暂无日志记录',
  size: '350px',
  modal: true,
})

const description = computed(() => props.description)
const emptyText = computed(() => props.emptyText)
const size = computed(() => props.size)
const modal = computed(() => props.modal)

defineEmits<{
  'update:visible': [value: boolean]
  'clear-logs': []
}>()
</script>
