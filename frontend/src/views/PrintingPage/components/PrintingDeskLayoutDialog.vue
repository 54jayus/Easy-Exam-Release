<template>
  <el-dialog
    :model-value="modelValue"
    title="设置座位布局"
    width="720px"
    class="!rounded-2xl"
    align-center
    append-to-body
    @update:model-value="handleVisibleChange"
  >
    <div class="space-y-6 px-6 py-4">
      <div class="grid grid-cols-2 gap-8">
        <div class="space-y-2">
          <label class="text-xs font-bold text-slate-500 uppercase tracking-wider">布局方式</label>
          <el-select v-model="deskLayoutDraft.layoutName" class="!w-full" size="default">
            <el-option v-for="opt in deskLayoutOptions" :key="opt.name" :label="opt.name" :value="opt.name" />
            <el-option label="自定义" value="自定义" />
          </el-select>
        </div>
        <div class="space-y-2">
          <label class="text-xs font-bold text-slate-500 uppercase tracking-wider">排列方式</label>
          <el-select v-model="deskLayoutDraft.layoutPattern" class="!w-full" size="default">
            <el-option label="S型横排" value="S型横排" />
            <el-option label="S型竖排" value="S型竖排" />
            <el-option label="Z型横排" value="Z型横排" />
            <el-option label="Z型竖排" value="Z型竖排" />
          </el-select>
        </div>
      </div>

      <div v-if="deskLayoutDraft.layoutName === '自定义'" class="space-y-2 animate-fade-in">
        <label class="text-xs font-bold text-slate-500 uppercase tracking-wider">自定义每列人数</label>
        <el-input v-model="deskLayoutDraft.customCountsText" placeholder="例如：7,7,8,8" size="default">
          <template #prefix>
            <el-icon class="text-slate-400"><Grid /></el-icon>
          </template>
        </el-input>
        <div class="text-[10px] text-slate-400 flex items-center gap-1.5">
          <el-icon><InfoFilled /></el-icon>
          <span>系统会自动计算行数、列数和容量，适合不规则座位布局。</span>
        </div>
      </div>

      <div class="space-y-2">
        <div class="flex items-center justify-between">
          <label class="text-xs font-bold text-slate-500 uppercase tracking-wider">起始位</label>
        </div>
        <div class="grid grid-cols-2 gap-3">
          <div
            class="cursor-pointer border-2 rounded-xl p-3 flex flex-col items-center gap-2 transition-all duration-200 hover:shadow-md"
            :class="deskLayoutDraft.startPos === 'left' ? 'border-primary-500 bg-primary-50/50' : 'border-slate-100 bg-white hover:border-slate-200'"
            @click="deskLayoutDraft.startPos = 'left'"
          >
            <span class="text-sm font-bold" :class="deskLayoutDraft.startPos === 'left' ? 'text-primary-700' : 'text-slate-700'">左手位</span>
            <span class="text-[10px] text-center leading-tight" :class="deskLayoutDraft.startPos === 'left' ? 'text-primary-600/80' : 'text-slate-400'">
              监考人员面向考生时，从左侧靠边座位开始编号。
            </span>
          </div>

          <div
            class="cursor-pointer border-2 rounded-xl p-3 flex flex-col items-center gap-2 transition-all duration-200 hover:shadow-md"
            :class="deskLayoutDraft.startPos === 'right' ? 'border-primary-500 bg-primary-50/50' : 'border-slate-100 bg-white hover:border-slate-200'"
            @click="deskLayoutDraft.startPos = 'right'"
          >
            <span class="text-sm font-bold" :class="deskLayoutDraft.startPos === 'right' ? 'text-primary-700' : 'text-slate-700'">右手位</span>
            <span class="text-[10px] text-center leading-tight" :class="deskLayoutDraft.startPos === 'right' ? 'text-primary-600/80' : 'text-slate-400'">
              监考人员面向考生时，从右侧靠边座位开始编号。
            </span>
          </div>
        </div>
        <div class="flex justify-end pt-1">
          <span class="text-[10px] text-slate-400 bg-slate-100 px-1.5 py-0.5 rounded flex items-center gap-1">
            <el-icon><InfoFilled /></el-icon>
            该设置会影响座位布局预览和座位编号。
          </span>
        </div>
      </div>
    </div>
    <template #footer>
      <span class="dialog-footer">
        <el-button size="default" @click="handleVisibleChange(false)">取消</el-button>
        <el-button type="primary" size="default" @click="$emit('apply')">应用设置</el-button>
      </span>
    </template>
  </el-dialog>
</template>

<script setup lang="ts">
import { Grid, InfoFilled } from '@element-plus/icons-vue'

defineProps<{
  modelValue: boolean
  deskLayoutOptions: readonly { name: string }[]
  deskLayoutDraft: Record<string, any>
}>()

const emit = defineEmits<{
  'update:modelValue': [value: boolean]
  apply: []
}>()

function handleVisibleChange(value: boolean) {
  emit('update:modelValue', value)
}
</script>
