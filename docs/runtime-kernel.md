# Runtime kernel

`JarvisRuntime` is the additive runtime composition root for predictable,
in-process engineering work. It does not replace the existing project manager,
agent orchestrator, or task queues.

```text
initialize → submit → priority/delay scheduler → execute → metrics/events
                                      └→ watchdog / bounded retry
                                      └→ snapshot / health
```

```python
from app.runtime import JarvisRuntime

runtime = JarvisRuntime()
runtime.initialize()
runtime.submit("validate", lambda payload: {"success": True, "checked": payload}, payload="workspace")
result = runtime.run_next()
assert result.success
print(runtime.health())
runtime.shutdown()
```

Jobs run only handlers supplied by the application. Snapshots record job state,
metrics, and resource signals but intentionally exclude handlers; restart and
recovery never execute saved work implicitly.
