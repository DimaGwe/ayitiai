#!/bin/bash
# AYITI AI Setup Script
# Sets up the development environment and initializes knowledge bases

set -e

echo "========================================="
echo "AYITI AI - Setup Script"
echo "========================================="

# Check if Python is installed
if ! command -v python3 &> /dev/null; then
    echo "Error: Python 3 is not installed"
    exit 1
fi

echo "✓ Python 3 found"

# Create virtual environment
if [ ! -d "ayiti_env" ]; then
    echo "Creating virtual environment..."
    python3 -m venv ayiti_env
    echo "✓ Virtual environment created"
else
    echo "✓ Virtual environment already exists"
fi

# Activate virtual environment
echo "Activating virtual environment..."
source ayiti_env/bin/activate

# Upgrade pip
echo "Upgrading pip..."
pip install --upgrade pip

# Install dependencies
echo "Installing dependencies..."
pip install -r requirements.txt

echo "✓ Dependencies installed"

# Create .env file if it doesn't exist
if [ ! -f ".env" ]; then
    echo "Creating .env file from template..."
    cp .env.example .env
    echo "✓ .env file created"
    echo "⚠️  Please edit .env and add your API keys"
else
    echo "✓ .env file already exists"
fi

# Create necessary directories
echo "Creating data directories..."
mkdir -p data/raw_documents
mkdir -p data/processed
mkdir -p data/vector_db
mkdir -p logs

echo "✓ Data directories created"

# Initialize agriculture knowledge base
echo ""
echo "========================================="
echo "Initializing Agriculture Knowledge Base"
echo "========================================="

python3 scripts/init_agriculture_kb.py

if [ $? -eq 0 ]; then
    echo "✓ Agriculture knowledge base initialized"
else
    echo "⚠️  Agriculture knowledge base initialization failed"
fi

echo ""
echo "========================================="
echo "Setup Complete!"
echo "========================================="
echo ""
echo "Next steps:"
echo "1. Edit .env file and add your DeepSeek API key"
echo "2. Activate virtual environment: source ayiti_env/bin/activate"
echo "3. Run the server: python -m uvicorn api.app:app --reload"
echo "4. Access API at: http://localhost:8000"
echo "5. View API docs at: http://localhost:8000/docs"
echo ""
