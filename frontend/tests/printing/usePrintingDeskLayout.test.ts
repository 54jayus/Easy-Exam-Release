import { describe, expect, it, vi } from 'vitest'
import { computed, reactive, ref } from 'vue'
import { usePrintingDeskLayout } from '@/views/PrintingPage/composables/usePrintingDeskLayout'

describe('usePrintingDeskLayout', () => {
  it('applies custom layout config while preserving downstream callbacks', async () => {
    const config = reactive({
      desk: {
        layoutName: '7行×6列',
        layoutRows: 7,
        layoutCols: 6,
        layoutPattern: 'S型竖排',
        startPos: 'left',
        customColCounts: null as number[] | null,
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
    const onAfterApply = vi.fn()

    const layoutApi = usePrintingDeskLayout({
      config,
      displayData,
      hasPreviewData,
      sourceType,
      onAfterApply,
    })

    expect(layoutApi.deskLayoutSummary.value).toContain('7行×6列')

    layoutApi.openDeskLayoutDialog()
    layoutApi.deskLayoutDraft.layoutName = '自定义'
    layoutApi.deskLayoutDraft.customCountsText = '2,1'

    await layoutApi.applyDeskLayoutDraft()

    expect(config.desk.customColCounts).toEqual([2, 1])
    expect(config.desk.layoutRows).toBe(2)
    expect(config.desk.layoutCols).toBe(2)
    expect(onAfterApply).toHaveBeenCalledTimes(1)
  })
})
