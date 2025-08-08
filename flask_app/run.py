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
    # Get dynamic port from env to avoid hardcoded 5000
    port = int(os.environ.get('FLASK_RUN_PORT', 5000))
    print("  Nigerian Customer Support Agent - Starting Flask Application")
    print("=" * 60)
    print(f"🌐 Local URL: http://localhost:{port}")
    print(f"📊 Dashboard: http://localhost:{port} (4 tabs available)")
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
        app.run(host="0.0.0.0", port=port, debug=True, threaded=True, use_reloader=False)

except ImportError as e:
    print(f"❌ Import Error: {e}")
    print("Make sure you're in the flask_app directory and have installed all dependencies:")
    print("pip install -r requirements.txt")
    sys.exit(1)
except Exception as e:
    print(f"❌ Error starting application: {e}")
    sys.exit(1)
