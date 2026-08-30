# Changelog

## 2026-08-25

- Added the intelligent requirement and architecture analyst layer. It produces
  a single planning package with intent, clarification questions, stack
  comparison, database/API designs, complexity, cost, and existing risk data,
  then passes it into multi-agent execution.

## 2026-08-25

- Added persistent multi-project workspaces with isolated state, registry,
  snapshots/restore, recoverable archive/delete lifecycle actions, metrics,
  events, pipeline persistence, and workspace CLI commands.

## 2026-08-25

- Added the resumable autonomous generation pipeline with ordered stage
  registration, per-stage validation/metrics/events, rollback, and a final
  report. The safe default only performs governed preflight; project execution
  is an explicit composition with the multi-agent orchestrator.

## 2026-08-25

- Added the additive runtime kernel: lifecycle management, priority and delayed
  job scheduling, bounded retries, watchdog recovery, snapshots, resource
  signals, and health integration.

## 2026-08-25

- Added a governed engineering intake pipeline for requirements, architecture,
  risk analysis, baseline research, policy approval, and decision audit trails.
- Exposed engineering briefs through both `BrainManager` and
  `AutonomousBrainLayer` without changing legacy command execution.
- Fixed task retry semantics when retries are disabled and excluded virtual
  environments and generated directories from project search traversal.

## 2026-08-24

- Added the Phase 1 multi-agent collaboration workflow.
- Added Sprint 2 strategy selection, project simulation, cost analysis,
  execution-plan optimization, and deterministic benchmarks.
- Added a 20-project Golden Benchmark Suite and release quality gates.
- Added shared `ExecutionResult` and `JarvisContext` contracts at the planning
  and multi-agent execution boundaries.
- Added the release pipeline, artifact bundle, CLI entry point, and shipped
  source security gate.
