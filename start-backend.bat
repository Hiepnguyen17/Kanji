@echo off
REM Run the API with the project virtual environment; no activation needed.
.\.venv\Scripts\python.exe -m uvicorn main:app --app-dir backend --host 127.0.0.1 --port 8010 --reload
