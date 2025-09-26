#!/usr/bin/env python3
"""
Quick Start Launcher for Multi-Region E-commerce System
Run this script to start everything at once!
"""

import subprocess
import sys
import os
from pathlib import Path

def main():
    """Main launcher function"""
    print("🚀 Multi-Region E-commerce Recommendation System")
    print("=" * 50)
    
    # Check if we're in the right directory
    if not os.path.exists("dashboard.py"):
        print("❌ Please run this script from the project root directory")
        sys.exit(1)
    
    print("🔧 Starting system...")
    print("   This will start:")
    print("   • Docker infrastructure (MinIO, PostgreSQL, Redis)")
    print("   • All regional APIs (US-West, EU-West, AP-South)")
    print("   • Streamlit Dashboard")
    print()
    
    # Check if launcher script exists
    launcher_path = Path("scripts/launchers/launch_complete_demo.py")
    if launcher_path.exists():
        print("✅ Found complete demo launcher")
        subprocess.run([sys.executable, str(launcher_path)])
    else:
        print("⚠️  Complete launcher not found, starting manually...")
        
        # Start Docker services
        print("🐳 Starting Docker services...")
        subprocess.run(["docker-compose", "up", "-d"])
        
        # Start dashboard
        print("📊 Starting Streamlit dashboard...")
        subprocess.run([sys.executable, "-m", "streamlit", "run", "dashboard.py", 
                       "--server.port", "8080", "--browser.gatherUsageStats", "false"])

if __name__ == "__main__":
    main()