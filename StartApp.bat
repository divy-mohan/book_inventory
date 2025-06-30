@echo off
REM Activate the virtual environment
call "%~dp0venv\Scripts\activate.bat"

REM Start Flask server (on port 5001)
start "" python serve_invoice.py --server.port 5001

REM Start Streamlit (on port 5000)
start "" streamlit run app.py --server.port 5000

REM Wait a moment for the server to start, then open browser
timeout /t 3 >nul
start http://localhost:5000/