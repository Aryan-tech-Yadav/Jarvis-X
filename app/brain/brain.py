"""Brain module - Central cognition and orchestration.

Layer 2 of the 5-layer AI Agent architecture.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

from app.core.logger import Logger


@dataclass
class BrainContext:
    """Context maintained by the Brain during processing."""
    user_input: str = ""
    language: str = "english"
    intent: str = "UNKNOWN"
    confidence: float = 0.0
    plan: List[str] = field(default_factory=list)
    entities: Dict[str, Any] = field(default_factory=dict)
    relevant_memories: List[Dict] = field(default_factory=list)
    selected_tools: List[str] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)


class Brain:
    """Central cognition module.

    Responsibilities:
      - Understand user intent
      - Plan execution steps
      - Select relevant tools
      - Retrieve relevant memories
      - Produce final response

    This is a clean abstraction separate from routing and execution.
    """

    def __init__(
        self,
        input_layer=None,
        planner=None,
        memory=None,
        tool_selector=None,
        llm_router=None,
        context_manager=None,
        event_bus=None,
    ):
        self.input_layer = input_layer
        self.planner = planner
        self.memory = memory
        self.tool_selector = tool_selector
        self.llm_router = llm_router
        self.context_manager = context_manager
        self.event_bus = event_bus
        self.context = BrainContext()
        self._intent_classifier = None
        self._entity_extractor = None
        self.brain_kernel = None

    def initialize(self):
        """Initialize sub-modules if not provided."""
        if self.input_layer is None:
            from app.input.input_layer import InputLayer
            self.input_layer = InputLayer()

        if self.planner is None:
            from app.planner.planner import Planner
            self.planner = Planner()

        if self.memory is None:
            from app.memory.memory_manager import MemoryManager
            self.memory = MemoryManager()

        if self.tool_selector is None:
            from app.tools.tool_selector import ToolSelector
            self.tool_selector = ToolSelector()

        if self.context_manager is None:
            from app.core.context_manager import ContextManager
            self.context_manager = ContextManager()

        # Initialize BrainKernel (Engineering Intelligence Kernel)
        try:
            from app.brain.brain_kernel import BrainKernel
            self.brain_kernel = BrainKernel(
                event_bus=self.event_bus,
                ai_router=self.llm_router,
                runtime_context=self.context_manager,
            )
            Logger.success("[Brain] BrainKernel (EIK) initialized")
        except Exception as exc:
            Logger.warning(f"[Brain] BrainKernel init failed: {exc}")
            self.brain_kernel = None

        try:
            from app.core.intent_router import IntentRouter
            self._intent_classifier = IntentRouter()
        except Exception:
            pass

        try:
            from app.core.entity_extractor import EntityExtractor
            self._entity_extractor = EntityExtractor()
        except Exception:
            pass

    def process(self, raw_input: Any, input_type: str = "text") -> Dict[str, Any]:
        """Main processing pipeline: Input -> Think -> Decide -> Plan -> Select Tools -> Respond.

        Returns dict with:
          - response: final text response
          - plan: execution steps
          - intent: detected intent
          - tools: selected tools
          - context: full brain context
          - thinking: thinking engine results
          - decision: decision engine results
          - strategy: selected strategy
        """
        # Layer 1: Input Processing
        from app.input.input_layer import InputLayer, InputType
        payload = self.input_layer.process(raw_input, InputType(input_type))
        self.context.user_input = payload.text
        self.context.language = payload.language

        Logger.info(f"[Brain] Input: {payload.text[:100]}...")

        # Use BrainKernel for intelligent processing if available
        thinking_result = None
        decision_result = None
        strategy_result = None

        if self.brain_kernel:
            try:
                kernel_result = self.brain_kernel.process(payload.text, {
                    "session_id": getattr(self.context, 'session_id', ''),
                    "available_tools": [],
                })
                thinking_result = kernel_result.get("thinking")
                decision_result = kernel_result.get("decision")
                strategy_result = kernel_result.get("strategy")
                Logger.info(f"[Brain] BrainKernel processed: mode={thinking_result.get('mode') if thinking_result else 'N/A'}, "
                           f"confidence={thinking_result.get('confidence', 0):.0f}%" if thinking_result else "")
            except Exception as exc:
                Logger.warning(f"[Brain] BrainKernel processing failed: {exc}")

        # Understand: Intent Detection
        intent_result = self._detect_intent(payload.text)
        self.context.intent = intent_result.get("intent", "UNKNOWN")
        self.context.confidence = intent_result.get("confidence", 0.0)

        # Understand: Entity Extraction
        entities = self._extract_entities(payload.text)
        self.context.entities = entities

        # Retrieve relevant memories
        relevant_memories = self._retrieve_memories(payload.text)
        self.context.relevant_memories = relevant_memories

        # Layer 3: Planning
        plan = self._create_plan(payload.text, self.context.intent)
        self.context.plan = plan

        # Layer 5: Tool Selection
        selected_tools = self._select_tools(self.context.intent, payload.text, plan)
        self.context.selected_tools = selected_tools

        # Execute or respond
        response = self._execute_or_respond(payload.text, self.context)

        result = {
            "response": response,
            "intent": self.context.intent,
            "confidence": self.context.confidence,
            "plan": self.context.plan,
            "tools": self.context.selected_tools,
            "entities": self.context.entities,
            "memories": len(self.context.relevant_memories),
            "context": self.context,
        }

        # Add BrainKernel results if available
        if thinking_result:
            result["thinking"] = thinking_result
        if decision_result:
            result["decision"] = decision_result
        if strategy_result:
            result["strategy"] = strategy_result

        return result

    def _detect_intent(self, text: str) -> Dict[str, Any]:
        """Detect user intent."""
        if self._intent_classifier:
            try:
                result = self._intent_classifier.detect_intent(text)
                if result.get("intent") != "UNKNOWN":
                    return result
            except Exception:
                pass

        # Fallback: simple keyword matching
        text_lower = text.lower()
        if any(w in text_lower for w in ["exit", "quit", "bye", "alvida"]):
            return {"intent": "EXIT", "confidence": 0.9, "source": "fallback"}
        if any(w in text_lower for w in ["help", "madad", "kya kar sakte"]):
            return {"intent": "HELP", "confidence": 0.9, "source": "fallback"}
        if any(w in text_lower for w in ["build", "create", "banao", "bana", "generate"]):
            return {"intent": "CREATE_CODE", "confidence": 0.85, "source": "fallback"}
        if any(w in text_lower for w in ["open", "kholo", "launch"]):
            return {"intent": "OPEN_APPLICATION", "confidence": 0.8, "source": "fallback"}
        if any(w in text_lower for w in ["search", "google", "dhundo", "khojo"]):
            return {"intent": "GOOGLE_SEARCH", "confidence": 0.85, "source": "fallback"}
        if any(w in text_lower for w in ["play", "bajao", "gaana"]):
            return {"intent": "PLAY_MUSIC", "confidence": 0.8, "source": "fallback"}
        if any(w in text_lower for w in ["news", "khabar", "headlines"]):
            return {"intent": "GET_NEWS", "confidence": 0.9, "source": "fallback"}

        return {"intent": "CHAT", "confidence": 0.5, "source": "fallback"}

    def _extract_entities(self, text: str) -> Dict[str, Any]:
        """Extract entities from text."""
        if self._entity_extractor:
            try:
                return self._entity_extractor.extract(text)
            except Exception:
                pass
        return {}

    def _retrieve_memories(self, text: str) -> List[Dict]:
        """Retrieve relevant memories for current input."""
        if self.memory:
            try:
                return self.memory.search_memory(text, limit=5)
            except Exception:
                pass
        return []

    def _create_plan(self, text: str, intent: str) -> List[str]:
        """Create execution plan based on intent and input."""
        if self.planner:
            try:
                return self.planner.plan(text, intent, self.context.entities)
            except Exception:
                pass
        return [text]

    def _select_tools(self, intent: str, text: str, plan: List[str]) -> List[str]:
        """Select tools needed for this request."""
        if self.tool_selector:
            try:
                return self.tool_selector.select(intent, text, plan)
            except Exception:
                pass
        return self._default_tool_selection(intent)

    def _default_tool_selection(self, intent: str) -> List[str]:
        """Default tool selection based on intent."""
        tool_map = {
            "OPEN_APPLICATION": ["automation"],
            "OPEN_WEBSITE": ["automation", "browser"],
            "GOOGLE_SEARCH": ["internet"],
            "GET_NEWS": ["internet"],
            "PLAY_MUSIC": ["automation", "media"],
            "CREATE_CODE": ["file", "python", "terminal"],
            "EXIT": [],
            "HELP": [],
            "CHAT": ["ai"],
            "WEATHER": ["internet"],
            "WIKIPEDIA": ["internet"],
        }
        return tool_map.get(intent, ["ai"])

    def _execute_or_respond(self, text: str, context: BrainContext) -> str:
        """Execute planned steps or generate LLM response."""
        if context.intent in ("CHAT", "GREETINGS", "HELP", "UNKNOWN"):
            return self._generate_llm_response(text, context)
        if context.intent == "EXIT":
            return "Shutting down..."
        return self._generate_fallback_response(context)

    def _generate_llm_response(self, text: str, context: BrainContext) -> str:
        """Generate response using LLM with memory context."""
        if self.llm_router:
            try:
                prompt = self._build_prompt_with_memory(text, context)
                return self.llm_router.ask(prompt, task_type="chat")
            except Exception:
                pass
        return "I'm here to help. What would you like to do?"

    def _generate_fallback_response(self, context: BrainContext) -> str:
        """Generate a response for non-chat intents when execution is not wired."""
        responses = {
            "OPEN_APPLICATION": f"Opening application for: {context.user_input}",
            "CLOSE_APPLICATION": f"Closing application for: {context.user_input}",
            "OPEN_WEBSITE": f"Opening website for: {context.user_input}",
            "GOOGLE_SEARCH": f"Searching Google for: {context.user_input}",
            "GET_NEWS": f"Fetching news for: {context.user_input}",
            "PLAY_MUSIC": f"Playing music for: {context.user_input}",
            "WEATHER": f"Checking weather for: {context.user_input}",
            "WIKIPEDIA": f"Looking up Wikipedia for: {context.user_input}",
            "CREATE_CODE": f"Starting engineering workflow for: {context.user_input}",
            "SAVE_MEMORY": "Remembering that for you.",
            "GET_MEMORY": "Let me check my memory.",
            "GET_TIME": "Checking current time.",
            "SHUTDOWN": "Initiating shutdown.",
            "RESTART": "Initiating restart.",
            "SLEEP": "Putting system to sleep.",
            "LOCK": "Locking system.",
        }
        return responses.get(context.intent, f"Processing: {context.user_input}")

    def _build_prompt_with_memory(self, text: str, context: BrainContext) -> str:
        """Build prompt enriched with relevant memories."""
        memory_context = ""
        if context.relevant_memories:
            memory_items = [m.get("content", "") for m in context.relevant_memories[:3]]
            memory_context = "\n\nRelevant memories:\n" + "\n".join(f"- {m}" for m in memory_items if m)

        return f"""You are Jarvis, an intelligent AI assistant.

Context:
- Language: {context.language}
- Intent: {context.intent}
- User: {text}
{memory_context}

Respond helpfully and concisely in {context.language}."""
