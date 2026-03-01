<template>
  <el-dialog
    :model-value="visible"
    @update:model-value="$emit('update:visible', $event)"
    title="选科编排高级设置"
    width="520px"
    align-center
    :close-on-click-modal="false"
  >
    <div class="space-y-3">
      <div class="text-sm text-slate-600">
        从上到下表示考试优先级从高到低（用于"考试顺序建议"的分段规则）。
      </div>
      <div class="rounded-lg border border-slate-200 bg-slate-50/50 divide-y divide-slate-200">
        <div
          v-for="(subj, idx) in localOrder"
          :key="subj"
          class="flex items-center justify-between px-3 py-2"
          :class="dragOverIndex === idx ? 'bg-blue-50/60' : ''"
          @dragover.prevent="onDragOver(idx)"
          @dragenter.prevent="onDragOver(idx)"
          @drop.prevent="onDrop(idx)"
        >
          <div class="flex items-center gap-2 min-w-0">
            <div
              class="w-5 h-8 rounded flex flex-col items-center justify-center text-slate-400 hover:text-slate-600 cursor-move select-none"
              draggable="true"
              @dragstart="onDragStart(idx)"
              @dragend="onDragEnd"
            >
              <span class="leading-[8px] text-xs">⋮</span>
              <span class="leading-[8px] text-xs">⋮</span>
            </div>
            <div class="w-6 h-6 rounded-full bg-white border border-slate-200 flex items-center justify-center text-xs font-bold text-slate-700 shrink-0">
              {{ idx + 1 }}
            </div>
            <div class="font-bold text-slate-800 truncate">{{ subj }}</div>
          </div>
          <div class="flex items-center gap-2 shrink-0">
            <el-button size="small" :disabled="idx === 0" @click="moveItem(idx, -1)">上移</el-button>
            <el-button size="small" :disabled="idx === localOrder.length - 1" @click="moveItem(idx, 1)">下移</el-button>
          </div>
        </div>
      </div>
    </div>
    <template #footer>
      <div class="flex justify-between w-full">
        <el-button @click="resetToDefault">恢复默认</el-button>
        <div class="flex gap-2">
          <el-button @click="$emit('update:visible', false)">取消</el-button>
          <el-button type="primary" :loading="saving" @click="handleSave">保存</el-button>
        </div>
      </div>
    </template>
  </el-dialog>
</template>

<script setup lang="ts">
import { ref, watch } from 'vue'
import { ElMessage } from 'element-plus'
import { pythonBackend } from '@/lib/pythonBackend'
import { SUBJECT_PRIORITY_DEFAULT } from './composables/useRoomsState'

interface Props {
  visible: boolean
  priorityOrder: string[]
}

const props = defineProps<Props>()

const emit = defineEmits<{
  'update:visible': [value: boolean]
  'update:priorityOrder': [value: string[]]
  'log-success': [msg: string]
  'log-error': [msg: string]
}>()

const localOrder = ref<string[]>([...props.priorityOrder])
const draggingIndex = ref<number | null>(null)
const dragOverIndex = ref<number | null>(null)
const saving = ref(false)

// Watch for external changes
watch(() => props.priorityOrder, (newOrder) => {
  localOrder.value = [...newOrder]
}, { deep: true })

watch(() => props.visible, (isVisible) => {
  if (isVisible) {
    localOrder.value = [...props.priorityOrder]
  }
})

const normalizeOrder = (order: unknown): string[] => {
  const allowed = SUBJECT_PRIORITY_DEFAULT
  if (!Array.isArray(order)) return [...allowed]
  const cleaned = order.map((v) => String(v || '').trim()).filter((v) => allowed.includes(v))
  const dedup: string[] = []
  for (const s of cleaned) {
    if (!dedup.includes(s)) dedup.push(s)
  }
  for (const s of allowed) {
    if (!dedup.includes(s)) dedup.push(s)
  }
  return dedup.slice(0, allowed.length)
}

const moveItem = (index: number, delta: number) => {
  const nextIndex = index + delta
  if (nextIndex < 0 || nextIndex >= localOrder.value.length) return
  const arr = [...localOrder.value]
  const tmp = arr[index]
  arr[index] = arr[nextIndex]
  arr[nextIndex] = tmp
  localOrder.value = arr
}

const onDragStart = (index: number) => {
  draggingIndex.value = index
}

const onDragOver = (index: number) => {
  if (draggingIndex.value == null) return
  if (dragOverIndex.value === index) return
  dragOverIndex.value = index
}

const onDrop = (targetIndex: number) => {
  const from = draggingIndex.value
  if (from == null) return
  if (from === targetIndex) return

  const arr = [...localOrder.value]
  const [moved] = arr.splice(from, 1)
  arr.splice(targetIndex, 0, moved)
  localOrder.value = arr
  draggingIndex.value = null
  dragOverIndex.value = null
}

const onDragEnd = () => {
  draggingIndex.value = null
  dragOverIndex.value = null
}

const resetToDefault = () => {
  localOrder.value = [...SUBJECT_PRIORITY_DEFAULT]
}

const handleSave = async () => {
  const normalized = normalizeOrder(localOrder.value)
  saving.value = true
  try {
    const res = await pythonBackend.request<any>('rooms.setSubjectPriority', { order: normalized })
    if (res?.error) {
      ElMessage.error(res.error)
      emit('log-error', `保存高级设置失败：${res.error}`)
      return
    }
    emit('update:priorityOrder', [...normalized])
    ElMessage.success('高级设置已保存')
    emit('log-success', `高级设置已保存：${normalized.join(' > ')}`)
    emit('update:visible', false)
  } catch (e) {
    ElMessage.error('保存失败: ' + e)
    emit('log-error', `保存高级设置异常：${e instanceof Error ? e.message : String(e)}`)
  } finally {
    saving.value = false
  }
}
</script>
