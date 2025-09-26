#!/usr/bin/env python3
"""
Setup script for Multi-Region E-commerce Project
"""

import subprocess
import sys
import os
from pathlib import Path

def check_docker():
    """Check if Docker is installed and running"""
    try:
        subprocess.run(["docker", "--version"], 
                      capture_output=True, check=True)
        print("✅ Docker is installed")
        
        # Check if Docker is running
        result = subprocess.run(["docker", "info"], 
                               capture_output=True, text=True)
        if result.returncode == 0:
            print("✅ Docker is running")
            return True
        else:
            print("❌ Docker is not running. Please start Docker Desktop.")
            return False
    except (subprocess.CalledProcessError, FileNotFoundError):
        print("❌ Docker is not installed.")
        print("   Please install Docker Desktop from: https://www.docker.com/products/docker-desktop/")
        return False

def install_requirements():
    """Install Python requirements"""
    try:
        print("📦 Installing Python dependencies...")
        subprocess.check_call([sys.executable, "-m", "pip", "install", "-r", "requirements.txt"])
        print("✅ Python dependencies installed")
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ Error installing dependencies: {e}")
        return False

def start_services():
    """Start Docker services"""
    try:
        print("🚀 Starting MinIO and database services...")
        subprocess.check_call(["docker-compose", "up", "-d"])
        print("✅ Services started successfully")
        print("\n📊 Access Information:")
        print("   MinIO Console: http://localhost:9001")
        print("   MinIO API: http://localhost:9000")
        print("   PostgreSQL: localhost:5432")
        print("   Redis: localhost:6379")
        print("\n🔑 Default Credentials:")
        print("   Username: admin")
        print("   Password: password123")
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ Error starting services: {e}")
        return False

def check_dataset():
    """Check if dataset is downloaded"""
    data_dir = Path("data/raw")
    expected_files = [
        "olist_orders_dataset.csv",
        "olist_customers_dataset.csv",
        "olist_products_dataset.csv"
    ]
    
    missing_files = []
    for file in expected_files:
        if not (data_dir / file).exists():
            missing_files.append(file)
    
    if missing_files:
        print("⚠️  Dataset not found!")
        print("   Please download from: https://www.kaggle.com/datasets/olistbr/brazilian-ecommerce")
        print(f"   Extract to: {data_dir.absolute()}")
        return False
    else:
        print("✅ Dataset files found")
        return True

def main():
    print("🚀 Multi-Region E-commerce Project Setup")
    print("=" * 50)
    
    # Check prerequisites
    if not check_docker():
        return False
    
    # Install requirements
    if not install_requirements():
        return False
    
    # Start services
    if not start_services():
        return False
    
    # Check dataset
    dataset_ready = check_dataset()
    
    print("\n" + "=" * 50)
    print("✅ Setup Complete!")
    print("\n📋 Next Steps:")
    
    if not dataset_ready:
        print("1. 📥 Download the Brazilian E-commerce dataset")
        print("   Go to: https://www.kaggle.com/datasets/olistbr/brazilian-ecommerce")
        print("   Extract to: data/raw/")
        print("2. 📊 Run data exploration:")
    else:
        print("1. 📊 Run data exploration:")
    
    print("   jupyter notebook notebooks/01_data_exploration.ipynb")
    print("3. 🌐 Access MinIO Console: http://localhost:9001")
    print("4. 📚 Read PHASE1_SETUP.md for detailed instructions")

if __name__ == "__main__":
    main()
