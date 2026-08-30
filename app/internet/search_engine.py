from ddgs import DDGS

class SearchEngine:
    
    def search(self, query):
        
        print("Searching for:",query)
        try:
            with DDGS() as ddgs:
                results = list(ddgs.text(query,max_results=3))
                
            print("REsults:", results)
            
            if not results:
                return "No results found."
        
            answer = ""
        
            for result in results:
            
                answer += f"{result['title']}\n"
                answer += f"{result['body']}\n"
                answer += f"{result['href']}\n\n"
            
            return answer
        
        except Exception as e:
            return str(e)