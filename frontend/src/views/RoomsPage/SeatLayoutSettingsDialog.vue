<template>
  <el-dialog v-model="visible" title="统一座位布局" width="760px" append-to-body align-center>
    <div class="space-y-5 px-4 py-2">
      <div class="rounded-xl border border-blue-100 bg-blue-50/60 p-3 text-xs leading-relaxed text-blue-700">
        默认布局用于全部考场；选择具体考场后可创建覆盖布局。桌角纸和点名表都会读取这里的设置。
      </div>
      <div class="grid grid-cols-2 gap-4">
        <div>
          <label class="mb-1 block text-xs font-bold text-slate-500">设置对象</label>
          <el-select v-model="targetRoom" class="w-full" @change="loadDraft">
            <el-option label="全部考场（默认布局）" value="" />
            <el-option v-for="room in rooms" :key="room.roomNum" :label="`${room.roomNum} - ${room.roomName}`" :value="String(room.roomNum)" />
          </el-select>
        </div>
        <div class="flex items-end">
          <el-checkbox v-if="targetRoom" v-model="useOverride" @change="handleOverrideChange">为该考场单独设置布局</el-checkbox>
          <span v-else class="pb-2 text-xs text-slate-400">当前设置将作为所有考场的默认值</span>
        </div>
      </div>
      <div class="grid grid-cols-2 gap-4">
        <div>
          <label class="mb-1 block text-xs font-bold text-slate-500">布局方式</label>
          <el-select v-model="draft.layoutName" class="w-full" @change="applyPreset">
            <el-option v-for="item in SEAT_LAYOUT_OPTIONS" :key="item.name" :label="item.name" :value="item.name" />
            <el-option label="自定义" value="自定义" />
          </el-select>
        </div>
        <div>
          <label class="mb-1 block text-xs font-bold text-slate-500">排列方式</label>
          <el-select v-model="draft.layoutPattern" class="w-full">
            <el-option v-for="item in ['S型横排','S型竖排','Z型横排','Z型竖排']" :key="item" :label="item" :value="item" />
          </el-select>
        </div>
      </div>
      <div v-if="draft.layoutName === '自定义'">
        <label class="mb-1 block text-xs font-bold text-slate-500">每列人数</label>
        <el-input v-model="customCountsText" placeholder="例如：7,7,8,8" />
      </div>
      <div>
        <label class="mb-2 block text-xs font-bold text-slate-500">监考员面向考生时的起始位</label>
        <el-radio-group v-model="draft.startPos">
          <el-radio-button value="left">左手位</el-radio-button>
          <el-radio-button value="right">右手位</el-radio-button>
        </el-radio-group>
      </div>
      <div class="rounded-xl border border-slate-200 p-3">
        <div class="mb-2 text-center text-xs font-bold text-slate-500">讲台</div>
        <div class="grid gap-1" :style="{ gridTemplateColumns: `repeat(${effective.layoutCols}, minmax(0, 1fr))` }">
          <div v-for="cell in previewCells" :key="cell.key" class="flex h-8 items-center justify-center border text-xs" :class="cell.valid ? 'border-slate-300 bg-white text-slate-600' : 'border-transparent text-transparent'">{{ cell.seat }}</div>
        </div>
      </div>
    </div>
    <template #footer>
      <el-button @click="visible = false">取消</el-button>
      <el-button type="primary" @click="save">保存布局</el-button>
    </template>
  </el-dialog>
</template>

<script setup lang="ts">
import { computed, reactive, ref, watch } from 'vue'
import { getSeatMapping, normalizeSeatLayout, parseCustomColCounts, SEAT_LAYOUT_OPTIONS, type SeatLayoutConfig } from '@/types/seatLayout'

const props = defineProps<{ modelValue: boolean; seatLayout: SeatLayoutConfig; rooms: any[] }>()
const emit = defineEmits<{ 'update:modelValue': [value: boolean]; save: [value: SeatLayoutConfig] }>()
const visible = computed({ get: () => props.modelValue, set: (value) => emit('update:modelValue', value) })
const targetRoom = ref('')
const useOverride = ref(false)
const customCountsText = ref('')
const draft = reactive(normalizeSeatLayout())

function loadDraft() {
  useOverride.value = Boolean(targetRoom.value && props.seatLayout.roomOverrides[targetRoom.value])
  const source = useOverride.value ? props.seatLayout.roomOverrides[targetRoom.value] : props.seatLayout.defaultLayout
  Object.assign(draft, normalizeSeatLayout(source))
  customCountsText.value = draft.customColCounts?.join(',') || ''
}
function applyPreset() {
  const preset = SEAT_LAYOUT_OPTIONS.find((item) => item.name === draft.layoutName)
  if (preset) Object.assign(draft, { layoutRows: preset.rows, layoutCols: preset.cols, customColCounts: null })
}
function handleOverrideChange(value: boolean | string | number) {
  useOverride.value = Boolean(value)
  const source = useOverride.value && props.seatLayout.roomOverrides[targetRoom.value]
    ? props.seatLayout.roomOverrides[targetRoom.value]
    : props.seatLayout.defaultLayout
  Object.assign(draft, normalizeSeatLayout(source))
  customCountsText.value = draft.customColCounts?.join(',') || ''
}
const effective = computed(() => normalizeSeatLayout(draft.layoutName === '自定义' ? { ...draft, customColCounts: parseCustomColCounts(customCountsText.value) } : draft))
const previewCells = computed(() => {
  const mapping = getSeatMapping(effective.value)
  const positions = new Map(Object.entries(mapping).map(([seat, pos]) => [`${pos[0]}-${pos[1]}`, seat]))
  return Array.from({ length: effective.value.layoutRows * effective.value.layoutCols }, (_, index) => {
    const row = Math.floor(index / effective.value.layoutCols)
    const col = index % effective.value.layoutCols
    const seat = positions.get(`${row}-${col}`) || ''
    return { key: `${row}-${col}`, seat, valid: Boolean(seat) }
  })
})
function save() {
  const next = { defaultLayout: normalizeSeatLayout(props.seatLayout.defaultLayout), roomOverrides: { ...props.seatLayout.roomOverrides } }
  const value = effective.value
  if (!targetRoom.value) next.defaultLayout = value
  else if (useOverride.value) next.roomOverrides[targetRoom.value] = value
  else delete next.roomOverrides[targetRoom.value]
  emit('save', next)
  visible.value = false
}
watch(() => props.modelValue, (value) => { if (value) loadDraft() })
</script>
