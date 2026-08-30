from app.self_improvement.scanner.project_scanner import ProjectScanner

scanner = ProjectScanner(root='.')
result = scanner.scan()

summary = result.report.summary
print('=' * 60)
print('JARVIS-X PROJECT SCANNER v1.0')
print('=' * 60)
print(f"Files:        {summary['files']}")
print(f"Classes:      {summary['classes']}")
print(f"Functions:    {summary['functions']}")
print(f"Imports:      {summary['imports']}")
print(f"Dead Files:   {summary['dead_files']}")
print(f"Circular Deps:{summary['circular_dependencies']}")
print(f"Complexity:   {summary['complexity_score']}")
print(f"Duration:     {result.scan_duration:.2f}s")
print('=' * 60)
print("Reports:")
for fmt, path in result.report_paths.items():
    print(f"  {fmt}: {path}")
print('=' * 60)
print('SCAN COMPLETE')
