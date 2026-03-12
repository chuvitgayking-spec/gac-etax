#!/usr/bin/env python3
"""Restore script for GAC E-Tax project"""
import shutil
import sys
from datetime import datetime

def restore_last_stable():
    """Restore last stable backup"""
    timestamp = "20260312_2039"
    files = [
        ("app_backup_" + timestamp + ".py", "app.py"),
        ("database_backup_" + timestamp + ".py", "database.py"),
        ("requirements_backup_" + timestamp + ".txt", "requirements.txt"),
    ]
    
    for backup, target in files:
        src = f"backups/{backup}"
        try:
            shutil.copy(src, target)
            print(f"✅ Restored: {target}")
        except FileNotFoundError:
            print(f"❌ Not found: {src}")
    
    print("\n🔄 Restart Streamlit to apply changes!")

if __name__ == "__main__":
    restore_last_stable()
