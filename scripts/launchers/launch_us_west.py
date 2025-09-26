#!/usr/bin/env python3
"""Launch US-West region"""

import os
import sys

# Set region
os.environ["REGION"] = "us-west-1"

# Add project to path
current_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, current_dir)

# Import and run
from app.minimal_main import app
import uvicorn

if __name__ == "__main__":
    print("🌴 Starting Multi-Region E-commerce Recommendation System")
    print("📍 Region: us-west-1")
    print("🌐 Server: http://localhost:8000")
    print("📖 Docs: http://localhost:8000/docs")
    print("❤️ Health: http://localhost:8000/api/v1/health/")
    
    uvicorn.run(app, host="0.0.0.0", port=8000, log_level="info")
