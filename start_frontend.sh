#!/bin/bash

echo "🚀 Starting Excel Visualizer Frontend..."

# Check if node_modules exists, if not install dependencies
if [ ! -d "node_modules" ]; then
    echo "📦 Installing Node.js dependencies..."
    npm install
    if [ $? -ne 0 ]; then
        echo "❌ Failed to install Node.js dependencies"
        exit 1
    fi
    echo "✅ Node.js dependencies installed successfully!"
fi

# Start the React development server
echo "🌐 Starting React development server..."
npm start