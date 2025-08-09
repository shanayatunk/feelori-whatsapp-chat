@echo OFF
echo --- Starting server in TEST mode ---
set ENVIRONMENT=test
python -m uvicorn app.server:app --host 127.0.0.1 --port 8000