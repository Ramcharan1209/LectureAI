@echo off
cd /d "%~dp0"
where py >nul 2>nul
if %errorlevel%==0 (set PYTHON=py -3) else (set PYTHON=python)
if not exist .venv\Scripts\python.exe (
  %PYTHON% -m venv .venv
  if errorlevel 1 goto failed
)
rem Some Python distributions create a venv without pip. Bootstrap it if needed.
.venv\Scripts\python.exe -m pip --version >nul 2>nul
if errorlevel 1 (
  .venv\Scripts\python.exe -m ensurepip --upgrade
  if errorlevel 1 goto failed
)
.venv\Scripts\python.exe -m pip install --upgrade pip
if errorlevel 1 goto failed
.venv\Scripts\python.exe -m pip install -r requirements.txt
if errorlevel 1 goto failed
if not exist .env copy .env.example .env >nul
if not exist .env (echo Could not create .env. & goto failed)
echo Starting LectureAI. Keep this window open.
.venv\Scripts\python.exe -m streamlit run app.py
goto end
:failed
echo Setup failed. Install Python 3.10 or newer and check your internet connection.
pause
:end
