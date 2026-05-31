import { ref } from 'vue'
import { ElMessage } from 'element-plus'
import { marked } from 'marked'
import { pythonBackend } from '@/lib/pythonBackend'

export function useMarkdown() {
  const manualMarkdown = ref('')
  const manualHtml = ref('')
  const loading = ref({
    manual: false
  })
  const loadError = ref(false)

  async function loadManual(): Promise<string | null> {
    loading.value.manual = true
    loadError.value = false
    try {
      const res = await pythonBackend.request('system.getHelpManual', {})
      const content = res.content || ''

      if (!content) {
        throw new Error('Empty manual content')
      }

      manualMarkdown.value = content
      manualHtml.value = await marked(content, { gfm: true, breaks: true })

      return content
    } catch (e) {
      console.error(e)
      loadError.value = true
      return null
    } finally {
      loading.value.manual = false
    }
  }

  return {
    manualMarkdown,
    manualHtml,
    loading,
    loadError,
    loadManual
  }
}
