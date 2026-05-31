import { ref, nextTick, type Ref } from 'vue'

export interface TocItem {
  id: string
  label: string
  level: number
  anchor: string
  sectionNum?: string
  children?: TocItem[]
}

function slugify(text: string) {
  return text
    .trim()
    .toLowerCase()
    .replace(/[^\w\u4e00-\u9fa5]+/g, '-')
    .replace(/-+/g, '-')
}

export function useTocGeneration() {
  const tocData = ref<TocItem[]>([])

  function generateToc(markdown: string) {
    const lines = markdown.split('\n')
    const toc: TocItem[] = []
    let currentLevel1: TocItem | null = null

    lines.forEach((line, index) => {
      const h1Match = line.match(/^#\s+(.+)/)
      const h2Match = line.match(/^##\s+(.+)/)
      const h3Match = line.match(/^###\s+(.+)/)

      if (h1Match) {
        // H1 is usually title, skip or add as root
      } else if (h2Match) {
        const anchorId = `header-${slugify(h2Match[1])}`
        const numMatch = h2Match[1].match(/^(\d+)\./)
        const item: TocItem = {
          id: `h2-${index}`,
          label: h2Match[1],
          level: 1,
          anchor: anchorId,
          sectionNum: numMatch?.[1],
          children: []
        }
        toc.push(item)
        currentLevel1 = item
      } else if (h3Match && currentLevel1) {
        const anchorId = `header-${slugify(h3Match[1])}`
        const item: TocItem = {
          id: `h3-${index}`,
          label: h3Match[1],
          level: 2,
          anchor: anchorId
        }
        currentLevel1.children?.push(item)
      }
    })

    tocData.value = toc
  }

  async function injectHeadingIds(containerRef?: Ref<HTMLElement | undefined>) {
    // Wait for DOM to render
    await nextTick()
    const container = containerRef?.value
    if (!container) return

    // Build anchor → tocId mapping
    const anchorMap = new Map<string, string>()
    const stack = [...tocData.value]
    while (stack.length) {
      const item = stack.shift()!
      anchorMap.set(item.label, item.anchor)
      if (item.children?.length) stack.push(...item.children)
    }

    // One-pass traversal to set IDs
    const headings = container.querySelectorAll('h2, h3')
    headings.forEach(heading => {
      const text = heading.textContent?.trim()
      const anchor = text ? anchorMap.get(text) : undefined
      if (anchor) {
        heading.id = anchor
      }
    })
  }

  return {
    tocData,
    generateToc,
    injectHeadingIds
  }
}
