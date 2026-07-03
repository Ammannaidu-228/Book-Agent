@echo off
REM Setup script for Lit-Pick backend on Windows

echo Installing dependencies...
pip install -r requirements.txt

echo Creating directories...
if not exist "chroma_db" mkdir chroma_db
if not exist "logs" mkdir logs

echo Initializing data...
python load_data.py

echo Setup complete! Run the backend with:
echo python main.py
echo or
echo uvicorn main:app --host 0.0.0.0 --port 5000 --reload
