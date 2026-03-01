from .manual_knowledge import build_sections, format_context_snippets, load_manual_markdown, search_sections


class AssistantKnowledge:
    def __init__(self):
        markdown = load_manual_markdown()
        self._sections = build_sections(markdown)

    def build_context(self, query, top_k=4, max_chars=4500):
        hits = search_sections(self._sections, query, top_k=top_k)
        return format_context_snippets(hits, max_chars=max_chars)

