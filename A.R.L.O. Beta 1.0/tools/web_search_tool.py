# =============================================================
# WEB_SEARCH_TOOL.PY
# Searches the web using DuckDuckGo (no API key required) and
# returns raw results for the AI to summarize.
# =============================================================

from ddgs import DDGS
from tools.registry import register


def web_search(query):
    """Searches the web and returns titles, URLs, and snippets for the AI to summarize."""
    results = []
    with DDGS() as ddgs:
        for r in ddgs.text(query, max_results=5):
            results.append(f"{r['title']} - {r['href']}\n{r['body']}")
    return "\n\n".join(results)


register(
    name="web_search",
    description=(
        "Search the web and read back a summarized answer with sources. Use this for "
        "any question you don't know the answer to, or anything involving current events, "
        "prices, scores, or facts that change over time."
    ),
    parameters={
        "type": "object",
        "properties": {
            "query": {"type": "string", "description": "What to search for."}
        },
        "required": ["query"],
    },
    function=web_search,
)