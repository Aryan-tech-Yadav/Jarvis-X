# Golden Benchmark Suite

The Golden Benchmark Suite is Jarvis-X's release-readiness catalog. It contains
twenty representative project briefs split into basic, intermediate, advanced,
and expert tiers. A benchmark preflight checks that the existing engineering
pipeline can consistently produce valid requirements, architecture, strategy,
simulation, and an optimized validation-and-test plan.

```python
from app.benchmark.golden_benchmark_runner import GoldenBenchmarkRunner

report = GoldenBenchmarkRunner().run()
assert report["quality_gate"]["passed"]
```

The default mode is non-destructive. It does not create projects, write source
files, or make model calls. To run a real execution benchmark, pass an explicit
`execution_handler`. The handler is invoked only for projects that passed
preflight and are approved by the governance policy. Payment-oriented projects
remain in `needs_approval` status unless policy changes deliberately authorize
them. A policy block does not lower the preflight quality-gate score; that score
measures whether Jarvis correctly prepared and routed the project for review.

`BenchmarkHistory(path)` can persist reports as JSON for release-over-release
comparison. Use a path under a chosen artifacts or data directory; no history
file is written unless a path is supplied.
