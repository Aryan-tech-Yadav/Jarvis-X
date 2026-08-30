"""Integration test for Multi-Agent Orchestrator."""

from unittest.mock import patch

from app.orchestrator.orchestrator import MultiAgentOrchestrator


def _fake_ai_ask(self, prompt):
    return '{"folders": ["backend", "frontend", "tests", "docs", "docker"], "architecture": {"pattern": "layered monolith", "layers": ["presentation", "application", "domain", "infrastructure"], "description": "Test architecture"}}'


if __name__ == "__main__":
    orchestrator = MultiAgentOrchestrator()
    
    with patch("app.ai.ai_manager.AIManager.ask", _fake_ai_ask):
        result = orchestrator.run("Build E-Commerce Platform")
    
    print("=" * 70)
    print("MULTI-AGENT ORCHESTRATOR RESULT")
    print("=" * 70)
    print(f"Workflow ID:    {result.workflow_id}")
    print(f"Success:        {result.success}")
    print(f"Duration:       {result.duration:.2f}s")
    print(f"Project Path:   {result.project_path}")
    print()
    print("AGENTS EXECUTED:")
    for agent in result.agents_executed:
        print(f"  - {agent}")
    print()
    print(f"Tasks Completed: {result.tasks_completed}")
    print(f"Tasks Failed:    {result.tasks_failed}")
    print(f"Issues Repaired: {result.issues_repaired}")
    if result.review_score is not None:
        print(f"Review Score:    {result.review_score}")
    if result.review_issues:
        print(f"Review Issues:   {len(result.review_issues)}")
    print()
    print("LOGS:")
    for log in result.logs[:10]:
        print(f"  {log}")
    if len(result.logs) > 10:
        print(f"  ... and {len(result.logs) - 10} more")
    print("=" * 70)
    
    if result.success:
        print("SPRINT 8 INTEGRATION TEST: PASSED")
    else:
        print(f"SPRINT 8 INTEGRATION TEST: FAILED - {result.error}")
