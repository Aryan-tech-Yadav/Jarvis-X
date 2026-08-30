# ADR-001: Separate Cognitive and Execution Operating Systems

- Status: Accepted
- Date: 2026-08-27

## Problem

Jarvis-X needs to reason, plan, choose strategies, and learn while continuing
to execute workflows, schedule tasks, manage agents, and invoke tools. Tightly
coupling those responsibilities would make model/provider changes and new
cognitive modules risky.

## Decision

Jarvis-X is split into three boundaries:

- BrainManager coordinates conversation and delegates work.
- Cognitive Operating System (COS) normalizes perception, attention, goals,
  reasoning, planning, decisions, reflection, and imagination.
- Engineering Operating System (EOS) executes approved work through workflow
  graphs, schedulers, agents, tools, workspaces, and reports.

COS may produce typed, serializable decisions and plans. EOS receives those
artifacts through injected interfaces and remains responsible for execution
and operational policy. COS must not directly mutate project files or invoke
execution tools.

## Alternatives Considered

1. Put cognitive behavior directly in BrainManager.
   - Rejected: creates a large composition-root dependency surface.
2. Let COS call EOS internals directly.
   - Rejected: prevents replacing execution, scheduling, or agent providers.
3. Keep planning and execution in one pipeline.
   - Rejected: makes simulation, approval, replay, and dry-run behavior harder
     to guarantee.

## Trade-offs

- Additional typed adapters and serialization are required.
- Some simple flows cross one extra interface boundary.
- The separation enables independent testing, provider replacement, safety
  gates, and deterministic benchmark comparisons.

## Impact

New cognitive modules belong under `app/cognition/` or dedicated intelligence
packages and expose replaceable contracts. Execution changes belong under
`app/eos/`, `app/workflow/`, or agent/tool packages. BrainManager should only
compose these services; new behavior should not be implemented there.

## Validation

The separation is covered by focused cognitive tests and existing EOS,
reasoning, agent, and orchestration regression suites.
