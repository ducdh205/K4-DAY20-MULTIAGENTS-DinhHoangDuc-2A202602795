### Human
Offline fixture: code. Create valid answer.json and summary.svg.

### Tool call: write_file
{"file_path": "workspace/report.py", "content": "import json\nfrom pathlib import Path\nfrom analysis import analyze\nlabel = \"Sales summary\"\nreport = analyze()\nPath(\"workspace/answer.json\").write_text(json.dumps(report), encoding=\"utf-8\")\nPath(\"workspace/summary.svg\").write_text(\n    f'<svg xmlns=\"http://www.w3.org/2000/svg\" width=\"300\" height=\"60\"><title>{label}</title>'\n    f'<rect width=\"{report[\"total_cents\"] / 10}\" height=\"20\" /></svg>', encoding=\"utf-8\")\nprint(json.dumps(report))\n"}

### Tool result
Updated file /workspace/report.py

### Tool call: execute
{"command": "python workspace/report.py"}

### Tool result
{"total_cents": 1375, "valid_rows": 3, "rejected_rows": 2, "sql_total_cents": 1375, "readonly": true}

[Command succeeded with exit code 0]

### Assistant
Fixture finished