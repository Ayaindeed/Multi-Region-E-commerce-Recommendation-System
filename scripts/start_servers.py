#!/usr/bin/env python3
"""
Multi-Region E-commerce Recommendation System Startup Script
"""

import os
import sys
import subprocess
import time
import argparse
from pathlib import Path

# Add the project root to Python path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

def check_dependencies():
    """Check if all required services are running."""
    print("🔍 Checking dependencies...")
    
    # Check if Docker services are running
    try:
        result = subprocess.run(['docker', 'ps'], capture_output=True, text=True)
        if result.returncode != 0:
            print("❌ Docker is not running. Please start Docker first.")
            return False
        
        # Check for required containers
        required_services = ['minio', 'postgres', 'redis']
        running_services = result.stdout.lower()
        
        for service in required_services:
            if service not in running_services:
                print(f"❌ {service} container is not running. Please run 'docker-compose up -d' first.")
                return False
        
        print("✅ All required services are running")
        return True
        
    except FileNotFoundError:
        print("❌ Docker is not installed or not in PATH")
        return False

def install_dependencies():
    """Install Python dependencies."""
    print("📦 Installing Python dependencies...")
    try:
        subprocess.run([sys.executable, '-m', 'pip', 'install', '-r', 'requirements.txt'], 
                      check=True)
        print("✅ Dependencies installed successfully")
    except subprocess.CalledProcessError as e:
        print(f"❌ Failed to install dependencies: {e}")
        return False
    return True

def start_region_server(region: str, port: int):
    """Start FastAPI server for a specific region."""
    print(f"🚀 Starting {region} server on port {port}")
    
    # Set environment variables
    env = os.environ.copy()
    env['REGION'] = region
    
    # Start the server
    cmd = [
        sys.executable, '-m', 'uvicorn',
        'app.main:app',
        '--host', '0.0.0.0',
        '--port', str(port),
        '--reload' if '--debug' in sys.argv else '--no-reload'
    ]
    
    try:
        return subprocess.Popen(cmd, env=env)
    except Exception as e:
        print(f"❌ Failed to start {region} server: {e}")
        return None

def main():
    """Main startup function."""
    parser = argparse.ArgumentParser(description='Start Multi-Region Recommendation System')
    parser.add_argument('--region', default='us-east-1', 
                       choices=['us-east-1', 'us-west-1', 'eu-west-1', 'ap-south-1'],
                       help='Region to start (default: us-east-1)')
    parser.add_argument('--all-regions', action='store_true',
                       help='Start all regions on different ports')
    parser.add_argument('--skip-checks', action='store_true',
                       help='Skip dependency checks')
    parser.add_argument('--debug', action='store_true',
                       help='Run in debug mode with auto-reload')
    
    args = parser.parse_args()
    
    print("🌟 Multi-Region E-commerce Recommendation System")
    print("=" * 50)
    
    # Check dependencies
    if not args.skip_checks:
        if not check_dependencies():
            print("💡 Please ensure Docker services are running: docker-compose up -d")
            return 1
        
        if not install_dependencies():
            return 1
    
    # Region to port mapping
    region_ports = {
        'us-east-1': 8000,
        'us-west-1': 8001,
        'eu-west-1': 8002,
        'ap-south-1': 8003
    }
    
    processes = []
    
    try:
        if args.all_regions:
            # Start all regions
            print("🌍 Starting all regions...")
            for region, port in region_ports.items():
                process = start_region_server(region, port)
                if process:
                    processes.append((region, port, process))
                    time.sleep(2)  # Stagger startup
            
            print("\n🎉 All regions started successfully!")
            print("\n📍 Region Endpoints:")
            for region, port, _ in processes:
                print(f"  • {region}: http://localhost:{port}")
                print(f"    - API Docs: http://localhost:{port}/docs")
                print(f"    - Health: http://localhost:{port}/api/v1/health")
            
        else:
            # Start single region
            port = region_ports[args.region]
            process = start_region_server(args.region, port)
            if process:
                processes.append((args.region, port, process))
                
                print(f"\n🎉 {args.region} server started successfully!")
                print(f"\n📍 Endpoints:")
                print(f"  • API: http://localhost:{port}")
                print(f"  • Docs: http://localhost:{port}/docs")
                print(f"  • Health: http://localhost:{port}/api/v1/health")
        
        if processes:
            print(f"\n⏸️  Press Ctrl+C to stop all servers")
            
            # Wait for processes
            while True:
                time.sleep(1)
                # Check if any process died
                for region, port, process in processes:
                    if process.poll() is not None:
                        print(f"❌ {region} server (port {port}) stopped unexpectedly")
                        return 1
        
    except KeyboardInterrupt:
        print("\n🛑 Stopping all servers...")
        for region, port, process in processes:
            print(f"Stopping {region} server (port {port})")
            process.terminate()
            try:
                process.wait(timeout=5)
            except subprocess.TimeoutExpired:
                process.kill()
        print("✅ All servers stopped")
    
    return 0

if __name__ == '__main__':
    sys.exit(main())
