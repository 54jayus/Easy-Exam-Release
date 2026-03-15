<template>
  <el-dialog
    :model-value="visible"
    @update:model-value="$emit('update:visible', $event)"
    title="高考模式时间设置"
    :width="dialogWidth"
    align-center
    :close-on-click-modal="false"
    append-to-body
    destroy-on-close
    class="gaokao-time-dialog"
  >
    <div class="dialog-content">
      <!-- 说明文字 -->
      <div class="info-banner">
        <i class="el-icon-info-filled"></i>
        <span>设置各科目的考试时间和自习时间，导出时将自动添加时间列。</span>
      </div>

      <!-- 考试时间设置 -->
      <section class="time-section">
        <h3 class="section-title">考试时间设置</h3>

        <!-- 列标题 -->
        <div class="table-header">
          <div class="header-cell subject-col">科目</div>
          <div class="header-cell date-col">考试日期</div>
          <div class="header-cell time-col">开始时间</div>
          <div class="header-cell time-col">结束时间</div>
        </div>

        <!-- 数据行 -->
        <div class="table-body">
          <div v-for="subject in examSubjects" :key="subject" class="table-row">
            <div class="cell subject-col">
              <span class="subject-name">{{ subject }}</span>
            </div>
            <div class="cell date-col">
              <el-date-picker
                v-model="localSettings.examTimes[subject].date"
                type="date"
                placeholder="选择日期"
                size="default"
                format="YYYY-MM-DD"
                value-format="YYYY-MM-DD"
                class="w-full"
              />
            </div>
            <div class="cell time-col">
              <el-time-picker
                v-model="localSettings.examTimes[subject].startTime"
                placeholder="开始时间"
                size="default"
                format="HH:mm"
                value-format="HH:mm"
                class="w-full"
              />
            </div>
            <div class="cell time-col">
              <el-time-picker
                v-model="localSettings.examTimes[subject].endTime"
                placeholder="结束时间"
                size="default"
                format="HH:mm"
                value-format="HH:mm"
                class="w-full"
              />
            </div>
          </div>
        </div>
      </section>

      <!-- 自习时间设置 -->
      <section class="time-section">
        <h3 class="section-title">自习时间设置（选考科目）</h3>

        <!-- 列标题 -->
        <div class="table-header">
          <div class="header-cell subject-col">科目</div>
          <div class="header-cell date-col">自习日期</div>
          <div class="header-cell time-col">开始时间</div>
          <div class="header-cell time-col">结束时间</div>
        </div>

        <!-- 数据行 -->
        <div class="table-body">
          <div v-for="subject in selfStudySubjects" :key="subject" class="table-row">
            <div class="cell subject-col">
              <span class="subject-name">{{ subject }}</span>
            </div>
            <div class="cell date-col">
              <el-date-picker
                v-model="localSettings.selfStudyTimes[subject].date"
                type="date"
                placeholder="选择日期"
                size="default"
                format="YYYY-MM-DD"
                value-format="YYYY-MM-DD"
                class="w-full"
              />
            </div>
            <div class="cell time-col">
              <el-time-picker
                v-model="localSettings.selfStudyTimes[subject].startTime"
                placeholder="开始时间"
                size="default"
                format="HH:mm"
                value-format="HH:mm"
                class="w-full"
              />
            </div>
            <div class="cell time-col">
              <el-time-picker
                v-model="localSettings.selfStudyTimes[subject].endTime"
                placeholder="结束时间"
                size="default"
                format="HH:mm"
                value-format="HH:mm"
                class="w-full"
              />
            </div>
          </div>
        </div>
      </section>
    </div>

    <template #footer>
      <div class="dialog-footer">
        <el-button @click="resetToDefault" class="reset-btn">
          <i class="el-icon-refresh-left"></i>
          恢复默认
        </el-button>
        <div class="action-buttons">
          <el-button @click="$emit('update:visible', false)">取消</el-button>
          <el-button type="primary" :loading="saving" @click="handleSave">
            <i v-if="!saving" class="el-icon-check"></i>
            保存
          </el-button>
        </div>
      </div>
    </template>
  </el-dialog>
</template>

<script setup lang="ts">
import { ref, watch, computed } from 'vue'
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

// 响应式对话框宽度
const dialogWidth = computed(() => {
  if (typeof window === 'undefined') return '900px'
  const width = window.innerWidth
  if (width < 768) return '95%'
  if (width < 1024) return '85%'
  if (width < 1280) return '900px'
  return '1000px'
})

// Watch for external changes
watch(() => props.visible, (isVisible) => {
  if (isVisible) {
    localSettings.value = JSON.parse(JSON.stringify(props.settings))
  }
})

// Methods
const resetToDefault = () => {
  localSettings.value = JSON.parse(JSON.stringify(GAOKAO_TIME_DEFAULTS))
  ElMessage.success('已恢复为默认时间设置')
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

<style scoped>
/* 确保对话框在整个视口中居中 */
.gaokao-time-dialog :deep(.el-dialog) {
  margin: 0 auto !important;
}

.gaokao-time-dialog :deep(.el-overlay) {
  display: flex;
  align-items: center;
  justify-content: center;
}

.gaokao-time-dialog :deep(.el-dialog__body) {
  padding: 20px 24px;
  max-height: 70vh;
  overflow-y: auto;
}

.dialog-content {
  display: flex;
  flex-direction: column;
  gap: 24px;
}

/* 信息横幅 */
.info-banner {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 12px 16px;
  background: linear-gradient(135deg, #e3f2fd 0%, #f3e5f5 100%);
  border-left: 4px solid #2196f3;
  border-radius: 8px;
  font-size: 14px;
  color: #424242;
  line-height: 1.6;
}

.info-banner i {
  color: #2196f3;
  font-size: 18px;
  flex-shrink: 0;
}

/* 时间设置区域 */
.time-section {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.section-title {
  font-size: 16px;
  font-weight: 600;
  color: #1a1a1a;
  margin: 0;
  padding-bottom: 8px;
  border-bottom: 2px solid #e0e0e0;
}

/* 表格样式 */
.table-header {
  display: grid;
  grid-template-columns: 100px 1fr 1fr 1fr;
  gap: 12px;
  padding: 10px 12px;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  border-radius: 8px;
  font-size: 13px;
  font-weight: 600;
  color: white;
}

.header-cell {
  display: flex;
  align-items: center;
  justify-content: center;
}

.table-body {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.table-row {
  display: grid;
  grid-template-columns: 100px 1fr 1fr 1fr;
  gap: 12px;
  padding: 8px 12px;
  background: #fafafa;
  border-radius: 8px;
  transition: all 0.2s ease;
}

.table-row:hover {
  background: #f0f0f0;
  transform: translateX(2px);
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.08);
}

.cell {
  display: flex;
  align-items: center;
}

.subject-col {
  justify-content: center;
}

.subject-name {
  font-size: 14px;
  font-weight: 600;
  color: #424242;
  padding: 6px 12px;
  background: white;
  border-radius: 6px;
  border: 1px solid #e0e0e0;
}

/* 底部按钮 */
.dialog-footer {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding-top: 16px;
  border-top: 1px solid #e0e0e0;
}

.reset-btn {
  display: flex;
  align-items: center;
  gap: 6px;
}

.action-buttons {
  display: flex;
  gap: 12px;
}

/* 响应式设计 */
@media (max-width: 1024px) {
  .table-header,
  .table-row {
    grid-template-columns: 90px 1fr 1fr 1fr;
    gap: 8px;
  }

  .subject-name {
    font-size: 13px;
    padding: 4px 8px;
  }
}

@media (max-width: 768px) {
  .gaokao-time-dialog :deep(.el-dialog__body) {
    padding: 16px;
  }

  .table-header,
  .table-row {
    grid-template-columns: 80px 1fr 1fr 1fr;
    gap: 6px;
    font-size: 12px;
  }

  .table-header {
    padding: 8px 10px;
  }

  .table-row {
    padding: 6px 10px;
  }

  .subject-name {
    font-size: 12px;
    padding: 4px 6px;
  }

  .section-title {
    font-size: 14px;
  }

  .info-banner {
    font-size: 13px;
    padding: 10px 12px;
  }

  .dialog-footer {
    flex-direction: column;
    gap: 12px;
  }

  .action-buttons {
    width: 100%;
    justify-content: flex-end;
  }
}

@media (max-width: 640px) {
  .table-header,
  .table-row {
    grid-template-columns: 70px 1fr 1fr 1fr;
    gap: 4px;
  }

  .subject-name {
    font-size: 11px;
    padding: 3px 5px;
  }

  .gaokao-time-dialog :deep(.el-date-picker),
  .gaokao-time-dialog :deep(.el-time-picker) {
    font-size: 12px;
  }
}

/* Element Plus 组件样式覆盖 */
.gaokao-time-dialog :deep(.el-input__wrapper) {
  border-radius: 6px;
  transition: all 0.2s ease;
}

.gaokao-time-dialog :deep(.el-input__wrapper:hover) {
  box-shadow: 0 0 0 1px #667eea inset;
}

.gaokao-time-dialog :deep(.el-input__wrapper.is-focus) {
  box-shadow: 0 0 0 1px #667eea inset;
}

.gaokao-time-dialog :deep(.el-button) {
  border-radius: 6px;
  font-weight: 500;
  transition: all 0.2s ease;
}

.gaokao-time-dialog :deep(.el-button--primary) {
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  border: none;
}

.gaokao-time-dialog :deep(.el-button--primary:hover) {
  transform: translateY(-1px);
  box-shadow: 0 4px 12px rgba(102, 126, 234, 0.4);
}
</style>

