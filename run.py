#!/usr/bin/env python3
"""
Simple script to run the Trade Opportunities API
"""

import os
import sys
import subprocess
from pathlib import Path

def check_requirements():
    """Check if all requirements are met."""
    print("🔍 Checking requirements...")
    
    # Check Python version
    if sys.version_info < (3, 8):
        print("❌ Python 3.8 or higher is required")
        return False
    
    print(f"✅ Python {sys.version.split()[0]} detected")
    
    # Check if .env file exists
    if not Path(".env").exists():
        print("❌ .env file not found")
        print("📝 Please create a .env file with the required configuration")
        return False
    
    print("✅ .env file found")
    
    # Check if requirements.txt exists
    if not Path("requirements.txt").exists():
        print("❌ requirements.txt not found")
        return False
    
    print("✅ requirements.txt found")
    
    return True

def install_dependencies():
    """Install required dependencies."""
    print("\n📦 Installing dependencies...")
    
    try:
        subprocess.check_call([
            sys.executable, "-m", "pip", "install", "-r", "requirements.txt"
        ])
        print("✅ Dependencies installed successfully")
        return True
    except subprocess.CalledProcessError:
        print("❌ Failed to install dependencies")
        return False

def run_server():
    """Start the FastAPI server."""
    print("\n🚀 Starting Trade Opportunities API server...")
    print("📋 Server will be available at: http://localhost:8000")
    print("📖 API Documentation: http://localhost:8000/docs")
    print("🛑 Press Ctrl+C to stop the server")
    print("-" * 50)
    
    try:
        subprocess.run([
            sys.executable, "-m", "uvicorn", 
            "app.main:app", 
            "--reload", 
            "--host", "0.0.0.0", 
            "--port", "8000"
        ])
    except KeyboardInterrupt:
        print("\n👋 Server stopped by user")
    except Exception as e:
        print(f"\n❌ Error starting server: {e}")

def main():
    """Main function."""
    print("🏢 Trade Opportunities API - Setup & Run Script")
    print("=" * 50)
    
    # Check requirements
    if not check_requirements():
        print("\n❌ Requirements check failed. Please fix the issues above.")
        sys.exit(1)
    
    # Ask user if they want to install dependencies
    install_deps = input("\n❓ Install/update dependencies? (y/n): ").lower().strip()
    if install_deps in ['y', 'yes', '']:
        if not install_dependencies():
            print("\n❌ Failed to install dependencies. Please check the error above.")
            sys.exit(1)
    
    # Run the server
    run_server()

if __name__ == "__main__":
    main()