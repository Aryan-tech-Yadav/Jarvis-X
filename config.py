import os


MODEL = os.getenv("JARVIS_MODEL", "llama3.2:3b")
MAX_RETRY = int(os.getenv("JARVIS_MAX_RETRY", "3"))
TIMEOUT = int(os.getenv("JARVIS_TIMEOUT", "30"))
WORKSPACE = os.getenv("JARVIS_WORKSPACE", "workspace")
KNOWLEDGE_PATH = os.getenv("JARVIS_KNOWLEDGE_PATH", os.path.join("data", "knowledge.json"))
EXPERIENCES_PATH = os.getenv("JARVIS_EXPERIENCES_PATH", os.path.join("data", "experiences.json"))
LESSONS_PATH = os.getenv("JARVIS_LESSONS_PATH", os.path.join("data", "lessons.json"))
SEMANTIC_MEMORY_PATH = os.getenv("JARVIS_SEMANTIC_MEMORY_PATH", os.path.join("data", "semantic_memory.json"))

MODEL_PLANNER = os.getenv("JARVIS_MODEL_PLANNER", "llama3.2:3b")
MODEL_CODER = os.getenv("JARVIS_MODEL_CODER", "llama3.2:3b")
MODEL_REVIEWER = os.getenv("JARVIS_MODEL_REVIEWER", "llama3.2:3b")
MODEL_FAST = os.getenv("JARVIS_MODEL_FAST", "llama3.2:1b")

QUALITY_GATE_SCORE = float(os.getenv("JARVIS_QUALITY_GATE", "95.0"))
MAX_REFINEMENT_CYCLES = int(os.getenv("JARVIS_MAX_REFINEMENT", "5"))
