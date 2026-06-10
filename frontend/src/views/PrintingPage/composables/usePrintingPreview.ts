import {
  computed,
  nextTick,
  onBeforeUnmount,
  onMounted,
  reactive,
  ref,
  watch,
  type Ref,
} from 'vue'

type PreviewTargetPx = {
  w: number
  h: number
}

type UsePrintingPreviewOptions = {
  activeTab: Ref<string>
  rollCallOrientation?: Ref<string>
}

export function usePrintingPreview({ activeTab, rollCallOrientation }: UsePrintingPreviewOptions) {
  const previewViewportRef = ref<HTMLElement | null>(null)
  const previewPageRef = ref<HTMLElement | null>(null)
  const previewOverlayRef = ref<HTMLElement | null>(null)
  const previewScale = ref(1)
  const autoFit = ref(true)
  const previewOffset = reactive({ x: 0, y: 0 })
  const isPanningPreview = ref(false)
  const isCtrlDown = ref(false)
  const previewMode = ref<'style' | 'print'>('style')
  const deskPreviewMode = ref<'seat' | 'print'>('seat')

  const previewBaseWidth = ref(0)
  const previewBaseHeight = ref(0)

  let previewResizeObserver: ResizeObserver | null = null
  let panStart: { x: number; y: number; ox: number; oy: number } | null = null

  const previewCursorClass = computed(() => {
    if (isPanningPreview.value) return 'cursor-grabbing select-none'
    if (isCtrlDown.value) return 'cursor-grab'
    return ''
  })

  const previewPageSizeMm = computed(() => {
    if (activeTab.value === 'desk' && deskPreviewMode.value === 'print') {
      return { width: '210mm', height: '297mm' }
    }
    if (activeTab.value === 'table') {
      return { width: '210mm', height: '297mm' }
    }
    if (activeTab.value === 'exam_bag_label') {
      return { width: '210mm', height: '297mm' }
    }
    if (activeTab.value === 'roll_call') {
      const mode = rollCallOrientation?.value || 'auto'
      if (mode === 'portrait') return { width: '210mm', height: '297mm' }
      if (mode === 'landscape') return { width: '297mm', height: '210mm' }
      return { width: '297mm', height: '210mm' }
    }
    return { width: '297mm', height: '210mm' }
  })

  const previewTargetPx = computed<PreviewTargetPx>(() => {
    if (activeTab.value === 'desk' && deskPreviewMode.value === 'print') return { w: 794, h: 1122 }
    if (activeTab.value === 'table') return { w: 794, h: 1122 }
    if (activeTab.value === 'exam_bag_label') return { w: 794, h: 1122 }
    if (activeTab.value === 'roll_call') {
      const mode = rollCallOrientation?.value || 'auto'
      if (mode === 'portrait') return { w: 794, h: 1122 }
      return { w: 1122, h: 794 }
    }
    return { w: 1122, h: 794 }
  })

  function getMaxAutoFitScale() {
    if (activeTab.value === 'desk') return 1
    return 1.5
  }

  function resetPreviewTransform() {
    autoFit.value = true
    previewOffset.x = 0
    previewOffset.y = 0
  }

  function handleZoomIn() {
    autoFit.value = false
    previewScale.value = Math.min(2.0, previewScale.value + 0.1)
  }

  function handleZoomOut() {
    autoFit.value = false
    previewScale.value = Math.max(0.2, previewScale.value - 0.1)
  }

  function updatePreviewScale() {
    if (!autoFit.value) return

    const viewportEl = previewViewportRef.value
    if (!viewportEl) return

    const baseW = previewBaseWidth.value
    const baseH = previewBaseHeight.value
    const { w, h } = previewTargetPx.value
    const targetWidth = baseW > 0 ? baseW : w
    const targetHeight = baseH > 0 ? baseH : h

    const availableW = Math.max(0, viewportEl.clientWidth - 64)
    let availableH = Math.max(0, viewportEl.clientHeight - 64)

    const overlayEl = previewOverlayRef.value
    if (overlayEl) {
      const overlayRect = overlayEl.getBoundingClientRect()
      if (overlayRect.height > 0) availableH = Math.max(0, availableH - overlayRect.height - 24)
    }

    const sx = availableW / targetWidth
    const sy = availableH / targetHeight
    const next = Math.min(sx, sy) * 0.98
    previewScale.value = Math.min(getMaxAutoFitScale(), Math.max(0.3, Number.isFinite(next) ? next : 1))
  }

  function handleAutoFit() {
    resetPreviewTransform()
    updatePreviewScale()
  }

  function handlePreviewWheel(event: WheelEvent) {
    if (!event.ctrlKey) return

    event.preventDefault()
    event.stopPropagation()

    const factor = 0.001
    const delta = -event.deltaY * factor
    const next = Math.min(3.0, Math.max(0.2, previewScale.value + delta))
    if (next !== previewScale.value) {
      previewScale.value = next
      autoFit.value = false
    }
  }

  function endPreviewPan() {
    if (!isPanningPreview.value) return

    isPanningPreview.value = false
    panStart = null
    document.body.style.userSelect = ''
    window.removeEventListener('mousemove', handlePreviewMouseMove, true)
    window.removeEventListener('mouseup', handlePreviewMouseUp, true)
  }

  function handlePreviewMouseMove(event: MouseEvent) {
    if (!isPanningPreview.value || !panStart) return

    previewOffset.x = panStart.ox + (event.clientX - panStart.x)
    previewOffset.y = panStart.oy + (event.clientY - panStart.y)
  }

  function handlePreviewMouseUp() {
    endPreviewPan()
  }

  function handlePreviewMouseDown(event: MouseEvent) {
    if (!event.ctrlKey) return
    if (event.button !== 0) return

    event.preventDefault()
    event.stopPropagation()

    autoFit.value = false
    isPanningPreview.value = true
    document.body.style.userSelect = 'none'
    panStart = { x: event.clientX, y: event.clientY, ox: previewOffset.x, oy: previewOffset.y }
    window.addEventListener('mousemove', handlePreviewMouseMove, true)
    window.addEventListener('mouseup', handlePreviewMouseUp, true)
  }

  function measurePreviewBaseSize() {
    const pageEl = previewPageRef.value
    if (!pageEl) return

    // 使用 offsetWidth/offsetHeight，这些属性不受 zoom 和 transform 的影响
    const width = pageEl.offsetWidth
    const height = pageEl.offsetHeight
    if (width > 0 && height > 0) {
      previewBaseWidth.value = width
      previewBaseHeight.value = height
    }
  }

  function initPreviewAutoScale() {
    if (previewResizeObserver) previewResizeObserver.disconnect()
    if (!previewViewportRef.value) return

    previewResizeObserver = new ResizeObserver(() => updatePreviewScale())
    previewResizeObserver.observe(previewViewportRef.value)
    updatePreviewScale()
  }

  function handleKeyDown(event: KeyboardEvent) {
    if (event.key === 'Control') isCtrlDown.value = true
  }

  function handleKeyUp(event: KeyboardEvent) {
    if (event.key !== 'Control') return

    isCtrlDown.value = false
    endPreviewPan()
  }

  function handleWindowBlur() {
    isCtrlDown.value = false
    endPreviewPan()
  }

  watch(previewMode, async () => {
    await nextTick()
    handleAutoFit()
  })

  watch(deskPreviewMode, async () => {
    resetPreviewTransform()
    await nextTick()
    measurePreviewBaseSize()
    updatePreviewScale()
  })

  onMounted(() => {
    window.addEventListener('keydown', handleKeyDown)
    window.addEventListener('keyup', handleKeyUp)
    window.addEventListener('blur', handleWindowBlur)
  })

  onBeforeUnmount(() => {
    window.removeEventListener('keydown', handleKeyDown)
    window.removeEventListener('keyup', handleKeyUp)
    window.removeEventListener('blur', handleWindowBlur)
    endPreviewPan()
    if (previewResizeObserver) previewResizeObserver.disconnect()
    previewResizeObserver = null
  })

  return {
    previewViewportRef,
    previewPageRef,
    previewOverlayRef,
    previewScale,
    autoFit,
    previewOffset,
    isPanningPreview,
    previewMode,
    deskPreviewMode,
    previewCursorClass,
    previewPageSizeMm,
    previewTargetPx,
    resetPreviewTransform,
    handleZoomIn,
    handleZoomOut,
    handleAutoFit,
    handlePreviewWheel,
    handlePreviewMouseDown,
    measurePreviewBaseSize,
    updatePreviewScale,
    initPreviewAutoScale,
  }
}
