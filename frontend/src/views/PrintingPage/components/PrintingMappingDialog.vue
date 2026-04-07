<template>
  <el-dialog :model-value="modelValue" title="字段映射" width="500px" @update:model-value="handleVisibleChange">
    <div class="space-y-4">
      <p class="text-sm text-slate-500">请将 Excel 列映射到系统字段。</p>
      <div v-for="(target, key) in requiredFields" :key="key" class="flex items-center gap-4">
        <div class="w-24 text-sm font-bold text-right text-slate-700">
          {{ target.label }}
          <span v-if="target.required" class="text-rose-500">*</span>
        </div>
        <el-select v-model="mapping[key]" placeholder="选择列" size="small" class="flex-1" clearable>
          <el-option v-for="header in headers" :key="header" :label="header" :value="header" />
        </el-select>
      </div>
    </div>
    <template #footer>
      <span class="dialog-footer">
        <el-button @click="handleVisibleChange(false)">取消</el-button>
        <el-button type="primary" @click="$emit('confirm')">确认并预览</el-button>
      </span>
    </template>
  </el-dialog>
</template>

<script setup lang="ts">
type RequiredField = {
  label: string
  required?: boolean
}

defineProps<{
  modelValue: boolean
  requiredFields: Record<string, RequiredField>
  headers: string[]
  mapping: Record<string, string>
}>()

const emit = defineEmits<{
  'update:modelValue': [value: boolean]
  confirm: []
}>()

function handleVisibleChange(value: boolean) {
  emit('update:modelValue', value)
}
</script>
