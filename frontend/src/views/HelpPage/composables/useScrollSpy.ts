import { ref, nextTick, type Ref } from 'vue'
import type { TocItem } from './useTocGeneration'

type ScrollSpyItem = {
  anchor: string
  tocId: string
  top: number
}

export function useScrollSpy(
  tocData: Ref<TocItem[]>,
  contentScrollRef: Ref<HTMLElement | undefined>,
  tocTreeRef: Ref<any>,
  tocScrollRef: Ref<HTMLElement | undefined>
) {
  const scrollProgress = ref(0)
  const showBackToTop = ref(false)
  const activeTocId = ref('')

  let scrollSpyIndex: ScrollSpyItem[] = []
  let anchorToTocId = new Map<string, string>()
  let scrollSyncScheduled = false
  let tocEnsureVisibleScheduled = false

  function ensureActiveTocVisible() {
    const container = tocScrollRef.value
    if (!container) return

    const el = container.querySelector<HTMLElement>('.el-tree-node.is-current')
    if (!el) return

    const containerRect = container.getBoundingClientRect()
    const elRect = el.getBoundingClientRect()
    const padding = 20

    if (elRect.top < containerRect.top + padding) {
      container.scrollTop -= containerRect.top + padding - elRect.top
    } else if (elRect.bottom > containerRect.bottom - padding) {
      container.scrollTop += elRect.bottom - (containerRect.bottom - padding)
    }
  }

  function scheduleEnsureActiveTocVisible() {
    if (tocEnsureVisibleScheduled) return
    tocEnsureVisibleScheduled = true
    requestAnimationFrame(() => {
      tocEnsureVisibleScheduled = false
      ensureActiveTocVisible()
    })
  }

  function rebuildScrollSpyIndex() {
    anchorToTocId = new Map<string, string>()
    const stack: TocItem[] = [...(tocData.value || [])]
    while (stack.length) {
      const item = stack.shift()!
      anchorToTocId.set(item.anchor, item.id)
      if (item.children?.length) stack.unshift(...item.children)
    }

    const container = contentScrollRef.value
    if (!container) {
      scrollSpyIndex = []
      return
    }

    const headings = Array.from(container.querySelectorAll<HTMLElement>('h2[id], h3[id]'))
    scrollSpyIndex = headings
      .map(el => {
        const anchor = el.id
        const tocId = anchorToTocId.get(anchor)
        if (!tocId) return null
        return { anchor, tocId, top: el.offsetTop }
      })
      .filter((x): x is ScrollSpyItem => Boolean(x))
      .sort((a, b) => a.top - b.top)

    syncTocByScroll()
  }

  function syncTocByScroll() {
    const container = contentScrollRef.value
    if (!container || scrollSpyIndex.length === 0) return

    const scrollTop = container.scrollTop
    const threshold = 120
    const target = scrollTop + threshold

    let candidate: ScrollSpyItem | null = null
    for (const item of scrollSpyIndex) {
      if (item.top <= target) candidate = item
      else break
    }

    // If we are at the bottom, select the last one
    if (container.scrollHeight - container.scrollTop <= container.clientHeight + 50) {
      candidate = scrollSpyIndex[scrollSpyIndex.length - 1]
    }

    if (!candidate && scrollSpyIndex.length > 0) candidate = scrollSpyIndex[0]

    if (candidate && activeTocId.value !== candidate.tocId) {
      activeTocId.value = candidate.tocId
      tocTreeRef.value?.setCurrentKey?.(candidate.tocId)
      nextTick(() => {
        scheduleEnsureActiveTocVisible()
      })
    }
  }

  function onContentScroll() {
    if (!contentScrollRef.value) return

    const { scrollTop, scrollHeight, clientHeight } = contentScrollRef.value
    scrollProgress.value = (scrollTop / (scrollHeight - clientHeight)) * 100
    showBackToTop.value = scrollTop > 400

    if (scrollSyncScheduled) return
    scrollSyncScheduled = true
    requestAnimationFrame(() => {
      scrollSyncScheduled = false
      syncTocByScroll()
    })
  }

  function scrollToTop() {
    contentScrollRef.value?.scrollTo({ top: 0, behavior: 'smooth' })
  }

  return {
    scrollProgress,
    showBackToTop,
    activeTocId,
    rebuildScrollSpyIndex,
    onContentScroll,
    scrollToTop
  }
}
