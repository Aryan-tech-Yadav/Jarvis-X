"""Jarvis-X - Autonomous Software Engineer

Main entry point that connects all systems:
  - Layer 1: Input Layer (text, voice, image)
  - Layer 2: Brain (LLM + cognition)
  - Layer 3: Planning & Reasoning
  - Layer 4: Memory Layer (short-term, long-term, user profile)
  - Layer 5: Tools Layer (APIs, automation, code execution)

Updated to follow 5-layer AI Agent architecture.
"""

from __future__ import annotations

import os
import sys
import time
from typing import Optional

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app.core.logger import Logger

class JarvisCLI:
    """Command-line interface for Jarvis-X with 5-layer architecture."""

    def __init__(self):
        self.input_layer = None
        self.brain = None
        self.planner = None
        self.memory = None
        self.tool_selector = None
        self.task_manager = None
        self.engineering_workflow = None
        self.autonomous_executor = None
        self.execution_monitor = None
        self.orchestrator = None
        self.voice = None
        self.automation = None
        self.running = False
        self.last_project = None
        self.runtime_context = None
        self.event_bus = None
        self.artifact_manager = None
        self.reflection_engine = None
        self.learning_engine = None
        self.dashboard_backend = None
        self.core_runtime = None
        self._init_systems()

    def _init_systems(self):
        """Initialize all 5 layers and supporting systems."""
        Logger.info("[JarvisCLI] Initializing 5-layer architecture...")

        # Runtime Core (Day 1-7)
        try:
            from app.events.event_bus import EventBus
            self.event_bus = EventBus()
            Logger.success("[JarvisCLI] EventBus initialized")
        except Exception as exc:
            Logger.warning(f"[JarvisCLI] EventBus init failed: {exc}")

        try:
            from app.runtime.runtime_context import RuntimeContext
            self.runtime_context = RuntimeContext()
            if self.event_bus:
                self.runtime_context.event_bus = self.event_bus
            Logger.success("[JarvisCLI] RuntimeContext initialized")
        except Exception as exc:
            Logger.warning(f"[JarvisCLI] RuntimeContext init failed: {exc}")

        try:
            from app.runtime.artifact_manager import ArtifactManager
            self.artifact_manager = ArtifactManager()
            Logger.success("[JarvisCLI] ArtifactManager initialized")
        except Exception as exc:
            Logger.warning(f"[JarvisCLI] ArtifactManager init failed: {exc}")

        try:
            from app.runtime.reflection_engine import ReflectionEngine
            self.reflection_engine = ReflectionEngine()
            Logger.success("[JarvisCLI] ReflectionEngine initialized")
        except Exception as exc:
            Logger.warning(f"[JarvisCLI] ReflectionEngine init failed: {exc}")

        try:
            from app.runtime.learning_engine import LearningEngine
            self.learning_engine = LearningEngine()
            Logger.success("[JarvisCLI] LearningEngine initialized")
        except Exception as exc:
            Logger.warning(f"[JarvisCLI] LearningEngine init failed: {exc}")

        try:
            from app.runtime.dashboard_backend import DashboardBackend
            self.dashboard_backend = DashboardBackend()
            Logger.success("[JarvisCLI] DashboardBackend initialized")
        except Exception as exc:
            Logger.warning(f"[JarvisCLI] DashboardBackend init failed: {exc}")

        try:
            from app.runtime.core_runtime import CoreRuntime
            if self.engineering_workflow and self.autonomous_executor:
                self.core_runtime = CoreRuntime(
                    workflow=self.engineering_workflow,
                    executor=self.autonomous_executor,
                    event_bus=self.event_bus,
                    context=self.runtime_context,
                    artifact_manager=self.artifact_manager,
                    reflection_engine=self.reflection_engine,
                    learning_engine=self.learning_engine,
                    dashboard_backend=self.dashboard_backend,
                )
                Logger.success("[JarvisCLI] Core Runtime initialized")
        except Exception as exc:
            Logger.warning(f"[JarvisCLI] Core Runtime init failed: {exc}")

        # Brain Kernel (EIK)
        try:
            from app.brain.brain_kernel import BrainKernel
            self.brain_kernel = BrainKernel(
                event_bus=self.event_bus,
                ai_router=self.ai_manager if hasattr(self, 'ai_manager') else None,
                runtime_context=self.runtime_context,
            )
            Logger.success("[JarvisCLI] Brain Kernel (EIK) initialized")
        except Exception as exc:
            Logger.warning(f"[JarvisCLI] Brain Kernel init failed: {exc}")
            self.brain_kernel = None

        # Layer 4: Memory
        try:
            from app.memory.enhanced_memory import EnhancedMemoryManager
            self.memory = EnhancedMemoryManager()
            self.memory.initialize()
            Logger.success("[JarvisCLI] Memory Layer initialized")
        except Exception as exc:
            Logger.warning(f"[JarvisCLI] Memory init failed: {exc}")
            try:
                from app.memory.memory_manager import MemoryManager
                self.memory = MemoryManager()
                Logger.success("[JarvisCLI] Fallback MemoryManager initialized")
            except Exception:
                self.memory = None

        # Layer 1: Input
        try:
            from app.input.input_layer import InputLayer
            self.input_layer = InputLayer()

            # Attach voice - prefer professional JarvisVoice architecture
            try:
                from app.voice.jarvis_voice import JarvisVoice
                self.voice = JarvisVoice()
                Logger.success("[JarvisCLI] Professional Voice System initialized")
            except Exception:
                try:
                    from app.voice.voice_manager import VoiceManager
                    self.voice = VoiceManager()
                    Logger.success("[JarvisCLI] Voice Manager initialized")
                except Exception:
                    self.voice = None

            # Attach vision
            try:
                from app.vision.vision_manager import VisionManager
                vision = VisionManager()
                vision.initialize()
                self.input_layer.initialize(vision_manager=vision)
            except Exception:
                pass

            Logger.success("[JarvisCLI] Input Layer initialized")
        except Exception as exc:
            Logger.warning(f"[JarvisCLI] Input Layer init failed: {exc}")

        # Layer 2: Brain
        try:
            from app.brain.brain import Brain
            self.brain = Brain(
                input_layer=self.input_layer,
                memory=self.memory,
            )
            self.brain.initialize()
            Logger.success("[JarvisCLI] Brain Layer initialized")
        except Exception as exc:
            Logger.warning(f"[JarvisCLI] Brain init failed: {exc}")

        # Layer 3: Planner
        try:
            from app.planner.planner import Planner
            self.planner = Planner()
            if self.brain:
                self.brain.planner = self.planner
            Logger.success("[JarvisCLI] Planning Layer initialized")
        except Exception as exc:
            Logger.warning(f"[JarvisCLI] Planner init failed: {exc}")

        # Layer 5: Tools
        try:
            from app.tools.tool_selector import ToolSelector
            self.tool_selector = ToolSelector()
            self.tool_selector.initialize()
            if self.brain:
                self.brain.tool_selector = self.tool_selector
            Logger.success("[JarvisCLI] Tool Selector initialized")
        except Exception as exc:
            Logger.warning(f"[JarvisCLI] Tool Selector init failed: {exc}")

        # Quality & Knowledge systems
        try:
            from app.engineering.project_type_detector import ProjectTypeDetector
            self.type_detector = ProjectTypeDetector()
            Logger.success("[JarvisCLI] Project Type Detector initialized")
        except Exception as exc:
            Logger.warning(f"[JarvisCLI] Project Type Detector init failed: {exc}")

        try:
            from app.knowledge.template_store import TemplateStore, TemplateRetriever
            self.template_store = TemplateStore()
            self.template_retriever = TemplateRetriever(self.template_store)
            Logger.success("[JarvisCLI] Template Store initialized")
        except Exception as exc:
            Logger.warning(f"[JarvisCLI] Template Store init failed: {exc}")

        try:
            from app.quality.comprehensive_scorer import ComprehensiveQualityScorer
            self.quality_scorer = None  # Initialized per-project
            Logger.success("[JarvisCLI] Quality Scorer available")
        except Exception as exc:
            Logger.warning(f"[JarvisCLI] Quality Scorer init failed: {exc}")

        # Supporting systems
        try:
            from app.automation.automation_manager import AutomationManager
            self.automation = AutomationManager()
            Logger.success("[JarvisCLI] AutomationManager initialized")
        except Exception as exc:
            Logger.warning(f"[JarvisCLI] Automation init failed: {exc}")

        try:
            from app.core.task_manager import TaskManager
            self.task_manager = TaskManager()
            Logger.success("[JarvisCLI] TaskManager initialized")
        except Exception as exc:
            Logger.warning(f"[JarvisCLI] TaskManager init failed: {exc}")

        try:
            from app.engineering.workflow import EngineeringWorkflow
            from app.engineering.autonomous_executor import AutonomousExecutor
            from app.engineering.execution_monitor import ExecutionMonitor
            self.engineering_workflow = EngineeringWorkflow()
            self.autonomous_executor = AutonomousExecutor()
            self.execution_monitor = ExecutionMonitor()
            Logger.success("[JarvisCLI] Engineering systems initialized")
        except Exception as exc:
            Logger.warning(f"[JarvisCLI] Engineering init failed: {exc}")

        try:
            from app.agents.scalable_orchestrator import ScalableOrchestrator
            from app.agents.agent_registry import AgentRegistry
            from app.events.event_bus import EventBus
            self.event_bus = EventBus()
            self.registry = AgentRegistry()
            self.orchestrator = ScalableOrchestrator(
                registry=self.registry,
                event_bus=self.event_bus,
            )
            Logger.success("[JarvisCLI] Multi-Agent Orchestrator initialized")
        except Exception as exc:
            Logger.warning(f"[JarvisCLI] Orchestrator init failed: {exc}")

        # Hindi/Hinglish processor
        try:
            from app.core.hinglish_processor import HindiHinglishProcessor, HinglishResponseGenerator
            self.hindi_processor = HindiHinglishProcessor()
            self.response_generator = HinglishResponseGenerator()
            Logger.success("[JarvisCLI] Hindi/Hinglish processor initialized")
        except Exception as exc:
            Logger.warning(f"[JarvisCLI] Hindi processor init failed: {exc}")
            self.hindi_processor = None
            self.response_generator = None

        Logger.success("[JarvisCLI] System initialization complete")

    def _get_language_processor(self):
        """Get language processor for input layer."""
        try:
            from app.core.language_processor import LanguageProcessor
            return LanguageProcessor()
        except Exception:
            return None

    def detect_intent(self, text: str) -> str:
        """Detect user intent."""
        if self.hindi_processor:
            parsed = self.hindi_processor.parse(text)
            return parsed.intent
        if self.brain:
            result = self.brain._detect_intent(text)
            return result.get("intent", "CHAT")
        return "CHAT"

    def _detect_language(self, text: str) -> str:
        """Detect user language."""
        if self.hindi_processor:
            parsed = self.hindi_processor.parse(text)
            return parsed.raw_entities.get("language", "english")
        if self.input_layer:
            return self.input_layer._detect_language(text)
        return "english"

    def handle_command(self, user_input: str) -> bool:
        """Process user input through 5-layer architecture."""
        user_input = user_input.strip()
        if not user_input:
            return True

        intent = self.detect_intent(user_input)
        language = self._detect_language(user_input)

        if intent == "EXIT":
            self._speak_response(self.response_generator.generate("goodbye", language=language) if self.response_generator else "Alvida! Goodbye!")
            return False

        if intent == "HELP":
            print(self.response_generator.help_message(language=language) if self.response_generator else self._show_help())
            self._speak_response("Here are the commands you can use.")
            return True

        if intent == "STATUS":
            self._show_status()
            return True

        if intent == "HISTORY":
            self._show_history()
            return True

        if intent == "SHUTDOWN":
            return self._handle_shutdown(language)

        if intent == "RESTART":
            return self._handle_restart(language)

        if intent == "SLEEP":
            return self._handle_sleep(language)

        if intent == "LOCK":
            return self._handle_lock(language)

        if intent == "CANCEL_SHUTDOWN":
            return self._handle_cancel_shutdown(language)

        if intent == "PLAY_MUSIC":
            return self._handle_play_music(language)

        if intent == "PLAY_SPOTIFY_SONG":
            return self._handle_play_spotify_song(user_input, language)

        if intent == "GET_NEWS":
            return self._handle_get_news(user_input, language)

        if intent == "GOOGLE_SEARCH":
            return self._handle_google_search(user_input, language)

        if intent == "CREATE_CODE":
            return self._handle_create_code(user_input, language)

        if intent == "OPEN_APPLICATION":
            return self._handle_open_application(user_input, language)

        if intent == "OPEN_WEBSITE":
            return self._handle_open_website(user_input, language)

        if intent == "CLOSE_APPLICATION":
            return self._handle_close_application(user_input, language)

        # Default: chat via Brain Layer
        print(self.response_generator.generate("thinking", language=language) if self.response_generator else "\nThinking...")
        try:
            if self.brain:
                result = self.brain.process(user_input, input_type="text")
                response = result.get("response", "I'm here to help.")
                print(f"\nJarvis: {response}")
            else:
                print("\nJarvis: Brain module unavailable.")
        except Exception as e:
            print(self.response_generator.generate("error", language=language, error=str(e)) if self.response_generator else f"\nError: {e}")

        return True

    def _handle_create_code(self, goal: str, language: str) -> bool:
        """Handle code/project creation with 5-layer enhanced pipeline."""
        print(self.response_generator.generate("engineering_started", language=language, project_name=goal) if self.response_generator else "\nStarting autonomous engineering pipeline...")
        print(f"Goal: {goal}")
        print("=" * 60)

        # Layer 3: Planning
        if self.planner:
            try:
                plan = self.planner.get_structured_plan(goal, "CREATE_CODE")
                print(f"\nPlan ({len(plan.steps)} steps):")
                for step in plan.steps:
                    print(f"  {step.step_id}: {step.description}")
                    if step.tool:
                        print(f"      -> Tool: {step.tool} | Action: {step.action}")
            except Exception:
                pass

        # Layer 5: Tool Selection
        if self.tool_selector:
            try:
                tools = self.tool_selector.select("CREATE_CODE", goal)
                print(f"\nSelected Tools: {', '.join(tools)}")
            except Exception:
                pass

        # Project Type Detection
        if hasattr(self, 'type_detector') and self.type_detector:
            try:
                detection = self.type_detector.detect(goal)
                print(f"\nProject Type: {detection.project_type.value}")
                print(f"Tech Stack: {detection.tech_stack.rationale}")
                print(f"Confidence: {detection.confidence:.0%}")
            except Exception:
                pass

        print("=" * 60)
        self._run_engineering_pipeline(goal, language)
        return True

    def _run_engineering_pipeline(self, goal: str, language: str = "english"):
        """Run the full engineering pipeline with quality focus."""
        try:
            from app.planning.goal_analyzer import GoalAnalyzer
            from app.planning.task_decomposer import TaskDecomposer
            from app.reasoning.cognitive_pipeline import CognitivePipeline
            goal_analysis = GoalAnalyzer().analyze(goal)
            task_graph = TaskDecomposer().decompose(goal_analysis)
            cognitive = CognitivePipeline().assess(goal)
            print(
                f"\nGoal Analysis: {goal_analysis.project_type} | "
                f"{goal_analysis.difficulty} | ~{goal_analysis.estimated_hours}h"
            )
            print(f"Technologies: {', '.join(goal_analysis.technologies) or 'default stack'}")
            print(f"Deliverables: {', '.join(goal_analysis.deliverables)}")
            print(
                f"Task Graph: {task_graph.get_stats()['total_tasks']} tasks | "
                f"{len(task_graph.get_parallel_groups())} execution groups"
            )
            print(
                f"Risk Score: {cognitive['risk'].get('risk_score', 0):.1f}/100 | "
                f"Clarifications: {len(cognitive['clarification']['questions'])}"
            )
            if not self.core_runtime and self.engineering_workflow and self.autonomous_executor:
                from app.runtime.core_runtime import CoreRuntime
                self.core_runtime = CoreRuntime(
                    workflow=self.engineering_workflow,
                    executor=self.autonomous_executor,
                    event_bus=self.event_bus,
                    context=self.runtime_context,
                    artifact_manager=self.artifact_manager,
                    reflection_engine=self.reflection_engine,
                    learning_engine=self.learning_engine,
                    dashboard_backend=self.dashboard_backend,
                )
            if self.core_runtime:
                runtime_result = self.core_runtime.execute(goal)
                self.last_project = runtime_result["project_name"]
                metrics = runtime_result.get("metrics", {})
                print(f"\nRuntime pipeline completed: {runtime_result['project_name']}")
                print(f"Generated: {metrics.get('files_generated', 0)} files")
                print(f"Quality: {metrics.get('quality_score', 0):.1f}%")
                self._speak_response(
                    "Project generated through the unified runtime pipeline."
                    if runtime_result["success"]
                    else "Project completed with some issues. Check logs."
                )
                return

            if not self.engineering_workflow:
                print("Engineering Brain not available.")
                return

            workflow_result = self.engineering_workflow.run(goal)

            if not workflow_result.success:
                print("Engineering analysis failed")
                return

            analysis = workflow_result.analysis or {}
            project_name = analysis.get("project_name", "unnamed_project")
            domain = analysis.get("domain", "general")

            print(f"Project: {project_name}")
            print(f"Domain: {domain}")
            print(f"Confidence: {analysis.get('confidence', 0) * 100:.0f}%")

            if workflow_result.tech_stack:
                tech = workflow_result.tech_stack
                print(f"\nTech Stack:")
                print(f"  Backend: {tech.get('backend', 'N/A')}")
                print(f"  Frontend: {tech.get('frontend', 'N/A')}")
                print(f"  Database: {tech.get('database', 'N/A')}")

            if workflow_result.risks:
                risk_level = workflow_result.risks.get("overall_risk_level", "low")
                print(f"\nRisk Level: {risk_level.upper()}")

            if self.autonomous_executor:
                print("\nGenerating project with quality pipeline...")
                exec_result = self.autonomous_executor.execute(workflow_result)

                metrics = exec_result.metrics or {}
                files = metrics.get("files_generated", 0)
                quality = metrics.get("quality_score", 0)
                duration = metrics.get("duration_seconds", 0)
                project_type = metrics.get("project_type", "unknown")
                template_used = metrics.get("template_used", "none")

                print(f"\nGenerated: {files} files")
                print(f"Project Type: {project_type}")
                print(f"Template: {template_used}")
                print(f"Quality: {quality:.1f}%")
                print(f"Duration: {duration:.1f}s")

                # Show quality breakdown if available
                if exec_result.data and "quality" in exec_result.data:
                    q = exec_result.data["quality"]
                    print(f"\nQuality Breakdown:")
                    print(f"  Compile: {q.get('compile', 0):.1f}%")
                    print(f"  Runtime: {q.get('runtime', 0):.1f}%")
                    print(f"  Tests: {q.get('tests', 0):.1f}%")
                    print(f"  Code Quality: {q.get('code_quality', 0):.1f}%")
                    print(f"  Architecture: {q.get('architecture', 0):.1f}%")
                    print(f"  Grade: {q.get('grade', 'N/A')}")

                # Show refinement cycles
                cycles = metrics.get("refinement_cycles", [])
                if cycles:
                    print(f"\nRefinement Cycles: {len(cycles)}")
                    for c in cycles:
                        print(f"  Cycle {c.get('cycle')}: {c.get('quality', 0):.1f}% quality")

                if exec_result.data:
                    project_path = exec_result.data.get("project_path", "")
                    if project_path:
                        print(f"\nProject: {project_path}")

                if exec_result.success:
                    self._speak_response(f"Project generated with {files} files and {quality:.0f}% quality.")
                else:
                    self._speak_response("Project completed with some issues. Check logs.")

            self.last_project = project_name

        except Exception as e:
            Logger.error(f"Pipeline failed: {e}")
            print(f"Pipeline failed: {e}")

    # ---- Handlers ----

    def _handle_open_application(self, user_input: str, language: str) -> bool:
        if not self.automation:
            print("Automation not available")
            return True
        app_name = self._extract_app_name(user_input)
        if not app_name:
            print("Which app do you want to open?")
            return True
        result = self.automation.open_application(app_name)
        print(f"\nJarvis: {result}")
        return True

    def _handle_open_website(self, user_input: str, language: str) -> bool:
        if not self.automation:
            print("Automation not available")
            return True
        website_name = self._extract_website_name(user_input)
        if not website_name:
            print("Which website do you want to open?")
            return True
        result = self.automation.open_Website(website_name)
        print(f"\nJarvis: {result}")
        return True

    def _handle_close_application(self, user_input: str, language: str) -> bool:
        if not self.automation:
            print("Automation not available")
            return True
        app_name = self._extract_app_name(user_input)
        if not app_name:
            print("Which app do you want to close?")
            return True
        result = self.automation.close_application(app_name)
        print(f"\nJarvis: {result}")
        return True

    def _handle_play_music(self, language: str) -> bool:
        if not self.automation:
            print("Automation not available")
            return True
        result = self.automation.play_music()
        self._speak_response(result)
        return True

    def _handle_play_spotify_song(self, user_input: str, language: str) -> bool:
        if not self.automation:
            print("Automation not available")
            return True
        song_name = self._extract_song_name(user_input)
        if not song_name:
            self._speak_response("Which song do you want to play?")
            return True
        result = self.automation.play_spotify(song_name)
        self._speak_response(result)
        return True

    def _handle_get_news(self, user_input: str, language: str) -> bool:
        if not self.automation:
            print("Automation not available")
            return True
        news_query = ""
        if self.hindi_processor:
            parsed = self.hindi_processor.parse(user_input)
            news_query = parsed.news_query or "latest"
        self._speak_response(f"Fetching {news_query} news.")
        result = self.automation.get_news(news_query)
        print(f"\nNews:\n{result}")
        self._speak_response("Here are the latest headlines.")
        return True

    def _handle_google_search(self, user_input: str, language: str) -> bool:
        if not self.automation:
            print("Automation not available")
            return True
        search_query = self._extract_search_query(user_input)
        if not search_query:
            self._speak_response("What do you want to search for?")
            return True
        self._speak_response(f"Searching for {search_query}.")
        result = self.automation.search_google(search_query)
        print(f"\nGoogle Search Results:\n{result}")
        self._speak_response("Here are the search results.")
        return True

    def _handle_shutdown(self, language: str) -> bool:
        if not self.automation:
            self._speak_response("Automation not available")
            return True
        result = self.automation.shutdown()
        self._speak_response(result)
        return True

    def _handle_restart(self, language: str) -> bool:
        if not self.automation:
            self._speak_response("Automation not available")
            return True
        result = self.automation.restart()
        self._speak_response(result)
        return True

    def _handle_sleep(self, language: str) -> bool:
        if not self.automation:
            self._speak_response("Automation not available")
            return True
        result = self.automation.sleep()
        self._speak_response(result)
        return True

    def _handle_lock(self, language: str) -> bool:
        if not self.automation:
            self._speak_response("Automation not available")
            return True
        result = self.automation.lock()
        self._speak_response(result)
        return True

    def _handle_cancel_shutdown(self, language: str) -> bool:
        if not self.automation:
            self._speak_response("Automation not available")
            return True
        result = self.automation.cancel_shutdown()
        self._speak_response(result)
        return True

    # ---- Extraction helpers ----

    def _extract_app_name(self, text: str) -> str:
        if self.hindi_processor:
            parsed = self.hindi_processor.parse(text)
            if parsed.app_name:
                return parsed.app_name
        text_lower = text.lower()
        for prefix in ["open", "launch", "start", "run", "close", "stop", "band", "karo", "kholo", "shuru", "chalu"]:
            text_lower = text_lower.replace(prefix, "")
        text_lower = text_lower.strip()
        for suffix in ["app", "application", "software", "karo", "kar", "do"]:
            if text_lower.endswith(suffix):
                text_lower = text_lower[:-len(suffix)].strip()
        return text_lower

    def _extract_website_name(self, text: str) -> str:
        if self.hindi_processor:
            parsed = self.hindi_processor.parse(text)
            if parsed.website_name:
                return parsed.website_name
        text_lower = text.lower()
        for prefix in ["open", "visit", "go to", "browse", "karo", "dekho"]:
            text_lower = text_lower.replace(prefix, "")
        text_lower = text_lower.strip()
        for suffix in ["website", "site", "page", "karo", "kar", "do"]:
            if text_lower.endswith(suffix):
                text_lower = text_lower[:-len(suffix)].strip()
        return text_lower

    def _extract_song_name(self, text: str) -> str:
        if self.hindi_processor:
            parsed = self.hindi_processor.parse(text)
            if parsed.song_name:
                return parsed.song_name
        text_lower = text.lower()
        for prefix in ["play", "play on spotify", "spotify pe", "spotify par", "bajao", "chalao"]:
            text_lower = text_lower.replace(prefix, "")
        text_lower = text_lower.strip()
        for suffix in ["on spotify", "spotify", "karo", "kar", "do"]:
            if text_lower.endswith(suffix):
                text_lower = text_lower[:-len(suffix)].strip()
        return text_lower

    def _extract_search_query(self, text: str) -> str:
        if self.hindi_processor:
            parsed = self.hindi_processor.parse(text)
            if parsed.search_query:
                return parsed.search_query
        text_lower = text.lower()
        for prefix in ["google", "search", "search on google", "google pe", "google par", "karo"]:
            text_lower = text_lower.replace(prefix, "")
        text_lower = text_lower.strip()
        return text_lower

    # ---- Status, History, Help ----

    def _show_help(self):
        if self.response_generator:
            print(self.response_generator.help_message())
        else:
            help_text = """
JARVIS-X COMMANDS (5-Layer Architecture)

Engineering Commands:
  build hospital management system
  create ecommerce platform
  banao hospital management system

Status Commands:
  status / kya hua / progress

History Commands:
  history / pehle ka project

General Chat:
  Any question in English, Hindi, or Hinglish

Voice Mode:
  Say "Jarvis" to wake up

Music:
  play shape of you on spotify

News:
  news / latest news / khabar

Google Search:
  google python tutorials

Exit:
  exit / quit / bye / alvida
"""
            print(help_text)

    def _show_status(self):
        print(f"\nSystem Status (5-Layer Architecture):")
        print(f"  Layer 1 - Input: {'Ready' if self.input_layer else 'Offline'}")
        print(f"  Layer 2 - Brain: {'Ready' if self.brain else 'Offline'}")
        print(f"  Layer 3 - Planner: {'Ready' if self.planner else 'Offline'}")
        print(f"  Layer 4 - Memory: {'Ready' if self.memory else 'Offline'}")
        print(f"  Layer 5 - Tools: {'Ready' if self.tool_selector else 'Offline'}")
        if self.last_project:
            print(f"  Current Project: {self.last_project}")

    def _show_history(self):
        try:
            if self.memory:
                memories = self.memory.search("", limit=10) if hasattr(self.memory, 'search') else []
                if memories:
                    print("\nRecent Memories:")
                    for i, mem in enumerate(memories, 1):
                        content = mem.get("content", str(mem))[:60]
                        print(f"  {i}. {content}")
                    return
            print("\nNo history yet")
        except Exception:
            print("\nNo history yet")

    def _speak_response(self, text: str):
        if self.voice and self.voice.is_available():
            try:
                self.voice.speak(text)
                return
            except Exception:
                pass
        print(f"\nJarvis: {text}")

    # ---- Mode Selection ----

    def run(self):
        welcome_msg = self.response_generator.generate("welcome", language="english") if self.response_generator else """
JARVIS-X - Autonomous Software Engineer v2.0
5-Layer Architecture: Input | Brain | Planning | Memory | Tools

Hindi English Hinglish Supported
Type 'help' for commands or 'exit' to quit
"""
        print(welcome_msg)
        print()

        mode = self._select_mode()
        if mode == "voice":
            self._run_voice_mode()
        elif mode == "wake":
            self._run_wake_word_mode()
        else:
            self._run_text_mode()

    def _select_mode(self) -> str:
        voice_available = self.voice is not None and self.voice.is_available()
        print("Select Mode:")
        print("  1. Text Mode")
        if voice_available:
            print("  2. Voice Mode")
            print("  3. Wake Word Mode")
        else:
            print("  2. Voice Mode (unavailable)")
            print("  3. Wake Word Mode (unavailable)")

        while True:
            try:
                choice = input("\nEnter choice (1/2/3): ").strip()
                if choice == "1":
                    return "text"
                elif choice == "2" and voice_available:
                    return "voice"
                elif choice == "3" and voice_available:
                    return "wake"
                else:
                    print("Please enter a valid choice")
            except KeyboardInterrupt:
                return "text"

    def _run_text_mode(self):
        self.running = True
        while self.running:
            try:
                user_input = input("Jarvis > ").strip()
                if not user_input:
                    continue
                if not self.handle_command(user_input):
                    break
            except KeyboardInterrupt:
                print("\nAlvida! Goodbye!")
                break
            except Exception as e:
                Logger.error(f"CLI Error: {e}")
                print(f"Error: {e}")
        self.running = False

    def _run_voice_mode(self):
        """Run in voice command mode with professional architecture."""
        if not self.voice or not self.voice.is_available():
            print("Voice system not available. Switching to text mode.")
            self._run_text_mode()
            return

        self.running = True
        try:
            self.voice.speak("Voice mode activated. How can I help you?")
        except Exception:
            print("Voice mode activated. How can I help you?")

        while self.running:
            try:
                print("\nListening...")
                user_input = self.voice.listen(timeout=10)
                if not user_input:
                    print("Didn't hear anything. Try again or type.")
                    continue
                print(f"You: {user_input}")
                if "text mode" in user_input.lower():
                    try:
                        self.voice.speak("Switching to text mode.")
                    except Exception:
                        pass
                    self._run_text_mode()
                    return
                if "exit" in user_input.lower() or "quit" in user_input.lower():
                    try:
                        self.voice.speak("Goodbye sir.")
                    except Exception:
                        pass
                    break
                response = self.handle_command(user_input)
                if response is False:
                    break
            except KeyboardInterrupt:
                print("\nSwitching to text mode...")
                self._run_text_mode()
                break
            except Exception as e:
                Logger.error(f"Voice Error: {e}")
                print(f"Error: {e}")
        self.running = False

    def _run_wake_word_mode(self):
        """Run in wake word detection mode with professional architecture."""
        if not self.voice or not self.voice.is_available():
            print("Voice system not available. Switching to text mode.")
            self._run_text_mode()
            return

        self.running = True

        def on_wake(text):
            print(f"\nWake word detected! Heard: {text}")
            try:
                self.voice.speak("Yes sir?")
            except Exception:
                print("Yes sir?")

        def on_command(command):
            print(f"You: {command}")
            self.handle_command(command)

        self.voice.set_wake_callback(on_wake)
        self.voice.set_command_callback(on_command)
        try:
            self.voice.speak("Wake word mode activated. Say Jarvis to wake me up.")
        except Exception:
            print("Wake word mode activated. Say Jarvis to wake me up.")
        print("\nListening for 'Jarvis'...")

        thread = self.voice.start_wake_word_listening()

        while self.running:
            try:
                user_input = input("").strip()
                if user_input:
                    if user_input.lower() in ["exit", "quit"]:
                        self.voice.stop_wake_word_listening()
                        try:
                            self.voice.speak("Goodbye sir.")
                        except Exception:
                            pass
                        break
                    self.handle_command(user_input)
            except KeyboardInterrupt:
                self.voice.stop_wake_word_listening()
                break
            except Exception as e:
                Logger.error(f"Wake word mode error: {e}")

        self.running = False

def main():
    try:
        cli = JarvisCLI()
        cli.run()
    except Exception as e:
        Logger.error(f"Fatal error: {e}")
        print(f"\nFatal error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()


