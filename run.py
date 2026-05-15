"""
Qlockain — Startup Script
Run this file to start the application: python run.py
"""
from app import app, init_db

if __name__ == "__main__":
    print("\n" + "="*55)
    print("  ██████  ██      ██████  ██████ ██   ██  █████  ██ ███    ██")
    print("  QLOCKAIN — Blockchain Identity Vault")
    print("="*55)
    print("  Starting server...")
    init_db()
    print("  ✓ Database initialized")
    print("  ✓ Blockchain ready")
    print("  ✓ Admin account: admin / Admin@123")
    print("="*55)
    print("  → Open browser: http://localhost:5000")
    print("  → Admin panel:  http://localhost:5000/admin")
    print("  → Press Ctrl+C to stop")
    print("="*55 + "\n")
    app.run(debug=True, host="0.0.0.0", port=5000)
