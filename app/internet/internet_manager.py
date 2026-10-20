from app.internet.search_engine import SearchEngine
from app.ai.ai_manager import AIManager


class InternetManager:

    def __init__(self):
        self.search = SearchEngine()
        self.ai = AIManager()
        
        #result  = self.engine.search()

    def search_and_summarize(self, query):

        results = self.search.search(query)

        prompt = f"""
Summarize the following search in 5-6 simple sentences.

Search Results:

{results}
"""

        try:
            return self.ai.ask(prompt)
        except Exception:
            return results

    def search(self, query):
        return self.search.search(query)

    def get_news(self):
        return self.search_and_summarize("latest news")

    def get_weather(self, city):
        return self.search_and_summarize(f"weather {city}")

    def wikipedia(self, topic):
        return self.search_and_summarize(f"wikipedia {topic}")

    def google(self, query):
        return self.search_and_summarize(query)