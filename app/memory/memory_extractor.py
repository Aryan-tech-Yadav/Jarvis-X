class MemoryExtractor:
    
    def extract(self, text):
        
        text = text.lower()
        
        if "my" in text and "is" in text:
            
            start = text.find("my") + 3
            end = text.find("is")
            
            key = text[start:end].strip().replace(" ","_")
            value = text[end + 2:].strip()
            
            return key, value
        
        return None, None