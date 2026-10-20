class QueryExctractor:
    
    def extract(self, text):
        
        text = text.lower()
        
        if "what is my " in text:
            
            key = text.replace("what is my", "")
            key = key.replace("?", "")
            key = key.strip().replace(" ", "_")
            
            return key
        
        return None