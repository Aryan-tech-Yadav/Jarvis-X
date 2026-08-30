import string

class LanguageProcessor:
    
    def clean(self,text):
        
        text =  text.lower().strip()
        
        fillers = [
            
            "please",
            "can you",
            "could you"
            "would you"
            "kindly",
            "for me",
            "i want to",
            " i want like to"
        ]
        
        for word in fillers:
            text = text.replace(word, "")
        
        #Remove punctuations(?,.,! etc.)
        text = text.translate(str.maketrans("", "", string.punctuation))
            
        return text.strip()
    
    