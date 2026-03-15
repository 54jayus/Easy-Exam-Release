<template>
  <el-dialog
    :model-value="visible"
    @update:model-value="$emit('update:visible', $event)"
    title="高考模式时间设置"
    width="800px"
    align-center
    :close-on-click-modal="false"
  >
    <div class="space-y-6">
      <!-- 说明文字 -->
      <div class="text-sm text-slate-600 bg-blue-50 p-3 rounded-lg">
        设置各科目的考试时间和自习时间，导出时将自动添加时间列。
      </div>

      <!-- 考试时间设置 -->
      <section>
        <h3 class="text-base font-bold text-slate-800 mb-3">考试时间设置</h3>
        <div class="space-y-2">
          <div v-for="subject in examSubjects" :key="subject"
               class="grid grid-cols-[100px_1fr_1fr_1fr] gap-3 items-center p-2 bg-slate-50 rounded-lg">
            <div class="font-bold text-slate-700">{{ subject }}</div>
            <el-date-picker
              v-model="localSettings.examTimes[subject].date"
              type="date"
              placeholder="选择日期"
              size="small"
              format="YYYY-MM-DD"
              value-format="YYYY-MM-DD"
              class="w-full"
            />
            <el-time-picker
              v-model="localSettings.examTimes[subject].startTime"
              placeholder="开始时间"
              size="small"
              format="HH:mm"
              value-format="HH:mm"
              class="w-full"
            />
            <el-time-picker
              v-model="localSettings.examTimes[subject].endTime"
              placeholder="结束时间"
              size="small"
              format="HH:mm"
              value-format="HH:mm"
              class="w-full"
            />
          </div>
        </div>
      </section>

      <!-- 自习时间设置 -->
      <section>
        <h3 class="text-base font-bold text-slate-800 mb-3">自习时间设置（选考科目）</h3>
        <div class="space-y-2">
          <div v-for="subject in selfStudySubjects" :key="subject"
               class="grid grid-cols-[100px_1fr_1fr_1fr] gap-3 items-center p-2 bg-slate-50 rounded-lg">
            <div class="font-bold text-slate-700">{{ subject }}</div>
            <el-date-picker
              v-model="localSettings.selfStudyTimes[subject].date"
              type="date"
              placeholder="选择日期"
              size="small"
              format="YYYY-MM-DD"
              value-format="YYYY-MM-DD"
              class="w-full"
            />
            <el-time-picker
              v-model="localSettings.selfStudyTimes[subject].startTime"
              placeholder="开始时间"
              size="small"
              format="HH:mm"
              value-format="HH:mm"
              class="w-full"
            />
            <el-time-picker
              v-model="localSettings.selfStudyTimes[subject].endTime"
              placeholder="结束时间"
              size="small"
              format="HH:mm"
              value-format="HH:mm"
              class="w-full"
            />
          </div>
        </div>
      </section>
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
import { GAOKAO_TIME_DEFAULTS, type GaokaoTimeSettings } from '@/types/gaokao'

// Props & Emits
interface Props {
  visible: boolean
  settings: GaokaoTimeSettings
}

const props = defineProps<Props>()
const emit = defineEmits<{
  'update:visible': [value: boolean]
  'update:settings': [value: GaokaoTimeSettings]
  'log-success': [msg: string]
  'log-error': [msg: string]
}>()

// State
const examSubjects = ['语文', '数学', '物理历史', '英语', '化学', '地理', '政治', '生物']
const selfStudySubjects = ['化学', '地理', '政治', '生物']
const localSettings = ref<GaokaoTimeSettings>(JSON.parse(JSON.stringify(props.settings)))
const saving = ref(false)

// Watch for external changes
watch(() => props.visible, (isVisible) => {
  if (isVisible) {
    localSettings.value = JSON.parse(JSON.stringify(props.settings))
  }
})

// Methods
const resetToDefault = () => {
  localSettings.value = JSON.parse(JSON.stringify(GAOKAO_TIME_DEFAULTS))
}

const validateSettings = (): string | null => {
  // 验证所有考试时间
  for (const subject of examSubjects) {
    const time = localSettings.value.examTimes[subject as keyof typeof localSettings.value.examTimes]
    if (!time.date || !time.startTime || !time.endTime) {
      return `${subject}的时间设置不完整`
    }
    if (time.startTime >= time.endTime) {
      return `${subject}的开始时间必须早于结束时间`
    }
  }

  // 验证所有自习时间
  for (const subject of selfStudySubjects) {
    const time = localSettings.value.selfStudyTimes[subject as keyof typeof localSettings.value.selfStudyTimes]
    if (!time.date || !time.startTime || !time.endTime) {
      return `${subject}的自习时间设置不完整`
    }
    if (time.startTime >= time.endTime) {
      return `${subject}的自习开始时间必须早于结束时间`
    }
  }

  return null
}

const handleSave = async () => {
  // 验证
  const error = validateSettings()
  if (error) {
    ElMessage.error(error)
    return
  }

  saving.value = true
  try {
    const res = await pythonBackend.request('rooms.setGaokaoTimeSettings', {
      settings: localSettings.value
    })

    if (res?.error) {
      ElMessage.error(res.error)
      emit('log-error', `保存时间设置失败：${res.error}`)
      return
    }

    emit('update:settings', JSON.parse(JSON.stringify(localSettings.value)))
    ElMessage.success('时间设置已保存')
    emit('log-success', '高考模式时间设置已保存')
    emit('update:visible', false)
  } catch (e) {
    ElMessage.error('保存失败: ' + e)
    emit('log-error', `保存时间设置异常：${e instanceof Error ? e.message : String(e)}`)
  } finally {
    saving.value = false
  }
}
</script>

