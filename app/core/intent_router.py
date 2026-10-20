from app.core.intent_registry import IntentRegistry
from app.core.text_normalizer import TextNormalizer
from app.core.fuzzy_matcher import FuzzyMatcher


class IntentRouter:

    THRESHOLD = 0.85

    def detect_intent(self, text):

        text = TextNormalizer.normalize(text)

        # Rule-based check for news — must be checked BEFORE the loop
        if (
            "news" in text
            or "headlines" in text
            or "breaking news" in text
        ):
            return {
                "intent": "NEWS",
                "confidence": 0.98,
                "source": "RULE"
            }

        best_intent = "UNKNOWN"
        best_score = 0

        for intent, phrases in IntentRegistry.INTENTS.items():

            for phrase in phrases:

                # exact match
                if text == phrase:
                    return {
                        "intent": intent,
                        "confidence": 1.0,
                        "source": "EXACT"
                    }

                # startswith
                if text.startswith(phrase):
                    score = 0.95
                else:
                    score = FuzzyMatcher.similarity(text, phrase)

                if score > best_score:
                    best_score = score
                    best_intent = intent

        if best_score >= self.THRESHOLD:

            return {
                "intent": best_intent,
                "confidence": round(best_score, 2),
                "source": "FUZZY"
            }

        return {
            "intent": "UNKNOWN",
            "confidence": 0.0,
            "source": "NONE"
        }











"""class IntentRouter:

    def detect_intent(self, text):

        text = text.lower().strip()

        if text in [
            "hi",
            "hello",
            "hey"
        ]:
            return "GREETINGS"

        if text in [
            "who are you",
            "what can you do",
            "do you know me",
            "how are you"
        ]:
            return "CHAT"

        if text.startswith(("who is", "what is", "tell me about", "latest")):
            return "WEB_SEARCH"

        if text.startswith(("create", "make", "build")):
            return "CREATE_CODE"

        if text.startswith(("open", "launch", "run")):
            return "OPEN_APPLICATION"

        if text.startswith(("close", "stop", "terminate")):
            return "CLOSE_APPLICATION"

        if text.startswith(("remember", "save")):
            return "SAVE_MEMORY"

        if "what is my" in text:
            return "GET_MEMORY"

        if "time" in text or "clock" in text:
            return "GET_TIME"

        return "UNKNOWN" """





"""class IntentRouter:
    
    def detect_intent(self, text):
        
        print("TEXT:",text)
        
        text = text.lower()
        
        INTENTS = {
            
            "OPEN_APPLICATION": [
                "open",
                "launch",
                "start",
                "run"
            ],
            
            "SAVE_MEMORY": [
                "remember",
                "save"
            ],
            
            "GET_TIME":[
                "time",
                "clock"
            ],
            
            "GREETINGS":[
                "hello",
                "hi"
            ],
            
            "EXIT": [
                "exit",
                "quit"
            ],
            
            "WEB_SEARCH": [
                "search",
                "find",
                "who is",
                "what is",
                "tell me about",
                "latest"
            ],
            
            "CREATE_CODE": [
                "create",
                "make",
                "build",
                "write code",
                "generate code"
            ],
            "CHAT":[
                "who are you",
                "what can you do",
                "do you know me",
                "how are you",
                "who made you",
                "your name",
            ]
            
            
        }
               
        
        if "what is my" in text:
            return "GET_MEMORY"
        
        elif any(word in text for word in ["close", "stop", "terminate"]):
            return "CLOSE_APPLICATION"
        
        elif (
           text.startswith("who is") 
           or text.startswith("what is")
           or text.startswith("tell me about")
           or text.startswith("latest")
        ):
            return "WEB_SEARCH"
        
        elif(
            text.startswith("create")
            or text.startswith("make")
            or text.startswith("build")
        ):
            return "CREATE_CODE"
        
        if any(text == phrase for phrase in [
        "who are you",
        "what can you do",
        "do you know me",
        "how are you",
        "who made you",
        ]):
            return "CHAT"
        
        for intent, keywords in INTENTS.items():
            words = text.split()
            if any(keyword in text for keyword in keywords):
                return intent
        print("Detected: UNKNOWN")
        
        return "UNKNOWN"   """
       