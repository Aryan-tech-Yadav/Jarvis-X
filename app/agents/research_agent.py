from app.agents.base_agent import BaseAgent
from app.knowledge.knowledge_manager import KnowledgeManager


class ResearchAgent(BaseAgent):
    name = "researcher"

    def __init__(self, knowledge_manager=None, internet_manager=None, limit=3):
        self.knowledge = knowledge_manager or KnowledgeManager()
        self.internet = internet_manager
        if self.internet is None:
            try:
                from app.internet.internet_manager import InternetManager
                self.internet = InternetManager()
            except ImportError:
                self.internet = None
        self.limit = limit

    def run(self, context):
        query = context.goal
        existing = self.knowledge.search(query, limit=self.limit, threshold=0.15)
        if existing:
            result = {"source": "knowledge_base", "results": existing, "query": query}
        else:
            if self.internet is None:
                return {"success": False, "output": "Web research is unavailable: install ddgs"}
            summary = self.internet.search_and_summarize(query)
            if not isinstance(summary, str) or not summary.strip():
                return {"success": False, "output": "Research returned no usable result"}
            document_id = self.knowledge.add_document(
                summary,
                {"source": "web_research", "query": query},
            )
            result = {
                "source": "web",
                "results": [{"id": document_id, "text": summary, "metadata": {"source": "web_research"}}],
                "query": query,
            }
        context.research = result
        return {"success": True, "output": result, "next_agent": "planner"}