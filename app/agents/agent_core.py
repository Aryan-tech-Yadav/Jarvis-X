"""Jarvis-X Agent Core - 5-Layer AI Agent Architecture.

Layer 1: Input Layer (Text, Voice, Image)
Layer 2: LLM Brain (Reasoning, Decision Making)
Layer 3: Planning & Reasoning (Task decomposition, Chain-of-thought)
Layer 4: Memory Layer (Short-term, Long-term, User preferences)
Layer 5: Tools Layer (APIs, Search, Code, System control)

Architecture:
  Input → LLM Brain → Planner → Memory + Tools → Executor → Response
"""

from __future__ import annotations

import json
import time
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Callable

from app.core.logger import Logger


# ============================
# Layer 1: Input Layer
# ============================

@dataclass
class AgentInput:
    """Input from any source: text, voice, image."""
    source: str = "text"  # text, voice, image
    content: str = ""
    raw_data: Any = None
    language: str = "english"
    confidence: float = 1.0
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict:
        return {
            "source": self.source,
            "content": self.content,
            "language": self.language,
            "confidence": self.confidence,
            "metadata": dict(self.metadata),
        }


class InputLayer:
    """Process inputs from text, voice, and image sources."""

    def __init__(self):
        self._processors = {
            "text": self._process_text,
            "voice": self._process_voice,
            "image": self._process_image,
        }

    def process(self, raw_input: str, source: str = "text", **kwargs) -> AgentInput:
        """Process raw input into structured AgentInput."""
        processor = self._processors.get(source, self._process_text)
        return processor(raw_input, **kwargs)

    def _process_text(self, text: str, **kwargs) -> AgentInput:
        """Process text input."""
        return AgentInput(
            source="text",
            content=text.strip(),
            language=kwargs.get("language", "english"),
            metadata=kwargs.get("metadata", {}),
        )

    def _process_voice(self, audio_data: Any, **kwargs) -> AgentInput:
        """Process voice input."""
        try:
            # Try to use existing voice system
            from app.voice.jarvis_voice import JarvisVoice
            voice = JarvisVoice()
            text = voice.listen()
            if text:
                return AgentInput(
                    source="voice",
                    content=text,
                    language=kwargs.get("language", "english"),
                    confidence=0.9,
                    metadata={"audio_data": str(audio_data)[:100]},
                )
        except Exception as exc:
            Logger.warning(f"[InputLayer] Voice processing failed: {exc}")

        return AgentInput(
            source="voice",
            content=str(audio_data) if audio_data else "",
            language=kwargs.get("language", "english"),
            confidence=0.0,
            metadata={"error": "voice processing failed"},
        )

    def _process_image(self, image_data: Any, **kwargs) -> AgentInput:
        """Process image input."""
        return AgentInput(
            source="image",
            content="",
            raw_data=image_data,
            language=kwargs.get("language", "english"),
            confidence=0.0,
            metadata={"note": "image processing not yet implemented"},
        )


# ============================
# Layer 2: LLM Brain
# ============================

@dataclass
class Thought:
    """Single reasoning step."""
    thought: str = ""
    action: str = ""
    action_input: str = ""
    observation: str = ""
    is_final: bool = False

    def to_dict(self) -> dict:
        return {
            "thought": self.thought,
            "action": self.action,
            "action_input": self.action_input,
            "observation": self.observation,
            "is_final": self.is_final,
        }


@dataclass
class AgentResponse:
    """Final agent response."""
    success: bool
    answer: str = ""
    reasoning: List[Thought] = field(default_factory=list)
    actions_taken: List[Dict[str, Any]] = field(default_factory=list)
    confidence: float = 0.0
    duration: float = 0.0
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict:
        return {
            "success": self.success,
            "answer": self.answer,
            "reasoning": [r.to_dict() for r in self.reasoning],
            "actions_taken": list(self.actions_taken),
            "confidence": round(self.confidence, 2),
            "duration": round(self.duration, 2),
            "metadata": dict(self.metadata),
        }


class LLMBrain:
    """LLM-powered reasoning and decision making."""

    SYSTEM_PROMPT = """You are Jarvis-X, an autonomous software engineer and AI assistant.

You have access to the following tools:
- search_google(query): Search Google for information
- get_news(category): Get latest news
- play_spotify(song): Play song on Spotify
- open_application(app): Open desktop applications
- open_website(website): Open websites in browser
- shutdown/restart/sleep/lock: System controls
- build_project(goal): Build software projects autonomously

When you need to use a tool, respond with JSON:
{
  "thought": "Your reasoning",
  "action": "tool_name",
  "action_input": "input for tool",
  "is_final": false
}

When you have the final answer, respond with JSON:
{
  "thought": "Final reasoning",
  "answer": "Your final response to user",
  "is_final": true
}

Always respond with valid JSON. Think step by step."""

    def __init__(self, router=None):
        self.router = router
        self._conversation: List[Dict[str, str]] = []
        self._init_conversation()

    def _init_conversation(self):
        """Initialize conversation with system prompt."""
        self._conversation = [
            {"role": "system", "content": self.SYSTEM_PROMPT}
        ]

    def think(self, user_input: str, context: Dict[str, Any] = None) -> Thought:
        """Generate reasoning for a single step."""
        prompt = self._build_prompt(user_input, context)
        
        try:
            response = self._ask_llm(prompt)
            return self._parse_thought(response)
        except Exception as exc:
            Logger.error(f"[LLMBrain] Thinking failed: {exc}")
            return Thought(
                thought=f"Error: {exc}",
                action="respond",
                action_input=str(exc),
                is_final=True,
            )

    def generate_final_answer(self, user_input: str, context: Dict[str, Any] = None) -> AgentResponse:
        """Generate final answer after reasoning."""
        start = time.perf_counter()
        
        reasoning_chain = []
        current_input = user_input
        max_iterations = 5
        
        for i in range(max_iterations):
            thought = self.think(current_input, context)
            reasoning_chain.append(thought)
            
            if thought.is_final:
                duration = time.perf_counter() - start
                return AgentResponse(
                    success=True,
                    answer=thought.answer or thought.thought,
                    reasoning=reasoning_chain,
                    confidence=0.8 if thought.answer else 0.5,
                    duration=duration,
                )
            
            # Execute action and get observation
            observation = self._execute_action(thought)
            thought.observation = observation
            
            # Continue reasoning with observation
            current_input = f"Observation: {observation}\nContinue reasoning."
        
        duration = time.perf_counter() - start
        return AgentResponse(
            success=True,
            answer=reasoning_chain[-1].thought if reasoning_chain else "I couldn't process that.",
            reasoning=reasoning_chain,
            confidence=0.5,
            duration=duration,
        )

    def _build_prompt(self, user_input: str, context: Dict[str, Any] = None) -> str:
        """Build prompt with context."""
        prompt = f"User: {user_input}\n\n"
        
        if context:
            if context.get("memory"):
                prompt += f"Memory: {context['memory'][:500]}\n\n"
            if context.get("available_tools"):
                prompt += f"Available tools: {', '.join(context['available_tools'])}\n\n"
        
        prompt += "Respond with JSON:"
        return prompt

    def _ask_llm(self, prompt: str) -> str:
        """Ask LLM for response."""
        try:
            from app.ai.ai_manager import AIManager
            ai = AIManager()
            return ai.ask(prompt)
        except Exception:
            # Fallback: simple rule-based response
            return json.dumps({
                "thought": "Processing user request",
                "answer": "I understand. Let me help you with that.",
                "is_final": True,
            })

    def _parse_thought(self, response: str) -> Thought:
        """Parse LLM response into Thought."""
        try:
            # Try to extract JSON from response
            response = response.strip()
            if response.startswith("```"):
                response = response.split("```")[1]
                if response.startswith("json"):
                    response = response[4:]
            
            data = json.loads(response)
            return Thought(
                thought=data.get("thought", ""),
                action=data.get("action", ""),
                action_input=data.get("action_input", ""),
                answer=data.get("answer", ""),
                is_final=data.get("is_final", True),
            )
        except (json.JSONDecodeError, AttributeError):
            return Thought(
                thought=response[:200],
                action="respond",
                action_input=response[:100],
                is_final=True,
            )

    def _execute_action(self, thought: Thought) -> str:
        """Execute an action from thought."""
        action = thought.action.lower()
        action_input = thought.action_input
        
        if not action or action == "respond":
            return thought.answer or thought.thought
        
        # Route to appropriate tool
        try:
            from app.automation.automation_manager import AutomationManager
            automation = AutomationManager()
            
            if action == "open_application":
                result = automation.open_application(action_input)
                return str(result)
            elif action == "open_website":
                result = automation.open_Website(action_input)
                return str(result)
            elif action == "play_spotify":
                result = automation.play_spotify(action_input)
                return str(result)
            elif action == "search_google":
                result = automation.search_google(action_input)
                return str(result)[:200]
            elif action == "get_news":
                result = automation.get_news(action_input)
                return str(result)[:200]
            elif action == "shutdown":
                result = automation.shutdown()
                return str(result)
            elif action == "restart":
                result = automation.restart()
                return str(result)
            elif action == "sleep":
                result = automation.sleep()
                return str(result)
            else:
                return f"Unknown action: {action}"
        except Exception as exc:
            return f"Action failed: {exc}"


# ============================
# Layer 3: Planning & Reasoning
# ============================

@dataclass
class Plan:
    """Execution plan with steps."""
    goal: str
    steps: List[Dict[str, Any]] = field(default_factory=list)
    reasoning: str = ""
    estimated_steps: int = 0

    def to_dict(self) -> dict:
        return {
            "goal": self.goal,
            "steps": list(self.steps),
            "reasoning": self.reasoning,
            "estimated_steps": self.estimated_steps,
        }


class AgentPlanner:
    """Plan and decompose tasks."""

    def __init__(self, brain: LLMBrain = None):
        self.brain = brain or LLMBrain()

    def create_plan(self, goal: str, context: Dict[str, Any] = None) -> Plan:
        """Create execution plan for a goal."""
        prompt = f"""Break down this task into steps:
Goal: {goal}

Return JSON:
{{
  "reasoning": "Why these steps",
  "steps": [
    {{"step": 1, "description": "...", "tool": "tool_name"}},
    ...
  ]
}}"""

        try:
            response = self.brain._ask_llm(prompt)
            data = json.loads(self._extract_json(response))
            return Plan(
                goal=goal,
                steps=data.get("steps", []),
                reasoning=data.get("reasoning", ""),
                estimated_steps=len(data.get("steps", [])),
            )
        except Exception as exc:
            Logger.warning(f"[AgentPlanner] Planning failed: {exc}")
            return Plan(
                goal=goal,
                steps=[{"step": 1, "description": goal, "tool": "direct_execute"}],
                reasoning="Fallback plan",
            )

    def _extract_json(self, text: str) -> str:
        """Extract JSON from text."""
        text = text.strip()
        if text.startswith("```"):
            text = text.split("```")[1]
            if text.startswith("json"):
                text = text[4:]
        return text.strip()


# ============================
# Layer 4: Memory Layer
# ============================

@dataclass
class MemoryEntry:
    """Single memory entry."""
    key: str
    value: Any
    memory_type: str = "short_term"  # short_term, long_term, preference
    importance: float = 0.5
    timestamp: float = field(default_factory=time.time)

    def to_dict(self) -> dict:
        return {
            "key": self.key,
            "value": str(self.value)[:200],
            "memory_type": self.memory_type,
            "importance": self.importance,
            "timestamp": self.timestamp,
        }


class AgentMemory:
    """Multi-layer memory system."""

    def __init__(self):
        self.short_term: List[MemoryEntry] = []
        self.long_term: List[MemoryEntry] = []
        self.preferences: Dict[str, Any] = {}
        self.max_short_term = 20

    def remember(self, key: str, value: Any, memory_type: str = "short_term", importance: float = 0.5):
        """Store a memory."""
        entry = MemoryEntry(key=key, value=value, memory_type=memory_type, importance=importance)
        
        if memory_type == "short_term":
            self.short_term.append(entry)
            if len(self.short_term) > self.max_short_term:
                self.short_term.pop(0)
        elif memory_type == "long_term":
            self.long_term.append(entry)
        elif memory_type == "preference":
            self.preferences[key] = value

    def recall(self, key: str) -> Optional[Any]:
        """Recall a memory by key."""
        # Check short-term first
        for entry in reversed(self.short_term):
            if entry.key == key:
                return entry.value
        
        # Check long-term
        for entry in reversed(self.long_term):
            if entry.key == key:
                return entry.value
        
        # Check preferences
        return self.preferences.get(key)

    def get_context(self, max_entries: int = 5) -> str:
        """Get memory context for LLM."""
        context_parts = []
        
        # Recent short-term memories
        for entry in self.short_term[-max_entries:]:
            context_parts.append(f"{entry.key}: {entry.value}")
        
        # Relevant long-term memories
        for entry in self.long_term[-max_entries:]:
            if entry.importance > 0.7:
                context_parts.append(f"[IMPORTANT] {entry.key}: {entry.value}")
        
        # User preferences
        if self.preferences:
            context_parts.append(f"User preferences: {json.dumps(self.preferences)[:200]}")
        
        return "\n".join(context_parts) if context_parts else "No relevant memory."

    def get_preference(self, key: str, default=None):
        """Get user preference."""
        return self.preferences.get(key, default)

    def set_preference(self, key: str, value: Any):
        """Set user preference."""
        self.preferences[key] = value
        self.remember(key, value, memory_type="preference", importance=1.0)


# ============================
# Layer 5: Tools Layer
# ============================

@dataclass
class Tool:
    """Standardized tool definition."""
    name: str
    description: str
    func: Callable
    parameters: Dict[str, Any] = field(default_factory=dict)
    requires_confirmation: bool = False

    def to_dict(self) -> dict:
        return {
            "name": self.name,
            "description": self.description,
            "parameters": self.parameters,
            "requires_confirmation": self.requires_confirmation,
        }


class AgentToolbox:
    """Tool registry and management."""

    def __init__(self):
        self._tools: Dict[str, Tool] = {}
        self._register_default_tools()

    def _register_default_tools(self):
        """Register default tools."""
        try:
            from app.automation.automation_manager import AutomationManager
            automation = AutomationManager()

            self.register(Tool(
                name="open_application",
                description="Open desktop applications (chrome, vscode, notepad, etc.)",
                func=automation.open_application,
                parameters={"app": "application name"},
            ))

            self.register(Tool(
                name="open_website",
                description="Open websites (youtube, instagram, google, etc.)",
                func=automation.open_Website,
                parameters={"website": "website name or URL"},
            ))

            self.register(Tool(
                name="play_spotify",
                description="Play specific song on Spotify",
                func=automation.play_spotify,
                parameters={"song": "song name"},
            ))

            self.register(Tool(
                name="search_google",
                description="Search Google for information",
                func=automation.search_google,
                parameters={"query": "search query"},
            ))

            self.register(Tool(
                name="get_news",
                description="Get latest news",
                func=automation.get_news,
                parameters={"category": "news category (optional)"},
            ))

            self.register(Tool(
                name="shutdown",
                description="Shutdown the computer",
                func=automation.shutdown,
                parameters={"delay": "seconds (optional)"},
                requires_confirmation=True,
            ))

            self.register(Tool(
                name="restart",
                description="Restart the computer",
                func=automation.restart,
                parameters={"delay": "seconds (optional)"},
                requires_confirmation=True,
            ))

        except Exception as exc:
            Logger.warning(f"[AgentToolbox] Failed to register default tools: {exc}")

    def register(self, tool: Tool):
        """Register a new tool."""
        self._tools[tool.name] = tool

    def get(self, name: str) -> Optional[Tool]:
        """Get tool by name."""
        return self._tools.get(name)

    def list_tools(self) -> List[Dict[str, Any]]:
        """List all available tools."""
        return [tool.to_dict() for tool in self._tools.values()]

    def execute(self, name: str, **kwargs) -> str:
        """Execute a tool."""
        tool = self._tools.get(name)
        if not tool:
            return f"Tool not found: {name}"
        
        try:
            result = tool.func(**kwargs)
            return str(result)
        except Exception as exc:
            return f"Tool execution failed: {exc}"

    def get_tool_descriptions(self) -> str:
        """Get descriptions of all tools for LLM prompt."""
        descriptions = []
        for tool in self._tools.values():
            desc = f"- {tool.name}: {tool.description}"
            if tool.parameters:
                params = ", ".join(f"{k}={v}" for k, v in tool.parameters.items())
                desc += f" (params: {params})"
            descriptions.append(desc)
        return "\n".join(descriptions)


# ============================
# Agent Core (Combines all layers)
# ============================

class AgentCore:
    """Main agent that combines all 5 layers.

    Flow:
      1. Input Layer: Receive and process input
      2. LLM Brain: Understand and reason
      3. Planner: Create execution plan
      4. Memory + Tools: Access memory and tools
      5. Executor: Execute plan and return response
    """

    def __init__(self):
        self.input_layer = InputLayer()
        self.brain = LLMBrain()
        self.planner = AgentPlanner(self.brain)
        self.memory = AgentMemory()
        self.toolbox = AgentToolbox()

    def process(self, user_input: str, source: str = "text", **kwargs) -> AgentResponse:
        """Process user input through all layers."""
        start = time.perf_counter()

        # Layer 1: Input
        agent_input = self.input_layer.process(user_input, source=source, **kwargs)
        Logger.info(f"[AgentCore] Input: {agent_input.content[:100]}")

        # Layer 4: Retrieve memory context
        memory_context = self.memory.get_context()
        context = {
            "memory": memory_context,
            "available_tools": list(self.toolbox._tools.keys()),
        }

        # Layer 2 + 3 + 5: LLM Brain + Planning + Tools
        response = self.brain.generate_final_answer(agent_input.content, context)

        # Layer 4: Store important memories
        if response.success and response.answer:
            self.memory.remember(
                f"interaction_{len(self.memory.short_term)}",
                {"input": agent_input.content[:100], "output": response.answer[:100]},
                importance=0.3,
            )

        # Log actions
        for thought in response.reasoning:
            if thought.action and thought.action != "respond":
                response.actions_taken.append({
                    "action": thought.action,
                    "input": thought.action_input,
                    "observation": thought.observation,
                })

        duration = time.perf_counter() - start
        response.duration = duration
        response.metadata = {
            "input_source": agent_input.source,
            "language": agent_input.language,
            "memory_entries": len(self.memory.short_term) + len(self.memory.long_term),
        }

        Logger.success(f"[AgentCore] Response generated in {duration:.2f}s")
        return response

    def execute_tool(self, tool_name: str, **kwargs) -> str:
        """Execute a tool directly."""
        return self.toolbox.execute(tool_name, **kwargs)

    def remember(self, key: str, value: Any, memory_type: str = "short_term"):
        """Store a memory."""
        self.memory.remember(key, value, memory_type=memory_type)

    def recall(self, key: str) -> Optional[Any]:
        """Recall a memory."""
        return self.memory.recall(key)

    def set_preference(self, key: str, value: Any):
        """Set user preference."""
        self.memory.set_preference(key, value)

    def get_preference(self, key: str, default=None):
        """Get user preference."""
        return self.memory.get_preference(key, default)
