"""
Complete Demo Launcher - Start All Regions + Dashboard
This script launches the complete multi-region system with dashboard
"""

import subprocess
import sys
import os
import time
import threading
import signal
import webbrowser
from concurrent.futures import ThreadPoolExecutor

class MultiRegionDemo:
    def __init__(self):
        self.processes = []
        self.dashboard_process = None
        self.current_dir = os.path.dirname(os.path.abspath(__file__))
        
    def signal_handler(self, sig, frame):
        """Handle Ctrl+C gracefully"""
        print("\n🛑 Shutting down all services...")
        self.shutdown()
        sys.exit(0)
        
    def launch_region(self, script_name, region_name, port):
        """Launch a single region"""
        try:
            script_path = os.path.join(self.current_dir, script_name)
            if os.path.exists(script_path):
                print(f"🚀 Starting {region_name} on port {port}...")
                process = subprocess.Popen(
                    [sys.executable, script_path],
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE
                )
                self.processes.append((process, region_name))
                return True
            else:
                print(f"❌ Script not found: {script_path}")
                return False
        except Exception as e:
            print(f"❌ Error starting {region_name}: {e}")
            return False
    
    def launch_dashboard(self):
        """Launch the dashboard after a delay"""
        time.sleep(8)  # Wait for APIs to start
        
        try:
            dashboard_path = os.path.join(self.current_dir, "dashboard.py")
            if os.path.exists(dashboard_path):
                print("📊 Starting Dashboard...")
                self.dashboard_process = subprocess.Popen(
                    [sys.executable, "-m", "streamlit", "run", dashboard_path,
                     "--server.port", "8080",
                     "--server.address", "localhost",
                     "--server.headless", "false",
                     "--browser.gatherUsageStats", "false"],
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE
                )
                
                # Wait a bit more then open browser
                time.sleep(3)
                print("🌐 Opening dashboard in browser...")
                webbrowser.open("http://localhost:8080")
                
            else:
                print("❌ Dashboard not found")
        except Exception as e:
            print(f"❌ Error starting dashboard: {e}")
    
    def check_processes(self):
        """Monitor process health"""
        while True:
            time.sleep(30)  # Check every 30 seconds
            
            # Check API processes
            for i, (process, region_name) in enumerate(self.processes):
                if process.poll() is not None:
                    print(f"⚠️  {region_name} has stopped (exit code: {process.poll()})")
            
            # Check dashboard
            if self.dashboard_process and self.dashboard_process.poll() is not None:
                print(f"⚠️  Dashboard has stopped (exit code: {self.dashboard_process.poll()})")
    
    def shutdown(self):
        """Shutdown all processes"""
        print("🔄 Terminating API processes...")
        for process, region_name in self.processes:
            try:
                process.terminate()
                process.wait(timeout=5)
                print(f"✅ {region_name} stopped")
            except subprocess.TimeoutExpired:
                process.kill()
                print(f"🔥 {region_name} force stopped")
            except Exception as e:
                print(f"⚠️  Error stopping {region_name}: {e}")
        
        if self.dashboard_process:
            try:
                self.dashboard_process.terminate()
                self.dashboard_process.wait(timeout=5)
                print("✅ Dashboard stopped")
            except subprocess.TimeoutExpired:
                self.dashboard_process.kill()
                print("🔥 Dashboard force stopped")
            except Exception as e:
                print(f"⚠️  Error stopping dashboard: {e}")
    
    def run(self):
        """Run the complete demo"""
        # Set up signal handler
        signal.signal(signal.SIGINT, self.signal_handler)
        
        print("=" * 70)
        print("🌍 Multi-Region E-commerce Recommendation System")
        print("🚀 Complete Demo Launcher")
        print("=" * 70)
        print()
        
        # Region configurations
        regions = [
            ("launch_demo.py", "US-West", "8000"),
            ("launch_eu_west.py", "EU-West", "8002"),
            ("launch_ap_south.py", "AP-South", "8003")
        ]
        
        # Start regions
        print("📡 Starting API regions...")
        successful_launches = 0
        
        for script, region, port in regions:
            if self.launch_region(script, region, port):
                successful_launches += 1
                time.sleep(2)  # Small delay between launches
        
        if successful_launches == 0:
            print("❌ No regions could be started. Exiting.")
            return
        
        print(f"✅ {successful_launches}/{len(regions)} regions started")
        print()
        
        # Start dashboard in background thread
        dashboard_thread = threading.Thread(target=self.launch_dashboard)
        dashboard_thread.daemon = True
        dashboard_thread.start()
        
        # Start health monitoring
        monitor_thread = threading.Thread(target=self.check_processes)
        monitor_thread.daemon = True
        monitor_thread.start()
        
        print("🎯 System Status:")
        print("   📡 API Regions: Starting up...")
        print("   📊 Dashboard: Will launch in ~8 seconds")
        print("   🌐 Browser: Will open automatically")
        print()
        print("🔗 Quick Access URLs:")
        print("   📊 Dashboard: http://localhost:8080")
        print("   🌴 US-West API: http://localhost:8000")
        print("   🇪🇺 EU-West API: http://localhost:8002") 
        print("   🌏 AP-South API: http://localhost:8003")
        print()
        print("💡 Tips:")
        print("   • The dashboard will show real-time region health")
        print("   • Test recommendations with any user ID")
        print("   • Compare performance across regions")
        print("   • Check the API docs at /docs endpoint")
        print()
        print("⌨️  Press Ctrl+C to stop all services")
        print("=" * 70)
        
        # Keep main thread alive
        try:
            while True:
                time.sleep(1)
        except KeyboardInterrupt:
            pass

def main():
    demo = MultiRegionDemo()
    demo.run()

if __name__ == "__main__":
    main()
