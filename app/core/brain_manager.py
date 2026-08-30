from app.automation.automation_manager import AutomationManager
from app.core.logger import Logger
from app.core.intent_router import IntentRouter
from app.core.task_manager import TaskManager
from app.core.entity_extractor import EntityExtractor
from app.voice.voice_manager import VoiceManager
from app.ai.ai_manager import AIManager
from app.core.command_parser import CommandParser
from app.ai.planner import TaskPlanner
from app.safety.confirmation_manager import ConfirmationManager
from app.core.action_queue import ActionQueue
from app.core.language_processor import LanguageProcessor
from app.core.context_manager import ContextManager
from app.memory.memory_manager import MemoryManager
from app.brain.brain_pipeline import BrainPipeline
from app.engineering.workflow import EngineeringWorkflow, EngineeringWorkflowResult
from app.engineering.autonomous_executor import AutonomousExecutor
from app.engineering.execution_monitor import ExecutionMonitor

class BrainManager:
    
    def __init__(self):
        self.automation = AutomationManager()
        self.router = IntentRouter()
        self.task_manager = TaskManager()
        self.extractor = EntityExtractor()
        self.voice = VoiceManager()
        self.ai = AIManager()
        self.parser = CommandParser()
        self.planner = TaskPlanner()
        self.confirmation = ConfirmationManager()
        self.queue = ActionQueue()
        self.language = LanguageProcessor()
        self.context = ContextManager()
        self.memory = MemoryManager()
        self.engineering_pipeline = BrainPipeline()
        self.engineering_workflow = EngineeringWorkflow()
        self.autonomous_executor = AutonomousExecutor()
        self.execution_monitor = ExecutionMonitor()
        
        Logger.info("Brain Manager Initialized")
        
    def process(self, user_input):

        # ===============================
        # Clean Input
        # ===============================
        user_input = self.language.clean(user_input)

        self.memory.add_message("user", user_input)

        Logger.info(f"Clean Input : {user_input}")

        # ===============================
        # Planning
        # ===============================
        plan = self.planner.create_plan(user_input)

        Logger.info("Execution Plan")

        for step in plan:
            Logger.info(step)

        # ===============================
        # Parse Commands
        # ===============================
        commands = self.parser.split_commands(user_input)

        if not commands:
            commands = [user_input]

        Logger.info(f"Commands : {commands}")
        Logger.info(f"Total Commands : {len(commands)}")

        responses = []

        # ===============================
        # Execute Commands
        # ===============================
        for command in commands:

            Logger.info(f"Processing : {command}")

            # ---------------------------
            # Intent Detection
            # ---------------------------
            result = self.router.detect_intent(command)

            intent = result.get("intent", "UNKNOWN")
            confidence = result.get("confidence", 1.0)
            source = result.get("source", "RULE")

            Logger.info(f"Intent      : {intent}")
            Logger.info(f"Confidence  : {confidence}")
            Logger.info(f"Source      : {source}")

            # ---------------------------
            # Entity Extraction
            # ---------------------------
            entity = None

            if intent in (
                "OPEN_APPLICATION",
                "CLOSE_APPLICATION",
                "WEB_SEARCH",
                "CREATE_CODE",
            ):
                entity = self.extractor.extract(command)

            Logger.info(f"Entity : {entity}")

            # ---------------------------
            # Context Resolution
            # ---------------------------
            if entity == "it":

                entity = self.context.get_last_app()

                Logger.info(f"Resolved Context : {entity}")

            # ---------------------------
            # Safety Check
            # ---------------------------
            if self.confirmation.needs_confirmation(intent):

                if not self.confirmation.confirm():

                    responses.append("Action Cancelled.")
                    continue

            # ---------------------------
            # Execute
            # ---------------------------
            try:

                if intent == "CREATE_CODE":

                    Logger.info("Engineering goal detected - running autonomous pipeline")
                    response = self._execute_engineering_goal(command)

                elif intent in ("UNKNOWN", "CHAT"):

                    Logger.info("Using AI")

                    response = self.ai.ask(command)

                else:

                    response = self.task_manager.execute(
                        intent,
                        entity,
                        command
                    )

                    if intent == "OPEN_APPLICATION" and entity:
                        self.context.set_last_app(entity)

            except Exception as e:

                Logger.error(str(e))

                if intent in ("UNKNOWN", "CHAT"):

                    response = (
                        "Sorry Sir, my AI engine is currently unavailable.\n"
                        "Please check the LLM server."
                    )

                else:

                    response = (
                        "Sorry Sir, I couldn't complete that task."
                    )

            # ---------------------------
            # Store Response
            # ---------------------------
            responses.append(response)

        # ===============================
        # Final Response
        # ===============================
        response_text = "\n".join(responses)

        self.memory.add_message(
            "assistant",
            response_text
        )

        return response_text
    
    
    def prepare_engineering_goal(self, goal):
        """Analyze a software goal before handing it to an executor."""
        return self.engineering_pipeline.prepare(goal)

    def prepare_engineering_goal_result(self, goal):
        """Return normalized engineering result."""
        return self.engineering_pipeline.prepare_result(goal)

    def _execute_engineering_goal(self, goal: str) -> str:
        """Execute a full engineering goal through the autonomous pipeline.

        Flow:
          1. EngineeringWorkflow - analyze, design, plan
          2. AutonomousExecutor - generate, QA, refine
          3. Return summary report
        """
        import uuid

        execution_id = uuid.uuid4().hex[:12]
        monitor = self.execution_monitor.start(execution_id, goal)

        try:
            # Phase 1: Engineering Brain
            monitor.stage_start("engineering_brain", {"goal": goal})
            workflow_result = self.engineering_workflow.run(goal)
            monitor.stage_complete(
                "engineering_brain",
                message=f"Domain: {workflow_result.analysis.get('domain') if workflow_result.analysis else 'unknown'}",
                metadata={"success": workflow_result.success},
            )

            if not workflow_result.success:
                return (
                    f"Engineering analysis failed for: {goal}\n"
                    f"Please provide more details about the project."
                )

            # Phase 2: Autonomous Execution
            monitor.stage_start("autonomous_execution", {"project": workflow_result.analysis.get("project_name")})
            exec_result = self.autonomous_executor.execute(workflow_result)
            monitor.stage_complete(
                "autonomous_execution",
                message=f"Generated {exec_result.metrics.get('files_generated', 0)} files",
                metadata={"success": exec_result.success},
            )

            # Phase 3: Finalize
            monitor.stage_start("finalization")
            project_path = exec_result.data.get("project_path", "")
            metrics = exec_result.metrics

            report_lines = [
                f"Engineering Report: {workflow_result.analysis.get('project_name', goal)}",
                f"Project Path: {project_path}",
                f"Files Generated: {metrics.get('files_generated', 0)}",
                f"Tests Passed: {metrics.get('tests_passed', 0)}",
                f"Tests Failed: {metrics.get('tests_failed', 0)}",
                f"Errors Fixed: {metrics.get('errors_fixed', 0)}",
                f"Quality Score: {metrics.get('quality_score', 0):.1f}%",
                f"Duration: {metrics.get('duration_seconds', 0):.1f}s",
            ]

            if exec_result.success:
                report_lines.insert(1, "Status: COMPLETED SUCCESSFULLY")
            else:
                report_lines.insert(1, "Status: COMPLETED WITH ISSUES")
                if exec_result.errors:
                    report_lines.append(f"Issues: {'; '.join(exec_result.errors[:3])}")

            monitor.stage_complete("finalization")
            monitor.complete(exec_result.success, "Engineering goal executed")

            return "\n".join(report_lines)

        except Exception as exc:
            Logger.error(f"[BrainManager] Engineering execution failed: {exc}")
            monitor.complete(False, str(exc))
            return f"Engineering execution failed: {exc}"

    def listen(self):
        return self.voice.listen()

    def speak(self, text):
        self.voice.speak(text)
                    

