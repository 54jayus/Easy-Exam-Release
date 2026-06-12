import { describe, expect, it } from 'vitest'
import { computed, reactive, ref } from 'vue'
import { usePrintingDeskLayout } from '@/views/PrintingPage/composables/usePrintingDeskLayout'

describe('usePrintingDeskLayout', () => {
  it('uses the shared layout for desk-label printing without exposing edit actions', () => {
    const config = reactive({
      desk: {
        layoutName: '自定义',
        layoutRows: 2,
        layoutCols: 2,
        layoutPattern: 'S型竖排',
        startPos: 'left',
        customColCounts: [2, 1] as number[] | null,
      },
    })

    const displayData = computed(() => [
      {
        考场: '第一考场',
        考场号: '101',
        考生姓名: '张三',
        考生考号: '1001',
        座位号: '01',
      },
    ])
    const hasPreviewData = computed(() => true)
    const sourceType = ref('schedule')
    const layoutApi = usePrintingDeskLayout({
      config,
      displayData,
      hasPreviewData,
      sourceType,
    })

    expect(layoutApi.deskLayoutSummary.value).toContain('2行×2列')
    expect(layoutApi.deskPrintCellText(0, 1)).toContain('姓名：张三')
    expect(layoutApi.deskPrintCellText(1, 1)).toBe('')
    expect('openDeskLayoutDialog' in layoutApi).toBe(false)
    expect('applyDeskLayoutDraft' in layoutApi).toBe(false)
  })
})
