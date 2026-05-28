import { ref, watch, onBeforeUnmount } from 'vue'

export function useSmoothProgress(source: { value: number }) {
  const smooth = ref(Number.isFinite(source.value) ? source.value : 0)
  let rafId: number | null = null

  const tick = () => {
    const diff = source.value - smooth.value
    if (Math.abs(diff) < 0.1) {
      smooth.value = source.value
      rafId = null
      return
    }
    smooth.value += diff * 0.15
    rafId = requestAnimationFrame(tick)
  }

  watch(() => source.value, () => {
    if (rafId == null) {
      rafId = requestAnimationFrame(tick)
    }
  }, { immediate: true })

  onBeforeUnmount(() => {
    if (rafId != null) {
      cancelAnimationFrame(rafId)
      rafId = null
    }
  })

  return smooth
}
