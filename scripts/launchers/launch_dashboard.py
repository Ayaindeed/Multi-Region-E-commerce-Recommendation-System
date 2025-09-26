"""
Launch the Streamlit Dashboard for Multi-Region E-commerce Recommendation System
"""

import subprocess
import sys
import os
import time
import webbrowser

def launch_dashboard():
    """Launch the Streamlit dashboard"""
    print("🚀 Starting Multi-Region Recommendation System Dashboard...")
    
    # Check if streamlit is installed
    try:
        import streamlit
        print(f"✅ Streamlit {streamlit.__version__} found")
    except ImportError:
        print("❌ Streamlit not found. Please install with: pip install streamlit")
        return
    
    # Get the current directory
    current_dir = os.path.dirname(os.path.abspath(__file__))
    dashboard_path = os.path.join(current_dir, "dashboard.py")
    
    if not os.path.exists(dashboard_path):
        print(f"❌ Dashboard file not found: {dashboard_path}")
        return
    
    print(f"📍 Dashboard path: {dashboard_path}")
    print("🌐 Starting dashboard server...")
    print("📊 Opening dashboard in your browser...")
    
    # Launch Streamlit
    try:
        subprocess.run([
            sys.executable, "-m", "streamlit", "run", dashboard_path,
            "--server.port", "8080",
            "--server.address", "localhost",
            "--server.headless", "false",
            "--server.fileWatcherType", "auto",
            "--browser.gatherUsageStats", "false"
        ], check=True)
    except subprocess.CalledProcessError as e:
        print(f"❌ Error launching dashboard: {e}")
    except KeyboardInterrupt:
        print("\n🛑 Dashboard stopped by user")

if __name__ == "__main__":
    print("=" * 60)
    print("🌍 Multi-Region E-commerce Recommendation System")
    print("📊 Interactive Dashboard")
    print("=" * 60)
    print()
    
    launch_dashboard()
