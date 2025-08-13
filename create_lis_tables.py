#!/usr/bin/env python3
"""
Script to create LIS tables directly in the database
"""

import sys
import os
from sqlalchemy import text

# Add the app directory to the Python path
sys.path.append(os.path.join(os.path.dirname(__file__), 'app'))

from app.core.database import engine, Base
from app.model.lis import LISPrompt, LISInteraction, LISAnalytics, LISLocationData, LISUserPreference

def create_lis_tables():
    """Create LIS tables in the database"""
    try:
        print("🔧 Creating LIS tables...")
        
        # Create all tables
        Base.metadata.create_all(bind=engine, tables=[
            LISPrompt.__table__,
            LISInteraction.__table__,
            LISAnalytics.__table__,
            LISLocationData.__table__,
            LISUserPreference.__table__
        ])
        
        print("✅ LIS tables created successfully!")
        
        # Verify tables exist
        with engine.connect() as conn:
            result = conn.execute(text("""
                SELECT table_name 
                FROM information_schema.tables 
                WHERE table_schema = 'public' 
                AND table_name LIKE 'lis_%'
                ORDER BY table_name
            """))
            
            tables = [row[0] for row in result]
            print(f"📋 LIS tables in database: {tables}")
            
            if len(tables) == 5:
                print("✅ All 5 LIS tables created successfully!")
            else:
                print(f"⚠️  Expected 5 tables, found {len(tables)}")
                
    except Exception as e:
        print(f"❌ Error creating LIS tables: {e}")
        raise

if __name__ == "__main__":
    create_lis_tables() 