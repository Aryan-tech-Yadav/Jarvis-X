"""Hindi/Hinglish language processor for Jarvis-X.

Provides:
  - Intent detection from Hindi/Hinglish text
  - Entity extraction (project names, domains, keywords)
  - Text normalization for mixed-language input
  - Natural response generation in Hindi/English/Hinglish
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Tuple


@dataclass
class ParsedIntent:
    """Parsed user intent with extracted entities."""

    intent: str = "CHAT"
    confidence: float = 0.0
    original_text: str = ""
    cleaned_text: str = ""
    project_name: str = ""
    domain: str = ""
    keywords: List[str] = field(default_factory=list)
    app_name: str = ""
    website_name: str = ""
    song_name: str = ""
    news_query: str = ""
    search_query: str = ""
    raw_entities: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict:
        return {
            "intent": self.intent,
            "confidence": self.confidence,
            "original_text": self.original_text,
            "cleaned_text": self.cleaned_text,
            "project_name": self.project_name,
            "domain": self.domain,
            "keywords": list(self.keywords),
            "app_name": self.app_name,
            "website_name": self.website_name,
            "song_name": self.song_name,
            "news_query": self.news_query,
            "search_query": self.search_query,
            "raw_entities": dict(self.raw_entities),
        }


class HindiHinglishProcessor:
    """Process Hindi/Hinglish input for Jarvis-X.

    Handles:
      - Devanagari and Romanized Hindi
      - Hinglish code-mixing
      - Common engineering command patterns
      - Project name extraction
      - Domain detection
    """

    # ============================
    # Intent patterns
    # ============================
    CREATE_CODE_PATTERNS = [
        # English
        r"\b(build|create|make|generate|develop|code|write)\b",
        # Hindi Devanagari
        r"\b(बनाओ|बनाओ|लिखो|कोड\s*करो|प्रोजेक्ट\s*बनाओ|ऐप\s*बनाओ|सॉफ्टवेयर\s*बनाओ)\b",
        # Romanized Hindi
        r"\b(banao|banado|likho|code\s*karo|project\s*banao|app\s*banao|software\s*banao)\b",
        # Hinglish
        r"\b(build\s*karo|create\s*karo|generate\s*karo|code\s*likh|project\s*bana)\b",
    ]

    STATUS_PATTERNS = [
        r"\b(status|progress|report|kya\s*hua|kya\s*hoga|क्या\s*हुआ|क्या\s*होगा)\b",
        r"\b(कहां\s*पहुंचा|कहां\s*तक|कैसा\s*चल\s*रहा|कैसा\s*है)\b",
    ]

    HISTORY_PATTERNS = [
        r"\b(history|previous|pehle|pahile|pichle|पहले|पिछले|इतिहास)\b",
    ]

    HELP_PATTERNS = [
        r"\b(help|madad|kaise|how|कैसे|मदद|सहायता)\b",
    ]

    EXIT_PATTERNS = [
        r"\b(exit|quit|bye|alvida|chup|बंद\s*करो|अलविदा|चुप)\b",
    ]

    SHUTDOWN_PATTERNS = [
        r"\b(shutdown|shut\s*down|power\s*off|turn\s*off|band\s*ho\s*ja|shut)\b",
        r"\b(शटडाउन|बंद\s*हो\s*जा|पावर\s*ऑफ|बंद\s*कर\s*दो)\b",
        r"\b(band\s*ho\s*jana|shut\s*down\s*karo|power\s*off\s*karo)\b",
    ]

    RESTART_PATTERNS = [
        r"\b(restart|reboot|restart\s*karo|reboot\s*karo)\b",
        r"\b(फिर\s*से\s*शुरू|रीस्टार्ट|रिबूट|restart\s*kar)\b",
    ]

    SLEEP_PATTERNS = [
        r"\b(sleep|suspend|hibernate|so\s*ja|sleep\s*mode)\b",
        r"\b(सो\s*जा|स्लीप|सस्पेंड|हाइबरनेट)\b",
    ]

    LOCK_PATTERNS = [
        r"\b(lock|lock\s*screen|screen\s*lock|lock\s*karo|lock\s*kar)\b",
        r"\b(लॉक|लॉक\s*करो|स्क्रीन\s*लॉक)\b",
    ]

    CANCEL_SHUTDOWN_PATTERNS = [
        r"\b(cancel\s*shutdown|stop\s*shutdown|cancel\s*restart|abort)\b",
        r"\b(बंद\s*न\s*करो|रुको|कैंसल|cancel\s*karo)\b",
    ]

    PLAY_MUSIC_PATTERNS = [
        r"\b(play\s*music|music\s*play|play\s*song|play\s*spotify|start\s*music)\b",
        r"\b(गाना\s*बजाओ|म्यूजिक\s*चलाओ|स्पॉटिफाई\s*चलाओ|गाना\s*सुनाओ)\b",
        r"\b(gaana\s*bajao|music\s*chalao|spotify\s*chalao|bajao|sunaao)\b",
    ]

    SPOTIFY_SONG_PATTERNS = [
        # English: "play shape of you on spotify"
        r"\bplay\s+(.+?)\s+on\s+spotify\b",
        # Hinglish: "spotify pe shape of you chalao", "spotify par shape of you bajao"
        r"\b(?:spotify\s*pe|spotify\s*par)\s+(.+?)(?:\s+chalao|\s+bajao|\s+play\s+karo)?\s*$",
        # Hindi: "spotify पर गाना बजाओ" (with specific song)
        r"\b(?:spotify\s*पर|स्पॉटिफाई)\s+(.+?)(?:\s*बजाओ|\s*चलाओ)?\s*$",
    ]

    NEWS_PATTERNS = [
        r"\b(news|latest\s*news|today\s*news|breaking\s*news|current\s*news|headlines)\b",
        r"\b(कhabar|समाचार|खबरें|न्यूज|ताजा\s*खबरें|ताजा\s*समाचार|खबर|समाचार)\b",
        r"\b(khabar|samachar|khabarein|news|taja\s*khabar|taza\s*khabar)\b",
    ]

    GOOGLE_SEARCH_PATTERNS = [
        r"\b(google|search|search\s*on\s*google|google\s*pe\s*search|google\s*karo)\b\s+(.+?)$",
        r"\b(google\s*pe|google\s*par)\b\s+(.+?)$",
    ]

    # Known websites for disambiguation between app vs website
    KNOWN_WEBSITES = {
        "youtube", "google", "github", "chatgpt", "gmail", "instagram",
        "facebook", "twitter", "x", "linkedin", "reddit", "whatsapp",
        "netflix", "amazon", "flipkart", "stackoverflow", "claude",
        "gemini", "bing", "yahoo", "maps", "drive", "docs", "sheets",
        "slides", "photos", "calendar", "outlook", "teams", "zoom",
        "discord", "telegram", "spotify", "soundcloud", "wikipedia",
        "quora", "medium", "dev", "hackernews", "producthunt",
        "dribbble", "behance", "figma", "canva", "trello", "notion",
        "slack", "asana", "jira", "confluence", "wordpress", "blogger",
        "tumblr", "pinterest", "tiktok", "snapchat", "twitch",
        "disney", "hotstar", "sonyliv", "jio", "airtel", "bsnl",
        "irctc", "paytm", "phonepe", "gpay", "amazonpay", "cred",
        "zomato", "swiggy", "uber", "ola", "rapido", "makemytrip",
        "goibibo", "yatra", "booking", "airbnb", "justdial", "indiamart",
    }

    OPEN_APP_PATTERNS = [
        # English: "open chrome", "launch vscode", "start notepad"
        r"\b(open|launch|start|run)\b\s+(.+?)(?:\s+app|\s+application|\s+software)?$",
        # Hinglish: "chrome kholo", "vscode band karo"
        r"(.+?)\s+(kholo|band\s*karo|close\s*karo|stop\s*karo|shuru\s*karo|chalu\s*karo|launch\s*karo|run\s*karo)$",
        # Hindi: "notepad खोलो", "chrome बंद करो"
        r"(.+?)\s+(खोलो|शुरू\s*करो|चालू\s*करो|बंद\s*करो|बंद\s*करो|रन\s*करो)\s*$",
    ]

    OPEN_WEBSITE_PATTERNS = [
        # English: "open youtube", "visit google", "go to github"
        r"\b(open|visit|go\s+to|browse)\b\s+(.+?)(?:\s+website|\s+site|\s+page)?$",
        # Hinglish: "youtube kholo", "google dekho"
        r"(.+?)\s+(kholo|dekho|browse\s*karo|visit\s*karo|open\s*karo)\s*$",
    ]

    CLOSE_APP_PATTERNS = [
        # Hinglish: "chrome band karo", "notepad close karo"
        r"(.+?)\s+(band\s*karo|close\s*karo|stop\s*karo|terminate\s*karo|बंद\s*करो)\s*$",
        # Hindi: "chrome बंद करो"
        r"(.+?)\s+(बंद\s*करो|बंद\s*करो|रोको)\s*$",
        # English: "close chrome", "stop notepad"
        r"\b(close|stop|band|terminate)\b\s+(.+?)(?:\s+app|\s+application)?$",
    ]

    # ============================
    # Domain patterns
    # ============================
    DOMAIN_PATTERNS = {
        "hospital": [
            "hospital", "clinic", "patient", "doctor", "medical", "healthcare",
            "appointment", "pharmacy", "hospital", "clinic", "patient", "doctor",
            "अस्पताल", "क्लिनिक", "डॉक्टर", "मेडिकल", "हेल्थकेयर", "रोगी",
            "aspataal", "clinic", "doctor", "medical", "healthcare", "rogi",
        ],
        "ecommerce": [
            "ecommerce", "shop", "store", "cart", "checkout", "product", "payment", "order",
            "दुकान", "स्टोर", "कार्ट", "ऑर्डर", "उत्पाद", "dukaan", "store", "cart", "order", "product",
        ],
        "education": [
            "education", "school", "student", "course", "learning", "exam", "teacher",
            "शिक्षा", "स्कूल", "छात्र", "पाठ्यक्रम", "शिक्षक", "shiksha", "school", "student", "teacher",
        ],
        "finance": [
            "finance", "bank", "transaction", "payment", "loan", "account", "billing",
            "वित्त", "बैंक", "लोन", "खाता", "भुगतान", "vitt", "bank", "loan", "payment",
        ],
        "social": [
            "social", "chat", "message", "post", "feed", "friend", "follow",
            "सामाजिक", "चैट", "संदेश", "दोस्त", "saamaajik", "chat", "message", "friend",
        ],
        "crm": [
            "crm", "customer", "client", "lead", "contact", "relationship",
            "ग्राहक", "क्लाइंट", "लीड", "grahak", "client", "customer", "lead",
        ],
        "inventory": [
            "inventory", "stock", "warehouse", "product", "item", "supply",
            "इन्वेंटरी", "स्टॉक", "गोदाम", "inventory", "stock", "warehouse",
        ],
        "blog": [
            "blog", "article", "post", "writer", "content", "news",
            "ब्लॉग", "लेख", "समाचार", "blog", "article", "post",
        ],
    }

    # ============================
    # Project name extraction patterns
    # ============================
    PROJECT_NAME_PATTERNS = [
        # English: "build a hospital management system" -> "hospital management system"
        r"(?:build|create|make|generate|develop|code|write)\s+(?:a\s+)?(.+?)(?:\s+app|\s+system|\s+platform|\s+project|\s+software|\s+website|\s+api|\s+service)?$",
        # Hindi: "hospital management system बनाओ" -> "hospital management system"
        r"(.+?)\s+(?:बनाओ|बनाओ|लिखो|कोड\s*करो|प्रोजेक्ट\s*बनाओ|ऐप\s*बनाओ|सॉफ्टवेयर\s*बनाओ)\s*$",
        # Hinglish: "hospital management system banao" -> "hospital management system"
        r"(.+?)\s+(?:banao|banado|likho|code\s*karo|project\s*banao|app\s*banao|software\s*banao)\s*$",
        # General: extract meaningful phrase
        r"(?:for\s+|of\s+|to\s+)?(.+?)(?:\s+system|\s+app|\s+platform|\s+project)?$",
    ]

    # ============================
    # Filler words to remove
    # ============================
    FILLERS = [
        # English
        "please", "can you", "could you", "would you", "kindly", "for me",
        "i want to", "i want like to", "i need", "i need to", "i would like",
        "kindly", "plz", "pls",
        # Hindi
        "कृपया", "क्या", "तुम", "आप", "मैं", "को", "के", "का", "की", "से",
        "में", "पर", "है", "हैं", "था", "थी", "थे", "होगा", "होगी", "होंगे",
        # Hinglish
        "kya", "tum", "aap", "main", "ko", "ke", "ka", "ki", "se", "mein", "par",
        "hai", "hain", "tha", "thi", "the", "hoga", "hogi", "honge",
    ]

    def __init__(self):
        self._compile_patterns()

    def _compile_patterns(self):
        """Pre-compile regex patterns for performance."""
        self._create_regex = [re.compile(p, re.IGNORECASE) for p in self.CREATE_CODE_PATTERNS]
        self._status_regex = [re.compile(p, re.IGNORECASE) for p in self.STATUS_PATTERNS]
        self._history_regex = [re.compile(p, re.IGNORECASE) for p in self.HISTORY_PATTERNS]
        self._help_regex = [re.compile(p, re.IGNORECASE) for p in self.HELP_PATTERNS]
        self._exit_regex = [re.compile(p, re.IGNORECASE) for p in self.EXIT_PATTERNS]
        self._shutdown_regex = [re.compile(p, re.IGNORECASE) for p in self.SHUTDOWN_PATTERNS]
        self._restart_regex = [re.compile(p, re.IGNORECASE) for p in self.RESTART_PATTERNS]
        self._sleep_regex = [re.compile(p, re.IGNORECASE) for p in self.SLEEP_PATTERNS]
        self._lock_regex = [re.compile(p, re.IGNORECASE) for p in self.LOCK_PATTERNS]
        self._cancel_shutdown_regex = [re.compile(p, re.IGNORECASE) for p in self.CANCEL_SHUTDOWN_PATTERNS]
        self._play_music_regex = [re.compile(p, re.IGNORECASE) for p in self.PLAY_MUSIC_PATTERNS]
        self._spotify_song_regex = [re.compile(p, re.IGNORECASE) for p in self.SPOTIFY_SONG_PATTERNS]
        self._news_regex = [re.compile(p, re.IGNORECASE) for p in self.NEWS_PATTERNS]
        self._google_search_regex = [re.compile(p, re.IGNORECASE) for p in self.GOOGLE_SEARCH_PATTERNS]
        self._open_app_regex = [re.compile(p, re.IGNORECASE) for p in self.OPEN_APP_PATTERNS]
        self._open_website_regex = [re.compile(p, re.IGNORECASE) for p in self.OPEN_WEBSITE_PATTERNS]
        self._close_app_regex = [re.compile(p, re.IGNORECASE) for p in self.CLOSE_APP_PATTERNS]
        self._project_name_regex = [re.compile(p, re.IGNORECASE) for p in self.PROJECT_NAME_PATTERNS]

    def parse(self, text: str) -> ParsedIntent:
        """Parse user input and extract intent + entities."""
        original = text.strip()
        if not original:
            return ParsedIntent(intent="CHAT", original_text=original)

        cleaned = self._clean_text(original)
        intent, confidence = self._detect_intent(cleaned)
        project_name = self._extract_project_name(original, cleaned)
        domain = self._detect_domain(cleaned)
        keywords = self._extract_keywords(cleaned)
        language = self.detect_language(original)

        # Extract app/website/song/news/search names
        app_name = ""
        website_name = ""
        song_name = ""
        news_query = ""
        search_query = ""
        
        if intent in ("OPEN_APPLICATION", "OPEN_WEBSITE"):
            target = self._extract_open_target(original)
            if intent == "OPEN_WEBSITE":
                website_name = target
            else:
                app_name = target
        elif intent == "CLOSE_APPLICATION":
            app_name = self._extract_app_name(original, cleaned)
        elif intent == "PLAY_SPOTIFY_SONG":
            song_name = self._extract_song_name(original, cleaned)
        elif intent == "GET_NEWS":
            news_query = self._extract_news_query(original, cleaned)
        elif intent == "GOOGLE_SEARCH":
            search_query = self._extract_search_query(original, cleaned)

        return ParsedIntent(
            intent=intent,
            confidence=confidence,
            original_text=original,
            cleaned_text=cleaned,
            project_name=project_name,
            domain=domain,
            keywords=keywords,
            app_name=app_name,
            website_name=website_name,
            song_name=song_name,
            news_query=news_query,
            search_query=search_query,
            raw_entities={
                "language": language,
                "app_name": app_name,
                "website_name": website_name,
                "song_name": song_name,
                "news_query": news_query,
                "search_query": search_query,
            },
        )

    def _clean_text(self, text: str) -> str:
        """Remove fillers and normalize text."""
        cleaned = text.lower().strip()
        # Remove fillers
        for filler in self.FILLERS:
            cleaned = re.sub(rf"\b{re.escape(filler)}\b", " ", cleaned, flags=re.IGNORECASE)
        # Remove extra whitespace
        cleaned = " ".join(cleaned.split())
        # Remove punctuation but keep meaningful chars
        cleaned = re.sub(r"[^\w\s\u0900-\u097F]", " ", cleaned)
        cleaned = " ".join(cleaned.split())
        return cleaned.strip()

    def _detect_intent(self, text: str) -> Tuple[str, float]:
        """Detect user intent from cleaned text."""
        # Check patterns in priority order
        
        # Exit patterns
        for pattern in self._exit_regex:
            if pattern.search(text):
                return "EXIT", 0.95

        # Cancel shutdown
        for pattern in self._cancel_shutdown_regex:
            if pattern.search(text):
                return "CANCEL_SHUTDOWN", 0.95

        # Power controls (check before open/close to avoid conflict)
        for pattern in self._shutdown_regex:
            if pattern.search(text):
                return "SHUTDOWN", 0.95

        for pattern in self._restart_regex:
            if pattern.search(text):
                return "RESTART", 0.95

        for pattern in self._sleep_regex:
            if pattern.search(text):
                return "SLEEP", 0.92

        for pattern in self._lock_regex:
            if pattern.search(text):
                return "LOCK", 0.92

        # News
        for pattern in self._news_regex:
            if pattern.search(text):
                return "GET_NEWS", 0.92

        # Google search
        for pattern in self._google_search_regex:
            match = pattern.search(text)
            if match:
                return "GOOGLE_SEARCH", 0.92

        # Spotify song (check before general play music)
        for pattern in self._spotify_song_regex:
            match = pattern.search(text)
            if match:
                return "PLAY_SPOTIFY_SONG", 0.93

        # Play music
        for pattern in self._play_music_regex:
            if pattern.search(text):
                return "PLAY_MUSIC", 0.9

        # Close app patterns (check before open to avoid conflict)
        for pattern in self._close_app_regex:
            match = pattern.search(text)
            if match:
                return "CLOSE_APPLICATION", 0.9

        # For open commands, extract target and disambiguate
        open_target = self._extract_open_target(text)
        if open_target:
            target_lower = open_target.lower()
            if target_lower in self.KNOWN_WEBSITES:
                return "OPEN_WEBSITE", 0.92
            return "OPEN_APPLICATION", 0.92

        # Create code patterns
        for pattern in self._create_regex:
            if pattern.search(text):
                return "CREATE_CODE", 0.9

        # Status patterns
        for pattern in self._status_regex:
            if pattern.search(text):
                return "STATUS", 0.85

        # History patterns
        for pattern in self._history_regex:
            if pattern.search(text):
                return "HISTORY", 0.8

        # Help patterns
        for pattern in self._help_regex:
            if pattern.search(text):
                return "HELP", 0.8

        return "CHAT", 0.5

    def _extract_open_target(self, text: str) -> str:
        """Extract target name from open/launch/visit commands."""
        # Verbs that indicate this is a command, not the target
        command_verbs = {
            "open", "visit", "go", "browse", "launch", "start", "run", "close", "stop",
            "band", "kholo", "dekho", "karo", "kar", "do", "shuru", "chalu", "terminate",
            "खोलो", "शुरू", "चालू", "बंद", "रन", "रोको", "करो",
        }

        def pick_target(group1: str, group2: str) -> str:
            """Pick the target from two regex groups."""
            g1 = group1.strip() if group1 else ""
            g2 = group2.strip() if group2 else ""
            # If group1 is a command verb, target is group2
            if g1.lower() in command_verbs:
                return g2
            # If group2 is a command verb phrase, target is group1
            if any(g2.lower().startswith(v) for v in command_verbs):
                return g1
            # Default: prefer longer non-verb group
            if len(g1) > len(g2) and g1.lower() not in command_verbs:
                return g1
            if len(g2) > len(g1) and g2.lower() not in command_verbs:
                return g2
            return g1 or g2

        # Check open website patterns first
        for pattern in self._open_website_regex:
            match = pattern.search(text)
            if match:
                target = pick_target(match.group(1), match.group(2))
                if target and len(target) > 1:
                    return self._normalize_app_name(target)

        # Check open app patterns
        for pattern in self._open_app_regex:
            match = pattern.search(text)
            if match:
                target = pick_target(match.group(1), match.group(2))
                if target and len(target) > 1:
                    return self._normalize_app_name(target)

        return ""

    def _extract_app_name(self, original: str, cleaned: str) -> str:
        """Extract application name from input text."""
        text = original.lower().strip()
        
        # Check close app patterns - both normal (close X) and reversed (X band karo)
        for pattern in self._close_app_regex:
            match = pattern.search(text)
            if match:
                app = self._pick_target_from_match(match)
                if app and app.lower() not in {"karo", "kar", "do", "band", "close", "stop", "terminate"}:
                    return self._normalize_app_name(app)

        # Check open app patterns - both normal (open X) and reversed (X kholo)
        for pattern in self._open_app_regex:
            match = pattern.search(text)
            if match:
                app = self._pick_target_from_match(match)
                if app and app.lower() not in {"karo", "kar", "do", "kholo", "open", "launch", "start", "run"}:
                    return self._normalize_app_name(app)

        return ""

    def _extract_website_name(self, original: str, cleaned: str) -> str:
        """Extract website name from input text."""
        text = original.lower().strip()
        
        for pattern in self._open_website_regex:
            match = pattern.search(text)
            if match:
                site = self._pick_target_from_match(match)
                if site:
                    return self._normalize_website_name(site)

        return ""

    def _pick_target_from_match(self, match) -> str:
        """Pick the target name from regex match groups, filtering out verbs."""
        command_verbs = {
            "open", "visit", "go", "browse", "launch", "start", "run", "close", "stop",
            "band", "kholo", "dekho", "karo", "kar", "do", "shuru", "chalu", "terminate",
            "खोलो", "शुरू", "चालू", "बंद", "रन", "रोको", "करो",
        }
        g1 = (match.group(1) or "").strip()
        g2 = (match.group(2) or "").strip()
        
        # If group1 is a command verb, target is group2
        if g1.lower() in command_verbs:
            return g2
        # If group2 starts with a command verb, target is group1
        if any(g2.lower().startswith(v) for v in command_verbs):
            return g1
        # Default: prefer longer non-verb group
        if len(g1) > len(g2) and g1.lower() not in command_verbs:
            return g1
        if len(g2) > len(g1) and g2.lower() not in command_verbs:
            return g2
        return g1 or g2

    def _normalize_app_name(self, name: str) -> str:
        """Normalize extracted app name."""
        # Remove common filler words
        name = re.sub(r"\b(app|application|software|karo|kar|do|please|plz)\b", "", name, flags=re.IGNORECASE).strip()
        # Remove articles
        name = re.sub(r"^(a|an|the|ek)\s+", "", name, flags=re.IGNORECASE).strip()
        return name[:50]

    def _normalize_website_name(self, name: str) -> str:
        """Normalize extracted website name."""
        # Remove common filler words
        name = re.sub(r"\b(website|site|page|karo|kar|do|please|plz)\b", "", name, flags=re.IGNORECASE).strip()
        # Remove articles
        name = re.sub(r"^(a|an|the|ek)\s+", "", name, flags=re.IGNORECASE).strip()
        return name[:50]

    def _extract_song_name(self, original: str, cleaned: str) -> str:
        """Extract song name from Spotify play command."""
        text = original.lower().strip()
        
        # Check spotify song patterns
        for pattern in self._spotify_song_regex:
            match = pattern.search(text)
            if match:
                # Song is in group 1 for all current patterns
                song = match.group(1) or ""
                song = song.strip()
                if song and song.lower() not in {"play", "karo", "chalao", "bajao", "music", "spotify"}:
                    return self._normalize_song_name(song)

        return ""

    def _extract_news_query(self, original: str, cleaned: str) -> str:
        """Extract news category/query."""
        text = cleaned.lower().strip()
        
        # Remove "news" keyword to get category
        for keyword in ["news", "latest", "today", "breaking", "current", "headlines", "khabar", "samachar", "khabarein", "taja"]:
            text = text.replace(keyword, "").strip()
        
        return text[:50] if text else "latest"

    def _extract_search_query(self, original: str, cleaned: str) -> str:
        """Extract search query for Google."""
        text = original.lower().strip()
        
        # Remove Google/search keywords with word boundaries
        for keyword in ["google", "search", "on", "pe", "par", "karo", "kare", "please"]:
            text = re.sub(rf"\b{re.escape(keyword)}\b", "", text, flags=re.IGNORECASE)
        
        text = " ".join(text.split())
        return text[:100] if text else ""

    def _normalize_song_name(self, name: str) -> str:
        """Normalize extracted song name."""
        # Remove common filler words
        name = re.sub(r"\b(play|karo|kar|do|please|plz|on|spotify|song|music)\b", "", name, flags=re.IGNORECASE).strip()
        # Remove articles
        name = re.sub(r"^(a|an|the|ek|yeh|is)\s+", "", name, flags=re.IGNORECASE).strip()
        return name[:80]

    def _extract_project_name(self, original: str, cleaned: str) -> str:
        """Extract project name from input text."""
        # Try patterns on original text first
        for pattern in self._project_name_regex:
            match = pattern.search(original.strip())
            if match:
                candidate = match.group(1).strip()
                if candidate and len(candidate) > 2:
                    return self._normalize_project_name(candidate)

        # Fallback: use cleaned text
        if cleaned and len(cleaned) > 2:
            return self._normalize_project_name(cleaned)

        return ""

    def _normalize_project_name(self, name: str) -> str:
        """Normalize extracted project name."""
        # Remove leading/trailing articles and fillers
        name = re.sub(r"^(a|an|the|ek|ek\s+saty|is\s+ka|yeh)\s+", "", name, flags=re.IGNORECASE).strip()
        # Remove trailing verbs
        name = re.sub(r"\s+(banao|banado|likho|karo|kar\s*do|karwana|hai|hain|tha|thi|the)$", "", name, flags=re.IGNORECASE).strip()
        # Capitalize words
        name = " ".join(word.capitalize() for word in name.split())
        return name[:80]

    def _detect_domain(self, text: str) -> str:
        """Detect project domain from text."""
        text_lower = text.lower()
        for domain, keywords in self.DOMAIN_PATTERNS.items():
            if any(kw.lower() in text_lower for kw in keywords):
                return domain
        return "general"

    def _extract_keywords(self, text: str) -> List[str]:
        """Extract meaningful keywords from text."""
        # Remove common words
        stopwords = {
            "the", "a", "an", "is", "are", "was", "were", "be", "been", "being",
            "have", "has", "had", "do", "does", "did", "will", "would", "could",
            "should", "may", "might", "must", "shall", "can", "need", "dare",
            "ought", "used", "to", "of", "in", "for", "on", "with", "at", "by",
            "from", "as", "into", "through", "during", "before", "after",
            "above", "below", "between", "out", "off", "over", "under", "again",
            "further", "then", "once", "here", "there", "when", "where", "why",
            "how", "all", "each", "every", "both", "few", "more", "most", "other",
            "some", "such", "no", "nor", "not", "only", "own", "same", "so",
            "than", "too", "very", "just", "because", "but", "and", "or", "if",
            "while", "about", "against", "up", "down", "also", "that", "this",
            "these", "those", "i", "me", "my", "we", "our", "you", "your",
            "he", "she", "it", "they", "them", "his", "her", "its", "their",
            "what", "which", "who", "whom", "whose", "ka", "ki", "ke", "ko",
            "se", "mein", "par", "hai", "hain", "tha", "thi", "the", "ho",
            "banao", "banado", "likho", "karo", "please", "kindly", "for",
        }
        words = text.split()
        keywords = [w for w in words if w not in stopwords and len(w) > 2]
        return keywords[:10]

    def detect_language(self, text: str) -> str:
        """Detect whether input is English, Hindi, or Hinglish.

        Returns:
            One of: "english", "hindi", "hinglish"
        """
        if not text or not text.strip():
            return "english"

        # Check for Devanagari script
        devanagari_chars = len(re.findall(r"[\u0900-\u097F]", text))
        total_chars = len(text.strip())

        # Count Hindi words (both Devanagari and Romanized)
        hindi_devanagari_words = [
            "बनाओ", "बनाओ", "लिखो", "कोड", "प्रोजेक्ट", "ऐप", "सॉफ्टवेयर",
            "क्या", "हुआ", "होगा", "मैं", "हूं", "है", "हैं", "था", "थी", "थे",
            "मदद", "अलविदा", "चुप", "बहुत", "अच्छा", "नमस्ते",
        ]
        hindi_romanized_words = [
            "banao", "banado", "likho", "karo", "hai", "hain", "tha", "thi",
            "hoga", "hogi", "ka", "ki", "ke", "ko", "se", "mein", "par",
            "aap", "tum", "main", "kya", "nahi", "haan", "thik", "sahi",
            "madad", "alvida", "chup", "bahut", "accha", "bura", "zara",
        ]

        text_lower = text.lower()
        devanagari_word_count = sum(1 for word in hindi_devanagari_words if word in text)
        romanized_word_count = sum(1 for word in hindi_romanized_words if word in text_lower)
        total_hindi_words = devanagari_word_count + romanized_word_count

        # If significant Devanagari content
        if devanagari_chars > total_chars * 0.15 or devanagari_word_count >= 2:
            return "hindi"

        # If mixed Hindi words in English text = Hinglish
        if total_hindi_words >= 1:
            return "hinglish"

        return "english"


class HinglishResponseGenerator:
    """Generate natural responses in Hindi/English/Hinglish."""

    TEMPLATES = {
        "english": {
            "welcome": [
                "Hello! I'm Jarvis-X, your autonomous software engineer.\nType 'help' to see what I can do.",
                "Hey! I'm Jarvis-X. I can help you write code, build projects, and debug.\nType 'help' for commands.",
            ],
            "thinking": [
                "Thinking...",
                "Let me think...",
                "One moment...",
            ],
            "engineering_started": [
                "🚀 Starting engineering pipeline for: {project_name}",
                "🚀 Engineering pipeline started for: {project_name}",
            ],
            "engineering_completed": [
                "🎉 Done! Project is ready. Generated {files} files with {quality:.0f}% quality.",
                "🎉 Success! Project generated with {files} files and {quality:.0f}% quality score.",
            ],
            "engineering_failed": [
                "❌ Pipeline failed. Please provide more details about the project.",
                "❌ Engineering failed. Can you give more details about the project?",
            ],
            "error": [
                "❌ Error: {error}\nPlease try again or type 'help'.",
                "❌ Error: {error}\nTry again or type 'help'.",
            ],
            "goodbye": [
                "👋 Goodbye! See you soon.",
                "👋 Bye! Have a great day.",
            ],
            "help": [
                """
╔═══════════════════════════════════════════════════════════════╗
║              🤖 JARVIS-X COMMANDS                            ║
╠═══════════════════════════════════════════════════════════════╣
║                                                               ║
║  🚀 Engineering Commands:                                     ║
║     • build hospital management system                        ║
║     • create ecommerce platform                               ║
║     • generate REST API for inventory                         ║
║                                                               ║
║  📊 Status Commands:                                          ║
║     • status / progress / report                              ║
║                                                               ║
║  📜 History Commands:                                         ║
║     • history / previous projects                             ║
║                                                               ║
║  💬 General Chat:                                             ║
║     • Any question in English, Hindi, or Hinglish            ║
║                                                               ║
║  ❌ Exit:                                                     ║
║     • exit / quit / bye                                       ║
║                                                               ║
╚═══════════════════════════════════════════════════════════════╝
""",
            ],
        },
        "hindi": {
            "welcome": [
                "नमस्ते! मैं जार्विस-X हूं। आपका स्वयंचलित सॉफ्टवेयर इंजीनियर।\nType 'help' देखें के मैं क्या कर सकता हूं।",
                "नमस्ते! मैं जार्विस-X हूं। आपके लिए कोड लिखना, प्रोजेक्ट बनाना, और डीबग करने में मदद करता हूं।",
            ],
            "thinking": [
                "सोच रहा हूं...",
                "एक मिनट...",
            ],
            "engineering_started": [
                "🚀 इंजीनियरिंग पाइपलाइन शुरू हो गई! प्रोजेक्ट: {project_name}",
                "🚀 इंजीनियरिंग शुरू: {project_name}",
            ],
            "engineering_completed": [
                "🎉 हो गया! प्रोजेक्ट तैयार है। {files} फाइल्स बनाईं, क्वालिटी {quality:.0f}%।",
                "🎉 सफलता! प्रोजेक्ट बना: {files} फाइल्स, {quality:.0f}% क्वालिटी।",
            ],
            "engineering_failed": [
                "❌ पाइपलाइन फेल हो गई। प्रोजेक्ट के बारे में थोड़ा और बताओ।",
                "❌ इंजीनियरिंग फेल। कृपया प्रोजेक्ट के बारे में अधिक विवरण दें।",
            ],
            "error": [
                "❌ त्रुटि: {error}\nदोबारा प्रयास करो या 'help' टाइप करो।",
                "❌ एरर: {error}\nफिर से ट्राई करो या 'help' लिखो।",
            ],
            "goodbye": [
                "👋 अलविदा! फिर मिलते हैं।",
                "👋 बाय! अच्छा दिन रहे।",
            ],
            "help": [
                """
╔═══════════════════════════════════════════════════════════════╗
║          🤖 जार्विस-X - स्वयंचलित सॉफ्टवेयर इंजीनियर         ║
╠═══════════════════════════════════════════════════════════════╣
║                                                               ║
║  🚀 इंजीनियरिंग कमांड:                                        ║
║     • build hospital management system                        ║
║     • banao hospital management system                        ║
║     • create ecommerce platform                               ║
║     • banado CRM app                                          ║
║     • generate REST API for inventory                         ║
║                                                               ║
║  📊 स्टेटस कमांड:                                              ║
║     • status / kya hua / progress                             ║
║                                                               ║
║  📜 हिस्ट्री कमांड:                                            ║
║     • history / pehle ka project / pichle projects            ║
║                                                               ║
║  💬 जनरल चैट:                                                 ║
║     • English, Hindi, ya Hinglish में कोई भी सवाल           ║
║                                                               ║
║  ❌ एक्सिट:                                                   ║
║     • exit / quit / bye / alvida / chup                       ║
║                                                               ║
╚═══════════════════════════════════════════════════════════════╝
""",
            ],
        },
        "hinglish": {
            "welcome": [
                "Namaste! Main Jarvis-X hoon. Aapka autonomous software engineer.\nType 'help' dekhein ke main kya kar sakta hoon.",
                "Hey! Main Jarvis-X hoon. Aapke liye code likhne, project banana, aur debugging karne mein madad karta hoon.",
            ],
            "thinking": [
                "Soch raha hoon...",
                "Let me think...",
                "Ek minute...",
            ],
            "engineering_started": [
                "🚀 Engineering pipeline shuru ho gaya! Project: {project_name}",
                "🚀 Starting engineering for: {project_name}",
            ],
            "engineering_completed": [
                "🎉 Ho gaya! Project ready hai. {files} files banaye, quality {quality:.0f}%.",
                "🎉 Done! {files} files generated, {quality:.0f}% quality.",
            ],
            "engineering_failed": [
                "❌ Pipeline failed. Thoda aur detail mein batao project ke baare mein.",
                "❌ Engineering failed. Project ke baare mein thoda aur batao.",
            ],
            "error": [
                "❌ Error: {error}\nDobara try karo ya 'help' type karo.",
                "❌ Error: {error}\nPhir try karo ya 'help' likho.",
            ],
            "goodbye": [
                "👋 Alvida! Phir milte hain.",
                "👋 Bye! Phir milte hain.",
            ],
            "help": [
                """
╔═══════════════════════════════════════════════════════════════╗
║          🤖 JARVIS-X - Autonomous Software Engineer          ║
╠═══════════════════════════════════════════════════════════════╣
║                                                               ║
║  🚀 Engineering Commands:                                     ║
║     • build hospital management system                        ║
║     • banao hospital management system                        ║
║     • create ecommerce platform                               ║
║     • banado CRM app                                          ║
║     • generate REST API for inventory                         ║
║                                                               ║
║  📊 Status Commands:                                          ║
║     • status / kya hua / progress                             ║
║                                                               ║
║  📜 History Commands:                                         ║
║     • history / pehle ka project / pichle projects            ║
║                                                               ║
║  💬 General Chat:                                             ║
║     • English, Hindi, ya Hinglish mein kuch bhi poocho      ║
║                                                               ║
║  ❌ Exit:                                                     ║
║     • exit / quit / bye / alvida / chup                       ║
║                                                               ║
╚═══════════════════════════════════════════════════════════════╝
""",
            ],
        },
    }

    def generate(self, template_key: str, language: str = "english", **kwargs) -> str:
        """Generate a response from a template in the specified language."""
        import random

        lang_templates = self.TEMPLATES.get(language, self.TEMPLATES["english"])
        templates = lang_templates.get(template_key, [""])
        template = random.choice(templates)
        try:
            return template.format(**kwargs)
        except (KeyError, ValueError):
            return template

    def help_message(self, language: str = "english") -> str:
        """Generate help message in the specified language."""
        return self.generate("help", language=language)
