from app.agent_loop.observation_manager import ObservationManager
from app.agent_loop.thought_generator import ThoughtGenerator
from app.reasoning.action_executor import ActionExecutor


class AgentLoop:
    def __init__(self, thinker, executor=None, observer=None, max_iterations=15, max_retries=2):
        self.thinker = thinker
        self.executor = executor or ActionExecutor()
        self.observer = observer or ObservationManager()
        self.max_iterations = max(1, max_iterations)
        self.max_retries = max(0, max_retries)

    def run(self, goal):
        from app.agent_loop.agent_state import AgentState
        state = AgentState(goal=goal)
        retries = 0
        while not state.finished and state.current_step < self.max_iterations:
            state.next_step()
            try:
                thought = self.thinker.generate(state) if hasattr(self.thinker, "generate") else self.thinker(state)
                action = thought if hasattr(thought, "tool") else thought["action"]
                observation = self.observer.normalize(self.executor.execute(action), action.tool, action.action)
            except Exception as error:
                thought = {"thought": "Execution failed", "error": str(error)}
                action = {"action": "", "tool": ""}
                observation = self.observer.normalize({"success": False, "error": str(error)})
            state.add_observation(getattr(thought, "to_dict", lambda: thought)(),
                                  getattr(action, "to_dict", lambda: action)(), observation.to_dict())
            if observation.success and getattr(thought, "finished", False):
                state.finished = True
            elif not observation.success:
                if retries < self.max_retries:
                    retries += 1
                    continue
                break
        return {"success": state.finished, "message": "Agent finished" if state.finished else "Agent stopped", "state": state.to_dict()}