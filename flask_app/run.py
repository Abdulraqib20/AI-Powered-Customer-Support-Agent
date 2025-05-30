#!/usr/bin/env python3
"""
Nigerian E-commerce Customer Support Agent - Application Runner
Simple script to start the Flask application with optimal settings
"""

import os
import sys
from pathlib import Path

# Add the parent directory to Python path for imports
sys.path.append(str(Path(__file__).parent.parent.resolve()))

try:
    from app import app
    print("  Nigerian Customer Support Agent - Starting Flask Application")
    print("=" * 60)
    print("🌐 Local URL: http://localhost:5000")
    print("📊 Dashboard: http://localhost:5000 (4 tabs available)")
    print("🤖 AI Chat: Navigate to 'Unified Support' tab")
    print("👥 Customers: Navigate to 'Customer Profiles' tab")
    print("📈 Analytics: Navigate to 'Usage Analytics' tab")
    print("💼 Business: Navigate to 'Support Dashboard' tab")
    print("=" * 60)
    print("💡 Example queries to try in AI chat:")
    print("   • 'Show customers from Lagos'")
    print("   • 'What are the pending orders?'")
    print("   • 'Show revenue by state'")
    print("   • 'Help resolve payment issues'")
    print("=" * 60)

    if __name__ == "__main__":
        # Run the Flask application
        app.run(
            host="0.0.0.0",
            port=5000,
            debug=True,
            threaded=True
        )

except ImportError as e:
    print(f"❌ Import Error: {e}")
    print("Make sure you're in the flask_app directory and have installed all dependencies:")
    print("pip install -r requirements.txt")
    sys.exit(1)
except Exception as e:
    print(f"❌ Error starting application: {e}")
    sys.exit(1)
