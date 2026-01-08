#!/usr/bin/env python3
"""
Simple script to check database contents
"""

import sqlite3
from pathlib import Path

def check_database():
    """Check database file and contents"""
    db_path = Path(__file__).parent / "backend" / "materials_explorer.db"
    
    if not db_path.exists():
        print(f"❌ Database file not found at {db_path}")
        return
    
    print(f"✅ Database file found at {db_path}")
    print(f"   File size: {db_path.stat().st_size / 1024:.1f} KB")
    
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # List all tables
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
        tables = [row[0] for row in cursor.fetchall()]
        print(f"\n📋 Tables in database: {len(tables)}")
        for table in tables:
            cursor.execute(f"SELECT COUNT(*) FROM {table}")
            count = cursor.fetchone()[0]
            print(f"   - {table}: {count} records")
        
        # Show sample materials
        if "materials" in tables:
            print(f"\n🧪 Sample materials:")
            cursor.execute("SELECT material_id, formula, spacegroup_number FROM materials LIMIT 10")
            for row in cursor.fetchall():
                print(f"   - {row[0]}: {row[1]} (spacegroup {row[2]})")
        
        conn.close()
        print("\n✅ Database check completed successfully")
        
    except Exception as e:
        print(f"❌ Database error: {e}")

if __name__ == "__main__":
    check_database()