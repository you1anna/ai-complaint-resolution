#!/bin/bash
# Quick start script for AI Complaint Resolution System

echo "===================================================================="
echo "  AI-Powered Complaint Resolution - Quick Start"
echo "===================================================================="
echo ""

# Check if .env exists
if [ ! -f .env ]; then
    echo "❌ .env file not found!"
    echo "Creating from .env.example..."
    cp .env.example .env
    echo ""
    echo "⚠️  IMPORTANT: Edit .env and add your ANTHROPIC_API_KEY"
    echo "   Then run this script again."
    exit 1
fi

# Check if API key is set
if grep -q "your_api_key_here" .env; then
    echo "❌ ANTHROPIC_API_KEY not configured in .env"
    echo "   Please edit .env and add your API key, then run this script again."
    exit 1
fi

echo "✅ Environment configured"
echo ""

# Check if virtual environment exists
if [ ! -d "venv" ]; then
    echo "📦 Creating virtual environment..."
    python3 -m venv venv
    echo "✅ Virtual environment created"
fi

echo "📦 Activating virtual environment..."
source venv/bin/activate

echo "📦 Installing dependencies..."
pip install -q -r requirements.txt

echo "✅ Dependencies installed"
echo ""

# Check if database exists
if [ ! -f "complaint_resolution.db" ]; then
    echo "💾 Seeding database with dummy data..."
    python scripts/seed_data.py
    echo "✅ Database seeded"
else
    echo "ℹ️  Database already exists (skipping seed)"
fi

echo ""
echo "===================================================================="
echo "  Setup Complete! 🎉"
echo "===================================================================="
echo ""
echo "Try these commands:"
echo ""
echo "  # List all complaints"
echo "  python scripts/process_complaint.py --list"
echo ""
echo "  # Process a complaint"
echo "  python scripts/process_complaint.py COMP-2024-001"
echo ""
echo "  # Review complaints"
echo "  python scripts/review_complaint.py --list"
echo ""
echo "===================================================================="
