import { ref, computed } from 'vue'

export interface SearchResult {
  id: string
  title: string
  content: string
  matchedText: string
  beforeText: string
  afterText: string
  anchor: string
}

export function useFullTextSearch() {
  const searchResults = ref<SearchResult[]>([])
  const isSearching = ref(false)

  function highlightText(text: string, query: string): string {
    if (!query) return text
    const regex = new RegExp(`(${escapeRegExp(query)})`, 'gi')
    return text.replace(regex, '<mark class="bg-yellow-200 text-slate-900 px-0.5 rounded">$1</mark>')
  }

  function escapeRegExp(str: string): string {
    return str.replace(/[.*+?^${}()|[\]\\]/g, '\\$&')
  }

  function extractContext(text: string, query: string, contextLength = 60): { before: string; matched: string; after: string } {
    const lowerText = text.toLowerCase()
    const lowerQuery = query.toLowerCase()
    const index = lowerText.indexOf(lowerQuery)

    if (index === -1) {
      return { before: '', matched: '', after: '' }
    }

    const start = Math.max(0, index - contextLength)
    const end = Math.min(text.length, index + query.length + contextLength)

    let before = text.substring(start, index)
    const matched = text.substring(index, index + query.length)
    let after = text.substring(index + query.length, end)

    // Add ellipsis if truncated
    if (start > 0) before = '...' + before
    if (end < text.length) after = after + '...'

    return { before, matched, after }
  }

  function searchInContent(htmlContent: string, query: string): SearchResult[] {
    if (!query || query.trim().length < 2) {
      return []
    }

    isSearching.value = true
    const results: SearchResult[] = []

    try {
      // Create a temporary DOM element to parse HTML
      const tempDiv = document.createElement('div')
      tempDiv.innerHTML = htmlContent

      // Get all headings and their content
      const headings = tempDiv.querySelectorAll('h1, h2, h3, h4, h5, h6')

      headings.forEach((heading, index) => {
        const headingId = heading.id || `heading-${index}`
        const headingText = heading.textContent || ''

        // Get all text content until next heading
        let currentElement = heading.nextElementSibling
        let sectionContent = ''

        while (currentElement && !currentElement.matches('h1, h2, h3, h4, h5, h6')) {
          sectionContent += ' ' + (currentElement.textContent || '')
          currentElement = currentElement.nextElementSibling
        }

        // Search in heading
        if (headingText.toLowerCase().includes(query.toLowerCase())) {
          const context = extractContext(headingText, query)
          results.push({
            id: `${headingId}-title`,
            title: headingText,
            content: sectionContent.substring(0, 100) + '...',
            matchedText: context.matched,
            beforeText: context.before,
            afterText: context.after,
            anchor: headingId
          })
        }

        // Search in section content
        const lowerContent = sectionContent.toLowerCase()
        const lowerQuery = query.toLowerCase()
        let searchIndex = 0
        let matchCount = 0
        const maxMatchesPerSection = 3

        while (searchIndex < lowerContent.length && matchCount < maxMatchesPerSection) {
          const foundIndex = lowerContent.indexOf(lowerQuery, searchIndex)
          if (foundIndex === -1) break

          // Extract context from the actual position in the content
          const actualStart = Math.max(0, foundIndex - 50)
          const actualEnd = Math.min(sectionContent.length, foundIndex + query.length + 50)

          let before = sectionContent.substring(actualStart, foundIndex)
          const matched = sectionContent.substring(foundIndex, foundIndex + query.length)
          let after = sectionContent.substring(foundIndex + query.length, actualEnd)

          // Add ellipsis if truncated
          if (actualStart > 0) before = '...' + before
          if (actualEnd < sectionContent.length) after = after + '...'

          results.push({
            id: `${headingId}-content-${matchCount}`,
            title: headingText,
            content: '',
            matchedText: matched,
            beforeText: before,
            afterText: after,
            anchor: headingId
          })

          matchCount++
          searchIndex = foundIndex + query.length
        }
      })
    } catch (error) {
      console.error('Search error:', error)
    } finally {
      isSearching.value = false
    }

    return results
  }

  function performSearch(htmlContent: string, query: string) {
    searchResults.value = searchInContent(htmlContent, query)
  }

  function clearSearch() {
    searchResults.value = []
  }

  const hasResults = computed(() => searchResults.value.length > 0)
  const resultCount = computed(() => searchResults.value.length)

  return {
    searchResults,
    isSearching,
    hasResults,
    resultCount,
    performSearch,
    clearSearch,
    highlightText
  }
}
