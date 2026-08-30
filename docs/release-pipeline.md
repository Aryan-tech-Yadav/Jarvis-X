# Release pipeline

Run a release candidate with:

```powershell
python -m app.release.cli release --output artifacts/releases --version 0.1.0-alpha
```

The pipeline creates a selected output directory and writes:

- `release-manifest.json` — machine-readable gates, benchmark output, and artifacts.
- `release-report.md` — concise human-readable summary.

The passing gates are:

1. The repository unit suite.
2. The 20-project Golden Benchmark preflight.
3. Required release documentation.
4. A lightweight static scan of shipped `app/` source for hardcoded credentials
   and direct `eval`/`exec` calls.

The pipeline returns a blocked release whenever any gate fails, but it still
writes the manifest and report to make failures debuggable. It never builds a
ZIP unless every gate passes; add `--package` to request a package explicitly.

The security gate deliberately limits this release check to the shipped
application package. Tests can contain controlled unsafe fixtures; run
`SecurityGate().scan(path)` directly when a broader audit is required.
