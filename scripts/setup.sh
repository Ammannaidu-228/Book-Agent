#!/bin/bash
# Setup script for Lit-Pick backend

echo "Installing dependencies..."
pip install -r requirements.txt

echo "Creating directories..."
mkdir -p ./chroma_db
mkdir -p ./logs

echo "Initializing data..."
python load_data.py

echo "Setup complete! Run the backend with:"
echo "python main.py"
echo "or"
echo "uvicorn main:app --host 0.0.0.0 --port 5000 --reload"
