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
      <div class="info-banner">
        <div class="info-badge">说明</div>
        <div class="info-text">
          <div class="info-title">高考模式时间设置</div>
          <div class="info-desc">可修改科目名称、考试日期和时间段；选考科目支持单独配置自习时间。</div>
        </div>
      </div>

      <section class="time-section">
        <div class="section-header">
          <div>
            <h3 class="section-title">考试时间设置</h3>
            <p class="section-desc">科目名称需唯一，日期默认使用系统当日。</p>
          </div>
          <div class="section-summary">{{ examSubjects.length }} 个考试时段</div>
        </div>

        <div class="table-header">
          <div class="header-cell subject-col">科目</div>
          <div class="header-cell date-col">日期</div>
          <div class="header-cell time-col">时间段</div>
        </div>

        <div class="table-body">
          <div v-for="subject in examSubjects" :key="subject" class="subject-group">
            <div class="table-row exam-row">
              <div class="cell subject-col">
                <el-input
                  v-model="(localSettings.examTimes as any)[subject].subjectName"
                  placeholder="请输入科目名称"
                  maxlength="20"
                  class="subject-name-input"
                  size="small"
                />
              </div>
              <div class="cell date-col">
                <el-date-picker
                  v-model="(localSettings.examTimes as any)[subject].date"
                  type="date"
                  placeholder="选择日期"
                  size="small"
                  format="YYYY-MM-DD"
                  value-format="YYYY-MM-DD"
                  class="w-full"
                />
              </div>
              <div class="cell time-col">
                <div class="time-range">
                  <el-time-picker
                    v-model="(localSettings.examTimes as any)[subject].startTime"
                    placeholder="开始"
                    size="small"
                    format="HH:mm"
                    value-format="HH:mm"
                    class="time-input"
                    :popper-options="{ strategy: 'fixed' }"
                    popper-class="time-picker-popper"
                  />
                  <span class="time-separator">-</span>
                  <el-time-picker
                    v-model="(localSettings.examTimes as any)[subject].endTime"
                    placeholder="结束"
                    size="small"
                    format="HH:mm"
                    value-format="HH:mm"
                    class="time-input"
                    :popper-options="{ strategy: 'fixed' }"
                    popper-class="time-picker-popper"
                  />
                </div>
              </div>
            </div>

            <div v-if="isElectiveSubject(subject)" class="self-study-row">
              <div class="self-study-toggle">
                <el-checkbox
                  v-model="customSelfStudyTime[subject]"
                  @change="handleSelfStudyToggle(subject)"
                >
                  自定义自习时间
                </el-checkbox>
              </div>
              <div v-if="customSelfStudyTime[subject]" class="self-study-settings">
                <div class="cell date-col">
                  <el-date-picker
                    v-model="(localSettings.selfStudyTimes as any)[subject].date"
                    type="date"
                    placeholder="选择日期"
                    size="small"
                    format="YYYY-MM-DD"
                    value-format="YYYY-MM-DD"
                    class="w-full"
                  />
                </div>
                <div class="cell time-col">
                  <div class="time-range">
                    <el-time-picker
                      v-model="(localSettings.selfStudyTimes as any)[subject].startTime"
                      placeholder="开始"
                      size="small"
                      format="HH:mm"
                      value-format="HH:mm"
                      class="time-input"
                      :popper-options="{ strategy: 'fixed' }"
                      popper-class="time-picker-popper"
                    />
                    <span class="time-separator">-</span>
                    <el-time-picker
                      v-model="(localSettings.selfStudyTimes as any)[subject].endTime"
                      placeholder="结束"
                      size="small"
                      format="HH:mm"
                      value-format="HH:mm"
                      class="time-input"
                      :popper-options="{ strategy: 'fixed' }"
                      popper-class="time-picker-popper"
                    />
                  </div>
                </div>
              </div>
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
import { ref, watch, computed, reactive } from 'vue'
import { ElMessage } from 'element-plus'
import { formatActionError, formatActionSuccess } from '@/lib/uiFeedback'
import { pythonBackend } from '@/lib/pythonBackend'
import {
  GAOKAO_ELECTIVE_SUBJECTS,
  GAOKAO_SUBJECT_ORDER,
  buildGaokaoTimeDefaults,
  normalizeGaokaoTimeSettings,
  type GaokaoElectiveSubjectKey,
  type GaokaoSubjectKey,
  type GaokaoTimeSettings,
} from '@/types/gaokao'

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
const examSubjects: GaokaoSubjectKey[] = [...GAOKAO_SUBJECT_ORDER]
const electiveSubjects: GaokaoElectiveSubjectKey[] = [...GAOKAO_ELECTIVE_SUBJECTS]
const localSettings = ref<GaokaoTimeSettings>(normalizeGaokaoTimeSettings(props.settings))
const saving = ref(false)

// 自定义自习时间的开关状态
const customSelfStudyTime = reactive<Record<string, boolean>>({
  化学: false,
  地理: false,
  政治: false,
  生物: false
})

// 响应式对话框宽度 - 增加宽度以容纳组件
const dialogWidth = computed(() => {
  if (typeof window === 'undefined') return '800px'
  const width = window.innerWidth
  if (width < 768) return '95%'
  if (width < 1024) return '85%'
  return '800px'
})

// 判断是否为选考科目
const isElectiveSubject = (subject: string) => {
  return electiveSubjects.includes(subject as GaokaoElectiveSubjectKey)
}

// 检查自习时间是否与考试时间不同
const checkCustomSelfStudyTime = () => {
  for (const subject of electiveSubjects) {
    const examTime = localSettings.value.examTimes[subject as keyof typeof localSettings.value.examTimes]
    const selfStudyTime = localSettings.value.selfStudyTimes[subject as keyof typeof localSettings.value.selfStudyTimes]

    if (examTime.date !== selfStudyTime.date ||
        examTime.startTime !== selfStudyTime.startTime ||
        examTime.endTime !== selfStudyTime.endTime) {
      customSelfStudyTime[subject] = true
    }
  }
}

// Watch for external changes
watch(() => props.visible, (isVisible) => {
  if (isVisible) {
    localSettings.value = normalizeGaokaoTimeSettings(props.settings)
    checkCustomSelfStudyTime()
  }
})

// 处理自习时间开关切换
const handleSelfStudyToggle = (subject: string) => {
  if (!customSelfStudyTime[subject]) {
    // 关闭自定义时，同步为考试时间
    const examTime = localSettings.value.examTimes[subject as keyof typeof localSettings.value.examTimes]
    const selfStudyTime = localSettings.value.selfStudyTimes[subject as keyof typeof localSettings.value.selfStudyTimes]
    selfStudyTime.date = examTime.date
    selfStudyTime.startTime = examTime.startTime
    selfStudyTime.endTime = examTime.endTime
  }
}

// Methods
const resetToDefault = () => {
  localSettings.value = buildGaokaoTimeDefaults()
  // 重置自定义开关
  for (const subject of electiveSubjects) {
    customSelfStudyTime[subject] = false
  }
  ElMessage.success('已恢复为默认时间设置')
  emit('log-success', formatActionSuccess('恢复默认时间设置'))
}

const validateSettings = (): string | null => {
  const normalizedNames = examSubjects.map((subject) => {
    return String(localSettings.value.examTimes[subject].subjectName ?? '').trim()
  })

  for (let index = 0; index < examSubjects.length; index += 1) {
    if (!normalizedNames[index]) {
      return `${examSubjects[index]}的科目名称不能为空`
    }
  }

  const duplicateNames = [...new Set(normalizedNames.filter((name, index) => normalizedNames.indexOf(name) !== index))]
  if (duplicateNames.length > 0) {
    return `科目名称不能重复：${duplicateNames.join('、')}`
  }

  // 验证所有考试时间
  for (const subject of examSubjects) {
    const time = localSettings.value.examTimes[subject as keyof typeof localSettings.value.examTimes]
    const subjectName = String(time.subjectName ?? '').trim() || subject
    if (!time.date || !time.startTime || !time.endTime) {
      return `${subjectName}的时间设置不完整`
    }
    if (time.startTime >= time.endTime) {
      return `${subjectName}的开始时间必须早于结束时间`
    }
  }

  // 验证自定义的自习时间
  for (const subject of electiveSubjects) {
    if (customSelfStudyTime[subject]) {
      const time = localSettings.value.selfStudyTimes[subject as keyof typeof localSettings.value.selfStudyTimes]
      const subjectName = String(localSettings.value.examTimes[subject].subjectName ?? '').trim() || subject
      if (!time.date || !time.startTime || !time.endTime) {
        return `${subjectName}的自习时间设置不完整`
      }
      if (time.startTime >= time.endTime) {
        return `${subjectName}的自习开始时间必须早于结束时间`
      }
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
    const settingsToSave = normalizeGaokaoTimeSettings(localSettings.value)
    for (const subject of examSubjects) {
      settingsToSave.examTimes[subject].subjectName = String(settingsToSave.examTimes[subject].subjectName ?? '').trim()
    }

    const res = await pythonBackend.request('rooms.setGaokaoTimeSettings', {
      settings: settingsToSave
    }) as { error?: string }

    if (res?.error) {
      ElMessage.error(res.error)
      emit('log-error', formatActionError('保存时间设置', res.error))
      return
    }

    localSettings.value = settingsToSave
    emit('update:settings', normalizeGaokaoTimeSettings(settingsToSave))
    ElMessage.success('时间设置已保存')
    emit('log-success', formatActionSuccess('保存高考模式时间设置'))
    emit('update:visible', false)
  } catch (e) {
    ElMessage.error(formatActionError('保存时间设置', e))
    emit('log-error', formatActionError('保存时间设置', e))
  } finally {
    saving.value = false
  }
}
</script>

<style scoped>
:deep(.gaokao-time-dialog.el-dialog) {
  margin: 0 auto !important;
  width: min(920px, calc(100vw - 32px)) !important;
  height: 88vh !important;
  max-height: 88vh !important;
  display: flex !important;
  flex-direction: column !important;
  overflow: hidden !important;
  border-radius: 20px !important;
  border: 1px solid rgba(226, 232, 240, 0.9) !important;
  box-shadow: 0 24px 80px -36px rgba(15, 23, 42, 0.28) !important;
}

:deep(.gaokao-time-dialog .el-dialog__header) {
  flex-shrink: 0 !important;
  margin-right: 0 !important;
  padding: 18px 22px 14px !important;
  border-bottom: 1px solid rgba(226, 232, 240, 0.9) !important;
  background: linear-gradient(180deg, rgba(255, 255, 255, 0.98), rgba(248, 250, 252, 0.95)) !important;
}

:deep(.gaokao-time-dialog .el-dialog__title) {
  font-size: 18px !important;
  font-weight: 700 !important;
  color: #0f172a !important;
  letter-spacing: -0.01em;
}

:deep(.gaokao-time-dialog .el-dialog__headerbtn) {
  top: 18px !important;
  right: 18px !important;
}

:deep(.gaokao-time-dialog .el-dialog__body) {
  padding: 18px 22px 20px !important;
  flex: 1 1 auto !important;
  overflow-y: auto !important;
  overflow-x: hidden !important;
  min-height: 0 !important;
  max-height: none !important;
  height: auto !important;
  background: linear-gradient(180deg, #f8fafc 0%, #f1f5f9 100%) !important;
}

:deep(.gaokao-time-dialog .el-dialog__footer) {
  flex-shrink: 0 !important;
  padding: 14px 22px 18px !important;
  border-top: 1px solid rgba(226, 232, 240, 0.9) !important;
  background: rgba(255, 255, 255, 0.96) !important;
}

:deep(.gaokao-time-dialog .el-dialog__body)::-webkit-scrollbar {
  width: 8px;
}

:deep(.gaokao-time-dialog .el-dialog__body)::-webkit-scrollbar-track {
  background: #f1f1f1;
  border-radius: 4px;
}

:deep(.gaokao-time-dialog .el-dialog__body)::-webkit-scrollbar-thumb {
  background: #c1c1c1;
  border-radius: 4px;
}

:deep(.gaokao-time-dialog .el-dialog__body)::-webkit-scrollbar-thumb:hover {
  background: #a8a8a8;
}

.dialog-content {
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.info-banner {
  display: flex;
  align-items: flex-start;
  gap: 12px;
  padding: 14px 16px;
  background: linear-gradient(135deg, rgba(239, 246, 255, 0.95), rgba(248, 250, 252, 0.98));
  border: 1px solid rgba(191, 219, 254, 0.9);
  border-radius: 14px;
  box-shadow: inset 0 1px 0 rgba(255, 255, 255, 0.9);
}

.info-badge {
  flex-shrink: 0;
  min-width: 42px;
  height: 24px;
  padding: 0 10px;
  border-radius: 999px;
  background: #dbeafe;
  color: #1d4ed8;
  font-size: 12px;
  font-weight: 700;
  display: flex;
  align-items: center;
  justify-content: center;
}

.info-text {
  min-width: 0;
}

.info-title {
  color: #0f172a;
  font-size: 14px;
  font-weight: 700;
}

.info-desc {
  margin-top: 2px;
  color: #475569;
  font-size: 13px;
  line-height: 1.6;
}

.time-section {
  display: flex;
  flex-direction: column;
  gap: 12px;
  padding: 16px;
  border-radius: 18px;
  background: rgba(255, 255, 255, 0.88);
  border: 1px solid rgba(226, 232, 240, 0.9);
  box-shadow: 0 14px 32px -24px rgba(15, 23, 42, 0.22);
}

.section-header {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: 12px;
}

.section-title {
  font-size: 16px;
  font-weight: 700;
  color: #0f172a;
  margin: 0;
}

.section-desc {
  margin: 4px 0 0;
  font-size: 12px;
  color: #64748b;
}

.section-summary {
  flex-shrink: 0;
  padding: 6px 10px;
  border-radius: 999px;
  background: #eff6ff;
  color: #2563eb;
  font-size: 12px;
  font-weight: 700;
}

.table-header {
  display: grid;
  grid-template-columns: 136px 148px minmax(0, 1fr);
  gap: 10px;
  padding: 10px 12px;
  background: #eff6ff;
  border: 1px solid #dbeafe;
  border-radius: 12px;
  font-size: 12px;
  font-weight: 700;
  color: #1e40af;
}

.header-cell {
  display: flex;
  align-items: center;
  justify-content: center;
}

.table-body {
  display: flex;
  flex-direction: column;
  gap: 10px;
}

.subject-group {
  display: flex;
  flex-direction: column;
  gap: 0;
  border-radius: 16px;
  border: 1px solid rgba(226, 232, 240, 0.95);
  background: rgba(255, 255, 255, 0.96);
  overflow: hidden;
  box-shadow: 0 10px 24px -22px rgba(15, 23, 42, 0.35);
}

.exam-row {
  display: grid;
  grid-template-columns: 136px 148px minmax(0, 1fr);
  gap: 10px;
  padding: 12px;
  background: transparent;
  transition: background-color 0.2s ease, box-shadow 0.2s ease;
}

.exam-row:hover {
  background: rgba(248, 250, 252, 0.85);
}

.cell {
  display: flex;
  align-items: center;
}

.subject-col {
  justify-content: flex-start;
}

.subject-name-input {
  width: 100%;
}

.time-range {
  display: flex;
  align-items: center;
  gap: 8px;
  width: 100%;
}

.time-input {
  flex: 1;
  min-width: 0;
}

.time-input :deep(.el-input__wrapper) {
  width: 100%;
}

.time-separator {
  color: #64748b;
  font-weight: 700;
  flex-shrink: 0;
  width: 12px;
  text-align: center;
}

.self-study-row {
  display: flex;
  flex-direction: column;
  gap: 10px;
  padding: 12px;
  background: linear-gradient(180deg, rgba(248, 250, 252, 0.96), rgba(241, 245, 249, 0.9));
  border-top: 1px dashed rgba(203, 213, 225, 0.95);
}

.self-study-toggle {
  display: flex;
  align-items: center;
  padding-left: 146px;
}

.self-study-toggle :deep(.el-checkbox) {
  font-size: 13px;
  color: #475569;
  font-weight: 500;
}

.self-study-settings {
  display: grid;
  grid-template-columns: 148px minmax(0, 1fr);
  gap: 10px;
  padding-left: 146px;
  align-items: center;
}

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

:deep(.gaokao-time-dialog .el-input__wrapper) {
  min-height: 34px;
  border-radius: 10px;
  background: #fff;
  box-shadow: none;
  border: 1px solid transparent;
  transition: border-color 0.2s ease, box-shadow 0.2s ease, background-color 0.2s ease;
}

:deep(.gaokao-time-dialog .el-input__wrapper:hover) {
  border-color: #bfdbfe;
  box-shadow: 0 0 0 1px rgba(191, 219, 254, 0.55);
}

:deep(.gaokao-time-dialog .el-input__wrapper.is-focus) {
  border-color: #60a5fa;
  box-shadow: 0 0 0 3px rgba(96, 165, 250, 0.18);
}

:deep(.gaokao-time-dialog .el-date-editor),
:deep(.gaokao-time-dialog .el-date-editor.el-input),
:deep(.gaokao-time-dialog .el-input),
:deep(.gaokao-time-dialog .el-time-editor.el-input) {
  width: 100%;
}

:deep(.gaokao-time-dialog .el-button) {
  border-radius: 10px;
  font-weight: 600;
}

:deep(.gaokao-time-dialog .el-button--primary) {
  background: #2563eb;
  border-color: #2563eb;
  box-shadow: 0 10px 22px -16px rgba(37, 99, 235, 0.65);
}

:deep(.gaokao-time-dialog .el-button--primary:hover) {
  background: #1d4ed8;
  border-color: #1d4ed8;
}

:deep(.gaokao-time-dialog .el-checkbox__label) {
  font-size: 13px;
}

:deep(.time-picker-popper) {
  max-width: 280px !important;
}

@media (max-width: 768px) {
  :deep(.gaokao-time-dialog.el-dialog) {
    height: 90vh !important;
    max-height: 90vh !important;
  }

  :deep(.gaokao-time-dialog .el-dialog__body) {
    padding: 16px;
  }

  .section-header {
    flex-direction: column;
    align-items: stretch;
  }

  .table-header,
  .exam-row {
    grid-template-columns: 112px 132px minmax(0, 1fr);
    gap: 8px;
    font-size: 12px;
  }

  .table-header {
    padding: 8px 10px;
  }

  .exam-row {
    padding: 8px 10px;
  }

  .info-banner {
    padding: 10px 12px;
  }

  .self-study-toggle {
    padding-left: 120px;
  }

  .self-study-settings {
    padding-left: 120px;
    grid-template-columns: 132px minmax(0, 1fr);
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
  :deep(.gaokao-time-dialog.el-dialog) {
    height: 95vh !important;
    max-height: 95vh !important;
    width: calc(100vw - 16px) !important;
  }

  :deep(.gaokao-time-dialog .el-dialog__body) {
    padding: 12px;
  }

  .exam-row {
    grid-template-columns: 1fr;
    gap: 10px;
  }

  .table-header {
    display: none;
  }

  .time-range {
    gap: 4px;
  }

  .time-separator {
    padding: 0 2px;
  }

  .self-study-toggle {
    padding-left: 0;
  }

  .self-study-settings {
    padding-left: 0;
    gap: 10px;
    grid-template-columns: 1fr;
  }

  .dialog-footer {
    flex-direction: column;
    align-items: stretch;
    gap: 12px;
  }

  .reset-btn,
  .action-buttons :deep(.el-button) {
    width: 100%;
    justify-content: center;
  }

  .action-buttons {
    width: 100%;
  }
}
</style>

