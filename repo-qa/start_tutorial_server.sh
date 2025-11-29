#!/bin/bash

# start_tutorial_server.sh - Start the tutorial generation server

echo "🚀 Starting Tutorial Generation Server"
echo "======================================"

# Check if virtual environment exists
if [ ! -d "venv" ]; then
    echo "❌ Virtual environment not found. Please create one first:"
    echo "   python3 -m venv venv"
    echo "   source venv/bin/activate"
    echo "   pip3 install -r requirements.txt"
    exit 1
fi

# Check if .env file exists
if [ ! -f ".env" ]; then
    echo "⚠️  .env file not found. Creating template..."
    cat > .env << EOF
GITHUB_TOKEN=your_github_token_here
GEMINI_API_KEY=your_gemini_api_key_here
EOF
    echo "📝 Please edit .env file with your API keys before starting the server"
    exit 1
fi

# Check if API keys are set
if grep -q "your_github_token_here" .env || grep -q "your_gemini_api_key_here" .env; then
    echo "⚠️  Please set your API keys in the .env file:"
    echo "   GITHUB_TOKEN=your_actual_github_token"
    echo "   GEMINI_API_KEY=your_actual_gemini_api_key"
    exit 1
fi

echo "🔧 Activating virtual environment..."
source venv/bin/activate

echo "🌐 Starting FastAPI server..."
echo "📡 Server will be available at: http://localhost:8000"
echo "📚 API documentation at: http://localhost:8000/docs"
echo ""
echo "🎯 New Endpoints:"
echo "   POST /generate-tutorial - Generate structured tutorial with chapters"
echo "   GET  /tutorial - Get generated tutorial data"
echo "   GET  /tutorial/chapter/{number} - Get specific chapter"
echo ""
echo "Press Ctrl+C to stop the server"
echo ""

# Start the server
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
