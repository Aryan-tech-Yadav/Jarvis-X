from app.core.logger import Logger
from app.memory.memory_manager import MemoryManager
from app.planning.progress_manager import ProgressManager
from app.reflection.reflection_agent import ReflectionAgent
from app.agent.self_critic import SelfCritic


class PlanExecutor:

    def __init__(self, manager, memory=None, progress=None, reflection=None, critic=None):
        self.manager = manager
        self.memory = memory or MemoryManager()
        self.progress = progress or ProgressManager(self.memory)
        self.reflection = reflection or ReflectionAgent()
        self.critic = critic or SelfCritic()

    def execute(self, base_path, plan, resume=False):
        if hasattr(base_path, "steps") and isinstance(plan, str):
            base_path, plan = plan, base_path

        steps = plan.steps if hasattr(plan, "steps") else plan.get("steps", [])
        goal = plan.goal if hasattr(plan, "goal") else plan.get("goal", "")
        results = []
        progress = self.progress.resume(goal, steps, base_path) if resume else self.progress.start(goal, steps, base_path)

        for index, step in enumerate(steps, start=1):
            if step in progress.get("completed", []):
                Logger.info(f"Skipping completed plan step: {step}")
                continue

            Logger.info(f"Plan step {index}/{len(steps)}: {step}")
            self.manager.analyze_project(base_path)
            success, result = self.manager.modify_project(base_path, step)
            step_result = {
                "step": step,
                "success": False,
                "result": result,
            }
            results.append(step_result)
            self.memory.add_message(
                "assistant",
                f"Plan step {index}/{len(steps)}: {step} ({'completed' if success else 'failed'})",
            )

            if not success:
                progress = self.progress.fail_step(step, result)
                Logger.error(f"Plan stopped at step {index}: {step}")
                break

            summary = self.manager.analyze_project(base_path)
            if summary.get("errors"):
                step_result["analysis_errors"] = summary["errors"]
                Logger.warning(f"Analysis warnings after step {index}: {summary['errors']}")

            valid, validation_message = self.manager.validate_project(base_path)
            if not valid:
                repaired_files = self.manager.repair_project(
                    base_path,
                    validation_message,
                )
                step_result["repaired_files"] = repaired_files
                valid, validation_message = self.manager.validate_project(base_path)
            if not valid:
                step_result["validation_error"] = validation_message
                progress = self.progress.fail_step(step, validation_message)
                Logger.error(f"Plan validation failed at step {index}: {validation_message}")
                break

            reflection = self.reflection.reflect(
                step,
                summary,
                result,
                validation_message,
            )
            step_result["reflection"] = reflection
            self.memory.add_message("assistant", f"Reflection for {step}: {reflection}")
            if reflection["needs_repair"] or reflection["next_action"] == "repair":
                repaired_files = self.manager.repair_project(
                    base_path,
                    reflection["feedback"],
                )
                step_result["reflection_repaired_files"] = repaired_files
                if not repaired_files:
                    step_result["success"] = False
                    self.progress.fail_step(step, reflection["feedback"])
                    Logger.error(f"Reflection requested repair at step {index}: {reflection['feedback']}")
                    break
                valid, validation_message = self.manager.validate_project(base_path)
                if not valid:
                    step_result["success"] = False
                    self.progress.fail_step(step, validation_message)
                    step_result["validation_error"] = validation_message
                    break

            critic = self.critic.review(step, summary, validation_message)
            step_result["critic"] = critic
            self.memory.add_message("assistant", f"Self-critic for {step}: {critic}")
            if not critic["approved"]:
                repaired_files = self.manager.repair_project(
                    base_path,
                    "\n".join(critic["issues"]),
                )
                step_result["critic_repaired_files"] = repaired_files
                if not repaired_files:
                    self.progress.fail_step(step, critic["issues"])
                    Logger.error(f"Self-critic rejected step {index}: {critic['issues']}")
                    break
                valid, validation_message = self.manager.validate_project(base_path)
                if not valid:
                    self.progress.fail_step(step, validation_message)
                    step_result["validation_error"] = validation_message
                    break

            step_result["success"] = True
            progress = self.progress.complete_step(step)

        completed_steps = progress.get("completed", []) if progress else []
        completed = len(completed_steps)
        return {
            "goal": goal,
            "completed_steps": completed_steps,
            "completed_count": completed,
            "total_steps": len(steps),
            "success": completed == len(steps),
            "progress": progress,
            "steps": results,
        }

    def resume_execution(self, base_path, plan):
        return self.execute(base_path, plan, resume=True)
