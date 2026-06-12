<template>
  <el-dialog
    :model-value="modelValue"
    title="编辑点名表使用说明"
    width="720px"
    class="!rounded-2xl"
    align-center
    append-to-body
    @update:model-value="handleVisibleChange"
  >
    <div class="space-y-3">
      <p class="text-xs leading-5 text-slate-500">
        此内容将显示在完整考务版点名表底部。支持换行，可按实际考务要求自由编辑。
      </p>
      <el-input
        v-model="draft"
        type="textarea"
        :rows="14"
        resize="vertical"
        placeholder="请输入点名表使用说明"
      />
    </div>

    <template #footer>
      <div class="flex justify-end gap-2">
        <el-button @click="handleVisibleChange(false)">取消</el-button>
        <el-button type="primary" @click="save">保存</el-button>
      </div>
    </template>
  </el-dialog>
</template>

<script setup lang="ts">
import { ref, watch } from 'vue'

const props = defineProps<{
  modelValue: boolean
  instructions: string
}>()

const emit = defineEmits<{
  'update:modelValue': [value: boolean]
  save: [value: string]
}>()

const draft = ref('')

watch(
  () => props.modelValue,
  (visible) => {
    if (visible) draft.value = String(props.instructions ?? '')
  }
)

function handleVisibleChange(value: boolean) {
  emit('update:modelValue', value)
}

function save() {
  emit('save', draft.value)
  emit('update:modelValue', false)
}
</script>
